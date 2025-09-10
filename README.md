# Code Review с Google Gemini AI

Автоматизированный анализ merge request'ов с использованием искусственного интеллекта.

## 🎯 Зачем это нужно?

Каждый разработчик знает боль code review:

- Ментальная усталость от просмотра сотен строк кода
- Пропуск багов из-за невнимательности  
- Субъективность оценок и непоследовательность
- Времязатратность процесса

Этот инструмент решает эти проблемы, предоставляя объективный AI-анализ изменений в коде с конкретными рекомендациями по улучшению.

## ⚡ Что умеет

**🧠 Анализ кода на уровне Senior+ инженера:**

- Выявление потенциальных багов и уязвимостей
- Проверка соответствия best practices
- Анализ архитектурных решений
- Оценка производительности и безопасности

**🌐 Поддержка платформ:**

- GitLab (gitlab.com и self-hosted)
- GitHub (github.com)

**🔍 Умная обработка diff'ов:**

- Анализирует только добавленный код (игнорирует удаляемые строки)
- Загружает полный контекст файлов для лучшего понимания
- Оптимизирует использование токенов API

**📊 Профессиональные отчеты:**

- Структурированные отчеты в Markdown
- Категоризация проблем по важности (CRITICAL/HIGH/MEDIUM/LOW)  
- Конкретные рекомендации с примерами кода
- Ссылки на профили авторов и merge request'ы

## 🏗️ Архитектура

Проект построен по принципам чистой архитектуры с разделением ответственности:

```text
code-review/
├── src/
│   ├── providers/       # Интеграция с GitLab/GitHub API
│   ├── reviewers/       # AI анализ с помощью Gemini
│   ├── parsers/         # Обработка diff'ов и файлов
│   ├── report/          # Генерация отчетов
│   ├── utils/           # Утилиты (HTTP, логирование)
│   └── config.py        # Конфигурация
├── tests/               # Unit тесты
├── outputs/             # Готовые отчеты
└── run_review.py        # Entry point
```

**Основные компоненты:**

- **Providers** - абстракция для работы с разными Git платформами
- **Reviewers** - AI анализ через Google Gemini
- **Parsers** - обработка diff'ов и классификация файлов
- **Report Builder** - генерация профессиональных отчетов

## 🚀 Быстрый старт

### Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# или .venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка API ключей

Создайте файл `.env` в корне проекта:

```bash
# Google Gemini API (обязательно)
GEMINI_API_KEY=your_gemini_api_key_here

# GitLab (если используете приватные репозитории)
GITLAB_API_KEY=your_gitlab_token
GITLAB_API_URL=https://gitlab.com/api/v4

# GitHub (если используете приватные репозитории)
GITHUB_API_KEY=your_github_token
GITHUB_API_URL=https://api.github.com

# Общие настройки
TIMEOUT=30
```

### Получение API ключей

**Google Gemini:**

1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Создайте новый API ключ
3. Скопируйте ключ в переменную `GEMINI_API_KEY`

**GitLab (опционально):**

1. Перейдите в Settings → Access Tokens
2. Создайте токен с scope: `read_api`, `read_repository`

**GitHub (опционально):**

1. Перейдите в Settings → Developer settings → Personal access tokens
2. Создайте токен с scope: `repo`

## 📋 Использование

### Основные команды

```bash
# Анализ GitLab MR
python run_review.py "https://gitlab.com/user/project/-/merge_requests/123"

# Анализ GitHub PR
python run_review.py "https://github.com/user/project/pull/123"

# Сохранить в определенную папку
python run_review.py -o /path/to/reports "MR_URL"

# Справка
python run_review.py --help
```

### Примеры URL

**GitLab:**

- `https://gitlab.com/user/project/-/merge_requests/123`
- `https://gitlab.example.com/group/project/-/merge_requests/456`

**GitHub:**

- `https://github.com/user/project/pull/123`
- `https://api.github.com/repos/user/project/pulls/123`

## 🔧 Конфигурация

Все настройки задаются через environment variables в файле `.env`:

| Переменная | Обязательность | Значение по умолчанию | Описание |
|------------|-----------------|----------------------|----------|
| `GEMINI_API_KEY` | ✅ Обязательно | - | API ключ Google Gemini |
| `GEMINI_MODEL` | ⚠️ Опционально | gemini-1.5-flash | Модель Gemini для анализа |
| `GITLAB_API_KEY` | ⚠️ Опционально | - | GitLab API токен |
| `GITLAB_API_URL` | ⚠️ Опционально | <https://gitlab.com/api/v4> | GitLab API URL |
| `GITHUB_API_KEY` | ⚠️ Опционально | - | GitHub API токен |
| `GITHUB_API_URL` | ⚠️ Опционально | <https://api.github.com> | GitHub API URL |
| `TIMEOUT` | ⚠️ Опционально | 30 | Таймаут HTTP запросов |

## 📊 Пример отчета

```markdown
# add: clear cache

## 👤 Автор: [aa-blinov](https://gitlab.com/aa-blinov)
## 🔗 Merge Request: [#11](https://gitlab.com/eora/dialog-systems/avandoc-admin-front-end/-/merge_requests/11)

## 🔍 Изменения в файлах

### 📄 src/assets/icons/index.ts
**Тип:** modified | **Статус:** ✅ Анализ завершен

```typescript
export { ReactComponent as ReloadIcon } from './reload.svg';
```

**💭 Анализ:**
[MEDIUM][FRONTEND] Добавлен экспорт иконки для функции очистки кэша...

## 📋 Итоговое резюме

**Статус ревью:** ✅ ОДОБРЕНО

**Критические проблемы:** Не обнаружены

**Основные риски:** Минимальные для данного изменения...

```

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m pytest tests/ -v

# Проверка качества кода
./check_quality.sh

# Только линтер
ruff check src/ tests/
```

## 🔍 Качество кода

Проект использует современные инструменты для поддержания качества:

- **ruff** - быстрый линтер и форматтер
- **pytest** - тестирование
- **type hints** - статическая типизация
- **mypy** готовность - современный Python синтаксис

## 🚀 Технологии

- **Python 3.12+** - современный синтаксис и возможности
- **Google Gemini API** - AI анализ кода
- **GitLab/GitHub API** - интеграция с Git платформами
- **requests** - HTTP клиент
- **pytest** - тестирование

## 🤝 Разработка

### Структура кода

- `src/providers/` - интеграция с внешними API
- `src/reviewers/` - AI логика анализа
- `src/parsers/` - обработка diff'ов и контента
- `src/report/` - генерация отчетов
- `src/utils/` - общие утилиты

### Добавление нового провайдера

1. Создайте класс, наследующий `BaseProvider`
2. Реализуйте методы `fetch_merge_request_data()` и `parse_merge_request_data()`
3. Добавьте определение провайдера в `main.py`
4. Создайте тесты в `tests/`

### Принципы

- **Single Responsibility** - каждый класс решает одну задачу
- **Dependency Injection** - внедрение зависимостей через конструктор
- **Тестируемость** - 100% покрытие критической логики
- **Читаемость** - понятные имена и структура

## 📈 Планы развития

- [ ] Поддержка Bitbucket
- [ ] Интеграция с Claude AI
- [ ] Веб-интерфейс
- [ ] CI/CD интеграция
- [ ] Кэширование результатов
- [ ] Batch обработка MR

## 🐛 Известные ограничения

- Требует доступ к сети для API вызовов
- Ограничен rate limits API провайдеров
- Gemini API может быть недоступен в некоторых регионах
- Максимальный размер diff'а ограничен токенами модели

## 📞 Поддержка

При возникновении проблем:

1. Проверьте правильность API ключей
2. Убедитесь что MR/PR доступен публично или у вас есть права доступа
3. Проверьте лимиты API
4. Создайте issue с подробным описанием проблемы

## 📄 Лицензия

Проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.

---

*Создано с ❤️ для улучшения процесса code review*
