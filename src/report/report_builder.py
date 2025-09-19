from typing import Any


class ReportBuilder:
    """Builds markdown report from simplified merge request data."""

    def __init__(self):
        pass

    def _format_author(self, author_data: Any) -> str:
        """Format author information for display."""
        if isinstance(author_data, dict):
            login = author_data.get("login", "")
            html_url = author_data.get("html_url", "")

            name = author_data.get("name", "")
            username = author_data.get("username", "")
            web_url = author_data.get("web_url", "")

            if login:
                if html_url:
                    return f"[@{login}]({html_url})"
                return f"@{login}"

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

        web_url = data.get("web_url", data.get("html_url", ""))
        mr_id = data.get("mr_id", data.get("number", data.get("id", "")))

        # Prefer richer author info if available (e.g., GitHub provides `user` with html_url)
        author_info = self._format_author(author_data)
        if isinstance(author_data, str):
            gh_user = data.get("user")
            if isinstance(gh_user, dict):
                enriched = self._format_author(gh_user)
                if enriched and enriched != "Unknown":
                    author_info = enriched

        lines = [f"## 📝 Название: {title}"]
        lines.append(f"## 👤 Автор: {author_info}")

        if web_url and mr_id:
            lines.append(f"## 🔗 Merge Request: [#{mr_id}]({web_url})")
        else:
            if web_url:
                lines.append(f"## 🔗 Link: [View PR/MR]({web_url})")

        description = data.get("description", "")
        if description and description.strip():
            lines.append("## 📋 Описание:")
            lines.append(description.strip())

        if ai_summary:
            lines.append("\n## Результат ревью")
            lines.append(ai_summary.strip())

        if file_reviews:
            lines.append("\n## Детальный анализ изменений")
            for i, review in enumerate(file_reviews, 1):
                file_name = review.get("file", "unknown")
                diff = review.get("diff", "")
                comments = review.get("comments", "")
                change_type = review.get("change_type", "modified")
                new_content = review.get("new_content", "")

                lines.append(f"\n### {i}. `{file_name}`")

                if change_type == "new":
                    lines.append("Новый файл")
                elif change_type == "deleted":
                    lines.append("Удалённый файл")
                else:
                    lines.append("Изменённый файл")

                lines.append("\nИзменения:")
                lines.append("```diff")
                lines.append(diff)
                lines.append("```")

                if change_type == "new" and new_content and len(new_content) < 2000:
                    lines.append("\nПолное содержимое файла:")
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

                if comments:
                    lines.append("\nАнализ:")
                    lines.append(comments)

                lines.append("\n---")
        else:
            lines.append("\n### Changes:")
            if not changes:
                lines.append("No changes detected.")
            else:
                lines.extend(f"- {c.get('file')}: {c.get('status')}" for c in changes)

            if ai_diff_comments:
                lines.append("\n### Детальные замечания по изменениям:")
                lines.extend(f"- {c}" for c in ai_diff_comments)

        return "\n".join(lines) + "\n"
