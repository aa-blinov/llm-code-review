# Code Review with AI (Gemini + OpenAI-compatible APIs)

Automated code review for merge/pull requests powered by AI.

Note: Application logs are in English. AI prompts and the final report are intentionally in Russian by design.

## Why

Manual reviews are time-consuming and error-prone:

- Cognitive fatigue scanning hundreds of lines
- Missed bugs and subtle issues
- Subjective, inconsistent feedback
- Expensive for busy teams

This tool provides objective AI analysis of diffs with actionable suggestions.

## Features

- Senior-level code analysis (bugs, vulnerabilities, best practices, design, performance, security)
- AI providers: Google Gemini; OpenAI-compatible APIs (OpenRouter, OpenAI, Ollama, Together AI, etc.)
- Platforms: GitLab (cloud/self-hosted), GitHub
- Smart diff handling: only added lines, optional full-file context, optimized token usage
- Markdown reports with severity (CRITICAL/HIGH/MEDIUM/LOW) and links to authors and MR/PR

## Architecture

```text
code-review/
├── src/
│   ├── providers/       # GitLab/GitHub integrations
│   ├── reviewers/       # AI analysis (Gemini/OpenAI-compatible APIs)
│   ├── parsers/         # Diff and file handling
│   ├── report/          # Report generation
│   ├── utils/           # Utilities (HTTP, logging)
│   └── config.py        # Configuration
├── tests/               # Unit tests
└── outputs/             # Generated reports
```

## Quickstart

### Install uv (recommended)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS (Homebrew)
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install dependencies

```bash
uv sync
```

## Configuration

Create a `.env` file in the project root:

```bash
# gemini or openai_like
REVIEWER_PROVIDER=gemini

# Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# OpenAI-compatible
OPENAI_LIKE_API_KEY=your_api_key_here
OPENAI_LIKE_MODEL=google/gemini-2.5-flash
OPENAI_LIKE_BASE_URL=https://openrouter.ai/api/v1

# Git providers
GITLAB_API_KEY=your_gitlab_token
GITLAB_API_URL=https://gitlab.com/api/v4
GITHUB_API_KEY=your_github_token
GITHUB_API_URL=https://api.github.com

# HTTP and providers
TIMEOUT=30
MAX_RETRIES=3
PROVIDERS_MODE=online
```

Where to get keys:

- Gemini: https://makersuite.google.com/app/apikey
- OpenRouter: https://openrouter.ai/ (keys: https://openrouter.ai/keys)
- OpenAI: https://platform.openai.com/api-keys
- Ollama (local): http://localhost:11434/v1
- Together AI: https://api.together.xyz/settings/api-keys
- GitLab: https://gitlab.com/-/user_settings/personal_access_tokens (scopes: `api`, `read_api`, `read_repository`)
- GitHub: https://github.com/settings/tokens (scopes: `repo`, `public_repo`)

Configuration reference:

| Variable | Required | Default | Description |
|---------|----------|---------|-------------|
| REVIEWER_PROVIDER | optional | gemini | gemini or openai_like |
| GEMINI_API_KEY | required* | - | Google Gemini API key |
| GEMINI_MODEL | optional | gemini-2.5-flash | Gemini model |
| OPENAI_LIKE_API_KEY | required** | - | OpenAI-compatible API key |
| OPENAI_LIKE_MODEL | optional | google/gemini-2.5-flash | Model name |
| OPENAI_LIKE_BASE_URL | optional | https://openrouter.ai/api/v1 | API base URL |
| GITLAB_API_KEY | optional | - | GitLab API token |
| GITLAB_API_URL | optional | https://gitlab.com/api/v4 | GitLab API URL |
| GITHUB_API_KEY | optional | - | GitHub API token |
| GITHUB_API_URL | optional | https://api.github.com | GitHub API URL |
| TIMEOUT | optional | 30 | HTTP timeout (s) |
| MAX_RETRIES | optional | 3 | HTTP retries |
| PROVIDERS_MODE | optional | online | online or mock |

* Required if `REVIEWER_PROVIDER=gemini`  
** Required if `REVIEWER_PROVIDER=openai_like`

## Usage

```bash
# GitLab MR
uv run python -m src.main "https://gitlab.com/user/project/-/merge_requests/123"

# GitHub PR
uv run python -m src.main "https://github.com/user/project/pull/123"

# Output folder
uv run python -m src.main -o ./outputs "MR_URL"

# Alternative using installed entry point
uv run code-review "https://gitlab.com/user/project/-/merge_requests/123"
```

Select provider (PowerShell example):

```powershell
$env:REVIEWER_PROVIDER = "gemini"; uv run python -m src.main "MR_URL"
$env:REVIEWER_PROVIDER = "openai_like"; uv run python -m src.main "MR_URL"
```

Outputs: reports are saved to the `outputs/` folder by default.

## Testing

```bash
uv run pytest -q
```

## Support

If you face issues:

1. Verify API keys are valid
2. Ensure the MR/PR is public or you have access
3. Check API rate limits
4. Open an issue with details

## License

MIT — see LICENSE for details.

---

Built to make code reviews better.
