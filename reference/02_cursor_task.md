# 🎯 CURSOR INSTRUCTIONS: Direct CQC → v2.2 (NO STAGING)

**Версия:** 3.1 FINAL (NO staging_cqc)  
**Дата:** 31 октября 2025  
**Статус:** ✅ PRODUCTION READY

---

## 🚀 COPY-PASTE В CURSOR AGENT PANEL

```
ЗАДАЧА: Загрузить CQC Dataset прямо в Care Homes v2.2 (БЕЗ staging таблицы)

ВХОДНЫЕ ДОКУМЕНТЫ:
- reference_FIELD_MAPPING.md — маппинг всех 93 полей CQC → v2.2
- reference_V2.2_SCHEMA.sql — CREATE TABLE care_homes v2.2
- reference_VALIDATION.md — 283 контрольные точки + 89 SQL queries
- CQC-DataSet_rows.csv — входные данные (271 запись)

ЭТАП 1: CREATE HELPER FUNCTIONS (10 функций)

CREATE OR REPLACE FUNCTION safe_boolean(p_value TEXT) RETURNS BOOLEAN AS $$
  SELECT CASE WHEN LOWER(COALESCE(p_value, '')) IN ('y', 'yes', 'true', '1', 't') THEN TRUE ELSE FALSE END;
$$ LANGUAGE SQL IMMUTABLE;

CREATE OR REPLACE FUNCTION safe_integer(p_value TEXT) RETURNS INTEGER AS $$
  BEGIN
    IF p_value IS NULL OR TRIM(p_value) = '' THEN RETURN NULL; END IF;
    RETURN REPLACE(REPLACE(p_value, ',', ''), ' ', '')::INTEGER;
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION safe_latitude(p_value TEXT) RETURNS NUMERIC(10,7) AS $$
  DECLARE v_num NUMERIC;
  BEGIN
    IF p_value IS NULL OR TRIM(p_value) = '' THEN RETURN NULL; END IF;
    v_num := REPLACE(p_value, ',', '.')::NUMERIC;
    IF v_num >= 49.0 AND v_num <= 61.0 THEN RETURN v_num; ELSE RETURN NULL; END IF;
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION safe_longitude(p_value TEXT) RETURNS NUMERIC(10,7) AS $$
  DECLARE v_num NUMERIC;
  BEGIN
    IF p_value IS NULL OR TRIM(p_value) = '' THEN RETURN NULL; END IF;
    v_num := REPLACE(p_value, ',', '.')::NUMERIC;
    IF v_num >= -8.0 AND v_num <= 2.0 THEN RETURN v_num; ELSE RETURN NULL; END IF;
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION safe_numeric(p_value TEXT) RETURNS NUMERIC(10,2) AS $$
  BEGIN
    IF p_value IS NULL OR TRIM(p_value) = '' THEN RETURN NULL; END IF;
    RETURN REPLACE(p_value, ',', '')::NUMERIC;
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION safe_date(p_value TEXT) RETURNS DATE AS $$
  DECLARE v_date DATE;
  BEGIN
    IF p_value IS NULL OR TRIM(p_value) = '' THEN RETURN NULL; END IF;
    BEGIN v_date := TO_DATE(p_value, 'DD/MM/YYYY'); RETURN v_date; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN v_date := TO_DATE(p_value, 'YYYY-MM-DD'); RETURN v_date; EXCEPTION WHEN OTHERS THEN NULL; END;
    BEGIN v_date := TO_DATE(p_value, 'DD-MM-YYYY'); RETURN v_date; EXCEPTION WHEN OTHERS THEN NULL; END;
    RETURN NULL;
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION clean_text(p_value TEXT) RETURNS TEXT AS $$
  BEGIN
    IF p_value IS NULL THEN RETURN NULL; END IF;
    RETURN TRIM(REGEXP_REPLACE(p_value, '\s+', ' ', 'g'));
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION normalize_cqc_rating(p_value TEXT) RETURNS TEXT AS $$
  BEGIN
    IF p_value IS NULL THEN RETURN NULL; END IF;
    RETURN CASE LOWER(TRIM(p_value))
      WHEN 'outstanding' THEN 'Outstanding'
      WHEN 'good' THEN 'Good'
      WHEN 'requires improvement' THEN 'Requires Improvement'
      WHEN 'ri' THEN 'Requires Improvement'
      WHEN 'inadequate' THEN 'Inadequate'
      ELSE NULL
    END;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION extract_year(p_date DATE) RETURNS INTEGER AS $$
  BEGIN RETURN EXTRACT(YEAR FROM p_date)::INTEGER; 
  EXCEPTION WHEN OTHERS THEN RETURN NULL;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION safe_dormant(p_value TEXT) RETURNS BOOLEAN AS $$
  BEGIN RETURN COALESCE(LOWER(TRIM(p_value)) = 'y', FALSE); 
  EXCEPTION WHEN OTHERS THEN RETURN FALSE;
  END;
$$ LANGUAGE plpgsql IMMUTABLE;

ЭТАП 2: CREATE TABLE care_homes (скопируй весь CREATE TABLE из reference_V2.2_SCHEMA.sql)
-- Полный CREATE TABLE statement ...

ЭТАП 3: INSERT ПРЯМО ИЗ CSV (БЕЗ staging_cqc!)

INSERT INTO care_homes (
  cqc_location_id, name, name_normalized, provider_name, provider_id,
  city, postcode, county, latitude, longitude, region, local_authority,
  telephone, website, beds_total, year_registered,
  care_residential, care_nursing, care_dementia,
  has_nursing_care_license, has_personal_care_license,
  has_surgical_procedures_license, has_treatment_license, has_diagnostic_license,
  serves_older_people, serves_younger_adults, serves_mental_health,
  serves_physical_disabilities, serves_sensory_impairments,
  serves_dementia_band, serves_children, serves_learning_disabilities,
  serves_detained_mha, serves_substance_misuse, serves_eating_disorders,
  serves_whole_population,
  cqc_rating_overall, cqc_rating_safe, cqc_rating_effective,
  cqc_rating_caring, cqc_rating_responsive, cqc_rating_well_led,
  cqc_last_inspection_date, cqc_publication_date,
  accepts_self_funding, accepts_local_authority, accepts_nhs_chc, accepts_third_party_topup,
  review_average_score, review_count, google_rating,
  wheelchair_access, ensuite_rooms, secure_garden, wifi_available, parking_onsite,
  is_dormant, data_quality_score
)
WITH csv_data AS (
  SELECT * FROM PROGRAM 'cat CQC-DataSet_rows.csv'
  WITH (FORMAT CSV, HEADER)
)
SELECT 
  location_id,
  COALESCE(NULLIF(clean_text(location_name), ''), 'Unknown'),
  LOWER(TRIM(COALESCE(location_name, ''))),
  clean_text(provider_name),
  clean_text(provider_id),
  COALESCE(NULLIF(clean_text(location_city), ''), 'Unknown'),
  clean_text(location_postal_code),
  clean_text(location_county),
  safe_latitude(location_latitude),
  safe_longitude(location_longitude),
  clean_text(location_region),
  clean_text(location_local_authority),
  clean_text(location_telephone_number),
  COALESCE(NULLIF(location_web_address, ''), provider_web_address),
  safe_integer(location_number_of_beds),
  extract_year(safe_date(location_hsca_start_date)),
  safe_boolean(service_type_care_home_service_without_nursing),
  safe_boolean(service_type_care_home_service_with_nursing),
  safe_boolean(service_user_band_dementia),
  safe_boolean(regulated_activity_nursing_care),
  safe_boolean(regulated_activity_personal_care),
  safe_boolean(regulated_activity_surgical_procedures),
  safe_boolean(regulated_activity_treatment_of_disease_disorder_or_injury),
  safe_boolean(regulated_activity_diagnostic_and_screening_procedures),
  safe_boolean(service_user_band_older_people),
  safe_boolean(service_user_band_younger_adults),
  safe_boolean(service_user_band_mental_health),
  safe_boolean(service_user_band_physical_disability),
  safe_boolean(service_user_band_sensory_impairment),
  safe_boolean(service_user_band_dementia),
  safe_boolean(service_user_band_children_0_18_years),
  safe_boolean(service_user_band_learning_disabilities_or_autistic_spectrum_di),
  safe_boolean(service_user_band_people_detained_under_the_mental_health_act),
  safe_boolean(service_user_band_people_who_misuse_drugs_and_alcohol),
  safe_boolean(service_user_band_people_with_an_eating_disorder),
  safe_boolean(service_user_band_whole_population),
  normalize_cqc_rating(location_latest_overall_rating),
  normalize_cqc_rating(location_latest_rating_safe),
  normalize_cqc_rating(location_latest_rating_effective),
  normalize_cqc_rating(location_latest_rating_caring),
  normalize_cqc_rating(location_latest_rating_responsive),
  normalize_cqc_rating(location_latest_rating_well_led),
  safe_date(location_last_inspection_date),
  safe_date(publication_date),
  safe_boolean(funding_self_funding),
  safe_boolean(funding_local_authority),
  safe_boolean(funding_nhs_chc),
  safe_boolean(funding_third_party),
  safe_numeric(review_average_score),
  safe_integer(review_count),
  safe_numeric(google_rating),
  safe_boolean(wheelchair_access),
  safe_boolean(ensuite_rooms),
  safe_boolean(secure_garden),
  safe_boolean(wifi_available),
  safe_boolean(parking_onsite),
  safe_dormant(dormant_y_n),
  ROUND(100.0 * (93 - COALESCE(SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END), 0)) / 93, 0)::INTEGER
FROM csv_data;

ЭТАП 4: ANALYZE & INDEX

ANALYZE care_homes;

-- Индексы из reference_V2.2_SCHEMA.sql
CREATE INDEX idx_care_homes_nursing ON care_homes WHERE has_nursing_care_license = TRUE;
CREATE INDEX idx_care_homes_dementia ON care_homes WHERE serves_dementia_band = TRUE;
-- ... остальные 51 индекс из reference_V2.2_SCHEMA.sql

ЭТАП 5: CREATE VIEWS

-- Views из reference_V2.2_SCHEMA.sql
CREATE VIEW v_data_coverage AS ...
CREATE VIEW v_service_user_bands_coverage AS ...
CREATE VIEW v_data_anomalies AS ...

ЭТАП 6: VALIDATION QUERIES

SELECT 
  COUNT(*) as total_records,
  COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) as nursing_licenses,
  ROUND(100.0 * COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) / COUNT(*), 1) as nursing_pct,
  COUNT(*) FILTER (WHERE latitude NOT BETWEEN 49 AND 61 OR longitude NOT BETWEEN -8 AND 2) as bad_coords,
  COUNT(*) FILTER (WHERE telephone LIKE '%.%') as numeric_phones_error,
  COUNT(*) FILTER (WHERE serves_dementia_band IS NULL) as null_dementia,
  COUNT(*) FILTER (WHERE name = 'Unknown') as unknown_names
FROM care_homes;

-- Ожидаемые результаты:
-- total_records: 271
-- nursing_licenses: ~198 (73%)
-- nursing_pct: ~73.0
-- bad_coords: 0
-- numeric_phones_error: 0
-- null_dementia: 0
-- unknown_names: 0

ВЫХОДНЫЕ ФАЙЛЫ (сохрани в output/):

1. load-cqc-to-v2.2-direct.sql
   - Полный SQL скрипт со всеми 10 functions
   - CREATE TABLE care_homes (из reference_V2.2_SCHEMA.sql)
   - INSERT ... SELECT с прямым маппингом
   - ANALYZE + CREATE INDEXES (все 53)
   - CREATE VIEWS (все 3)
   - VALIDATION QUERIES (89 шт)

2. cqc-to-v2.2-mapping.json
   - JSON маппинг всех 93 полей
   - Формат: [{"cqc_field": "...", "v22_field": "...", "function": "..."}]

3. CQC_LOAD_EXECUTION_GUIDE.md
   - Пошаговое руководство по запуску
   - Описание каждого преобразования
   - Возможные проблемы и решения

4. LOAD_VALIDATION_REPORT.json
   - Результаты валидации
   - Passed/Failed metrics
   - Scoring (ожидается 95%+)

КРИТИЧНЫЕ ТРЕБОВАНИЯ:
✅ БЕЗ staging_cqc таблицы! Прямо INSERT из CSV
✅ has_*_license ТОЛЬКО из regulated_activity_* (НЕ service_type_*)
✅ telephone как TEXT (НЕ NUMERIC!)
✅ Координаты: 49-61°N, -8 to 2°E
✅ 7 новых полей v2.2 обязательны
✅ Все 93 поля маппированы
✅ 10 helper functions работают
✅ 53 индекса созданы
✅ 3 Views созданы
✅ 271 запись загружена
✅ 0 критичных ошибок
✅ Scoring 95%+ (283/283 checks)
```

---

## ✅ ФИНАЛЬНАЯ СТРУКТУРА ВЫХОДНОГО SQL

```sql
-- 1. DROP existing (если нужно)
DROP TABLE IF EXISTS care_homes CASCADE;

-- 2. CREATE FUNCTIONS (10 шт)
CREATE OR REPLACE FUNCTION safe_boolean(...) ...
CREATE OR REPLACE FUNCTION safe_integer(...) ...
... (8 остальных)

-- 3. CREATE TABLE
CREATE TABLE care_homes (
  ... 93 поля с типами ...
);

-- 4. INSERT SELECT (прямо из CSV)
INSERT INTO care_homes (93 поля)
SELECT ...
FROM PROGRAM 'cat CQC-DataSet_rows.csv'
WITH (FORMAT CSV, HEADER);

-- 5. ANALYZE
ANALYZE care_homes;

-- 6. CREATE INDEXES (53 шт)
CREATE INDEX ...

-- 7. CREATE VIEWS (3 шт)
CREATE VIEW ...

-- 8. VALIDATION
SELECT COUNT(*) FROM care_homes;
-- Expected: 271
```

---

## 📊 МАППИНГ 93 ПОЛЕЙ (КРАТКАЯ СПРАВКА)

| Группа | CQC Поля | v2.2 Поля | Функция |
|--------|----------|----------|---------|
| ID | location_id | cqc_location_id | clean_text |
| Name | location_name | name | clean_text |
| City | location_city | city | clean_text |
| Coords | location_latitude | latitude | safe_latitude (49-61) |
| Coords | location_longitude | longitude | safe_longitude (-8 to 2) |
| Phone | location_telephone_number | telephone | clean_text (TEXT!) |
| 🔴 License | regulated_activity_nursing_care | has_nursing_care_license | safe_boolean |
| Care Type | service_type_care_home_service_with_nursing | care_nursing | safe_boolean |
| 🆕 Band | service_user_band_dementia | serves_dementia_band | safe_boolean |
| Rating | location_latest_overall_rating | cqc_rating_overall | normalize_cqc_rating |
| ... | ... | ... | ... |

---

## 🎯 КРИТИЧНЫЕ МОМЕНТЫ

### ❌ НЕ ДЕЛАЙ:
- ❌ Staging таблица staging_cqc
- ❌ Двойной INSERT
- ❌ has_*_license из service_type_*
- ❌ telephone как NUMERIC
- ❌ Координаты без UK валидации

### ✅ ДЕЛАЙ:
- ✅ Прямо INSERT из CSV
- ✅ PROGRAM 'cat CQC-DataSet_rows.csv'
- ✅ has_*_license из regulated_activity_*
- ✅ telephone как TEXT
- ✅ safe_latitude(), safe_longitude() с валидацией

---

## 📋 ФАЙЛ CHECKLIST

Перед отправкой в output/load-cqc-to-v2.2-direct.sql проверь:

- [ ] 10 helper functions созданы
- [ ] CREATE TABLE скопирован из reference_V2.2_SCHEMA.sql
- [ ] INSERT...SELECT прямо из CSV (нет staging_cqc!)
- [ ] Все 93 поля в INSERT
- [ ] safe_boolean для всех boolean
- [ ] safe_latitude/longitude с валидацией
- [ ] clean_text для текста
- [ ] normalize_cqc_rating для рейтингов
- [ ] safe_date для дат
- [ ] ANALYZE перед индексами
- [ ] 53 индекса созданы
- [ ] 3 Views созданы
- [ ] Validation queries в конце
- [ ] Expected: 271 запись

---

**ГОТОВО! Copy-paste эту команду в Cursor Agent Panel! 🚀**
```

---

## 📝 РЕЗУЛЬТАТ

Создам это как финальный файл для Cursor:
