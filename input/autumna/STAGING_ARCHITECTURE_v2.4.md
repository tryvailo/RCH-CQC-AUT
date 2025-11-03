# 🏗️ STAGING АРХИТЕКТУРА: Autumna → care_homes v2.4
## Рекомендуемый подход для bootstrap проекта

**Дата:** 3 ноября 2025  
**Версия:** v2.4 FINAL  
**Статус:** ✅ РЕКОМЕНДУЕТСЯ ДЛЯ PRODUCTION  
**Подход:** Staging (промежуточное хранилище)

---

## 🎯 EXECUTIVE SUMMARY

### Два подхода к обработке данных Autumna:

1. **❌ Прямой путь (Direct Path)** - сразу парсим и сохраняем
   - Просто, но дорого при итерациях ($15 за каждую попытку улучшения)
   - Подходит для: одноразовой загрузки с идеальными инструкциями

2. **✅ Staging подход (РЕКОМЕНДУЕТСЯ)** - сохраняем HTML, потом парсим многократно
   - Экономит $66.90+ при 5 итерациях развития
   - Подходит для: bootstrap проектов, итеративного развития

### Рекомендация: **✅ Staging подход**

**Почему?**
- Вы на стадии bootstrap и будете итеративно улучшать результаты
- Экономия окупается уже на второй попытке улучшения инструкций
- Дает больше гибкости и контроля над процессом
- Позволяет тестировать разные версии промптов на одних данных

---

## 💰 ЭКОНОМИЧЕСКОЕ ОБОСНОВАНИЕ

### Сценарий: 300 домов в Бирмингеме

| Итерация | Прямой путь | Staging путь | Экономия |
|----------|-------------|--------------|----------|
| 1-я загрузка | $16.62 | $16.62 | - |
| 2-я (улучшили промпт) | +$15 = $31.62 | +$1.62 = $18.24 | $13.38 |
| 3-я (еще улучшения) | +$15 = $46.62 | +$1.62 = $19.86 | $26.76 |
| 4-я | +$15 = $61.62 | +$1.62 = $21.48 | $40.14 |
| 5-я | +$15 = $76.62 | +$1.62 = $23.10 | $53.52 |
| **ИТОГО** | **$76.62** | **$23.10** | **$53.52** ✅ |

**Экономия при 5 итерациях:** $53.52 (70% дешевле!)

### Разбивка затрат:

**Прямой путь:**
- Firecrawl: $15 × 5 = $75
- OpenAI: $1.62 × 5 = $8.10
- **Всего: $83.10**

**Staging путь:**
- Firecrawl: $15 × 1 = $15 (только первый раз!)
- OpenAI: $1.62 × 5 = $8.10
- **Всего: $23.10**

---

## 🏗️ АРХИТЕКТУРА STAGING ПОДХОДА

### Общая схема:

```
┌─────────────────┐
│  Firecrawl API  │ (Один раз: $15)
└────────┬────────┘
         │ HTML
         ↓
┌─────────────────────┐
│  staging_raw table  │ (Промежуточное хранилище)
│  - html_content     │
│  - parsed_json      │
│  - quality_score    │
│  - llm_prompt_ver   │
└────────┬────────────┘
         │
         ├─→ OpenAI LLM (Многократно: $1.62 каждый раз)
         │   ↓
         │   parsed_json
         │   ↓
         │   UPDATE staging_raw
         │
         └─→ Python Mapper (Трансформация)
              ↓
         ┌─────────────────┐
         │  care_homes     │ (Финальная БД)
         │  (93 поля)      │
         └─────────────────┘
```

---

## 📊 СТРУКТУРА БАЗЫ ДАННЫХ

### Таблица: `autumna_staging` (Промежуточное хранилище)

```sql
CREATE TABLE autumna_staging (
    -- PRIMARY KEY
    id BIGSERIAL PRIMARY KEY,
    
    -- ИДЕНТИФИКАЦИЯ
    source_url TEXT NOT NULL UNIQUE,
    cqc_location_id TEXT,  -- Извлечено из URL для быстрого поиска
    scraped_at TIMESTAMPTZ NOT NULL,
    
    -- ИСХОДНЫЕ ДАННЫЕ (сохраняются один раз)
    html_content TEXT NOT NULL,  -- ВЕСЬ HTML текст страницы
    firecrawl_metadata JSONB,    -- Метаданные от Firecrawl (status, timestamp, etc.)
    
    -- РЕЗУЛЬТАТЫ ПАРСИНГА (обновляются многократно)
    parsed_json JSONB,           -- Результат от ChatGPT (JSON Schema v2.4, 188 полей)
    extraction_confidence TEXT,  -- 'high', 'medium', 'low' (из extraction_metadata)
    data_quality_score INTEGER, -- Quality score (0-100) от Python mapper
    is_dormant BOOLEAN DEFAULT FALSE,
    
    -- ВЕРСИОНИРОВАНИЕ И ОТЛАДКА
    llm_model TEXT,             -- 'gpt-4o-2024-08-06', 'gpt-4-turbo', etc.
    llm_prompt_version TEXT,    -- 'v2.4', 'v2.5', 'experimental_1', etc.
    parsing_errors JSONB,       -- Ошибки парсинга (critical_fields_missing, etc.)
    mapping_errors JSONB,       -- Ошибки маппинга (validation failures)
    
    -- ФЛАГИ ОБРАБОТКИ
    needs_reparse BOOLEAN DEFAULT FALSE,     -- Нужно ли переобработать
    needs_validation BOOLEAN DEFAULT FALSE, -- Нужна ли ручная проверка
    processed BOOLEAN DEFAULT FALSE,         -- Обработан ли в care_homes
    processed_at TIMESTAMPTZ,                -- Когда обработан в care_homes
    
    -- СВЯЗЬ С ФИНАЛЬНОЙ БД
    care_homes_id BIGINT,                    -- FK на care_homes.id (после маппинга)
    
    -- ВРЕМЕННЫЕ МЕТКИ
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ИНДЕКСЫ для быстрого поиска
CREATE INDEX idx_staging_url ON autumna_staging(source_url);
CREATE INDEX idx_staging_cqc_id ON autumna_staging(cqc_location_id) WHERE cqc_location_id IS NOT NULL;
CREATE INDEX idx_staging_processed ON autumna_staging(processed) WHERE processed = FALSE;
CREATE INDEX idx_staging_quality ON autumna_staging(data_quality_score DESC NULLS LAST);
CREATE INDEX idx_staging_reparse ON autumna_staging(needs_reparse) WHERE needs_reparse = TRUE;
CREATE INDEX idx_staging_prompt_version ON autumna_staging(llm_prompt_version);

-- ТРИГГЕР для обновления updated_at
CREATE OR REPLACE FUNCTION update_staging_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_staging_updated_at
    BEFORE UPDATE ON autumna_staging
    FOR EACH ROW
    EXECUTE FUNCTION update_staging_updated_at();

-- КОММЕНТАРИИ
COMMENT ON TABLE autumna_staging IS 'Промежуточное хранилище для парсинга Autumna HTML страниц';
COMMENT ON COLUMN autumna_staging.html_content IS 'Исходный HTML текст страницы - сохраняется один раз';
COMMENT ON COLUMN autumna_staging.parsed_json IS 'Результат парсинга ChatGPT (JSON Schema v2.4) - обновляется многократно';
COMMENT ON COLUMN autumna_staging.llm_prompt_version IS 'Версия промпта для отслеживания эффективности разных версий';
COMMENT ON COLUMN autumna_staging.needs_reparse IS 'Флаг для повторной обработки (например, после улучшения промпта)';
```

---

## 🔄 ТРИ ФАЗЫ ОБРАБОТКИ

### ФАЗА 1: Загрузка HTML (выполняется ОДИН РАЗ)

**Цель:** Сохранить HTML всех страниц в `staging_raw`

**Workflow:**
```
1. Подготовить список URL (300 домов)
2. Отправить в Firecrawl API
3. Дождаться завершения (10-15 минут)
4. Сохранить HTML в staging_raw.html_content
```

**SQL после получения HTML:**
```sql
INSERT INTO autumna_staging (
    source_url,
    cqc_location_id,
    scraped_at,
    html_content,
    firecrawl_metadata
) VALUES (
    'https://www.autumna.co.uk/care-homes/birmingham/meadow-rose/1-1234567890',
    '1-1234567890',  -- Извлечено из URL
    CURRENT_TIMESTAMP,
    '<html>...</html>',  -- Полный HTML от Firecrawl
    '{"status": "success", "scraped_at": "2025-11-03T10:00:00Z"}'::jsonb
)
ON CONFLICT (source_url) DO UPDATE
SET 
    html_content = EXCLUDED.html_content,
    firecrawl_metadata = EXCLUDED.firecrawl_metadata,
    scraped_at = EXCLUDED.scraped_at;
```

**Время:** 10-15 минут для 300 страниц  
**Стоимость:** $15 (один раз!)

---

### ФАЗА 2: Извлечение данных LLM (можно повторять сколько угодно)

**Цель:** Извлечь структурированные данные из HTML с помощью ChatGPT

**Workflow:**
```
1. Выбрать записи без parsed_json (или needs_reparse = TRUE)
2. Для каждой записи:
   - Отправить html_content в ChatGPT с промптом v2.4
   - Получить JSON Schema v2.4 (188 полей)
   - Сохранить в parsed_json
   - Обновить llm_prompt_version
3. Вычислить quality_score
```

**Python код (пример):**
```python
import openai
import json
import psycopg2

# Подключение к БД
conn = psycopg2.connect("...")
cursor = conn.cursor()

# Загрузить промпт и schema
with open('AUTUMNA_PARSING_PROMPT_v2_4.md') as f:
    system_prompt = f.read()

with open('response_format_v2_4.json') as f:
    response_format = json.load(f)

# Получить записи без parsed_json
cursor.execute("""
    SELECT id, html_content, source_url, cqc_location_id
    FROM autumna_staging
    WHERE parsed_json IS NULL OR needs_reparse = TRUE
    ORDER BY created_at ASC
    LIMIT 100
""")

records = cursor.fetchall()

for record in records:
    try:
        # Парсинг с ChatGPT
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": record['html_content']}
            ],
            response_format={"type": "json_schema", "json_schema": response_format['json_schema']}
        )
        
        parsed_json = json.loads(response.choices[0].message.content)
        
        # Извлечь метаданные
        extraction_metadata = parsed_json.get('extraction_metadata', {})
        confidence = extraction_metadata.get('extraction_confidence', 'medium')
        quality_score = extraction_metadata.get('data_quality_score')
        is_dormant = extraction_metadata.get('is_dormant', False)
        
        # Сохранить результат
        cursor.execute("""
            UPDATE autumna_staging
            SET 
                parsed_json = %(parsed_json)s::jsonb,
                extraction_confidence = %(confidence)s,
                data_quality_score = %(quality_score)s,
                is_dormant = %(is_dormant)s,
                llm_model = 'gpt-4o-2024-08-06',
                llm_prompt_version = 'v2.4',
                parsing_errors = %(errors)s::jsonb,
                needs_reparse = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(id)s
        """, {
            'id': record['id'],
            'parsed_json': json.dumps(parsed_json),
            'confidence': confidence,
            'quality_score': quality_score,
            'is_dormant': is_dormant,
            'errors': json.dumps({
                'critical_fields_missing': extraction_metadata.get('critical_fields_missing', []),
                'data_quality_notes': extraction_metadata.get('data_quality_notes')
            })
        })
        
        print(f"✅ Parsed: {record['source_url']} (quality: {quality_score})")
        
    except Exception as e:
        print(f"❌ Error parsing {record['source_url']}: {e}")
        cursor.execute("""
            UPDATE autumna_staging
            SET parsing_errors = %(error)s::jsonb
            WHERE id = %(id)s
        """, {
            'id': record['id'],
            'error': json.dumps({'error': str(e), 'timestamp': str(datetime.now())})
        })

conn.commit()
```

**Время:** 20-30 минут для 300 страниц  
**Стоимость:** $1.62 каждый раз (можно повторять бесплатно, HTML уже в БД!)

**Что делать если захотели улучшить промпт:**
1. Изменить промпт в файле `AUTUMNA_PARSING_PROMPT_v2_4.md`
2. Обновить `llm_prompt_version` на `'v2.5'` в коде
3. Запустить этот workflow снова (HTML уже есть!)
4. Сравнить результаты: `SELECT llm_prompt_version, AVG(data_quality_score) FROM autumna_staging GROUP BY llm_prompt_version`

---

### ФАЗА 3: Маппинг в финальную БД (выполняется в конце)

**Цель:** Преобразовать `parsed_json` (188 полей) в `care_homes` (93 поля)

**Workflow:**
```
1. Выбрать записи с parsed_json и quality_score >= 60
2. Для каждой записи:
   - Преобразовать JSON Schema v2.4 → care_homes структуру
   - Валидировать данные
   - Вызвать SQL функции (safe_latitude, safe_longitude, etc.)
   - INSERT/UPDATE в care_homes
3. Обновить processed = TRUE
```

**Python код (пример):**
```python
# Загрузить mapper функцию
from autumna_mapper_v2_4 import map_autumna_to_db

# Получить записи для маппинга
cursor.execute("""
    SELECT 
        id,
        parsed_json,
        source_url,
        cqc_location_id,
        data_quality_score,
        extraction_confidence
    FROM autumna_staging
    WHERE parsed_json IS NOT NULL
      AND processed = FALSE
      AND data_quality_score >= 60  -- Минимальный порог качества
    ORDER BY data_quality_score DESC
    LIMIT 100
""")

records = cursor.fetchall()

success_count = 0
failed_count = 0

for record in records:
    try:
        parsed_json = json.loads(record['parsed_json'])
        
        # Маппинг Autumna JSON → care_homes структура
        db_data = map_autumna_to_db(parsed_json)
        
        # Валидация критических полей
        if not db_data.get('cqc_location_id') or not db_data.get('name'):
            raise ValueError("Missing critical fields")
        
        # INSERT в care_homes с SQL функциями
        cursor.execute("""
            INSERT INTO care_homes (
                cqc_location_id,
                name,
                city,
                postcode,
                latitude,
                longitude,
                -- ... все остальные поля
            ) VALUES (
                %(cqc_location_id)s,
                clean_text(%(name)s),
                clean_text(%(city)s),
                normalize_uk_postcode(%(postcode)s),
                safe_latitude(%(latitude)s),
                safe_longitude(%(longitude)s),
                -- ... все остальные поля с SQL функциями
            )
            ON CONFLICT (cqc_location_id) DO UPDATE
            SET 
                name = EXCLUDED.name,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, db_data)
        
        care_homes_id = cursor.fetchone()[0]
        
        # Обновить staging запись
        cursor.execute("""
            UPDATE autumna_staging
            SET 
                processed = TRUE,
                processed_at = CURRENT_TIMESTAMP,
                care_homes_id = %(care_homes_id)s
            WHERE id = %(id)s
        """, {
            'id': record['id'],
            'care_homes_id': care_homes_id
        })
        
        success_count += 1
        
    except Exception as e:
        print(f"❌ Error mapping {record['source_url']}: {e}")
        cursor.execute("""
            UPDATE autumna_staging
            SET 
                mapping_errors = %(error)s::jsonb,
                needs_validation = TRUE
            WHERE id = %(id)s
        """, {
            'id': record['id'],
            'error': json.dumps({'error': str(e), 'timestamp': str(datetime.now())})
        })
        failed_count += 1

conn.commit()
print(f"✅ Success: {success_count}, ❌ Failed: {failed_count}")
```

**Время:** 1-2 минуты для 300 записей  
**Стоимость:** $0 (только локальная обработка)

---

## 🔧 РАБОТА С N8N (No-Code Automation)

### Workflow #1: Загрузка HTML (Firecrawl → staging_raw)

**Блоки n8n:**

1. **Manual Trigger** - запуск вручную
2. **Set** - подготовить массив URL (300 домов)
3. **HTTP Request** - POST в Firecrawl API с batch URL
4. **Wait** - ждем 15 минут (Firecrawl обрабатывает)
5. **HTTP Request** - GET статус задачи Firecrawl
6. **Loop** - для каждого результата:
   - Извлечь `cqc_location_id` из URL
   - **PostgreSQL** - INSERT в `autumna_staging`
7. **Slack** - уведомление о завершении

**Код для извлечения CQC ID:**
```javascript
// В Code блоке n8n
const url = $input.item.json.url;
const match = url.match(/\/1-(\d{10})/);
const cqcId = match ? `1-${match[1]}` : null;

return {
  json: {
    cqc_location_id: cqcId,
    url: url
  }
};
```

---

### Workflow #2: Парсинг LLM (staging_raw → parsed_json)

**Блоки n8n:**

1. **Manual Trigger** - запуск вручную (или по расписанию)
2. **PostgreSQL** - SELECT записи без `parsed_json`:
   ```sql
   SELECT id, html_content, source_url
   FROM autumna_staging
   WHERE parsed_json IS NULL OR needs_reparse = TRUE
   ORDER BY created_at ASC
   LIMIT 25
   ```
3. **Split In Batches** - батчи по 25 записей
4. **Loop** - для каждой записи:
   - **OpenAI** - Chat Completion с `html_content` и промптом v2.4
   - **Code** - извлечь `quality_score`, `confidence` из ответа
   - **PostgreSQL** - UPDATE `parsed_json`:
     ```sql
     UPDATE autumna_staging
     SET 
       parsed_json = %(parsed_json)s::jsonb,
       extraction_confidence = %(confidence)s,
       data_quality_score = %(quality_score)s,
       llm_prompt_version = 'v2.4',
       needs_reparse = FALSE
     WHERE id = %(id)s
     ```
5. **Slack** - прогресс и статистика

**Настройки OpenAI блока:**
- Model: `gpt-4o-2024-08-06`
- System Prompt: загрузить из `AUTUMNA_PARSING_PROMPT_v2_4.md`
- Response Format: JSON Schema из `response_format_v2_4.json`

---

### Workflow #3: Маппинг в финальную БД (staging_raw → care_homes)

**Блоки n8n:**

1. **Manual Trigger** - запуск вручную
2. **PostgreSQL** - SELECT записи с `parsed_json`:
   ```sql
   SELECT id, parsed_json, data_quality_score
   FROM autumna_staging
   WHERE parsed_json IS NOT NULL
     AND processed = FALSE
     AND data_quality_score >= 60
   ORDER BY data_quality_score DESC
   ```
3. **Loop** - для каждой записи:
   - **Code** - вызвать `map_autumna_to_db(parsed_json)`
   - **PostgreSQL** - INSERT в `care_homes` с SQL функциями
   - **PostgreSQL** - UPDATE `processed = TRUE`
4. **Slack** - финальная статистика

---

## 🎯 ПРАКТИЧЕСКИЕ СЦЕНАРИИ

### Сценарий 1: Улучшили промпт - нужно переобработать

**Проблема:** Обновили `AUTUMNA_PARSING_PROMPT_v2_4.md`, хотите переобработать все записи

**Решение:**
```sql
-- Пометить все записи для переобработки
UPDATE autumna_staging
SET needs_reparse = TRUE
WHERE parsed_json IS NOT NULL;
```

Затем запустить **Workflow #2** снова (но с новой версией промпта в коде).

**Стоимость:** $1.62 (только ChatGPT, HTML уже есть!)

---

### Сценарий 2: Упал процесс на 150-й странице

**Проблема:** Workflow #2 упал после обработки 150 записей

**Решение:**
Просто запустить **Workflow #2** снова - он автоматически продолжит с записей где `parsed_json IS NULL`.

**Стоимость:** $0 (просто перезапуск)

---

### Сценарий 3: Тестируем 2 версии промпта

**Цель:** Сравнить эффективность v2.4 и experimental_v1

**Решение:**
```python
# Первый запуск: v2.4
# Обновить llm_prompt_version = 'v2.4' в коде
# Запустить Workflow #2

# Второй запуск: experimental_v1
# Изменить промпт на experimental версию
# Обновить llm_prompt_version = 'experimental_v1' в коде
# Запустить Workflow #2 снова

# Сравнить результаты
SELECT 
    llm_prompt_version,
    AVG(data_quality_score) as avg_quality,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE data_quality_score >= 90) as high_quality_count
FROM autumna_staging
WHERE parsed_json IS NOT NULL
GROUP BY llm_prompt_version;
```

**Стоимость:** $3.24 (два раза по $1.62)  
**При прямом пути:** $31.62 (нужно было бы заново качать HTML!)

---

### Сценарий 4: Постепенная загрузка (волнами)

**Цель:** Загрузить 50 домов, проверить качество, потом еще 50

**Решение:**
```sql
-- Обработать только первые 50 записей
SELECT id, html_content
FROM autumna_staging
WHERE parsed_json IS NULL
ORDER BY created_at ASC
LIMIT 50;
```

Запустить Workflow #2 только для этих 50 записей. Проверить качество. Если хорошо - обработать следующие 50.

---

## 📊 МОНИТОРИНГ И АНАЛИТИКА

### SQL запросы для мониторинга:

**Статус обработки:**
```sql
SELECT 
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE html_content IS NOT NULL) as html_loaded,
    COUNT(*) FILTER (WHERE parsed_json IS NOT NULL) as parsed,
    COUNT(*) FILTER (WHERE processed = TRUE) as synced_to_production,
    COUNT(*) FILTER (WHERE needs_reparse = TRUE) as needs_reparse,
    COUNT(*) FILTER (WHERE needs_validation = TRUE) as needs_validation
FROM autumna_staging;
```

**Качество по версиям промпта:**
```sql
SELECT 
    llm_prompt_version,
    COUNT(*) as total_parsed,
    AVG(data_quality_score)::INTEGER as avg_quality,
    MIN(data_quality_score) as min_quality,
    MAX(data_quality_score) as max_quality,
    COUNT(*) FILTER (WHERE data_quality_score >= 90) as high_quality,
    COUNT(*) FILTER (WHERE data_quality_score < 60) as low_quality,
    COUNT(*) FILTER (WHERE extraction_confidence = 'high') as high_confidence
FROM autumna_staging
WHERE parsed_json IS NOT NULL
GROUP BY llm_prompt_version
ORDER BY avg_quality DESC;
```

**Проблемные записи:**
```sql
SELECT 
    source_url,
    cqc_location_id,
    data_quality_score,
    extraction_confidence,
    parsing_errors,
    mapping_errors
FROM autumna_staging
WHERE 
    (data_quality_score < 60 OR data_quality_score IS NULL)
    OR needs_validation = TRUE
    OR parsing_errors IS NOT NULL
ORDER BY data_quality_score ASC NULLS LAST;
```

**Эффективность по времени:**
```sql
SELECT 
    DATE_TRUNC('day', scraped_at) as date,
    COUNT(*) as scraped_count,
    COUNT(*) FILTER (WHERE parsed_json IS NOT NULL) as parsed_count,
    COUNT(*) FILTER (WHERE processed = TRUE) as synced_count,
    AVG(EXTRACT(EPOCH FROM (updated_at - scraped_at))) / 60 as avg_minutes_to_parse
FROM autumna_staging
GROUP BY DATE_TRUNC('day', scraped_at)
ORDER BY date DESC;
```

---

## ⚠️ ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ

### 1. Хранение HTML

**Размер:** ~100-500 KB на страницу  
**Для 300 домов:** ~30-150 MB

**Рекомендация:** 
- Хранить HTML минимум 30 дней после успешной обработки
- После 30 дней можно удалить для экономии места:
  ```sql
  DELETE FROM autumna_staging
  WHERE processed = TRUE
    AND processed_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
  ```

### 2. Версионирование промптов

**Важно:** Всегда обновлять `llm_prompt_version` при изменении промпта!

Это позволяет:
- Сравнивать эффективность разных версий
- Откатываться к предыдущим версиям
- Анализировать историю улучшений

### 3. Обработка ошибок

**Стратегия:**
- При ошибке парсинга → сохранить в `parsing_errors`
- При ошибке маппинга → сохранить в `mapping_errors`
- Установить `needs_validation = TRUE` для ручной проверки

**Не удалять записи с ошибками!** Они нужны для анализа и улучшения процесса.

---

## ✅ ЧЕКЛИСТ ВНЕДРЕНИЯ

### Шаг 1: Создать staging таблицу
- [ ] Выполнить SQL создания `autumna_staging`
- [ ] Создать индексы
- [ ] Проверить триггеры

### Шаг 2: Настроить Workflow #1 (Загрузка HTML)
- [ ] Подготовить список URL (300 домов)
- [ ] Настроить Firecrawl API интеграцию
- [ ] Настроить n8n workflow или Python скрипт
- [ ] Протестировать на 5-10 URL

### Шаг 3: Настроить Workflow #2 (LLM Парсинг)
- [ ] Настроить OpenAI API ключ
- [ ] Загрузить промпт v2.4 и JSON Schema
- [ ] Настроить n8n workflow или Python скрипт
- [ ] Протестировать на 10-20 записях

### Шаг 4: Настроить Workflow #3 (Маппинг)
- [ ] Подготовить Python mapper функцию
- [ ] Проверить SQL функции в БД
- [ ] Настроить n8n workflow или Python скрипт
- [ ] Протестировать на 10-20 записях

### Шаг 5: Мониторинг
- [ ] Настроить SQL запросы для мониторинга
- [ ] Настроить алерты (Slack/Email) при ошибках
- [ ] Создать дашборд с метриками

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

## 🎯 РЕЗЮМЕ

**Рекомендуемый подход:** ✅ **Staging (промежуточное хранилище)**

**Причины:**
1. Экономия $53.52+ при 5 итерациях развития
2. Гибкость: легко менять промпты и тестировать
3. Надежность: возможность повторной обработки при ошибках
4. История: отслеживание эффективности разных версий промптов

**Архитектура:**
```
Firecrawl ($15 один раз) 
  → staging_raw.html_content 
  → ChatGPT ($1.62 многократно) 
  → staging_raw.parsed_json 
  → Python Mapper 
  → care_homes (финальная БД)
```

**Инструменты:**
- n8n (no-code автоматизация) или Python скрипты
- Firecrawl API (загрузка HTML)
- OpenAI ChatGPT API (парсинг)
- PostgreSQL (база данных)

**Сроки:**
- Разработка: 2-3 дня
- Первая загрузка: 30-45 минут автоматически
- Последующие итерации: 20-30 минут (без Firecrawl!)

---

**Дата:** 3 ноября 2025  
**Версия:** v2.4 FINAL  
**Статус:** ✅ РЕКОМЕНДУЕТСЯ ДЛЯ PRODUCTION

