"""OpenAI-compatible code reviewer for various providers."""

from typing import Any

from loguru import logger
from tqdm import tqdm

from src.config import Config
from src.parsers.diff_parser import DiffParser
from src.reviewers.base_reviewer import BaseReviewer
from src.utils.openai_like_client import OpenAILikeClient


class OpenAILikeReviewer(BaseReviewer):
    """Code reviewer using OpenAI-compatible API with multiple provider support."""

    def __init__(self, merge_request_data: dict[str, Any], client: OpenAILikeClient | None = None):
        """Initialize OpenAI-compatible reviewer.

        Args:
            merge_request_data: Merge request data
            client: Optional OpenAI-compatible client instance
        """
        super().__init__(merge_request_data)
        self.enable_ai = bool(Config.OPENAI_LIKE_API_KEY)
        self._client = client or (OpenAILikeClient() if self.enable_ai else None)
        self._diff_parser = DiffParser()

    def get_review_comments(self) -> dict[str, Any]:
        """Get review comments from OpenAI-compatible models.

        Returns:
            Dictionary with review results
        """
        if not self.enable_ai or not self._client:
            return {"diff_comments": [], "summary": "", "file_reviews": []}

        enhanced_changes = self.merge_request_data.get("enhanced_changes", [])
        if enhanced_changes:
            file_reviews = []
            all_comments = []

            logger.info(f"Starting AI analysis of {len(enhanced_changes)} files...")

            with tqdm(total=len(enhanced_changes), desc="Analyzing files", unit="file") as pbar:
                for change in enhanced_changes:
                    file_path = change["file_path"]
                    pbar.set_description(f"Analyzing: {file_path.split('/')[-1]}")
                    diff = change["diff"]
                    new_content = change["new_content"]

                    context_parts = []

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
                            "Используй полный файл только для понимания контекста."
                        )

                    full_context = "\n".join(context_parts)

                    try:
                        file_comments = self._client.review_diffs(full_context)
                        if file_comments.strip() and "Код выглядит корректно" not in file_comments:
                            file_reviews.append(
                                {
                                    "file": file_path,
                                    "diff": diff,
                                    "comments": file_comments.strip(),
                                    "new_content": new_content,
                                    "change_type": "new"
                                    if change["new_file"]
                                    else "deleted"
                                    if change["deleted_file"]
                                    else "modified",
                                }
                            )
                            all_comments.append(file_comments)
                            logger.debug(f"Found comments for {file_path}")
                    except Exception as e:
                        logger.error(f"File analysis error for {file_path}: {e}")
                    finally:
                        pbar.update(1)

            logger.info("Building overall summary...")
            try:
                if all_comments:
                    summary = self._client.global_summary("\n".join(all_comments))
                else:
                    summary = "Серьёзных проблем в коде не обнаружено."
            except Exception as exc:
                logger.debug(f"Summary build error: {exc}")
                summary = ""

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
                if file_comments.strip() and "Код выглядит корректно" not in file_comments:
                    file_reviews.append({"file": file_name, "diff": file_diff, "comments": file_comments.strip()})
                    all_comments.append(file_comments)
            except Exception as exc:
                logger.debug(f"File analysis error for {file_name}: {exc}")

        try:
            if all_comments:
                summary = self._client.global_summary("\n".join(all_comments))
            else:
                summary = "Серьёзных проблем в коде не обнаружено."
        except Exception as exc:
            logger.debug(f"Summary generation error: {exc}")
            summary = ""

        return {
            "diff_comments": [],
            "summary": summary,
            "file_reviews": file_reviews,
        }

    def is_available(self) -> bool:
        """Check if OpenAI-compatible reviewer is available.

        Returns:
            True if API key is configured and client is ready
        """
        return self.enable_ai and self._client is not None and self._client.is_available()

    @property
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name with model info
        """
        if self._client:
            return self._client.provider_name
        return "OpenAI-Like (unavailable)"
