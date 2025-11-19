# Postcode Resolver Module

Модуль для преобразования UK postcode в Local Authority и Region с кэшированием.

## Функционал

1. **Валидация UK postcode формата**
   - Проверка формата согласно UK стандартам
   - Нормализация (uppercase, единый формат)

2. **Разрешение postcode через postcodes.io API**
   - Получение Local Authority, Region, координат
   - Поддержка всех UK регионов (England, Scotland, Wales, Northern Ireland)

3. **Кэширование**
   - Redis (production)
   - SQLite fallback (development)
   - Автоматическое истечение кэша (90 дней)

4. **Batch режим**
   - Обработка 100+ postcode за раз
   - Автоматическое разбиение на батчи
   - Оптимизация через кэш

5. **Streamlit интерфейс**
   - Тестирование отдельных postcode
   - Batch обработка
   - Визуализация на карте (Folium)

## Установка

```bash
pip install -e .
```

## Использование

### Single Postcode

```python
from postcode_resolver import PostcodeResolver

resolver = PostcodeResolver()
result = resolver.resolve("B15 2HQ")

print(f"Local Authority: {result.local_authority}")
print(f"Region: {result.region}")
print(f"Coordinates: {result.lat}, {result.lon}")
```

### Batch Postcodes

```python
from postcode_resolver import BatchPostcodeResolver

batch_resolver = BatchPostcodeResolver()
postcodes = ["B15 2HQ", "SW1A 1AA", "M1 1AA"]

result = batch_resolver.resolve_batch(postcodes)
print(f"Found: {result.found}/{result.total}")
for info in result.results:
    if info:
        print(f"{info.postcode}: {info.local_authority}")
```

### Валидация

```python
from postcode_resolver import validate_postcode, is_valid_postcode

# С исключением
try:
    validate_postcode("B15 2HQ")
    print("Valid!")
except InvalidPostcodeError as e:
    print(f"Invalid: {e}")

# Без исключения
if is_valid_postcode("B15 2HQ"):
    print("Valid!")
```

## Конфигурация

Создайте `.env` файл:

```env
# Cache type: "redis" or "sqlite"
CACHE_TYPE=sqlite

# Redis settings (if CACHE_TYPE=redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Batch settings
BATCH_SIZE=100
BATCH_DELAY_SECONDS=0.1
```

## Streamlit интерфейс

```bash
streamlit run src/postcode_resolver/streamlit_tester.py
```

## Тестирование

```bash
pytest src/postcode_resolver/tests/ -v --cov=src/postcode_resolver
```

Тесты включают 50 реальных postcode из всех UK регионов:
- England (все 9 регионов)
- Scotland
- Wales
- Northern Ireland

## Структура модуля

```
src/postcode_resolver/
├── __init__.py
├── config.py              # Конфигурация
├── models.py             # Pydantic модели
├── validator.py          # Валидация UK postcode
├── cache.py             # Кэширование (Redis/SQLite)
├── resolver.py          # Single postcode resolver
├── batch_resolver.py    # Batch resolver
├── streamlit_tester.py  # Streamlit интерфейс
├── exceptions.py        # Исключения
└── tests/
    ├── test_validator.py
    ├── test_resolver.py
    ├── test_batch_resolver.py
    ├── test_real_postcodes.py  # 50 реальных postcode
    └── test_cache.py
```

## Production Ready

- ✅ Валидация UK postcode формата
- ✅ Кэширование (Redis/SQLite)
- ✅ Batch обработка
- ✅ Обработка ошибок
- ✅ Логирование через structlog
- ✅ Тесты на 50 реальных postcode
- ✅ Streamlit интерфейс с картами

