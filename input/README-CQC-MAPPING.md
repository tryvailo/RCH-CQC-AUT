# 📋 README: Маппинг CQC Dataset → care_homes v2.4
## Руководство по преобразованию данных CQC в структуру care_homes

**Дата:** 3 ноября 2025  
**Версия:** v2.4 FINAL  
**Статус:** ✅ Production Ready  
**Источник данных:** CQC Dataset (CSV/таблица `cqc_dataset_test`)

---

## 🎯 ЧТО ЭТО?

Это руководство описывает процесс маппинга данных из официального CQC Dataset в структуру базы данных `care_homes` v2.4.

**Источник:** CQC Dataset (129 полей)  
**Цель:** care_homes таблица (95 полей: 78 плоских + 17 JSONB)

---

## 📋 СОДЕРЖАНИЕ

1. [Быстрый старт](#быстрый-старт)
2. [Структура маппинга](#структура-маппинга)
3. [SQL функции нормализации](#sql-функции-нормализации)
4. [Критические исправления v2.4](#критические-исправления-v24)
5. [Примеры использования](#примеры-использования)
6. [Мониторинг и валидация](#мониторинг-и-валидация)

---

## 🚀 БЫСТРЫЙ СТАРТ

### Шаг 1: Подготовить исходные данные

Исходные данные должны быть в таблице `cqc_dataset_test` или импортированы из CSV файла.

**Пример создания таблицы из CSV:**
```sql
-- Импорт CSV в временную таблицу
CREATE TABLE cqc_dataset_test AS
SELECT * FROM read_csv_auto('path/to/cqc_dataset.csv');
```

### Шаг 2: Установить SQL функции

```bash
psql -U postgres -d care_homes -f input/mapping_improved_script.sql
```

Этот скрипт создаст:
- ✅ Все SQL helper функции (clean_text, safe_latitude, safe_longitude, etc.)
- ✅ Выполнит INSERT SELECT маппинг в `care_homes`

### Шаг 3: Проверить результаты

```sql
-- Проверить количество записей
SELECT COUNT(*) FROM care_homes;

-- Проверить качество данных
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE cqc_location_id IS NOT NULL) as with_cqc_id,
    COUNT(*) FILTER (WHERE name IS NOT NULL) as with_name,
    COUNT(*) FILTER (WHERE city IS NOT NULL) as with_city,
    COUNT(*) FILTER (WHERE postcode IS NOT NULL) as with_postcode,
    AVG(data_quality_score)::INTEGER as avg_quality_score
FROM care_homes;
```

---

## 📊 СТРУКТУРА МАППИНГА

### Общая схема

```
cqc_dataset_test (129 полей)
        ↓
   SQL маппинг с функциями нормализации
        ↓
care_homes (95 полей: 78 плоских + 17 JSONB)
```

### Полная таблица маппинга полей

#### ГРУППА 1: ИДЕНТИФИКАТОРЫ (3 поля)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `cqc_location_id` | `location_id` | `clean_text()` | Уникальный ID CQC (формат: 1-XXXXXXXXXX) |
| `location_ods_code` | `location_ods_code` | `clean_text()` | ODS код NHS (если есть) |

#### ГРУППА 2: БАЗОВАЯ ИНФОРМАЦИЯ (5 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `name` | `location_name` | `clean_text()` | Название дома престарелых |
| `name_normalized` | `location_name` | `LOWER(TRIM())` | Нормализованное название для поиска |
| `provider_name` | `provider_name` | `clean_text()` | Название компании-провайдера |
| `provider_id` | `provider_id` | `clean_text()` | ID провайдера (формат: 1-XXXXXXXXX) |
| `brand_name` | `brand_name` | `clean_text()` | Торговая марка/бренд (если есть) |

#### ГРУППА 3: КОНТАКТНАЯ ИНФОРМАЦИЯ (4 поля)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `telephone` | `location_telephone_number` | `clean_text()` | ⚠️ TEXT, НЕ NUMERIC! |
| `provider_telephone_number` | `provider_telephone_number` | `clean_text()` | 🆕 v2.4 Телефон провайдера |
| `email` | — | `NULL` | Нет в CQC Dataset |
| `website` | `COALESCE(location_web_address, provider_web_address)` | `clean_text()` | ✅ Fallback логика |

#### ГРУППА 4: АДРЕС И ЛОКАЦИЯ (7 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `city` | `location_city` | `clean_text()` | Город |
| `county` | `location_county` | `clean_text()` | Графство |
| `postcode` | `location_postal_code` | `clean_text()` | Почтовый индекс UK |
| `latitude` | `location_latitude` | `safe_latitude()` | 🔥 КРИТИЧНО: обработка запятой! |
| `longitude` | `location_longitude` | `safe_longitude()` | 🔥 КРИТИЧНО: обработка запятой! |
| `region` | `location_region` | `clean_text()` | Регион UK |
| `local_authority` | `location_local_authority` | `clean_text()` | Местная администрация |

#### ГРУППА 5: ВМЕСТИМОСТЬ И ДОСТУПНОСТЬ (8 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `beds_total` | `care_homes_beds` | `safe_integer()` | Общее количество мест |
| `beds_available` | — | `NULL` | Нет в CQC Dataset |
| `has_availability` | — | `FALSE` | Нет в CQC Dataset |
| `availability_status` | — | `NULL` | Нет в CQC Dataset |
| `availability_last_checked` | — | `NULL` | Нет в CQC Dataset |
| `year_opened` | — | `NULL` | ⚠️ КРИТИЧНО: НЕ маппить из location_hsca_start_date! |
| `year_registered` | `location_hsca_start_date` | `extract_year()` | Год регистрации в CQC |
| `provider_hsca_start_date` | `provider_hsca_start_date` | `safe_date()` | 🆕 v2.4 Дата регистрации провайдера |

**⚠️ КРИТИЧНО:** `year_opened` НЕ маппится из `location_hsca_start_date`!

- `location_hsca_start_date` = дата регистрации в CQC (административная дата)
- `year_opened` = фактический год открытия дома
- Многие дома перерегистрировались в 2010 году при переходе на HSCA 2008
- Реальные дома могли работать десятилетиями до регистрации

#### ГРУППА 6: ТИПЫ УХОДА (4 поля)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `care_residential` | `service_type_care_home_service_without_nursing` | `safe_boolean()` | Резидентский уход без сестринского |
| `care_nursing` | `service_type_care_home_service_with_nursing` | `safe_boolean()` | Сестринский уход |
| `care_dementia` | `service_user_band_dementia` | `safe_boolean()` | Уход при деменции |
| `care_respite` | — | `NULL` | Нет в CQC Dataset |

#### ГРУППА 7: ЛИЦЕНЗИИ (5 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `has_nursing_care_license` | `service_type_care_home_service_with_nursing` | `safe_boolean()` | ⚠️ КРИТИЧНО: НЕ из regulated_activity! |
| `has_personal_care_license` | `service_type_care_home_service_without_nursing` | `safe_boolean()` | Лицензия на персональный уход |
| `has_surgical_procedures_license` | `regulated_activity_surgical_procedures` | `safe_boolean()` | Лицензия на хирургические процедуры |
| `has_treatment_license` | `regulated_activity_treatment_of_disease` | `safe_boolean()` | Лицензия на лечение |
| `has_diagnostic_license` | `regulated_activity_diagnostic_and_screening_procedures` | `safe_boolean()` | Лицензия на диагностику |

**⚠️ КРИТИЧНО:** `has_nursing_care_license` маппится из `service_type_care_home_service_with_nursing`, НЕ из `regulated_activity_nursing_care`!

**Причина:**
- `regulated_activity_nursing_care` ВСЕГДА `FALSE` в CQC Dataset (даже для nursing homes!)
- `service_type_care_home_service_with_nursing` корректно идентифицирует nursing homes (~26.9%)
- Это соответствует логике: если дом предлагает "care home service with nursing", значит имеет лицензию

#### ГРУППА 8: SERVICE USER BANDS (12 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `serves_older_people` | `service_user_band_older_people` | `safe_boolean()` | Люди 65+ |
| `serves_younger_adults` | `service_user_band_younger_adults` | `safe_boolean()` | Взрослые 18-64 |
| `serves_mental_health` | `service_user_band_mental_health` | `safe_boolean()` | Психическое здоровье |
| `serves_physical_disabilities` | `service_user_band_physical_disabilities` | `safe_boolean()` | Физические ограничения |
| `serves_sensory_impairments` | `service_user_band_sensory_impairments` | `safe_boolean()` | Нарушения слуха/зрения |
| `serves_dementia_band` | `service_user_band_dementia` | `safe_boolean()` | Деменция |
| `serves_children` | `service_user_band_children` | `safe_boolean()` | Дети |
| `serves_learning_disabilities` | `service_user_band_learning_disabilities` | `safe_boolean()` | Нарушения обучаемости |
| `serves_detained_mha` | `service_user_band_detained_mha` | `safe_boolean()` | Задержанные по Mental Health Act |
| `serves_substance_misuse` | `service_user_band_substance_misuse` | `safe_boolean()` | Проблемы с зависимостями |
| `serves_eating_disorders` | `service_user_band_eating_disorders` | `safe_boolean()` | Расстройства пищевого поведения |
| `serves_whole_population` | `service_user_band_whole_population` | `safe_boolean()` | Вся популяция |

#### ГРУППА 9: ЦЕНООБРАЗОВАНИЕ (4 поля)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `fee_residential_from` | — | `NULL` | Нет в CQC Dataset |
| `fee_nursing_from` | — | `NULL` | Нет в CQC Dataset |
| `fee_dementia_from` | — | `NULL` | Нет в CQC Dataset |
| `fee_respite_from` | — | `NULL` | Нет в CQC Dataset |

#### ГРУППА 10: ФИНАНСИРОВАНИЕ (4 поля)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `accepts_self_funding` | — | `NULL` | Нет в CQC Dataset |
| `accepts_local_authority` | — | `NULL` | Нет в CQC Dataset |
| `accepts_nhs_chc` | — | `NULL` | Нет в CQC Dataset |
| `accepts_third_party_topup` | — | `NULL` | Нет в CQC Dataset |

#### ГРУППА 11: CQC РЕЙТИНГИ (9 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `cqc_rating_overall` | `cqc_rating_overall` | `normalize_cqc_rating()` | Общий рейтинг |
| `cqc_rating_safe` | `cqc_rating_safe` | `normalize_cqc_rating()` | Безопасность |
| `cqc_rating_effective` | `cqc_rating_effective` | `normalize_cqc_rating()` | Эффективность |
| `cqc_rating_caring` | `cqc_rating_caring` | `normalize_cqc_rating()` | Забота |
| `cqc_rating_responsive` | `cqc_rating_responsive` | `normalize_cqc_rating()` | Отзывчивость |
| `cqc_rating_well_led` | `cqc_rating_well_led` | `normalize_cqc_rating()` | Управление |
| `cqc_last_inspection_date` | `cqc_last_inspection_date` | `safe_date()` | Дата последней инспекции |
| `cqc_publication_date` | `publication_date` | `safe_date()` | Дата публикации отчета |
| `cqc_latest_report_url` | `cqc_latest_report_url` | `clean_text()` | URL отчета CQC |

#### ГРУППА 12: ОТЗЫВЫ (3 поля)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `review_average_score` | — | `NULL` | Нет в CQC Dataset |
| `review_count` | — | `0` | Нет в CQC Dataset |
| `google_rating` | — | `NULL` | Нет в CQC Dataset |

#### ГРУППА 13: УДОБСТВА (5 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `wheelchair_access` | — | `NULL` | Нет в CQC Dataset |
| `ensuite_rooms` | — | `NULL` | Нет в CQC Dataset |
| `secure_garden` | — | `NULL` | Нет в CQC Dataset |
| `wifi_available` | — | `NULL` | Нет в CQC Dataset |
| `parking_onsite` | — | `NULL` | Нет в CQC Dataset |

#### ГРУППА 14: JSONB ПОЛЯ (17 полей)

| Поле care_homes | Источник CQC | SQL функция | Комментарий |
|----------------|--------------|-------------|-------------|
| `regulated_activities` | `regulated_activity_*` (14 полей) | JSONB агрегация | 🆕 v2.2 Все 14 CQC regulated activities |
| `service_types` | `service_type_*` (множество полей) | JSONB массив | Типы услуг |
| `service_user_bands` | `service_user_band_*` (12 полей) | JSONB массив | Группы пользователей |
| `facilities` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `medical_specialisms` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `dietary_options` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `activities` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `pricing_details` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `staff_information` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `reviews_detailed` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `media` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `location_context` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `building_info` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `accreditations` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `source_urls` | — | `'{}'::jsonb` | Нет в CQC Dataset |
| `source_metadata` | Метаданные импорта | JSONB объект | Информация об источнике |
| `extra` | — | `'{}'::jsonb` | Для будущего расширения |

---

## 🔧 SQL ФУНКЦИИ НОРМАЛИЗАЦИИ

Все функции находятся в `input/mapping_improved_script.sql` и должны быть установлены перед маппингом.

### 1. `clean_text(input TEXT)`
Очистка текста от лишних пробелов.
```sql
SELECT clean_text('  Hello World  ');  -- 'Hello World'
SELECT clean_text(NULL);                -- NULL
SELECT clean_text('');                  -- NULL
```

### 2. `safe_integer(input TEXT, default_value INTEGER)`
Безопасное преобразование в INTEGER.
```sql
SELECT safe_integer('1,150', 0);  -- 1150 (удаляет запятые)
SELECT safe_integer('abc', 0);    -- 0 (ошибка → default)
SELECT safe_integer(NULL, 0);     -- 0
```

### 3. `safe_latitude(input TEXT, default_value NUMERIC)` 🔥 КРИТИЧНО
Обработка координат с запятой как десятичным разделителем.
```sql
SELECT safe_latitude('52,533398', NULL);  -- 52.533398
SELECT safe_latitude('-1,88634', NULL);    -- -1.88634 (НЕ -0.188634!)
SELECT safe_latitude('52.533398', NULL);   -- 52.533398
SELECT safe_latitude('100', NULL);          -- NULL (вне диапазона UK)
```

**Валидация:** Диапазон UK: 49.0 - 61.0

### 4. `safe_longitude(input TEXT, default_value NUMERIC)` 🔥 КРИТИЧНО
Аналогично `safe_latitude` для долготы.
```sql
SELECT safe_longitude('-1,989241', NULL);  -- -1.989241
SELECT safe_longitude('-1.989241', NULL);   -- -1.989241
SELECT safe_longitude('10', NULL);           -- NULL (вне диапазона UK)
```

**Валидация:** Диапазон UK: -8.0 - 2.0

### 5. `safe_boolean(input TEXT, default_value BOOLEAN)`
Преобразование в BOOLEAN.
```sql
SELECT safe_boolean('TRUE', NULL);   -- TRUE
SELECT safe_boolean('false', NULL);  -- FALSE
SELECT safe_boolean('1', NULL);      -- TRUE
SELECT safe_boolean('0', NULL);      -- FALSE
SELECT safe_boolean('yes', NULL);    -- TRUE
```

### 6. `safe_date(input TEXT, default_value DATE)`
Преобразование в DATE с поддержкой разных форматов.
```sql
SELECT safe_date('2025-01-15', NULL);   -- 2025-01-15
SELECT safe_date('15/01/2025', NULL);    -- 2025-01-15
SELECT safe_date('15-01-2025', NULL);    -- 2025-01-15
```

### 7. `normalize_cqc_rating(input TEXT)`
Нормализация CQC рейтингов.
```sql
SELECT normalize_cqc_rating('outstanding');          -- 'Outstanding'
SELECT normalize_cqc_rating('GOOD');                 -- 'Good'
SELECT normalize_cqc_rating('requires improvement');  -- 'Requires Improvement'
SELECT normalize_cqc_rating('RI');                    -- 'Requires Improvement'
```

### 8. `extract_year(input DATE)`
Извлечение года из даты.
```sql
SELECT extract_year('2025-01-15'::DATE);  -- 2025
SELECT extract_year(NULL);                 -- NULL
```

---

## ⚠️ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ v2.4

### 1. `year_opened` НЕ маппится из `location_hsca_start_date`

**Проблема:** Многие скрипты маппят `location_hsca_start_date` → `year_opened`, но это **НЕПРАВИЛЬНО**.

**Правильная логика:**
```sql
-- ❌ НЕПРАВИЛЬНО:
extract_year(location_hsca_start_date) AS year_opened,

-- ✅ ПРАВИЛЬНО:
NULL AS year_opened,  -- Оставить пустым, данных нет в CQC
extract_year(location_hsca_start_date) AS year_registered,  -- Это год регистрации
```

**Причина:** `location_hsca_start_date` = дата регистрации в CQC, не год открытия дома. Многие дома перерегистрировались в 2010 году при переходе на HSCA 2008.

### 2. `has_nursing_care_license` маппится из `service_type`, НЕ из `regulated_activity`

**Проблема:** `regulated_activity_nursing_care` ВСЕГДА `FALSE` в CQC Dataset (даже для nursing homes!).

**Правильная логика:**
```sql
-- ❌ НЕПРАВИЛЬНО:
safe_boolean(regulated_activity_nursing_care) AS has_nursing_care_license,

-- ✅ ПРАВИЛЬНО:
safe_boolean(service_type_care_home_service_with_nursing) AS has_nursing_care_license,
```

**Статистика:**
- `service_type_care_home_service_with_nursing = TRUE`: ~26.9% домов
- `regulated_activity_nursing_care = TRUE`: 0% домов (всегда FALSE!)

### 3. Добавлены новые поля v2.4

- `provider_telephone_number` ← `provider_telephone_number`
- `provider_hsca_start_date` ← `provider_hsca_start_date`

---

## 📝 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Полный маппинг из таблицы

```sql
-- Использовать готовый скрипт
\i input/mapping_improved_script.sql
```

Этот скрипт:
1. Создаст все SQL функции (если не существуют)
2. Выполнит INSERT SELECT маппинг из `cqc_dataset_test` в `care_homes`
3. Использует `ON CONFLICT DO UPDATE` для обновления существующих записей

### Пример 2: Ручной маппинг одной записи

```sql
INSERT INTO care_homes (
    cqc_location_id,
    name,
    city,
    postcode,
    latitude,
    longitude
) SELECT
    clean_text(location_id),
    clean_text(location_name),
    clean_text(location_city),
    clean_text(location_postal_code),
    safe_latitude(location_latitude),
    safe_longitude(location_longitude)
FROM cqc_dataset_test
WHERE location_id = '1-1234567890';
```

### Пример 3: Маппинг с проверкой качества

```sql
-- Маппить только записи с валидными данными
INSERT INTO care_homes (...)
SELECT ...
FROM cqc_dataset_test
WHERE 
    location_id IS NOT NULL
    AND location_name IS NOT NULL
    AND location_city IS NOT NULL
    AND location_postal_code IS NOT NULL
    AND location_latitude IS NOT NULL
    AND location_longitude IS NOT NULL;
```

---

## 📊 МОНИТОРИНГ И ВАЛИДАЦИЯ

### Проверка покрытия полей

```sql
-- Сколько полей заполнено?
SELECT 
    COUNT(*) as total_records,
    COUNT(cqc_location_id) as with_cqc_id,
    COUNT(name) as with_name,
    COUNT(city) as with_city,
    COUNT(postcode) as with_postcode,
    COUNT(latitude) as with_latitude,
    COUNT(longitude) as with_longitude,
    COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) as nursing_homes
FROM care_homes;
```

### Проверка критических полей

```sql
-- Найти записи без критических полей
SELECT 
    cqc_location_id,
    name,
    city,
    postcode
FROM care_homes
WHERE 
    cqc_location_id IS NULL
    OR name IS NULL
    OR city IS NULL
    OR postcode IS NULL;
```

### Проверка координат

```sql
-- Найти записи с некорректными координатами
SELECT 
    cqc_location_id,
    name,
    latitude,
    longitude
FROM care_homes
WHERE 
    latitude IS NOT NULL 
    AND (latitude < 49.0 OR latitude > 61.0)
    OR longitude IS NOT NULL
    AND (longitude < -8.0 OR longitude > 2.0);
```

### Проверка лицензий

```sql
-- Статистика по лицензиям
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) as with_nursing_license,
    COUNT(*) FILTER (WHERE has_personal_care_license = TRUE) as with_personal_license,
    COUNT(*) FILTER (WHERE care_nursing = TRUE) as nursing_care_homes
FROM care_homes;

-- Проверить логическую согласованность
SELECT 
    COUNT(*) as inconsistency_count
FROM care_homes
WHERE 
    has_nursing_care_license = TRUE
    AND care_nursing = FALSE;  -- Должно быть 0 или очень мало
```

### Проверка year_opened и year_registered

```sql
-- Убедиться что year_opened НЕ маппится из location_hsca_start_date
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE year_opened IS NOT NULL) as with_year_opened,
    COUNT(*) FILTER (WHERE year_registered IS NOT NULL) as with_year_registered
FROM care_homes;

-- Ожидается: year_opened = NULL для всех записей из CQC
```

---

## 🐛 ОТЛАДКА

### Проблема: Ошибка "function safe_latitude does not exist"

**Решение:**
```bash
psql -U postgres -d care_homes -f input/mapping_improved_script.sql
```

Скрипт создаст все необходимые функции.

### Проблема: Координаты неправильные (например, 52.533 вместо 52.533398)

**Причина:** Не используется `safe_latitude()` / `safe_longitude()`

**Решение:** Убедитесь, что в INSERT используются SQL функции:
```sql
safe_latitude(location_latitude) AS latitude,
safe_longitude(location_longitude) AS longitude,
```

### Проблема: `has_nursing_care_license` всегда FALSE

**Причина:** Используется `regulated_activity_nursing_care` вместо `service_type_care_home_service_with_nursing`

**Решение:** См. раздел "Критические исправления v2.4" выше.

---

## 📈 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### После маппинга из CQC Dataset:

- ✅ Все 95 полей замапплены
- ✅ Критические поля заполнены: `cqc_location_id`, `name`, `city`, `postcode` (100%)
- ✅ Координаты: ~75-80% заполнены
- ✅ CQC рейтинги: ~60-70% заполнены
- ✅ Лицензии: `has_nursing_care_license` ~26.9% (если исправлено!)
- ✅ Service User Bands: ~80-90% заполнены

### Поля, которые НЕ заполняются из CQC:

- `year_opened` (остаётся NULL)
- `beds_available`, `has_availability`, `availability_status` (нет в CQC)
- Все поля ценообразования (`fee_*_from`) (нет в CQC)
- Все поля финансирования (`accepts_*`) (нет в CQC)
- Отзывы (`review_*`) (нет в CQC)
- Удобства (`wheelchair_access`, etc.) (нет в CQC)

---

## 📞 РЕСУРСЫ

**Документация:**
- Полная спецификация БД: `reference/CARE_HOMES_SPECIFICATION.md`
- Чеклист маппинга: `reference/MAPPING_CHECKLIST.md`
- Практические исправления: `input/MAPPING_FIXES_PRACTICAL_STEPS.md`

**SQL скрипты:**
- Основной скрипт маппинга: `input/mapping_improved_script.sql`
- Альтернативный скрипт: `input/cqc-to-care_homes_grok.sql`

**Анализ:**
- Сравнение скриптов: `input/MAPPING_SCRIPTS_COMPARISON_REPORT.md`
- Неиспользованные поля: `input/unused_fields_analysis.md`

---

**Дата:** 3 ноября 2025  
**Версия:** v2.4 FINAL  
**Статус:** ✅ Production Ready

