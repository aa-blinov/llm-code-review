# config.py

import os
from pathlib import Path

from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)


class Config:
    # Git providers
    GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", "")
    GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")

    GITLAB_API_KEY = os.getenv("GITLAB_API_KEY", "")
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")

    # AI Reviewers
    REVIEWER_PROVIDER = os.getenv("REVIEWER_PROVIDER", "gemini").lower()  # gemini, openai_like

    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # OpenAI-Like API (OpenRouter, Ollama, Together AI, etc.)
    OPENAI_LIKE_API_KEY = os.getenv("OPENAI_LIKE_API_KEY", "")
    OPENAI_LIKE_MODEL = os.getenv("OPENAI_LIKE_MODEL", "google/gemini-2.5-flash")
    OPENAI_LIKE_BASE_URL = os.getenv("OPENAI_LIKE_BASE_URL", "https://openrouter.ai/api/v1")

    # HTTP settings
    TIMEOUT = int(os.getenv("TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

    # Development settings
    PROVIDERS_MODE = os.getenv("PROVIDERS_MODE", "online").lower()
