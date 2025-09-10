"""Simple Gemini API client wrapper (placeholder HTTP implementation).

In production you might switch to official SDK if available.
"""

from __future__ import annotations

from typing import Any

import requests

from src.config import Config


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.GEMINI_MODEL
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        # Hypothetical endpoint (adjust when real endpoint differs)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def review_chunk(self, prompt: str, code_diff: str) -> str:
        body = {
            "contents": [
                {"parts": [{"text": self._system_prompt()}, {"text": f"Prompt:\n{prompt}\n\nDiff:\n{code_diff}"}]}
            ]
        }
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        resp = requests.post(url, json=body, timeout=Config.TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
        data = resp.json()
        return self._extract_text(data)

    def _extract_text(self, data: dict[str, Any]) -> str:
        try:
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0]["content"]["parts"]
                return "\n".join(p.get("text", "") for p in parts if p.get("text"))
        except Exception:
            pass
        return ""

    def _system_prompt(self) -> str:
        return (
            "Ты — опытный старший инженер (Staff/Principal) с экспертизой в backend, frontend, DevOps, инфраструктуре и безопасности.\n\n"
            "ЗАДАЧА: Провести техническое ревью кода, выявляя критические проблемы и улучшения.\n\n"
            "ПРИОРИТЕТЫ анализа:\n"
            "1. Функциональные баги и логические ошибки\n"
            "2. Уязвимости безопасности (инъекции, утечки, права доступа)\n"
            "3. Проблемы производительности и ресурсов\n"
            "4. Архитектурные нарушения и coupling\n"
            "5. Надёжность (обработка ошибок, race conditions)\n"
            "6. Качество тестирования\n"
            "7. Читаемость и поддерживаемость\n\n"
            "ТЕХНОЛОГИИ: Автоматически определяй стек по расширениям (.py, .js/.ts, .go, .java, Dockerfile, .tf, .yaml) и применяй соответствующие best practices.\n\n"
            "ФОРМАТ ответа: Используй теги [CRITICAL/HIGH/MEDIUM/LOW] и [BACKEND/FRONTEND/DEVOPS/SECURITY] для категоризации.\n\n"
            "ОГРАНИЧЕНИЯ: Не давай общие советы без конкретики. Избегай очевидных замечаний. Фокусируйся на реальных рисках."
        )

    def review_diffs(self, diffs: str) -> str:
        print("  🧠 Отправка кода на анализ в Gemini...")
        prompt = (
            "Проанализируй ТОЛЬКО изменения в коде и выдай конкретные замечания.\n\n"
            "ПОНИМАНИЕ DIFF ФОРМАТА:\n"
            "- Строки с префиксом `-` (минус) = СТАРЫЙ код, который УДАЛЯЕТСЯ\n"
            "- Строки с префиксом `+` (плюс) = НОВЫЙ код, который ДОБАВЛЯЕТСЯ\n"
            "- Строки без префикса = контекст (не изменяются)\n"
            "- АНАЛИЗИРУЙ ТОЛЬКО строки с `+` (новый код)\n"
            "- НЕ анализируй строки с `-` (они удаляются и больше не актуальны)\n\n"
            "ФОКУС анализа:\n"
            "- Анализируй ТОЛЬКО новые строки (помеченные `+` в diff)\n"
            "- Игнорируй удаляемые строки (помеченные `-` в diff)\n"
            "- Используй полное содержимое файла только для понимания контекста\n"
            "- Если старый код (строки с `-`) содержал проблемы, а новый код (строки с `+`) их исправляет - это ХОРОШО, не проблема\n\n"
            "АЛГОРИТМ анализа:\n"
            "1. Определи технологии по расширениям файлов\n"
            "2. Найди потенциальные баги, уязвимости, проблемы производительности в НОВОМ коде (`+` строки)\n"
            "3. Проверь соответствие best practices для добавленного кода\n"
            "4. Оцени влияние добавленного кода на архитектуру\n\n"
            "ФОРМАТ вывода:\n"
            "- [SEVERITY][AREA] файл:строка - Описание проблемы в НОВОМ коде (`+` строки). Рекомендация с примером.\n\n"
            "SEVERITY: CRITICAL (блокеры), HIGH (важные проблемы), MEDIUM (улучшения), LOW (стиль)\n"
            "AREA: SECURITY, PERFORMANCE, LOGIC, ARCH, TESTS, STYLE\n\n"
            "СПЕЦИФИЧНЫЕ проверки для НОВОГО кода (`+` строки):\n"
            "- Python: async/await usage, exception handling, memory leaks, SQL injections в добавленных строках\n"
            "- JavaScript/TypeScript: null checks, async patterns, XSS, performance в новых строках\n"
            "- Docker: layer optimization, security, base images в новых командах\n"
            "- Terraform: state management, security groups, cost optimization в новых ресурсах\n"
            "- YAML: syntax, security contexts, resource limits в добавленных конфигурациях\n\n"
            "Если серьёзных проблем в НОВОМ коде (`+` строки) нет, ответь: 'Изменения выглядят корректно, серьёзных проблем не обнаружено.'"
        )
        return self.review_chunk(prompt, diffs)

    def global_summary(self, context: str) -> str:
        print("  🧠 Формирование итогового резюме...")
        prompt = (
            "На основе детального анализа создай итоговое резюме ревью.\n\n"
            "СТРУКТУРА отчёта:\n\n"
            "## Статус ревью\n"
            "Одно из: ✅ ОДОБРЕНО | ⚠️ УСЛОВНО ОДОБРЕНО | ❌ ТРЕБУЕТ ДОРАБОТКИ\n"
            "Кратко обоснуй решение (1-2 предложения).\n\n"
            "## Критические проблемы\n"
            "Только блокирующие проблемы, требующие исправления. Если нет — напиши 'Не обнаружены'.\n\n"
            "## Основные риски\n"
            "Проблемы, которые могут проявиться в production:\n"
            "- Производительность и масштабируемость\n"
            "- Безопасность и доступы\n"
            "- Надёжность и отказоустойчивость\n\n"
            "## Рекомендации по улучшению\n"
            "Разбей по категориям (пропускай пустые):\n"
            "**Архитектура:** проблемы дизайна, coupling, separation of concerns\n"
            "**Безопасность:** уязвимости, секреты, доступы\n"
            "**Производительность:** оптимизации, ресурсы\n"
            "**Тестирование:** покрытие, качество тестов\n"
            "**DevOps:** CI/CD, мониторинг, деплой\n\n"
            "## Хорошие решения\n"
            "Отметь качественные архитектурные или технические решения в данном PR.\n\n"
            "Будь конкретен, избегай общих фраз."
        )
        result = self.review_chunk(prompt, context)
        print("  ✅ Итоговое резюме готово")
        return result
