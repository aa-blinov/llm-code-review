from typing import Any

from src.config import Config
from src.parsers.diff_parser import DiffParser
from src.utils.gemini_client import GeminiClient


class GeminiReviewer:
    """Stub reviewer that would call Gemini model in future.

    For now it produces a simplified structure used by ReportBuilder.
    """

    def __init__(self, merge_request_data: dict[str, Any], client: GeminiClient | None = None):
        self.merge_request_data = merge_request_data
        self._processed: dict[str, Any] = {}
        self.enable_ai = bool(Config.GEMINI_API_KEY)
        self._client = client or (GeminiClient() if self.enable_ai else None)
        self._diff_parser = DiffParser()

    def process_merge_request(self) -> None:
        # Placeholder processing logic; could analyze diffs, complexity, etc.
        self._processed = {
            "title": self.merge_request_data.get("title"),
            "author": self.merge_request_data.get("author") or self.merge_request_data.get("user", {}).get("login"),
            "changes": self.merge_request_data.get("changes", []),
            "diffs": self.merge_request_data.get("diffs", ""),
        }

    def generate_report_data(self) -> dict[str, Any]:
        if not self._processed:
            self.process_merge_request()
        return self._processed

    def get_review_comments(self) -> dict[str, Any]:
        if not self.enable_ai or not self._client:
            return {"diff_comments": [], "summary": "", "file_reviews": []}

        # Use enhanced changes with full file content if available
        enhanced_changes = self.merge_request_data.get("enhanced_changes", [])
        if enhanced_changes:
            file_reviews = []
            all_comments = []

            print(f"🔍 AI анализ {len(enhanced_changes)} файлов...")

            # Analyze each file with optimized context
            for i, change in enumerate(enhanced_changes, 1):
                file_path = change["file_path"]
                diff = change["diff"]
                new_content = change["new_content"]

                print(f"🤖 [{i}/{len(enhanced_changes)}] {file_path}")

                # Create optimized context for AI analysis
                context_parts = []

                if change["new_file"]:
                    context_parts.append(f"📄 **Новый файл**: `{file_path}`")
                    if new_content:
                        context_parts.append(f"\n**Содержимое нового файла:**\n```\n{new_content}\n```")
                elif change["deleted_file"]:
                    context_parts.append(f"🗑️ **Удаленный файл**: `{file_path}`")
                    # For deleted files, we might still want to show what was deleted via diff
                    context_parts.append(f"\n**Diff удаления:**\n```diff\n{diff}\n```")
                else:
                    context_parts.append(f"📝 **Изменённый файл**: `{file_path}`")

                    if new_content:
                        context_parts.append(
                            f"\n**Текущее состояние файла (ПОСЛЕ изменений):**\n```\n{new_content}\n```"
                        )

                    context_parts.append(f"\n**Конкретные изменения (что поменялось):**\n```diff\n{diff}\n```")
                    context_parts.append(
                        "\n**ВАЖНО**: Анализируй только изменения, показанные в diff выше. Используй полный файл только для понимания контекста."
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
                        print(f"✅ Найдены замечания для {file_path}")
                    else:
                        print(f"✅ Файл {file_path} - замечаний нет")
                except Exception as e:
                    print(f"❌ Ошибка анализа файла {file_path}: {e}")

            # Generate global summary
            print("📝 Формирование общего резюме...")
            try:
                if all_comments:
                    summary = self._client.global_summary("\n".join(all_comments))
                else:
                    summary = "Серьёзных проблем в коде не обнаружено."
            except Exception:
                summary = ""

            return {
                "diff_comments": [],  # Keep for compatibility
                "summary": summary,
                "file_reviews": file_reviews,
            }

        # Fallback to old logic if enhanced_changes not available
        diffs = self.merge_request_data.get("diffs", "")
        if not diffs:
            # Fallback to change list format
            diff_list = [f"{c.get('file')}:{c.get('status')}" for c in self._processed.get("changes", [])]
            diff_block = "\n".join(diff_list) if diff_list else "Нет явных изменений"

            try:
                raw_comments = self._client.review_diffs(diff_block)
                diff_comments = [ln.strip("- ").strip() for ln in raw_comments.splitlines() if ln.strip()]
            except Exception:
                diff_comments = []

            return {"diff_comments": diff_comments[:12], "summary": "", "file_reviews": []}

        # Extract file chunks from diff (old logic)
        file_chunks = self._diff_parser.extract_file_chunks(diffs)
        file_reviews = []
        all_comments = []

        # Analyze each file separately
        for chunk in file_chunks:
            file_name = chunk["file"]
            file_diff = chunk["diff"]

            try:
                file_comments = self._client.review_diffs(file_diff)
                if file_comments.strip() and "Код выглядит корректно" not in file_comments:
                    file_reviews.append({"file": file_name, "diff": file_diff, "comments": file_comments.strip()})
                    all_comments.append(file_comments)
            except Exception:
                pass

        # Generate global summary
        try:
            if all_comments:
                summary = self._client.global_summary("\n".join(all_comments))
            else:
                summary = "Серьёзных проблем в коде не обнаружено."
        except Exception:
            summary = ""

        return {
            "diff_comments": [],  # Keep for compatibility
            "summary": summary,
            "file_reviews": file_reviews,
        }
