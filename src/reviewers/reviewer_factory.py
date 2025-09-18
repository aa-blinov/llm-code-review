"""Factory for creating code reviewers."""

from typing import Any

from src.config import Config
from src.reviewers.base_reviewer import BaseReviewer
from src.reviewers.gemini_reviewer import GeminiReviewer
from src.reviewers.openai_like_reviewer import OpenAILikeReviewer
from src.utils.logging import get_logger

logger = get_logger()


class ReviewerFactory:
    """Factory for creating code reviewers based on configuration."""

    @staticmethod
    def create_reviewer(merge_request_data: dict[str, Any]) -> BaseReviewer:
        """Create a reviewer based on configuration.

        Args:
            merge_request_data: Merge request data

        Returns:
            Configured reviewer instance

        Raises:
            ValueError: If no suitable reviewer is available
        """
        provider = Config.REVIEWER_PROVIDER.lower()

        if provider == "gemini":
            reviewer = GeminiReviewer(merge_request_data)
            if reviewer.is_available():
                logger.info(f"Using AI reviewer: {reviewer.provider_name}")
                return reviewer
            logger.warning("Warning: Gemini API unavailable (check GEMINI_API_KEY)")

        elif provider == "openai_like":
            reviewer = OpenAILikeReviewer(merge_request_data)
            if reviewer.is_available():
                logger.info(f"Using AI reviewer: {reviewer.provider_name}")
                return reviewer
            logger.warning("Warning: OpenAI-Like API unavailable (check OPENAI_LIKE_API_KEY)")

        else:
            logger.warning(f"Warning: Unknown reviewer provider: {provider}")

        logger.info("Attempting to use any available reviewer...")

        gemini_reviewer = GeminiReviewer(merge_request_data)
        if gemini_reviewer.is_available():
            logger.info(f"Fallback to: {gemini_reviewer.provider_name}")
            return gemini_reviewer

        openai_like_reviewer = OpenAILikeReviewer(merge_request_data)
        if openai_like_reviewer.is_available():
            logger.info(f"Fallback to: {openai_like_reviewer.provider_name}")
            return openai_like_reviewer

        raise ValueError("No AI reviewer available. Configure GEMINI_API_KEY or OPENAI_LIKE_API_KEY")

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available reviewer providers.

        Returns:
            List of available provider names
        """
        available = []

        if Config.GEMINI_API_KEY:
            available.append("gemini")

        if Config.OPENAI_LIKE_API_KEY:
            available.append("openai_like")

        return available

    @staticmethod
    def validate_configuration() -> dict[str, Any]:
        """Validate reviewer configuration.

        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "available_providers": [],
            "configured_provider": Config.REVIEWER_PROVIDER.lower(),
        }

        available_providers = ReviewerFactory.get_available_providers()
        result["available_providers"] = available_providers

        if not available_providers:
            result["errors"].append("No AI provider configured")
            return result

        configured_provider = Config.REVIEWER_PROVIDER.lower()
        if configured_provider not in ["gemini", "openai_like"]:
            result["warnings"].append(f"Unknown provider '{configured_provider}', fallback will be used")

        if configured_provider == "gemini" and "gemini" not in available_providers:
            result["warnings"].append("Gemini selected, but GEMINI_API_KEY is not configured")

        if configured_provider == "openai_like" and "openai_like" not in available_providers:
            result["warnings"].append("OpenAI-Like selected, but OPENAI_LIKE_API_KEY is not configured")

        result["valid"] = True
        return result
