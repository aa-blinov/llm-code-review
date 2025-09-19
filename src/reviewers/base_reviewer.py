"""Base class for all code reviewers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseReviewer(ABC):
    """Abstract base class for code reviewers."""

    def __init__(self, merge_request_data: dict[str, Any]):
        """Initialize reviewer.

        Args:
            merge_request_data: Merge request data with files and changes
        """
        self.merge_request_data = merge_request_data
        self._processed: dict[str, Any] = {}

    def process_merge_request(self) -> None:
        """Process merge request data to build report payload."""
        mr_id = self.merge_request_data.get("number") or self.merge_request_data.get("id")

        self._processed = {
            "title": self.merge_request_data.get("title"),
            "author": self.merge_request_data.get("author") or self.merge_request_data.get("user", {}).get("login"),
            "description": self.merge_request_data.get("description", ""),
            "changes": self.merge_request_data.get("changes", []),
            "diffs": self.merge_request_data.get("diffs", ""),
            "web_url": self.merge_request_data.get("web_url", ""),
            "mr_id": str(mr_id) if mr_id else "",
            # Pass through raw user info (e.g., GitHub user with html_url) for richer author formatting
            "user": self.merge_request_data.get("user", {}),
        }

    def generate_report_data(self) -> dict[str, Any]:
        """Generate base data for the report.

        Returns:
            Dict with data used to build the final report
        """
        if not self._processed:
            self.process_merge_request()
        return self._processed

    @abstractmethod
    def get_review_comments(self) -> dict[str, Any]:
        """Get AI review comments.

        Returns:
            Dict with analysis results:
            {
                "diff_comments": List[str],  # Comments on diffs
                "summary": str,              # Overall summary (RU)
                "file_reviews": List[dict]   # Per-file analysis (RU)
            }
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check reviewer availability (API key, config).

        Returns:
            True if reviewer can operate, otherwise False
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name.

        Returns:
            Provider name string (e.g., "Gemini", "OpenAI-Like")
        """
