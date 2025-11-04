# 🚀 STAGING РЕШЕНИЕ: Autumna → care_homes v2.4
## Полное решение со staging таблицей и маппингом

**Дата:** 3 ноября 2025  
**Версия:** v2.4 FINAL  
**Статус:** ✅ Production Ready  
**Подход:** Staging (промежуточное хранилище)

---

## 📋 СОДЕРЖАНИЕ

1. [Установка](#установка)
2. [Структура файлов](#структура-файлов)
3. [Фаза 1: Загрузка HTML](#фаза-1-загрузка-html)
4. [Фаза 2: Парсинг LLM](#фаза-2-парсинг-llm)
5. [Фаза 3: Маппинг в care_homes](#фаза-3-маппинг-в-care_homes)
6. [Мониторинг](#мониторинг)
7. [Примеры использования](#примеры-использования)

---

## 🛠️ УСТАНОВКА

### Шаг 1: Установить зависимости

```bash
pip install psycopg2-binary python-dotenv openai requests
```

### Шаг 2: Настроить .env файл

Создайте `.env` файл в корне проекта:

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=care_homes
DB_USER=postgres
DB_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=sk-...

# Firecrawl (опционально, если используете phase1_load_html.py)
FIRECRAWL_API_KEY=fc-...
```

### Шаг 3: Создать staging таблицу

```bash
psql -U postgres -d care_homes -f input/autumna/staging/01_create_staging_table.sql
```

### Шаг 4: Установить SQL функции нормализации

```bash
psql -U postgres -d care_homes -f input/autumna/staging/02_sql_helper_functions.sql
```

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
input/autumna/staging/
├── 01_create_staging_table.sql          # SQL для создания staging таблицы
├── 02_sql_helper_functions.sql          # SQL функции нормализации
├── phase1_load_html.py                  # Фаза 1: Загрузка HTML из Firecrawl
├── phase2_parse_llm.py                  # Фаза 2: Парсинг через OpenAI
├── phase3_map_to_care_homes.py          # Фаза 3: Маппинг в care_homes
└── README.md                             # Этот файл
```

---

## 🔄 ФАЗА 1: ЗАГРУЗКА HTML

**Цель:** Сохранить HTML всех страниц Autumna в staging таблицу один раз

**Использование:**

```bash
# Подготовить список URL (по одному на строку)
echo "https://www.autumna.co.uk/care-homes/birmingham/home1/1-1234567890" > urls.txt
echo "https://www.autumna.co.uk/care-homes/birmingham/home2/1-2345678901" >> urls.txt

# Запустить загрузку с Firecrawl API v2.5 (рекомендуется)
python input/autumna/staging/phase1_load_html.py \
    --urls urls.txt \
    --api-key YOUR_FIRECRAWL_API_KEY \
    --api-version v2.5 \
    --use-cache

# Или без cache (для получения свежих данных)
python input/autumna/staging/phase1_load_html.py \
    --urls urls.txt \
    --api-key YOUR_FIRECRAWL_API_KEY \
    --api-version v2.5

# Использовать старую версию v1 (для обратной совместимости)
python input/autumna/staging/phase1_load_html.py \
    --urls urls.txt \
    --api-key YOUR_FIRECRAWL_API_KEY \
    --api-version v1
```

**Параметры:**
- `--api-version`: Версия API (`v1`, `v2`, `v2.5`). По умолчанию `v2.5`
- `--use-cache`: Использовать semantic index cache (v2.5+). Ускоряет запросы и экономит средства
- `--dry-run`: Тестовый запуск без сохранения

**Что происходит:**
1. Отправляет URLs в Firecrawl API (v2.5 по умолчанию)
2. Получает HTML для каждой страницы (с улучшенным качеством благодаря custom browser stack)
3. Сохраняет в `autumna_staging.html_content`
4. Извлекает `cqc_location_id` из URL

**🔥 Firecrawl API v2.5 преимущества:**
- 🚀 **Semantic Index**: До 40% запросов обслуживаются мгновенно из cache
- 🎯 **Custom Browser Stack**: Максимальное качество данных
- ⚡ **Автоматическое определение рендеринга**: Быстрая обработка любых страниц
- 💰 **Экономия**: Использование cache снижает стоимость и время обработки

**Время:** 
- С cache (v2.5): 5-8 минут для 300 страниц (40% из cache)
- Без cache (v2.5): 10-15 минут для 300 страниц
- v1: 15-20 минут для 300 страниц

**Стоимость:** $15 (один раз!)

**Проверка результатов:**

```sql
SELECT COUNT(*) as total, 
       COUNT(*) FILTER (WHERE html_content IS NOT NULL) as with_html
FROM autumna_staging;
```

---

## 🤖 ФАЗА 2: ПАРСИНГ LLM

**Цель:** Извлечь структурированные данные из HTML с помощью ChatGPT

**Использование:**

```bash
# Стандартный запуск
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.4 \
    --batch-size 25

# Переобработать записи с needs_reparse=TRUE
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.5 \
    --reparse \
    --batch-size 25
```

**Параметры:**
- `--prompt-version`: Версия промпта (v2.4, v2.5, experimental_1, etc.)
- `--batch-size`: Размер батча (по умолчанию: 25)
- `--reparse`: Переобработать записи с `needs_reparse=TRUE`
- `--dry-run`: Тестовый запуск без сохранения

**Что происходит:**
1. Выбирает записи без `parsed_json` (или с `needs_reparse=TRUE`)
2. Отправляет `html_content` в OpenAI ChatGPT
3. Получает JSON Schema v2.4 (188 полей)
4. Сохраняет в `autumna_staging.parsed_json`
5. Обновляет `llm_prompt_version`, `data_quality_score`, `extraction_confidence`

**Время:** 20-30 минут для 300 страниц  
**Стоимость:** $1.62 каждый раз (можно повторять многократно!)

**Проверка результатов:**

```sql
SELECT 
    llm_prompt_version,
    COUNT(*) as total,
    AVG(data_quality_score)::INTEGER as avg_quality,
    COUNT(*) FILTER (WHERE extraction_confidence = 'high') as high_confidence
FROM autumna_staging
WHERE parsed_json IS NOT NULL
GROUP BY llm_prompt_version;
```

---

## 🔄 ФАЗА 3: МАППИНГ В CARE_HOMES

**Цель:** Преобразовать `parsed_json` (188 полей) в `care_homes` (93 поля)

**Использование:**

```bash
# Стандартный запуск (минимальный quality score = 60)
python input/autumna/staging/phase3_map_to_care_homes.py \
    --min-quality 60 \
    --batch-size 100

# Более строгий фильтр (quality score >= 90)
python input/autumna/staging/phase3_map_to_care_homes.py \
    --min-quality 90 \
    --batch-size 100
```

**Параметры:**
- `--min-quality`: Минимальный quality score (по умолчанию: 60)
- `--batch-size`: Размер батча (по умолчанию: 100)
- `--dry-run`: Тестовый запуск без сохранения

**Что происходит:**
1. Выбирает записи с `parsed_json` и `quality_score >= min_quality`
2. Преобразует JSON Schema v2.4 → care_homes структуру
3. Валидирует данные (критические поля, координаты, beds)
4. Вставляет в `care_homes` с SQL функциями нормализации
5. Обновляет `autumna_staging.processed = TRUE`

**Время:** 1-2 минуты для 300 записей  
**Стоимость:** $0 (только локальная обработка)

**Проверка результатов:**

```sql
SELECT 
    COUNT(*) as total_processed,
    COUNT(*) FILTER (WHERE processed = TRUE) as synced_to_care_homes
FROM autumna_staging
WHERE parsed_json IS NOT NULL;
```

---

## 📊 МОНИТОРИНГ

### Статистика обработки

```sql
SELECT * FROM v_staging_stats;
```

Показывает:
- Сколько HTML загружено
- Сколько распарсено
- Сколько синхронизировано в care_homes
- Средний quality score
- Количество записей с высоким/низким качеством

### Качество по версиям промпта

```sql
SELECT * FROM v_staging_prompt_stats;
```

Показывает эффективность разных версий промптов для сравнения.

### Записи готовые для маппинга

```sql
SELECT * FROM v_staging_ready_for_mapping LIMIT 10;
```

### Проблемные записи

```sql
SELECT * FROM v_staging_problems LIMIT 20;
```

---

## 💡 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Сценарий 1: Первая загрузка (300 домов)

```bash
# 1. Загрузить HTML
python input/autumna/staging/phase1_load_html.py \
    --urls urls_birmingham_300.txt \
    --api-key $FIRECRAWL_API_KEY

# 2. Парсинг LLM
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.4 \
    --batch-size 25

# 3. Маппинг в care_homes
python input/autumna/staging/phase3_map_to_care_homes.py \
    --min-quality 60 \
    --batch-size 100
```

**Стоимость:** $16.62 ($15 Firecrawl + $1.62 OpenAI)

---

### Сценарий 2: Улучшили промпт - переобработать все записи

```bash
# 1. Пометить все записи для переобработки
psql -d care_homes -c "
UPDATE autumna_staging
SET needs_reparse = TRUE
WHERE parsed_json IS NOT NULL;
"

# 2. Переобработать с новым промптом
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.5 \
    --reparse \
    --batch-size 25

# 3. Сравнить результаты
psql -d care_homes -c "
SELECT 
    llm_prompt_version,
    AVG(data_quality_score)::INTEGER as avg_quality,
    COUNT(*) as count
FROM autumna_staging
WHERE parsed_json IS NOT NULL
GROUP BY llm_prompt_version;
"
```

**Стоимость:** $1.62 (только OpenAI, HTML уже есть!)

---

### Сценарий 3: Тестируем 2 версии промпта

```bash
# Версия A: v2.4
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.4 \
    --batch-size 25

# Версия B: experimental_v1
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version experimental_v1 \
    --batch-size 25

# Сравнить результаты
psql -d care_homes -c "
SELECT * FROM v_staging_prompt_stats;
"
```

**Стоимость:** $3.24 (два раза по $1.62)  
**При прямом пути:** $31.62 (нужно было бы заново качать HTML!)

---

### Сценарий 4: Упал процесс на 150-й странице

```bash
# Просто запустить снова - он продолжит с 151-й
python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.4 \
    --batch-size 25
```

**Стоимость:** $0 (просто перезапуск)

---

### Сценарий 5: Постепенная загрузка (волнами)

```bash
# День 1: Первые 50 домов
python input/autumna/staging/phase1_load_html.py \
    --urls urls_first_50.txt \
    --api-key $FIRECRAWL_API_KEY

python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.4 \
    --batch-size 25

# Проверить качество
psql -d care_homes -c "SELECT * FROM v_staging_stats;"

# День 2: Если качество хорошее - загрузить следующие 50
python input/autumna/staging/phase1_load_html.py \
    --urls urls_next_50.txt \
    --api-key $FIRECRAWL_API_KEY

python input/autumna/staging/phase2_parse_llm.py \
    --prompt-version v2.4 \
    --batch-size 25
```

---

## 🔍 ОТЛАДКА

### Проблема: OpenAI API ошибки

**Симптом:** `phase2_parse_llm.py` падает с ошибками API

**Решение:**
- Проверить `OPENAI_API_KEY` в `.env`
- Проверить баланс OpenAI аккаунта
- Уменьшить `--batch-size` для меньшей нагрузки
- Добавить задержки между запросами

### Проблема: SQL функции не найдены

**Симптом:** `ERROR: function safe_latitude(text) does not exist`

**Решение:**
```bash
psql -U postgres -d care_homes -f input/autumna/staging/02_sql_helper_functions.sql
```

### Проблема: Низкое качество парсинга

**Симптом:** `data_quality_score < 60` для многих записей

**Решение:**
1. Проверить проблемные записи:
   ```sql
   SELECT * FROM v_staging_problems LIMIT 10;
   ```
2. Улучшить промпт в `AUTUMNA_PARSING_PROMPT_v2_4.md`
3. Переобработать с новым промптом (см. Сценарий 2)

---

## 📈 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### После первой загрузки (300 домов):

- ✅ HTML загружен: 300 записей
- ✅ Парсинг завершен: 285-300 записей (95-100%)
- ✅ Высокое качество (score ≥ 90): 255-270 записей (85-90%)
- ✅ Среднее качество (score 60-89): 25-30 записей (8-10%)
- ✅ Низкое качество (score < 60): 5-15 записей (2-5%)

### После маппинга в care_homes:

- ✅ Успешно обработано: 270-285 записей (90-95%)
- ✅ Требуют проверки: 15-30 записей (5-10%)
- ✅ Ошибки: 0-5 записей (0-2%)

---

## 💰 ЭКОНОМИЯ

### Прямой путь (без staging):

- 1-я загрузка: $16.62
- 2-я (улучшили промпт): $31.62
- 3-я: $46.62
- **5 итераций: $76.62**

### Staging путь:

- 1-я загрузка: $16.62
- 2-я (улучшили промпт): $18.24 ($1.62 только OpenAI!)
- 3-я: $19.86
- **5 итераций: $23.10**

**Экономия:** $53.52 (70% дешевле!)

---

## 📞 ПОДДЕРЖКА

**Документация:**
- Полная архитектура: `input/autumna/STAGING_ARCHITECTURE_v2.4.md`
- Методология: `input/autumna/AUTUMNA_SCRAPING_METHODOLOGY_PM.md`

**Ключевые файлы:**
- System Prompt: `input/autumna/AUTUMNA_PARSING_PROMPT_v2_4.md`
- JSON Schema: `input/autumna/response_format_v2_4.json`
- Database Schema: `input/care_homes_db_v2_2.sql`

---

**Дата:** 3 ноября 2025  
**Версия:** v2.4 FINAL  
**Статус:** ✅ Production Ready

