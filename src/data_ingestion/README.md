# Data Ingestion Module

Автоматическое обновление данных MSIF и Lottie для RightCareHome.

## Функционал

1. **Автоматическое скачивание MSIF XLS файлов**
   - MSIF 2025-2026
   - MSIF 2024-2025
   - **Поддержка загрузки из CSV** (быстрее, для development)

2. **Парсинг Lottie страниц**
   - Региональные средние цены для residential, nursing, dementia care

3. **Обновление базы данных**
   - Таблицы `msif_fees_2025`, `msif_fees_2024`
   - Таблица `lottie_regional_averages`
   - Логирование в `data_update_log`

4. **Streamlit Admin интерфейс**
   - Кнопки для ручного обновления данных
   - Таблица статуса обновлений

5. **Автоматическое обновление (APScheduler)**
   - Обновление каждые 7 дней (настраивается)

6. **Telegram алерты**
   - Уведомления об ошибках скачивания/парсинга

## Установка

```bash
pip install -e .
```

## Конфигурация

Создайте `.env` файл:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=care_homes
DB_USER=postgres
DB_PASSWORD=your_password

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_DAYS=7

# Telegram Alerts (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ALERTS_ENABLED=true
```

## Использование

### Инициализация базы данных

```python
from data_ingestion.database import init_database

init_database()
```

### Ручное обновление данных

```python
from data_ingestion.service import DataIngestionService

service = DataIngestionService()

# Обновить MSIF 2025 (Excel с CSV fallback)
result = service.refresh_msif_data(year=2025)
print(result)

# Обновить MSIF 2025 из CSV (быстрее, для development)
result = service.refresh_msif_data(year=2025, prefer_csv=True)
print(result)

# Обновить Lottie
result = service.refresh_lottie_data()
print(result)
```

### Загрузка из CSV файла

Модуль поддерживает загрузку MSIF данных из предобработанных CSV файлов:

```python
from data_ingestion.msif_loader import MSIFLoader
from pathlib import Path

loader = MSIFLoader()

# Загрузка из CSV (по умолчанию: input/other/msif_2025_2026_processed.csv)
data = loader.load_msif_from_csv(year=2025)

# Загрузка из кастомного CSV файла
csv_path = Path("path/to/custom/msif.csv")
data = loader.load_msif_from_csv(csv_path=csv_path, year=2025)

# Использование CSV как основной источник с Excel fallback
records = loader.load_msif_data(
    year=2025,
    prefer_csv=True,
    fallback_to_csv=True
)
```

### Конфигурация CSV загрузки

Настройте через переменные окружения:

```env
# Предпочитать CSV над Excel (быстрее, для development)
MSIF_PREFER_CSV=true

# Использовать CSV как fallback при ошибках Excel (рекомендуется)
MSIF_FALLBACK_TO_CSV=true

# Кастомный путь к CSV файлу
MSIF_CSV_PATH=/path/to/custom/msif.csv
```

### Автоматическое обновление (APScheduler)

```python
from data_ingestion.scheduler import DataIngestionScheduler

scheduler = DataIngestionScheduler()
scheduler.start()

# Scheduler будет работать в фоне
# Остановка:
# scheduler.stop()
```

### Streamlit Admin интерфейс

```bash
streamlit run src/data_ingestion/streamlit_admin.py
```

## Тестирование

```bash
pytest src/data_ingestion/tests/ -v --cov=src/data_ingestion --cov-report=html
```

## Структура модуля

```
src/data_ingestion/
├── __init__.py
├── config.py              # Конфигурация
├── database.py            # Подключение к БД
├── msif_loader.py         # Загрузка MSIF данных
├── lottie_scraper.py      # Парсинг Lottie
├── telegram_alerts.py     # Telegram уведомления
├── scheduler.py           # APScheduler настройка
├── service.py             # Основной сервис
├── streamlit_admin.py     # Streamlit интерфейс
├── exceptions.py          # Исключения
└── tests/                 # Тесты
    ├── test_msif_loader.py
    ├── test_lottie_scraper.py
    ├── test_service.py
    ├── test_telegram_alerts.py
    └── test_database.py
```

## Production Ready

- ✅ Полное логирование через structlog
- ✅ Обработка ошибок с Telegram алертами
- ✅ Тесты с 95%+ coverage
- ✅ Автоматическое обновление через APScheduler
- ✅ Streamlit интерфейс для админа
- ✅ Кеширование скачанных файлов
- ✅ Логирование всех обновлений в БД

