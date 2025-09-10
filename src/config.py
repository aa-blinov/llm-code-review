# config.py

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Config:
    GITHUB_API_KEY = os.getenv("API_KEY_GITHUB", os.getenv("GITHUB_API_KEY", ""))
    GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")

    GITLAB_API_KEY = os.getenv("API_KEY_GITLAB", os.getenv("GITLAB_API_KEY", ""))
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    TIMEOUT = 30
    MAX_RETRIES = 3
