"""Google Gemini API client using official google-genai SDK."""

from __future__ import annotations

from typing import Any

from src.config import Config
from src.utils.logging import get_logger

logger = get_logger()

try:
    from google import genai
    from google.genai import types
except ImportError:
    logger.error("google-genai not installed. Run: pip install google-genai")
    raise


class GeminiClient:
    """Official Google GenAI client wrapper."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model: Model name (e.g., 'gemini-2.5-flash')
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.GEMINI_MODEL

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        self.client = genai.Client(api_key=self.api_key)
        # Token usage counters
        self._prompt_tokens = 0
        self._completion_tokens = 0

    def review_chunk(self, prompt: str, code_diff: str) -> str:
        """Review code chunk using Gemini.

        Args:
            prompt: System prompt for review
            code_diff: Code diff to review

        Returns:
            Review response from the model
        """
        try:
            system_instruction = self._system_prompt()
            user_content = f"Prompt:\n{prompt}\n\nDiff:\n{code_diff}"

            response = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    max_output_tokens=4000,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )

            # Accumulate token usage if available on response
            try:
                usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)
                if usage is not None:
                    # Try multiple attribute names used across SDK versions
                    in_tokens = (
                        getattr(usage, "input_tokens", None)
                        or getattr(usage, "prompt_token_count", None)
                        or getattr(usage, "prompt_tokens", None)
                        or 0
                    )
                    out_tokens = (
                        getattr(usage, "output_tokens", None)
                        or getattr(usage, "candidates_token_count", None)
                        or getattr(usage, "completion_tokens", None)
                        or 0
                    )
                    self._prompt_tokens += int(in_tokens or 0)
                    self._completion_tokens += int(out_tokens or 0)
            except Exception as exc:
                logger.debug(f"Gemini usage parsing failed: {exc}")

            return response.text or ""

        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc

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
            "Никогда не предлагай в качестве рекомендации те же правки, которые уже присутствуют в '+' — \n"
            "это уже сделано разработчиком. Если '+' исправляет или улучшает то, что было в '-', \n"
            "не помечай это как проблему — пропусти.\n"
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
            "Пиши коротко, по делу, без эмодзи. Не повторяй содержимое строк '+', \n"
            "если это и есть внесённые изменения.\n"
            "</style>\n\n"
            "<fallback>\n"
            "Если существенных проблем нет: 'Код выглядит корректно. Доработок не требуется.'\n"
            "</fallback>"
        )

    def review_diffs(self, diffs: str) -> str:
        """Review code diffs.

        Args:
            diffs: Code diffs to review

        Returns:
            Review response
        """
        logger.debug(f"Sending code for analysis to Gemini ({self.model})...")
        prompt = "Проведи ревью следующих изменений в коде:"
        return self.review_chunk(prompt, diffs)

    def global_summary(self, context: str, pr_info: dict[str, Any] | None = None) -> str:
        """Generate global summary of review.

        Args:
            context: Context from all file reviews
            pr_info: Additional PR/MR information (title, url, author, etc.)

        Returns:
            Global summary response
        """
        logger.debug("Building global summary...")

        prompt = (
            "<task>\n"
            "На основе найденных проблем создай итоговое резюме с акцентом на общую оценку и положительные моменты.\n"
            "ВАЖНО: Начни с краткого описания того, что было реализовано в данном изменении кода.\n"
            "</task>\n\n"
            "<format>\n"
            "### Обзор изменений\n"
            "[Краткое описание того, что было реализовано/исправлено в данном merge request]\n\n"
            "### Статус ревью: APPROVED | REQUEST_CHANGES | COMMENT\n\n"
            "### Основные проблемы по столпам:\n"
            "1. ФУНКЦИОНАЛЬНОСТЬ: [краткий статус]\n"
            "2. АРХИТЕКТУРА: [краткий статус]\n"
            "3. СТИЛЬ И ЧИТАЕМОСТЬ: [краткий статус]\n"
            "4. ИНФРАСТРУКТУРА: [краткий статус]\n"
            "5. БЕЗОПАСНОСТЬ: [краткий статус]\n\n"
            "### Что сделано хорошо:\n"
            "- [положительные аспекты кода]\n"
            "- [хорошие архитектурные решения]\n"
            "- [качественная реализация]\n\n"
            "### Ключевые рекомендации:\n"
            "- [список ключевых рекомендаций]\n\n"
            "## Заключение\n"
            "[Итоговый комментарий о качестве изменений и готовности к мержу]\n"
            "</format>\n\n"
            "<style>\n"
            "Пиши коротко, без эмодзи, используй форматирование Markdown.\n"
            "</style>"
        )
        result = self.review_chunk(prompt, context)
        logger.debug("Global summary ready")
        return result

    def is_available(self) -> bool:
        """Check if Gemini client is available.

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
        return f"Gemini ({self.model})"

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

        # Build a compact PR view — diffs only (no full file content) to stay within token budget
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
