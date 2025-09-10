#!/bin/bash

echo "🔍 Проверка качества кода..."

# Активируем виртуальное окружение
source .venv/bin/activate

echo "📝 Проверка стиля кода с помощью ruff..."
ruff check src/ tests/

RUFF_EXIT_CODE=$?

if [ $RUFF_EXIT_CODE -eq 0 ]; then
    echo "✅ Проверка ruff прошла успешно"
else
    echo "❌ Найдены проблемы в коде"
    echo "💡 Попробуйте: ruff check src/ tests/ --fix"
    exit 1
fi

echo "🧪 Запуск тестов..."
python -m pytest tests/ -v

PYTEST_EXIT_CODE=$?

if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Все тесты прошли успешно"
else
    echo "❌ Некоторые тесты не прошли"
    exit 1
fi

echo "🎉 Проверка качества завершена успешно!"
