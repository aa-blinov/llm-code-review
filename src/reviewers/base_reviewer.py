"""Базовый класс для всех ревьюеров кода."""

from abc import ABC, abstractmethod
from typing import Any


class BaseReviewer(ABC):
    """Абстрактный базовый класс для ревьюеров кода."""

    def __init__(self, merge_request_data: dict[str, Any]):
        """Инициализация ревьюера.

        Args:
            merge_request_data: Данные merge request с информацией о файлах и изменениях
        """
        self.merge_request_data = merge_request_data
        self._processed: dict[str, Any] = {}

    def process_merge_request(self) -> None:
        """Обработка данных merge request для формирования отчета."""
        mr_id = self.merge_request_data.get("number") or self.merge_request_data.get("id")

        self._processed = {
            "title": self.merge_request_data.get("title"),
            "author": self.merge_request_data.get("author") or self.merge_request_data.get("user", {}).get("login"),
            "description": self.merge_request_data.get("description", ""),
            "changes": self.merge_request_data.get("changes", []),
            "diffs": self.merge_request_data.get("diffs", ""),
            "web_url": self.merge_request_data.get("web_url", ""),
            "mr_id": str(mr_id) if mr_id else "",
        }

    def generate_report_data(self) -> dict[str, Any]:
        """Генерация базовых данных для отчета.

        Returns:
            Словарь с данными для формирования отчета
        """
        if not self._processed:
            self.process_merge_request()
        return self._processed

    @abstractmethod
    def get_review_comments(self) -> dict[str, Any]:
        """Получение комментариев ревью от AI модели.

        Returns:
            Словарь с результатами анализа:
            {
                "diff_comments": List[str],  # Комментарии по изменениям
                "summary": str,              # Общее резюме
                "file_reviews": List[dict]   # Детальный анализ файлов
            }
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности ревьюера (API ключ, настройки).

        Returns:
            True если ревьюер может работать, False иначе
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Название провайдера ревьюера.

        Returns:
            Строка с названием провайдера (например, "Gemini", "OpenAI-Like")
        """
