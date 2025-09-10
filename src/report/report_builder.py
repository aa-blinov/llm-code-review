from typing import Any


class ReportBuilder:
    """Builds markdown report from simplified merge request data."""

    def __init__(self):
        pass

    def _format_author(self, author_data: Any) -> str:
        """Format author information for display."""
        if isinstance(author_data, dict):
            # GitLab format
            name = author_data.get("name", "")
            username = author_data.get("username", "")
            web_url = author_data.get("web_url", "")

            # Build author string
            if name and username:
                if web_url:
                    return f"**{name}** ([@{username}]({web_url}))"
                return f"**{name}** (@{username})"
            if username:
                if web_url:
                    return f"[@{username}]({web_url})"
                return f"@{username}"
            if name:
                return f"**{name}**"
            return "Unknown"
        if isinstance(author_data, str):
            return author_data
        return str(author_data)

    def generate_report(self, data: dict[str, Any]) -> str:
        title = data.get("title") or "No Title"
        author_data = data.get("author") or "Unknown"
        changes: list[dict[str, Any]] = data.get("changes") or []
        ai_diff_comments: list[str] = data.get("ai_diff_comments") or []
        ai_summary: str = data.get("ai_summary") or ""
        file_reviews: list[dict[str, Any]] = data.get("file_reviews") or []

        # Format author information nicely
        author_info = self._format_author(author_data)

        lines = [f"# {title}", f"## 👤 Автор: {author_info}"]

        # Add review summary at the top if we have AI analysis
        if ai_summary:
            lines.append("\n## 🎯 Результат ревью")
            lines.append(ai_summary.strip())

        # Show file reviews with diffs and comments
        if file_reviews:
            lines.append("\n## 📋 Детальный анализ изменений")
            for i, review in enumerate(file_reviews, 1):
                file_name = review.get("file", "unknown")
                diff = review.get("diff", "")
                comments = review.get("comments", "")
                change_type = review.get("change_type", "modified")
                new_content = review.get("new_content", "")

                lines.append(f"\n### {i}. 📁 `{file_name}`")

                # Show change type
                if change_type == "new":
                    lines.append("**🆕 Новый файл**")
                elif change_type == "deleted":
                    lines.append("**🗑️ Удалённый файл**")
                else:
                    lines.append("**📝 Изменённый файл**")

                # Show diff in code block
                lines.append("\n**Изменения:**")
                lines.append("```diff")
                lines.append(diff)
                lines.append("```")

                # Show full content for small files or new files
                if change_type == "new" and new_content and len(new_content) < 2000:
                    lines.append("\n**Полное содержимое файла:**")
                    # Detect file extension for syntax highlighting
                    ext = file_name.split(".")[-1] if "." in file_name else ""
                    lang_map = {
                        "ts": "typescript",
                        "js": "javascript",
                        "tsx": "tsx",
                        "jsx": "jsx",
                        "py": "python",
                        "go": "go",
                        "java": "java",
                        "cpp": "cpp",
                        "c": "c",
                        "css": "css",
                        "scss": "scss",
                        "html": "html",
                        "xml": "xml",
                        "json": "json",
                        "yaml": "yaml",
                        "yml": "yaml",
                        "md": "markdown",
                        "sql": "sql",
                        "sh": "bash",
                        "dockerfile": "dockerfile",
                    }
                    syntax = lang_map.get(ext.lower(), ext.lower())
                    lines.append(f"```{syntax}")
                    lines.append(new_content)
                    lines.append("```")

                # Show AI comments
                if comments:
                    lines.append("\n**💭 Анализ:**")
                    lines.append(comments)

                lines.append("\n---")
        else:
            # Fallback to old format
            lines.append("\n### Changes:")
            if not changes:
                lines.append("No changes detected.")
            else:
                lines.extend(f"- {c.get('file')}: {c.get('status')}" for c in changes)

            if ai_diff_comments:
                lines.append("\n### Детальные замечания по изменениям:")
                lines.extend(f"- {c}" for c in ai_diff_comments)

        return "\n".join(lines) + "\n"
