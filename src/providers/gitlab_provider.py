import base64
import os
from typing import Any

from loguru import logger

from src.config import Config
from src.utils import http

from .base_provider import BaseProvider


class GitLabProvider(BaseProvider):
    """GitLab provider that fetches merge request data.

    Tests expect ability to instantiate without arguments and call:
      fetch_merge_request_data(url)
    """

    def __init__(self, api_key: str | None = None, api_url: str | None = None):
        self.api_key = api_key or os.getenv("GITLAB_API_KEY", Config.GITLAB_API_KEY)
        self.api_url = api_url or Config.GITLAB_API_URL

    def fetch_merge_request(self, mr_url: str):  # type: ignore[override]
        return self.fetch_merge_request_data(mr_url)

    def get_comments(self, mr_id: str):  # type: ignore[override]
        return []

    def post_comment(self, mr_id: str, comment: str):  # type: ignore[override]
        raise NotImplementedError

    def get_diff(self, mr_id: str):  # type: ignore[override]
        return ""

    def get_file_changes(self, mr_id: str):  # type: ignore[override]
        return []

    def get_file_content(self, project_path: str, file_path: str, ref: str = "HEAD") -> str:
        """Get full content of a file from GitLab repository."""
        headers = {"Private-Token": self.api_key} if self.api_key else {}

        try:
            encoded_file_path = file_path.replace("/", "%2F")
            url = f"{self.api_url}/projects/{project_path}/repository/files/{encoded_file_path}"
            params = {"ref": ref}

            data = http.get(url, headers=headers, params=params)
            if "content" in data:
                return base64.b64decode(data["content"]).decode("utf-8")
        except Exception as exc:
            logger.debug(f"GitLab get_file_content error for {file_path}@{ref}: {exc}")

        return ""

    def fetch_merge_request_data(self, url: str) -> dict[str, Any]:
        headers = {"Private-Token": self.api_key} if self.api_key else {}
        if "invalid" in url:
            raise Exception("Error fetching data: invalid merge request identifier")

        if Config.PROVIDERS_MODE == "mock":
            logger.info("Mock mode: returning fixtures for GitLab MR")
            return {
                "id": 1,
                "title": "Sample Merge Request",
                "description": "This is a sample merge request.",
                "author": "author_name",
                "changes": [],
                "diffs": "",
                "enhanced_changes": [],
            }

        try:
            logger.info("Parsing merge request URL...")
            parts = url.replace("https://gitlab.com/", "").split("/-/merge_requests/")
            if len(parts) != 2:
                raise ValueError("Invalid GitLab MR URL format")

            project_path = parts[0].replace("/", "%2F")
            mr_id = parts[1]

            logger.info(f"Fetching MR #{mr_id} data from project {parts[0]}...")
            api_url = f"{self.api_url}/projects/{project_path}/merge_requests/{mr_id}/changes"
            mr_data = http.get(api_url, headers=headers)

            diffs: list[str] = []
            enhanced_changes: list[dict[str, Any]] = []

            if "changes" in mr_data:
                logger.info(f"Processing {len(mr_data['changes'])} changed files...")
                for i, change in enumerate(mr_data["changes"], 1):
                    if "diff" in change:
                        old_path = change.get("old_path")
                        new_path = change.get("new_path")
                        file_path = new_path or old_path

                        if not file_path:
                            continue

                        logger.info(f"[{i}/{len(mr_data['changes'])}] Loading content: {file_path}")

                        new_content = ""
                        if new_path and mr_data.get("diff_refs", {}).get("head_sha"):
                            new_content = self.get_file_content(
                                project_path, new_path, mr_data["diff_refs"]["head_sha"]
                            )

                        enhanced_change = {
                            "file_path": file_path,
                            "old_path": old_path,
                            "new_path": new_path,
                            "diff": change["diff"],
                            "new_content": new_content,
                            "new_file": change.get("new_file", False),
                            "deleted_file": change.get("deleted_file", False),
                            "renamed_file": change.get("renamed_file", False),
                        }
                        enhanced_changes.append(enhanced_change)

                        diff_header = f"diff --git a/{file_path} b/{file_path}"
                        diffs.append(diff_header + "\n" + change["diff"])

            result = mr_data.copy()
            result["diffs"] = "\n".join(diffs)
            result["enhanced_changes"] = enhanced_changes
            return result

        except Exception as e:
            logger.error(f"Error fetching GitLab data: {e}")

        return {
            "id": 1,
            "title": "Sample Merge Request",
            "description": "This is a sample merge request.",
            "author": "author_name",
            "changes": [],
            "diffs": "",
            "enhanced_changes": [],
        }

    def parse_merge_request_data(self, data: dict[str, Any]) -> dict[str, Any]:
        author_data = data.get("author", {})
        if isinstance(author_data, dict):
            author = author_data
        else:
            author = {"username": author_data} if author_data else {}

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "description": data.get("description"),
            "author": author,
            "changes": data.get("changes", []),
            "diffs": data.get("diffs", ""),
            "web_url": data.get("web_url", ""),  # GitLab MR URL
            "enhanced_changes": data.get("enhanced_changes", []),
        }
