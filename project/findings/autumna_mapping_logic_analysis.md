# 🔄 ЛОГИКА МАППИНГА: Autumna → care_homes v2.2

**Дата анализа:** 27 января 2025  
**Версия БД:** v2.2  
**Версия парсера:** v2.4  
**Источник:** `input/autumna/autumna-mapping/`

---

## 📋 EXECUTIVE SUMMARY

### Два варианта workflow:

1. **Прямой путь (Streaming/Real-time)** — маппинг после каждого парсинга
2. **Через staging таблицу (Batch processing)** — накопление данных и батч-обработка

**Текущая документация описывает оба варианта**, но **РЕКОМЕНДУЕТСЯ staging подход** для bootstrap проектов.

**Подробнее о staging подходе:** см. `input/autumna/STAGING_ARCHITECTURE_v2.4.md`

---

## 🔄 ВАРИАНТ 1: ПРЯМОЙ ПУТЬ (Streaming/Real-time)

### Архитектура:
```
HTML (Firecrawl) → LLM Парсинг → Python Mapper → INSERT в care_homes
```

### Workflow (4 шага):

#### Шаг 1: Scraping HTML (Firecrawl)
```python
import requests

html_content = requests.get('https://www.autumna.co.uk/care-homes/...').text
# Результат: Raw HTML страницы
```

#### Шаг 2: LLM Парсинг (OpenAI Structured Outputs)
```python
import openai
import json

# Загрузить JSON Schema и System Prompt
response = openai.chat.completions.create(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": html_content}
    ],
    response_format=response_format  # JSON Schema v2.4
)

extracted_data = json.loads(response.choices[0].message.content)
# Результат: JSON с 188 полями в структуре v2.4
```

**Что происходит:**
- LLM извлекает данные из HTML в структурированный JSON
- Гарантирует 4 обязательных поля: `cqc_location_id`, `name`, `city`, `postcode`
- Возвращает валидный JSON Schema v2.4
- Время: ~2-5 сек/страница

#### Шаг 3: Python Маппинг (Валидация + Трансформация)
```python
from autumna_mapper_v2_4 import map_autumna_to_db

result = map_autumna_to_db(extracted_data)

# Результат:
# {
#   'data': {
#     'cqc_location_id': '1-1234567890',
#     'name': 'Sunrise',  # Нормализовано!
#     'city': 'London',
#     'postcode': 'SW1A 1AA',
#     'latitude': 51.5074,
#     'longitude': -0.1278,
#     'medical_specialisms': {...},  # JSONB
#     'activities': {...},           # JSONB
#     ...
#   },
#   'validation': {
#     'is_valid': True,
#     'errors': [],
#     'warnings': [],
#     'quality_score': 115  # 100 + бонусы!
#   }
# }
```

**Что делает Python Mapper:**
- ✅ Маппит 188 полей JSON → 93 поля БД v2.2 (76 flat + 17 JSONB)
- ✅ Валидирует форматы (CQC ID, postcode, email, URL)
- ✅ Валидирует диапазоны (coordinates, beds, pricing, years)
- ✅ Нормализует данные (names, phones, postcodes)
- ✅ Вычисляет Quality Score (0-100+)
- ✅ Возвращает errors, warnings, validation status
- Время: ~0.01-0.05 сек/запись

**Quality Score система:**
```
Начальный: 100

ШТРАФЫ:
- Критические ошибки (блокеры): -30 каждая
- Обычные ошибки: -5 каждая
- Warnings: -1 каждый

БОНУСЫ (max +20):
- registered_manager: +5
- CQC ratings: +5
- Coordinates: +5
- Pricing: +5

РЕШЕНИЯ:
- 90-100+: ✅ Auto-insert
- 60-89: ⚠️ Insert with review flag
- < 60: ❌ Manual review
- 0: 🔴 REJECT (критические блокеры)
```

#### Шаг 4: INSERT в БД (с SQL функциями)
```python
import psycopg2

# Проверка качества
if result['validation']['is_valid'] and result['validation']['quality_score'] >= 60:
    db_record = result['data']
    
    # SQL INSERT с функциями нормализации
    cursor.execute("""
        INSERT INTO care_homes (
            cqc_location_id,
            name,
            provider_name,
            city,
            postcode,
            latitude,
            longitude,
            telephone,
            email,
            website,
            medical_specialisms,
            activities,
            building_info,
            data_quality_score,
            is_dormant,
            ...
        ) VALUES (
            %(cqc_location_id)s,
            %(name)s,
            %(provider_name)s,
            %(city)s,
            normalize_uk_postcode(%(postcode)s),
            safe_latitude(%(latitude)s),        -- 🔥 КРИТИЧНО!
            safe_longitude(%(longitude)s),      -- 🔥 КРИТИЧНО!
            normalize_phone(%(telephone)s),
            %(email)s,
            %(website)s,
            %(medical_specialisms)s::jsonb,
            %(activities)s::jsonb,
            %(building_info)s::jsonb,
            %(data_quality_score)s,
            %(is_dormant)s,
            ...
        )
        ON CONFLICT (cqc_location_id) DO UPDATE
        SET
            name = EXCLUDED.name,
            city = EXCLUDED.city,
            postcode = EXCLUDED.postcode,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            updated_at = CURRENT_TIMESTAMP
    """, db_record)
    
    connection.commit()
    print(f"✅ Inserted/Updated: {db_record['cqc_location_id']}")
else:
    print(f"❌ Validation failed: {result['validation']['errors']}")
```

**Что делает SQL:**
- Использует 11 SQL функций для нормализации и валидации
- Особенно критично: `safe_latitude()` и `safe_longitude()` (обработка запятой!)
- `ON CONFLICT DO UPDATE` для обновления существующих записей
- Время: ~0.01-0.1 сек/запись

### Преимущества прямого пути:
- ✅ Real-time обновление данных
- ✅ Простая архитектура
- ✅ Меньше места для хранения
- ✅ Нет задержек между scraping и БД

### Недостатки:
- ⚠️ Нет возможности повторной обработки при ошибках
- ⚠️ Сложнее отладка (нет истории парсинга)
- ⚠️ Нет возможности батч-оптимизации

---

## 🔄 ВАРИАНТ 2: ЧЕРЕЗ STAGING ТАБЛИЦУ (Batch Processing)

### Архитектура:
```
HTML (Firecrawl) → autumna_staging → LLM Парсинг → autumna_staging.parsed_json → Batch Mapper → care_homes
```

### Схема staging таблицы:

```sql
CREATE TABLE autumna_staging (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,
    html_content TEXT,                    -- Исходный HTML
    parsed_json JSONB NOT NULL,           -- Парсинг результат (JSON Schema v2.4)
    extraction_confidence TEXT,           -- 'high', 'medium', 'low'
    data_quality_score INTEGER,          -- Quality score от mapper
    is_dormant BOOLEAN,
    parsing_errors JSONB,                -- Ошибки парсинга
    mapping_errors JSONB,                -- Ошибки маппинга
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,     -- Флаг обработки
    processed_at TIMESTAMPTZ,
    care_homes_id BIGINT                 -- FK на care_homes.id (после маппинга)
);

CREATE INDEX idx_staging_processed ON autumna_staging(processed);
CREATE INDEX idx_staging_quality ON autumna_staging(data_quality_score);
CREATE INDEX idx_staging_url ON autumna_staging(source_url);
```

### Workflow (5 шагов):

#### Шаг 1: Scraping HTML → Staging
```python
# Firecrawl сохраняет HTML в staging
cursor.execute("""
    INSERT INTO autumna_staging (
        source_url,
        scraped_at,
        html_content
    ) VALUES (
        %(url)s,
        CURRENT_TIMESTAMP,
        %(html)s
    )
""", {'url': 'https://www.autumna.co.uk/...', 'html': html_content})
```

#### Шаг 2: LLM Парсинг → Обновление staging.parsed_json
```python
# Обработка всех непроцессированных записей
cursor.execute("""
    SELECT id, html_content, source_url 
    FROM autumna_staging 
    WHERE parsed_json IS NULL 
    LIMIT 100
""")

for record in cursor.fetchall():
    # Парсинг OpenAI
    extracted_data = parse_with_openai(record['html_content'])
    
    # Сохранение результата в staging
    cursor.execute("""
        UPDATE autumna_staging
        SET 
            parsed_json = %(parsed_json)s::jsonb,
            extraction_confidence = %(confidence)s,
            parsing_errors = %(errors)s::jsonb
        WHERE id = %(id)s
    """, {
        'id': record['id'],
        'parsed_json': json.dumps(extracted_data),
        'confidence': extracted_data.get('extraction_metadata', {}).get('extraction_confidence'),
        'errors': json.dumps(extracted_data.get('extraction_metadata', {}).get('critical_fields_missing', []))
    })
```

#### Шаг 3: Batch Маппинг (из staging → care_homes)
```python
# Обработка батчами из staging таблицы
cursor.execute("""
    SELECT id, parsed_json, source_url, extraction_confidence
    FROM autumna_staging 
    WHERE processed = false 
      AND parsed_json IS NOT NULL
    ORDER BY data_quality_score DESC NULLS LAST
    LIMIT 100
""")

records = cursor.fetchall()

success = 0
failed = 0

for record in records:
    try:
        parsed_json = json.loads(record['parsed_json'])
        
        # Python маппинг
        result = map_autumna_to_db(parsed_json)
        
        if result['validation']['is_valid'] and result['validation']['quality_score'] >= 60:
            # INSERT в care_homes
            db_record = result['data']
            
            cursor.execute("""
                INSERT INTO care_homes (...) VALUES (...)
                ON CONFLICT (cqc_location_id) DO UPDATE SET ...
                RETURNING id
            """, db_record)
            
            care_homes_id = cursor.fetchone()[0]
            
            # Обновление staging: пометить как обработанное
            cursor.execute("""
                UPDATE autumna_staging
                SET 
                    processed = true,
                    processed_at = CURRENT_TIMESTAMP,
                    care_homes_id = %(care_homes_id)s,
                    data_quality_score = %(score)s,
                    mapping_errors = NULL
                WHERE id = %(staging_id)s
            """, {
                'staging_id': record['id'],
                'care_homes_id': care_homes_id,
                'score': result['validation']['quality_score']
            })
            
            success += 1
        else:
            # Сохранение ошибок маппинга
            cursor.execute("""
                UPDATE autumna_staging
                SET 
                    mapping_errors = %(errors)s::jsonb,
                    data_quality_score = %(score)s
                WHERE id = %(staging_id)s
            """, {
                'staging_id': record['id'],
                'errors': json.dumps(result['validation']['errors']),
                'score': result['validation']['quality_score']
            })
            
            failed += 1
            
    except Exception as e:
        log_exception(record['id'], e)
        failed += 1

connection.commit()
print(f"✅ Success: {success}, ❌ Failed: {failed}")
```

#### Шаг 4: Обработка ошибок (опционально)
```python
# Ручная проверка записей с низким quality_score
cursor.execute("""
    SELECT *
    FROM autumna_staging
    WHERE processed = false
      AND parsed_json IS NOT NULL
      AND (data_quality_score < 60 OR data_quality_score IS NULL)
    ORDER BY created_at DESC
""")

# Отправить в очередь для ручной проверки
```

#### Шаг 5: Очистка (опционально)
```sql
-- Удалить обработанные записи старше 30 дней
DELETE FROM autumna_staging
WHERE processed = true
  AND processed_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

### Преимущества staging таблицы:
- ✅ Возможность повторной обработки при ошибках
- ✅ История всех парсингов (для отладки)
- ✅ Батч-оптимизация (обработка группами)
- ✅ Возможность ручной проверки перед маппингом
- ✅ Отделение scraping от маппинга (можно парсить отдельно от маппинга)
- ✅ Возможность параллельной обработки

### Недостатки:
- ⚠️ Дополнительное хранилище (HTML + JSON)
- ⚠️ Более сложная архитектура
- ⚠️ Задержка между scraping и БД

---

## 📊 СРАВНЕНИЕ ВАРИАНТОВ

| Критерий | Прямой путь | Через staging |
|----------|-------------|---------------|
| **Сложность** | Простая | Средняя |
| **Real-time** | ✅ Да | ❌ Нет |
| **Повторная обработка** | ❌ Нет | ✅ Да |
| **История парсингов** | ❌ Нет | ✅ Да |
| **Батч-оптимизация** | ❌ Нет | ✅ Да |
| **Отладка** | ⚠️ Сложнее | ✅ Проще |
| **Хранилище** | Минимальное | Больше (HTML + JSON) |
| **Производительность** | ~2-6 сек/запись | ~2-6 сек/запись + batch overhead |

---

## 🎯 РЕКОМЕНДАЦИИ ПО ВЫБОРУ

### Используйте **ПРЯМОЙ ПУТЬ** если:
- ✅ Нужны real-time обновления
- ✅ Простая архитектура предпочтительнее
- ✅ Ограниченное хранилище
- ✅ Низкий объем данных (< 1000 записей/день)

### Используйте **STAGING ТАБЛИЦУ** если:
- ✅ Нужна возможность повторной обработки
- ✅ Важна история и отладка
- ✅ Большой объем данных (> 1000 записей/день)
- ✅ Нужна ручная проверка перед маппингом
- ✅ Нужна батч-оптимизация
- ✅ Разделение scraping и маппинга на разные процессы

---

## 🔍 ДЕТАЛЬНАЯ ЛОГИКА МАППИНГА

### Структура маппинга (188 JSON полей → 93 БД поля)

#### 1. Flat Fields (76 полей) - Прямой маппинг

**Идентификаторы:**
```python
'cqc_location_id' = identity['cqc_location_id']  # REQUIRED
'location_ods_code' = identity.get('location_ods_code')
```

**Базовая информация:**
```python
'name' = identity['name']  # REQUIRED, нормализовано
'provider_name' = identity.get('provider_name')
'provider_id' = identity.get('provider_id')
'brand_name' = identity.get('brand_name')
```

**Контакты:**
```python
'telephone' = contact.get('telephone')  # Нормализовано
'email' = contact.get('email')
'website' = contact.get('website')
```

**Локация:**
```python
'city' = location['city']  # REQUIRED
'county' = location.get('county')
'postcode' = location['postcode']  # REQUIRED, нормализовано
'latitude' = location.get('latitude')  # Обработано safe_latitude()
'longitude' = location.get('longitude')  # Обработано safe_longitude()
'region' = location.get('region')
'local_authority' = location.get('local_authority')
```

**Вместимость:**
```python
'beds_total' = capacity.get('beds_total')
'beds_available' = capacity.get('beds_available')
'has_availability' = capacity.get('has_availability')
'availability_status' = capacity.get('availability_status')
'availability_last_checked' = capacity.get('availability_last_checked')
'year_opened' = capacity.get('year_opened')
'year_registered' = capacity.get('year_registered')
```

**Типы ухода:**
```python
'care_residential' = care_services.get('care_residential')
'care_nursing' = care_services.get('care_nursing')
'care_dementia' = care_services.get('care_dementia')
'care_respite' = care_services.get('care_respite')  # Или NULL (нет в CQC)
```

**Лицензии (КРИТИЧНО: из licenses, НЕ из care_services!):**
```python
'has_nursing_care_license' = licenses.get('has_nursing_care_license')
'has_personal_care_license' = licenses.get('has_personal_care_license')
'has_surgical_procedures_license' = licenses.get('has_surgical_procedures_license')
'has_treatment_license' = licenses.get('has_treatment_license')
'has_diagnostic_license' = licenses.get('has_diagnostic_license')
```

**Service User Bands (12 полей - 5 старых + 7 новых v2.2):**
```python
# Старые 5 полей:
'serves_older_people' = user_categories.get('serves_older_people')
'serves_younger_adults' = user_categories.get('serves_younger_adults')
'serves_mental_health' = user_categories.get('serves_mental_health')
'serves_physical_disabilities' = user_categories.get('serves_physical_disabilities')
'serves_sensory_impairments' = user_categories.get('serves_sensory_impairments')

# Новые 7 полей v2.2:
'serves_dementia_band' = user_categories.get('serves_dementia_band')  # 🆕 v2.2
'serves_children' = user_categories.get('serves_children')  # 🆕 v2.2
'serves_learning_disabilities' = user_categories.get('serves_learning_disabilities')  # 🆕 v2.2
'serves_detained_mha' = user_categories.get('serves_detained_mha')  # 🆕 v2.2
'serves_substance_misuse' = user_categories.get('serves_substance_misuse')  # 🆕 v2.2
'serves_eating_disorders' = user_categories.get('serves_eating_disorders')  # 🆕 v2.2
'serves_whole_population' = user_categories.get('serves_whole_population')  # 🆕 v2.2
```

**Ценообразование:**
```python
'fee_residential_from' = pricing.get('fee_residential_from')
'fee_nursing_from' = pricing.get('fee_nursing_from')
'fee_dementia_from' = pricing.get('fee_dementia_from')
'fee_respite_from' = pricing.get('fee_respite_from')
```

**Финансирование:**
```python
'accepts_self_funding' = funding.get('accepts_self_funding')
'accepts_local_authority' = funding.get('accepts_local_authority')
'accepts_nhs_chc' = funding.get('accepts_nhs_chc')
'accepts_third_party_topup' = funding.get('accepts_third_party_topup')
```

**CQC Рейтинги:**
```python
'cqc_rating_overall' = cqc_ratings.get('cqc_rating_overall')  # Нормализовано
'cqc_rating_safe' = cqc_ratings.get('cqc_rating_safe')
'cqc_rating_effective' = cqc_ratings.get('cqc_rating_effective')
'cqc_rating_caring' = cqc_ratings.get('cqc_rating_caring')
'cqc_rating_responsive' = cqc_ratings.get('cqc_rating_responsive')
'cqc_rating_well_led' = cqc_ratings.get('cqc_rating_well_led')
'cqc_last_inspection_date' = cqc_ratings.get('cqc_last_inspection_date')
'cqc_publication_date' = cqc_ratings.get('cqc_publication_date')
'cqc_latest_report_url' = cqc_ratings.get('cqc_latest_report_url')
```

**Отзывы:**
```python
'review_average_score' = reviews.get('review_average_score')
'review_count' = reviews.get('review_count')
'google_rating' = reviews.get('google_rating')
```

**Удобства:**
```python
'wheelchair_access' = building_and_facilities.get('wheelchair_access')
'ensuite_rooms' = building_and_facilities.get('ensuite_rooms')
'secure_garden' = building_and_facilities.get('secure_garden')
'wifi_available' = building_and_facilities.get('wifi_available')
'parking_onsite' = building_and_facilities.get('parking_onsite')
```

**Статус:**
```python
'is_dormant' = extraction_metadata.get('is_dormant')
'data_quality_score' = extraction_metadata.get('data_quality_score')
```

**Временные метки:**
```python
'created_at' = CURRENT_TIMESTAMP  # Автоматически
'updated_at' = CURRENT_TIMESTAMP  # Автоматически
```

#### 2. JSONB Fields (17 полей) - Прямой маппинг БЕЗ трансформации

**Критический принцип:** JSONB поля маппятся **НАПРЯМУЮ** без трансформации структуры!

```python
# Регулируемые активности (🆕 v2.2)
'regulated_activities' = regulated_activities  # Прямой маппинг структуры {"activities": [...]}

# Медицинские специализации
'medical_specialisms' = medical_specialisms  # Прямой маппинг всей структуры

# Диетические опции
'dietary_options' = dietary_options  # Прямой маппинг всей структуры

# Активности
'activities' = activities  # Прямой маппинг всей структуры

# Информация о персонале
'staff_information' = staff_information  # Прямой маппинг всей структуры

# Информация о здании
'building_info' = building_and_facilities.get('building_details')  # Из вложенной секции

# Детали ценообразования
'pricing_details' = pricing  # Вся структура pricing целиком

# Детали отзывов
'reviews_detailed' = reviews  # Вся структура reviews целиком

# Медиа
'media' = media  # Прямой маппинг всей структуры

# Контекст локации
'location_context' = location.get('location_context')  # Из вложенной секции

# Типы услуг
'service_types' = jsonb_build_object('services', care_services.get('service_types_list', []))

# Service User Bands (JSONB)
'service_user_bands' = jsonb_build_object('bands', user_categories.get('service_user_bands_list', []))

# Аккредитации
'accreditations' = accreditations  # Прямой маппинг всей структуры

# Метаданные источника
'source_metadata' = source_metadata  # Прямой маппинг всей структуры

# URLs источника
'source_urls' = jsonb_build_object('autumna', source_metadata.get('source_url'))

# Дополнительные данные
'extra' = jsonb_build_object()  # Пустой, для будущего расширения
```

**Важно:** JSONB структуры сохраняются **как есть**, без изменения иерархии!

---

## 🔐 КРИТИЧЕСКИЕ ОСОБЕННОСТИ МАППИНГА

### 1. Координаты с запятой (🔥 КРИТИЧНО!)

**Проблема:**
```
HTML: <span>-1,8904</span>
JSON: {"longitude": "-1,8904"}
PostgreSQL parse: SELECT '-1,8904'::numeric;  -- ERROR!
```

**Решение:**
```sql
-- ВСЕГДА используйте SQL функции при INSERT:
INSERT INTO care_homes (longitude) 
VALUES (safe_longitude('-1,8904'));  -- -1.8904 ✅
```

**Почему критично:**
- Без обработки: Координаты неверные → Карты ошибочные
- С обработкой: Координаты точные → Корректное отображение

### 2. licenses vs care_services (🔥 ЮРИДИЧЕСКИ ВАЖНО!)

**Критическое различие:**

```python
# licenses = Что дом МОЖЕТ делать (по лицензии CQC)
has_nursing_care_license = licenses.get('has_nursing_care_license')  # TRUE

# care_services = Что дом ПРЕДЛАГАЕТ (на практике)
care_nursing = care_services.get('care_nursing')  # Может быть FALSE!

# Пример: Дом ИМЕЕТ лицензию но НЕ ПРЕДЛАГАЕТ услугу
# Это абсолютно легально и часто встречается!
```

### 3. User Categories - DERIVED поля (🔥 ВАЖНО!)

**Критично:** Поля `serves_*` **НЕ ищутся в HTML напрямую**, а **ДЕРИВИРУЮТСЯ** из контента!

```python
# НЕПРАВИЛЬНО:
if html.find('serves_older_people'):  # ❌ Такого текста нет!

# ПРАВИЛЬНО:
if 'dementia' in medical_specialisms or 'Alzheimer' in medical_specialisms:
    serves_older_people = True  # ✅ Деривация из контента
```

### 4. Regulated Activities JSONB (🆕 v2.2)

**Структура:**
```json
{
  "regulated_activities": {
    "activities": [
      {
        "activity_id": "nursing_care",
        "activity_name": "Nursing care",
        "is_active": true
      },
      {
        "activity_id": "personal_care",
        "activity_name": "Personal care",
        "is_active": true
      }
    ]
  }
}
```

**Маппинг:**
```python
'regulated_activities' = regulated_activities.get('activities', [])
# Маппится напрямую в JSONB поле БД
```

---

## 📊 ОБРАБОТКА КОНФЛИКТОВ (UPSERT)

### Используется `ON CONFLICT DO UPDATE`:

```sql
ON CONFLICT (cqc_location_id) DO UPDATE
SET
    name = EXCLUDED.name,
    city = EXCLUDED.city,
    postcode = EXCLUDED.postcode,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    updated_at = CURRENT_TIMESTAMP
```

**Логика:**
- Если `cqc_location_id` уже существует → **UPDATE** существующей записи
- Если `cqc_location_id` не существует → **INSERT** новой записи
- Поле `updated_at` автоматически обновляется при UPDATE

**Почему это важно:**
- Данные из Autumna могут обновляться
- Один дом может быть отскраплен несколько раз
- Нужно обновлять существующие записи, а не создавать дубликаты

---

## 🎯 ВЫВОДЫ

### Текущая логика в документации:

**Основной workflow (ПОЛНАЯ_СИСТЕМА_v2_4_FINAL):**
- Показывает **ПРЯМОЙ ПУТЬ** (streaming/real-time)
- Маппинг происходит **после каждого парсинга**
- Нет staging таблицы в основном workflow

**Альтернативный вариант (ACTION_CHECKLIST, ФИНАЛЬНЫЙ_АНАЛИЗ):**
- Упоминается **staging таблица** `autumna_staging`
- Описан **batch processing** workflow
- Возможность повторной обработки

### Рекомендация:

**Для production рекомендуется использовать ПРЯМОЙ ПУТЬ** с добавлением:
- Логирования всех операций
- Очереди для повторной обработки ошибок
- Мониторинга quality scores

**Staging таблица полезна для:**
- Первоначальной загрузки больших объемов данных
- Отладки и тестирования
- Ручной проверки перед маппингом

---

**Дата анализа:** 27 января 2025  
**Версия документа:** 1.0

