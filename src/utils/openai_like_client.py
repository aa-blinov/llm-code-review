"""OpenAI-compatible API client for various providers (supports any OpenAI-compatible API)."""

from __future__ import annotations

from src.config import Config
from src.utils.logging import get_logger

logger = get_logger()

try:
    from openai import OpenAI
except ImportError:
    logger.error("OpenAI SDK not installed. Run: pip install openai")
    raise


class OpenAILikeClient:
    """OpenAI-compatible API client for various providers."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize OpenAI-compatible client.

        Args:
            api_key: API key for the provider
            model: Model identifier (e.g., 'anthropic/claude-3.5-sonnet')
            base_url: API base URL (e.g., 'https://api.openai.com/v1', 'https://openrouter.ai/api/v1')
        """
        self.api_key = api_key or Config.OPENAI_LIKE_API_KEY
        self.model = model or Config.OPENAI_LIKE_MODEL
        self.base_url = base_url or Config.OPENAI_LIKE_BASE_URL

        if not self.api_key:
            raise ValueError("OPENAI_LIKE_API_KEY not configured")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # Token usage counters
        self._prompt_tokens: int = 0
        self._completion_tokens: int = 0

    def review_chunk(self, prompt: str, code_diff: str) -> str:
        """Review code chunk using OpenAI-compatible API.

        Args:
            prompt: System prompt for review
            code_diff: Code diff to review

        Returns:
            Review response from the model
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": f"Prompt:\n{prompt}\n\nDiff:\n{code_diff}"},
                ],
                extra_body={
                    "transforms": ["middle-out"],
                },
            )

            # Accumulate token usage if provided by the API
            try:
                usage = getattr(completion, "usage", None)
                if usage is not None:
                    self._prompt_tokens += int(getattr(usage, "prompt_tokens", 0) or 0)
                    self._completion_tokens += int(getattr(usage, "completion_tokens", 0) or 0)
            except Exception as exc:
                # Usage data is optional; log at debug level and continue
                logger.debug(f"Usage parsing failed: {exc}")

            return completion.choices[0].message.content or ""

        except Exception as exc:
            raise RuntimeError(f"OpenAI-compatible API error: {exc}") from exc

    def _system_prompt(self) -> str:
        """Get system prompt for code review."""
        return (
            "<role>\n"
            "Ты — опытный Senior Software Engineer, который проводит ревью кода. "
            "Твой фидбек должен быть конструктивным, вежливым и обучающим. "
            "Ты не просто указываешь на ошибки, но и объясняешь, почему это важно и как сделать лучше.\n"
            "</role>\n\n"
            "<diff_semantics>\n"
            "Работай с unified diff. В нём:\n"
            "- строки, начинающиеся с '-' — это было ДО (удалённые/заменённые строки),\n"
            "- строки с '+' — это стало ПОСЛЕ (новые/заменяющие строки).\n"
            "Сопоставляй пары '-' → '+', оценивай изменение как единое целое.\n"
            "Никогда не предлагай в качестве рекомендации те же правки, которые уже присутствуют в '+', — \n"
            "это уже сделано разработчиком.\n"
            "Если '+' исправляет или улучшает то, что было в '-', не помечай это как проблему — пропусти.\n"
            "</diff_semantics>\n\n"
            "<task>\n"
            "Анализируй только изменения из diff. Используй полный контекст файла только для понимания смысла.\n"
            "Цель — находить реальные проблемы в получившемся коде (состояние ПОСЛЕ), \n"
            "а не описывать или повторять внесённые изменения.\n"
            "Если в контексте присутствуют связанные файлы (зависимости/зависимые модули), \n"
            "проверь, не нарушен ли контракт между ними: изменились ли сигнатуры, типы, \n"
            "поведение функций так, что вызывающий/вызываемый код может сломаться.\n"
            "</task>\n\n"
            "<pillars>\n"
            "Ревью должно базироваться на шести столпах:\n"
            "1. ФУНКЦИОНАЛЬНОСТЬ (FUNC): логические ошибки, обработка исключений, runtime-ошибки.\n"
            "2. АРХИТЕКТУРА (ARCH): нарушение SOLID/DRY/KISS, связность, чистота кода, паттерны проектирования.\n"
            "3. СТИЛЬ И ЧИТАЕМОСТЬ (STYLE): naming, сложность кода, магические числа, комментарии.\n"
            "4. ИНФРАСТРУКТУРА (INFRA): производительность, управление ресурсами, развертывание.\n"
            "5. БЕЗОПАСНОСТЬ (SEC): SQL-инъекции, XSS, CSRF, безопасные пути файлов, права доступа.\n"
            "6. МЕЖМОДУЛЬНАЯ КОНСИСТЕНТНОСТЬ (CROSS): нарушение контрактов между модулями, "
            "изменение сигнатур функций/методов без обновления вызывающего кода, "
            "нарушение ожиданий зависимых/зависящих файлов, циклические зависимости.\n"
            "</pillars>\n\n"
            "<output_structure>\n"
            "- Группируй проблемы СТРОГО по приоритетам: CRITICAL → HIGH → MEDIUM → LOW.\n"
            "- Внутри каждого столпа сортируй по столпам: 1 → 2 → 3 → 4 → 5.\n"
            "- Используй Markdown для форматирования.\n\n"
            "Формат для каждой проблемы:\n"
            "[<столп>][<приоритет>] <исходный_файл>:<номер_строки> - <описание_проблемы> - <как_исправить>\n"
            "Для CROSS-проблем указывай оба файла: [CROSS][CRITICAL] fileA.py:42 → fileB.py:17 - ...\n"
            "</output_structure>\n\n"
            "<style>\n"
            "Пиши коротко, без эмодзи, используй форматирование Markdown. \n"
            "Не повторяй содержимое строк '+', если это и есть внесённые изменения.\n"
            "</style>\n\n"
            "<fallback>\n"
            "Если существенных проблем нет: 'LGTM, доработок не требуется.'\n"
            "</fallback>"
        )

    def review_diffs(self, diffs: str) -> str:
        """Review code diffs.

        Args:
            diffs: Code diffs to review

        Returns:
            Review response
        """
        logger.debug(f"Sending code for analysis to {self.model}...")
        prompt = "Проведи ревью следующих изменений в коде:"
        return self.review_chunk(prompt, diffs)

    def global_summary(self, context: str) -> str:
        """Generate global summary of review.

        Args:
            context: Context from all file reviews

        Returns:
            Global summary response
        """
        logger.debug("Building global summary...")
        prompt = (
            "<task>\n"
            "На основе найденных проблем создай итоговое резюме с акцентом на общую оценку и положительные моменты.\n"
            "</task>\n\n"
            "<format>\n"
            "## Статус: APPROVED | REQUEST_CHANGES | COMMENT\n\n"
            "## Основные проблемы по столпам:\n"
            "1. ФУНКЦИОНАЛЬНОСТЬ: [краткий статус]\n"
            "2. АРХИТЕКТУРА: [краткий статус]\n"
            "3. СТИЛЬ И ЧИТАЕМОСТЬ: [краткий статус]\n"
            "4. ИНФРАСТРУКТУРА: [краткий статус]\n"
            "5. БЕЗОПАСНОСТЬ: [краткий статус]\n\n"
            "## Что сделано хорошо:\n"
            "- [положительные аспекты кода]\n"
            "- [хорошие архитектурные решения]\n"
            "- [качественная реализация]\n\n"
            "## Ключевые рекомендации:\n"
            "- [список ключевых рекомендаций]\n"
            "</format>\n\n"
            "<style>\n"
            "Пиши коротко, без эмодзи, используй форматирование Markdown.\n"
            "</style>"
        )
        result = self.review_chunk(prompt, context)
        logger.debug("Global summary ready")
        return result

    def is_available(self) -> bool:
        """Check if OpenAI-compatible client is available.

        Returns:
            True if API key is configured and client is ready
        """
        return bool(self.api_key)

    @property
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name
        """
        return f"OpenAI-Like ({self.model})"

    def holistic_review(self, enhanced_changes: list[dict], pr_title: str = "") -> str:
        """Run a holistic cross-file review pass over the entire PR.

        Based on SOTA research (AACR-Bench 2026), ~15% of defects require
        repository-level context and cannot be detected by per-file analysis.
        This method sends all diffs together to find cross-module issues.

        Args:
            enhanced_changes: All changed files with their diffs.
            pr_title: PR title for context.

        Returns:
            Cross-file issues found, or empty string if none.
        """
        if len(enhanced_changes) <= 1:
            return ""

        # Build a compact PR view — diffs only to stay within token budget
        compact_parts = []
        if pr_title:
            compact_parts.append(f"PR: {pr_title}")
        compact_parts.append(f"Изменено файлов: {len(enhanced_changes)}\n")

        max_diff_per_file = 1500
        for c in enhanced_changes:
            fp = c.get("file_path", "?")
            diff = c.get("diff", "")
            if not diff:
                continue
            snippet = diff[:max_diff_per_file]
            if len(diff) > max_diff_per_file:
                snippet += "\n... (сокращено)"
            compact_parts.append(f"### `{fp}`\n```diff\n{snippet}\n```")

        compact_pr = "\n".join(compact_parts)

        holistic_prompt = (
            "<task>\n"
            "Проведи ЦЕЛОСТНЫЙ анализ всего Pull Request, глядя НА ВСЕ изменения СРАЗУ.\n"
            "Твоя задача — найти ТОЛЬКО проблемы, которые невозможно обнаружить при анализе файлов по отдельности:\n"
            "1. Нарушения контракта между модулями: изменилась сигнатура функции в файле A, "
            "но вызовы в файле B не обновлены.\n"
            "2. Несогласованность данных/типов: одна часть кода передаёт X, другая ожидает Y.\n"
            "3. Неполные изменения: добавлен новый атрибут/метод, но не обновлены все "
            "зависимые места (serializers, validators, tests).\n"
            "4. Потенциальные дублирования или противоречия между изменениями в разных файлах.\n"
            "5. Отсутствие тестов для нового кода при наличии test-файлов в PR.\n"
            "</task>\n\n"
            "<output>\n"
            "Если нашёл — перечисли конкретно: [CROSS][<приоритет>] fileA.py → fileB.py — описание.\n"
            "Если проблем нет — напиши только: 'Межмодульных проблем не обнаружено.'\n"
            "НЕ повторяй проблемы, которые видны из анализа одного файла.\n"
            "</output>"
        )
        logger.debug("Running holistic cross-file review pass...")
        try:
            return self.review_chunk(holistic_prompt, compact_pr)
        except Exception as exc:
            logger.debug(f"Holistic review error: {exc}")
            return ""

    def get_usage(self) -> dict[str, int]:
        """Get aggregated token usage for this client session.

        Returns:
            Dict with 'prompt_tokens', 'completion_tokens', 'total_tokens'.
        """
        total = self._prompt_tokens + self._completion_tokens
        return {
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_tokens": total,
        }
