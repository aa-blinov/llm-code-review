from typing import Any

from loguru import logger
from tqdm import tqdm

from src.config import Config
from src.parsers.diff_parser import DiffParser
from src.reviewers.base_reviewer import BaseReviewer
from src.utils.cross_file_context import (
    build_cross_file_section,
    build_pr_map,
    find_related_changes,
)
from src.utils.gemini_client import GeminiClient


class GeminiReviewer(BaseReviewer):
    """Reviewer that uses Gemini AI to analyze merge requests."""

    def __init__(self, merge_request_data: dict[str, Any], client: GeminiClient | None = None):
        """Initialize Gemini reviewer.

        Args:
            merge_request_data: Merge request data
            client: Optional Gemini client instance
        """
        super().__init__(merge_request_data)
        self.enable_ai = bool(Config.GEMINI_API_KEY)
        self._client = client or (GeminiClient() if self.enable_ai else None)
        self._diff_parser = DiffParser()

    def get_review_comments(self) -> dict[str, Any]:
        if not self.enable_ai or not self._client:
            return {"diff_comments": [], "summary": "", "file_reviews": []}

        enhanced_changes = self.merge_request_data.get("enhanced_changes", [])
        if enhanced_changes:
            file_reviews = []
            all_comments = []

            logger.info(f"Starting AI analysis of {len(enhanced_changes)} files...")

            # Build a PR-level map once — shared context across all file reviews
            pr_map = build_pr_map(
                enhanced_changes,
                pr_title=self.merge_request_data.get("title", ""),
                pr_description=self.merge_request_data.get("description", ""),
            )

            with tqdm(total=len(enhanced_changes), desc="Analyzing files", unit="file") as pbar:
                for change in enhanced_changes:
                    file_path = change["file_path"]
                    pbar.set_description(f"Analyzing: {file_path.split('/')[-1]}")
                    diff = change["diff"]
                    new_content = change["new_content"]
                    context_parts = []

                    # --- PR-level map (gives the LLM a bird's-eye view) ---
                    if len(enhanced_changes) > 1 and pr_map:
                        context_parts.append(pr_map)

                    if change["new_file"]:
                        context_parts.append(f"Новый файл: `{file_path}`")
                        if new_content:
                            context_parts.append(f"\nСодержимое нового файла:\n```\n{new_content}\n```")
                    elif change["deleted_file"]:
                        context_parts.append(f"Удаленный файл: `{file_path}`")
                        context_parts.append(f"\nDiff удаления:\n```diff\n{diff}\n```")
                    else:
                        context_parts.append(f"Изменённый файл: `{file_path}`")

                        if new_content:
                            context_parts.append(
                                f"\nТекущее состояние файла (ПОСЛЕ изменений):\n```\n{new_content}\n```"
                            )

                        context_parts.append(f"\nКонкретные изменения (что поменялось):\n```diff\n{diff}\n```")
                        context_parts.append(
                            "\nВАЖНО: Анализируй только изменения, показанные в diff выше. "
                            "Считай '-' как было ДО, '+' как стало ПОСЛЕ и оценивай пару '-'→'+'. "
                            "Если '+' исправляет недочёт из '-', не отмечай это как проблему. "
                            "Не предлагай те же изменения повторно — они уже применены. "
                            "Используй полный файл только для понимания контекста."
                        )

                    # --- Cross-file context (imports / dependents within this PR) ---
                    deps, dependents = find_related_changes(file_path, new_content, enhanced_changes)
                    cross_ctx = build_cross_file_section(deps, dependents)
                    if cross_ctx:
                        context_parts.append(cross_ctx)

                    full_context = "\n".join(context_parts)

                    try:
                        file_comments = self._client.review_diffs(full_context)
                        comments_text = (file_comments or "").strip()
                        if "Код выглядит корректно" in comments_text:
                            comments_text = ""

                        review_entry = {
                            "file": file_path,
                            "diff": diff,
                            "comments": comments_text,
                            "new_content": new_content,
                            "change_type": "new"
                            if change["new_file"]
                            else "deleted"
                            if change["deleted_file"]
                            else "modified",
                        }
                        file_reviews.append(review_entry)
                        if comments_text:
                            all_comments.append(comments_text)
                    except Exception as e:
                        logger.error(f"File analysis error for {file_path}: {e}")
                    finally:
                        pbar.update(1)

            logger.info("Building overall summary...")
            try:
                if all_comments:
                    summary = self._client.global_summary("\n".join(all_comments), self.merge_request_data)
                else:
                    summary = "Проблем в коде не обнаружено."
            except Exception as exc:
                logger.debug(f"Summary build error: {exc}")
                summary = ""

            # --- Holistic cross-file pass (catches issues invisible per-file) ---
            if len(enhanced_changes) > 1:
                logger.info("Running holistic cross-file analysis...")
                try:
                    holistic = self._client.holistic_review(
                        enhanced_changes,
                        pr_title=self.merge_request_data.get("title", ""),
                    )
                    if holistic and "Межмодульных проблем не обнаружено" not in holistic:
                        summary = (
                            f"### Межмодульный анализ\n{holistic}\n\n---\n\n{summary}"
                            if summary
                            else f"### Межмодульный анализ\n{holistic}"
                        )
                except Exception as exc:
                    logger.debug(f"Holistic review error: {exc}")

            return {
                "diff_comments": [],
                "summary": summary,
                "file_reviews": file_reviews,
            }

        diffs = self.merge_request_data.get("diffs", "")
        if not diffs:
            diff_list = [f"{c.get('file')}:{c.get('status')}" for c in self._processed.get("changes", [])]
            diff_block = "\n".join(diff_list) if diff_list else "Нет явных изменений"

            try:
                raw_comments = self._client.review_diffs(diff_block)
                diff_comments = [ln.strip("- ").strip() for ln in raw_comments.splitlines() if ln.strip()]
            except Exception as exc:
                logger.debug(f"diff_comments generation error: {exc}")
                diff_comments = []

            return {"diff_comments": diff_comments[:12], "summary": "", "file_reviews": []}

        file_chunks = self._diff_parser.extract_file_chunks(diffs)
        file_reviews = []
        all_comments = []

        for chunk in file_chunks:
            file_name = chunk["file"]
            file_diff = chunk["diff"]

            try:
                file_comments = self._client.review_diffs(file_diff)
                comments_text = (file_comments or "").strip()
                if "Код выглядит корректно" in comments_text:
                    comments_text = ""
                file_reviews.append({"file": file_name, "diff": file_diff, "comments": comments_text})
                if comments_text:
                    all_comments.append(comments_text)
            except Exception as exc:
                logger.debug(f"File analysis error for {file_name}: {exc}")

        try:
            if all_comments:
                summary = self._client.global_summary("\n".join(all_comments), self.merge_request_data)
            else:
                summary = "Проблем в коде не обнаружено."
        except Exception as exc:
            logger.debug(f"Summary generation error: {exc}")
            summary = ""

        return {
            "diff_comments": [],
            "summary": summary,
            "file_reviews": file_reviews,
        }

    def is_available(self) -> bool:
        """Check if Gemini reviewer is available.

        Returns:
            True if API key is configured and client is ready
        """
        return self.enable_ai and self._client is not None

    @property
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name with model info
        """
        if self._client:
            return f"Gemini ({self._client.model})"
        return "Gemini (unavailable)"

    def get_usage(self) -> dict[str, int]:
        """Return token usage collected by the underlying client."""
        if self._client:
            return self._client.get_usage()
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
