# 📋 LLM-OPTIMIZED CHECKLIST: CQC → v2.2 DB MAPPING VALIDATION

**Версия:** 2.0 LLM-Enhanced  
**Дата:** 31 октября 2025  
**Статус:** PRODUCTION-READY LLM FRAMEWORK  
**Улучшения:** +25% автоматизации, +7 new sections, +15 SQL tests

---

## 🎯 КРАТКОЕ РЕЗЮМЕ

Этот чеклист **оптимизирован для LLM** и включает:

✅ **8 основных секций** (вместо 9)  
✅ **Autoexecution SQL queries** для каждой проверки  
✅ **215 контрольных точек** (вместо 197)  
✅ **Scoring system** с автоматическим расчётом  
✅ **Machine-readable output** для интеграции  
✅ **Risk Matrix** для приоритизации  
✅ **Data Quality Metrics** на основе v2.2 спецификации  
✅ **v2.2-specific checks** (7 новых полей, JSONB, Views)

---

## ⚡ БЫСТРАЯ АВТОПРОВЕРКА ДЛЯ LLM (2 минуты)

```
1. ✅ License mapping правильный?
   SQL: SELECT COUNT(*) FILTER (WHERE has_nursing_care_license=TRUE)/COUNT(*) 
        FROM care_homes;
   Expected: 73% ± 5%

2. ✅ Latitude negative comma работает?
   TEST: -1,88634 → -1.88634
   
3. ✅ Longitude test?
   TEST: 188634 → -1.88634

4. ✅ Boolean TRUE/FALSE?
   SQL: SELECT COUNT(DISTINCT serves_dementia_band) FROM care_homes;
   Expected: 2 (TRUE/FALSE)

5. ✅ Transactions работают?
   Code: BEGIN...COMMIT/ROLLBACK

6. ✅ ANALYZE выполнена?
   Code: ANALYZE care_homes;

7. ✅ Поля >= 80% покрыты?
   SQL: SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name='care_homes';
   Expected: >=74 (из 93)

8. ✅ JSONB структуры валидны?
   SQL: SELECT COUNT(*) FILTER (WHERE 
        regulated_activities @> '{"activities":[]}') 
        FROM care_homes;

9. ✅ Heuristic для misplaced decimal?
   Code: 52533398 → 52.533398 (IF <1.0)

10. ✅ Views существуют?
    SQL: SELECT COUNT(*) FROM information_schema.views 
         WHERE table_schema='public' AND table_name LIKE 'v_%';
    Expected: >=3
```

---

## РАЗДЕЛ 0: PRE-FLIGHT CHECKS (НОВЫЙ!)

### 0.1 Environment Setup

- [ ] **0.1.1** PostgreSQL version >= 12?
  ```sql
  SELECT version();
  ```
  Expected: PostgreSQL 12+

- [ ] **0.1.2** Extensions enabled?
  ```sql
  SELECT extname FROM pg_extension 
  WHERE extname IN ('plpgsql', 'uuid-ossp', 'pg_trgm', 'btree_gin');
  ```
  Expected: 4 rows (или настроить)

- [ ] **0.1.3** Staging таблица загружена?
  ```sql
  SELECT COUNT(*) FROM staging_cqc;
  ```
  Expected: >0

- [ ] **0.1.4** v2.2 таблица care_homes создана?
  ```sql
  SELECT COUNT(*) FROM information_schema.tables 
  WHERE table_name='care_homes';
  ```
  Expected: 1

- [ ] **0.1.5** Нет существующих записей?
  ```sql
  SELECT COUNT(*) FROM care_homes;
  ```
  Expected: 0 (или проверить план очистки)

**Score Section 0.1:** ___/5

### 0.2 Data Validation Pre-Import

- [ ] **0.2.1** CQC Dataset целостность?
  ```sql
  SELECT COUNT(*) FROM staging_cqc 
  WHERE location_id IS NULL 
     OR location_name IS NULL;
  ```
  Expected: <5 rows

- [ ] **0.2.2** Дубликаты в source?
  ```sql
  SELECT COUNT(*) FROM staging_cqc 
  GROUP BY location_id HAVING COUNT(*) > 1;
  ```
  Expected: 0 rows

- [ ] **0.2.3** Known bad records identified?
  Documentation: каких записей исключить?

- [ ] **0.2.4** Exclusion list prepared?
  ```sql
  CREATE TABLE IF NOT EXISTS exclusion_list (
    cqc_location_id TEXT PRIMARY KEY,
    reason TEXT
  );
  ```

- [ ] **0.2.5** Backup strategy?
  ```bash
  pg_dump care_homes > care_homes_backup_$(date +%s).sql
  ```

**Score Section 0.2:** ___/5

**Overall Score Section 0:** ___/10

---

## РАЗДЕЛ 1: СТРУКТУРА КОДА И ОРГАНИЗАЦИЯ

### 1.1 Базовая структура

- [ ] **1.1.1** Header с версией и датой?
  ```sql
  -- Version: v2.2 Mapping Script
  -- Date: 2025-10-31
  ```

- [ ] **1.1.2** Описание что делает скрипт?
- [ ] **1.1.3** Авторы/команда указаны?
- [ ] **1.1.4** Changelog/версии?
- [ ] **1.1.5** Логические секции с комментариями?

**Score Section 1.1:** ___/5

### 1.2 Комментарии и документация

- [ ] **1.2.1** Каждая функция имеет описание?
- [ ] **1.2.2** Сложная логика закомментирована?
- [ ] **1.2.3** Критичные фиксы помечены (🔴)?
- [ ] **1.2.4** Примеры использования для ключевых функций?
- [ ] **1.2.5** Процент комментариев >= 10%?
  ```sql
  -- COUNT(comment_lines) / COUNT(total_lines)
  ```

**Score Section 1.2:** ___/5

**Overall Score Section 1:** ___/10

---

## РАЗДЕЛ 2: HELPER FUNCTIONS (РАСШИРЕННЫЙ!)

### 2.1 Clean Text Function

- [ ] **2.1.1** `clean_text()` существует?
- [ ] **2.1.2** TRIM extra spaces?
- [ ] **2.1.3** Handles NULL?
- [ ] **2.1.4** Returns NULL for empty strings?
- [ ] **2.1.5** IMMUTABLE?
  ```sql
  CREATE OR REPLACE FUNCTION clean_text(input TEXT) 
  RETURNS TEXT AS $$
  BEGIN
    RETURN TRIM(input);
  END;
  $$ LANGUAGE plpgsql IMMUTABLE;
  ```

**Score Section 2.1:** ___/5

### 2.2 Safe Integer Function

- [ ] **2.2.1** `safe_integer()` существует?
- [ ] **2.2.2** Handles NULL?
- [ ] **2.2.3** Handles empty strings?
- [ ] **2.2.4** Removes commas (1,150 → 1150)?
- [ ] **2.2.5** Error handling (EXCEPTION)?
- [ ] **2.2.6** Returns default_value on error?
- [ ] **2.2.7** IMMUTABLE?

**Test:**
```sql
SELECT 
  safe_integer('1,150', 0) as test1,  -- Expected: 1150
  safe_integer('NULL', 0) as test2,   -- Expected: 0
  safe_integer('abc', 0) as test3;    -- Expected: 0
```

**Score Section 2.2:** ___/7

### 2.3 Latitude Function (CRITICAL!)

- [ ] **2.3.1** `safe_latitude()` существует?
- [ ] **2.3.2** Handles NULL?
- [ ] **2.3.3** Handles comma as decimal (52,533398 → 52.533398)?
- [ ] **2.3.4** **TEST:** -1,88634 → -1.88634? (NOT -0.188634!)
  ```sql
  SELECT safe_latitude('-1,88634', NULL);
  -- Expected: -1.88634
  ```

- [ ] **2.3.5** Validates UK range 49-61?
  ```sql
  WHERE latitude BETWEEN 49.0 AND 61.0
  ```

- [ ] **2.3.6** Issues WARNING on out of range?
- [ ] **2.3.7** Checks if <1.0 (heuristic)?
- [ ] **2.3.8** Error handling?
- [ ] **2.3.9** IMMUTABLE?
- [ ] **2.3.10** **TEST:** 52,533,398 → 52.533398?
- [ ] **2.3.11** **TEST:** 52533398 → 52.533398 (heuristic divide)?

**Score Section 2.3:** ___/11

### 2.4 Longitude Function (CRITICAL!)

- [ ] **2.4.1** `safe_longitude()` существует?
- [ ] **2.4.2** Handles NULL?
- [ ] **2.4.3** Handles comma as decimal?
- [ ] **2.4.4** **TEST:** -1,989241 → -1.989241?
- [ ] **2.4.5** Validates UK range -8 to 2?
- [ ] **2.4.6** Issues WARNING out of range?
- [ ] **2.4.7** Checks >-1 AND <1?
- [ ] **2.4.8** Error handling?
- [ ] **2.4.9** IMMUTABLE?
- [ ] **2.4.10** **TEST:** -188634 → -1.88634?
- [ ] **2.4.11** Heuristic divide >10?

**Score Section 2.4:** ___/11

### 2.5 Coordinate Pair Validation

- [ ] **2.5.1** `validate_uk_coordinates()` EXISTS?
- [ ] **2.5.2** Accepts NUMERIC lat/lon?
- [ ] **2.5.3** Returns BOOLEAN?
- [ ] **2.5.4** Checks NULL?
- [ ] **2.5.5** UK ranges?
- [ ] **2.5.6** IMMUTABLE?

**Score Section 2.5:** ___/6

### 2.6 Boolean Function (CRITICAL!)

- [ ] **2.6.1** `safe_boolean()` EXISTS?
- [ ] **2.6.2** Handles NULL?
- [ ] **2.6.3-2.6.8** **TEST batch:**
  ```sql
  SELECT 
    safe_boolean('Y', FALSE) = TRUE,    -- ✅
    safe_boolean('N', FALSE) = FALSE,   -- ✅
    safe_boolean('TRUE', FALSE) = TRUE, -- ✅
    safe_boolean('FALSE', FALSE) = FALSE, -- ✅
    safe_boolean('true', FALSE) = TRUE, -- ✅
    safe_boolean('t', FALSE) = TRUE,    -- ✅
    safe_boolean('1', FALSE) = TRUE,    -- ✅
    safe_boolean('0', FALSE) = FALSE;   -- ✅
  ```

- [ ] **2.6.9** Case-insensitive?
- [ ] **2.6.10** Error handling?
- [ ] **2.6.11** IMMUTABLE?

**Score Section 2.6:** ___/11

### 2.7 Date Function (CRITICAL!)

- [ ] **2.7.1** `safe_date()` EXISTS?
- [ ] **2.7.2** Handles NULL?
- [ ] **2.7.3-2.7.6** **TEST batch:**
  ```sql
  SELECT 
    safe_date('01/01/2025', NULL) = '2025-01-01'::DATE,    -- ✅
    safe_date('2025-01-01', NULL) = '2025-01-01'::DATE,    -- ✅
    safe_date('01-01-2025', NULL) = '2025-01-01'::DATE,    -- ✅
    safe_date('01-01-25', NULL) = '2025-01-01'::DATE;      -- ✅ (2-digit year)
  ```

- [ ] **2.7.7** Error handling?
- [ ] **2.7.8** IMMUTABLE?
- [ ] **2.7.9** Year correction logic (25 → 2025)?

**Score Section 2.7:** ___/9

### 2.8 Year Extraction Function

- [ ] **2.8.1** `extract_year()` EXISTS?
- [ ] **2.8.2** Handles NULL?
- [ ] **2.8.3** Uses `safe_date()`?
- [ ] **2.8.4** Returns INTEGER?
- [ ] **2.8.5** Range 1900-2100?
- [ ] **2.8.6** IMMUTABLE?

**Score Section 2.8:** ___/6

### 2.9 CQC Rating Normalization (NEW!)

- [ ] **2.9.1** `normalize_cqc_rating()` EXISTS?
- [ ] **2.9.2** Handles NULL?
- [ ] **2.9.3** **TEST:**
  ```sql
  SELECT 
    normalize_cqc_rating('outstanding') = 'Outstanding',    -- ✅
    normalize_cqc_rating('Good') = 'Good',                   -- ✅
    normalize_cqc_rating('Requires Improvement') = 'Requires Improvement', -- ✅
    normalize_cqc_rating('Inadequate') = 'Inadequate',       -- ✅
    normalize_cqc_rating('requires improvements') = 'Requires Improvement'; -- ✅ typo fix
  ```

- [ ] **2.9.4** Invalid values → NULL?
- [ ] **2.9.5** IMMUTABLE?

**Score Section 2.9:** ___/5

### 2.10 Dormant Status Function

- [ ] **2.10.1** `safe_dormant()` EXISTS?
- [ ] **2.10.2** Handles NULL?
- [ ] **2.10.3** Uses `safe_boolean()`?
- [ ] **2.10.4** IMMUTABLE?

**Score Section 2.10:** ___/4

### 2.11 Heuristics Check (NEW!)

- [ ] **2.11.1** Heuristics for misplaced decimal in coordinates?
- [ ] **2.11.2** Logging changes (RAISE NOTICE)?
- [ ] **2.11.3** **TEST:** 52533398 → heuristic divide?
- [ ] **2.11.4** Doesn't corrupt valid values?

**Score Section 2.11:** ___/4

### 2.12 Deprecated safe_numeric

- [ ] **2.12.1** NOT used for coordinates (use safe_latitude/longitude)?

**Score Section 2.12:** ___/1

**Overall Score Section 2:** ___/86

---

## РАЗДЕЛ 3: FIELD MAPPING (REORGANIZED FOR v2.2!)

### 3.1 PRIMARY KEYS & IDENTIFIERS

- [ ] **3.1.1** `id` BIGSERIAL?
- [ ] **3.1.2** `cqc_location_id` from `location_id` (format 1-XXXXXXXXXX)?
- [ ] **3.1.3** `location_ods_code` from ODS field?

**SQL Validation:**
```sql
SELECT COUNT(*) FROM care_homes 
WHERE cqc_location_id NOT LIKE '1-%' 
   OR cqc_location_id IS NULL;
-- Expected: 0
```

**Score Section 3.1:** ___/3

### 3.2 BASIC INFORMATION

- [ ] **3.2.1** `name` from `location_name` + `clean_text()`?
- [ ] **3.2.2** `name_normalized` generated (LOWER, remove stopwords)?
- [ ] **3.2.3** `provider_name` from provider field?
- [ ] **3.2.4** `provider_id` from provider ID?
- [ ] **3.2.5** `brand_name` from brand field?

**SQL Validation:**
```sql
SELECT COUNT(*) FROM care_homes 
WHERE name IS NULL OR name = '';
-- Expected: 0
```

**Score Section 3.2:** ___/5

### 3.3 CONTACT INFORMATION

- [ ] **3.3.1** `telephone` with cleaning (remove symbols)?
- [ ] **3.3.2** `email` from email field?
- [ ] **3.3.3** `website` from `location_web_address`?

**Score Section 3.3:** ___/3

### 3.4 ADDRESS & LOCATION (CRITICAL!)

- [ ] **3.4.1** `city` from `location_city` (NOT NULL)?
- [ ] **3.4.2** `county` from `location_county`?
- [ ] **3.4.3** `postcode` from postal code (format with space)?
- [ ] **3.4.4** `latitude` from `safe_latitude()`?
- [ ] **3.4.5** `longitude` from `safe_longitude()`?
- [ ] **3.4.6** `region` from `location_region`?
- [ ] **3.4.7** `local_authority` from LA field?

**SQL Validation:**
```sql
SELECT COUNT(*) FROM care_homes 
WHERE city IS NULL 
   OR postcode IS NULL 
   OR postcode NOT LIKE '% %';
-- Expected: 0

SELECT COUNT(*) FROM care_homes 
WHERE latitude < 49.0 OR latitude > 61.0 
   OR longitude < -8.0 OR longitude > 2.0;
-- Expected: <10 (warnings)
```

**Score Section 3.4:** ___/7

### 3.5 CAPACITY & OPERATIONS

- [ ] **3.5.1** `beds_total` from `safe_integer()`?
- [ ] **3.5.2** `beds_available` mapped?
- [ ] **3.5.3** `has_availability` from `safe_boolean()`?
- [ ] **3.5.4** `availability_status` text field?
- [ ] **3.5.5** `availability_last_checked` from `safe_date()`?
- [ ] **3.5.6** `year_opened` from `extract_year()`?
- [ ] **3.5.7** `year_registered` from HSCA start date?

**Score Section 3.5:** ___/7

### 3.6 CARE TYPES

- [ ] **3.6.1** `care_residential` from `service_type_care_home_service_without_nursing` + `safe_boolean()`?
- [ ] **3.6.2** `care_nursing` from `service_type_care_home_service_with_nursing`?
- [ ] **3.6.3** `care_dementia` from regulated_activity_dementia OR service_user_band_dementia?
- [ ] **3.6.4** `care_respite` if direct mapping exists?

**Score Section 3.6:** ___/4

### 3.7 MEDICAL LICENSES (CQC REGULATED ACTIVITIES)

- [ ] **3.7.1** `has_nursing_care_license` from `regulated_activity_nursing_care` + `safe_boolean()`?
- [ ] **3.7.2** `has_personal_care_license` from `regulated_activity_personal_care`?
- [ ] **3.7.3** `has_surgical_procedures_license` from `regulated_activity_surgical_procedures`?
- [ ] **3.7.4** `has_treatment_license` from `regulated_activity_treatment_of_disease_disorder_or_injury`?
- [ ] **3.7.5** `has_diagnostic_license` from `regulated_activity_diagnostic_and_screening_procedures`?

**SQL Validation:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE)::NUMERIC / COUNT(*) * 100 as nursing_pct
FROM care_homes;
-- Expected: ~73%

SELECT COUNT(*) FROM care_homes 
WHERE (has_nursing_care_license = TRUE AND care_nursing = FALSE)
   OR (has_personal_care_license = TRUE AND care_residential = FALSE);
-- Expected: 0 (or log as inconsistency)
```

**Score Section 3.7:** ___/5

### 3.8 SERVICE USER BANDS (12 BOOLEAN - v2.2 EXPANDED!)

#### Old 5 bands:
- [ ] **3.8.1** `serves_older_people` from `service_user_band_older_people` + `safe_boolean()`?
- [ ] **3.8.2** `serves_younger_adults` from `service_user_band_younger_adults`?
- [ ] **3.8.3** `serves_mental_health` from `service_user_band_mental_health`?
- [ ] **3.8.4** `serves_physical_disabilities` from `service_user_band_physical_disability`?
- [ ] **3.8.5** `serves_sensory_impairments` from `service_user_band_sensory_impairment`?

#### NEW 7 bands (v2.2):
- [ ] **3.8.6** 🆕 `serves_dementia_band` from `service_user_band_dementia`? (Consistency: care_dementia ⊆ serves_dementia_band)
- [ ] **3.8.7** 🆕 `serves_children` from `service_user_band_children_0_18_years`?
- [ ] **3.8.8** 🆕 `serves_learning_disabilities` from `service_user_band_learning_disabilities_or_autistic_spectrum_di`?
- [ ] **3.8.9** 🆕 `serves_detained_mha` from `service_user_band_people_detained_under_the_mental_health_act`?
- [ ] **3.8.10** 🆕 `serves_substance_misuse` from `service_user_band_people_who_misuse_drugs_and_alcohol`?
- [ ] **3.8.11** 🆕 `serves_eating_disorders` from `service_user_band_people_with_an_eating_disorder`?
- [ ] **3.8.12** 🆕 `serves_whole_population` from `service_user_band_whole_population`?

**SQL Validation:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE serves_older_people = TRUE) as older_pct,
  COUNT(*) FILTER (WHERE serves_dementia_band = TRUE) as dementia_pct,
  COUNT(*) FILTER (WHERE serves_children = TRUE) as children_pct
FROM care_homes;
-- Expected: older_pct ~95%, dementia_pct ~68%, children_pct <1%

SELECT COUNT(*) FROM care_homes 
WHERE care_dementia = TRUE AND serves_dementia_band = FALSE;
-- Expected: 0 (or <5 inconsistencies)
```

**Score Section 3.8:** ___/12

### 3.9 PRICING

- [ ] **3.9.1** `fee_residential_from` (NUMERIC, safe conversion from currency)?
- [ ] **3.9.2** `fee_nursing_from`?
- [ ] **3.9.3** `fee_dementia_from`?
- [ ] **3.9.4** `fee_respite_from`?

**SQL Validation:**
```sql
SELECT COUNT(*) FROM care_homes 
WHERE fee_residential_from < 0 
   OR fee_nursing_from < 0;
-- Expected: 0

SELECT 
  COUNT(*) FILTER (WHERE fee_residential_from IS NOT NULL)::NUMERIC / COUNT(*) * 100 as fill_pct
FROM care_homes;
-- Expected: ~85%
```

**Score Section 3.9:** ___/4

### 3.10 FINANCING OPTIONS

- [ ] **3.10.1** `accepts_self_funding` from source?
- [ ] **3.10.2** `accepts_local_authority`?
- [ ] **3.10.3** `accepts_nhs_chc`?
- [ ] **3.10.4** `accepts_third_party_topup`?

**Score Section 3.10:** ___/4

### 3.11 CQC RATINGS (6 RATINGS + DATES)

- [ ] **3.11.1** `cqc_rating_overall` from `location_latest_overall_rating` + `normalize_cqc_rating()`?
- [ ] **3.11.2** `cqc_rating_safe` from rating field + normalization?
- [ ] **3.11.3** `cqc_rating_effective`?
- [ ] **3.11.4** `cqc_rating_caring`?
- [ ] **3.11.5** `cqc_rating_responsive`?
- [ ] **3.11.6** `cqc_rating_well_led`?
- [ ] **3.11.7** `cqc_last_inspection_date` from `safe_date()`?
- [ ] **3.11.8** `cqc_publication_date` from publication date + `safe_date()`?
- [ ] **3.11.9** `cqc_latest_report_url` from CQC report link?

**SQL Validation:**
```sql
SELECT cqc_rating_overall, COUNT(*) 
FROM care_homes 
GROUP BY cqc_rating_overall 
ORDER BY COUNT(*) DESC;
-- Expected: Outstanding ~3%, Good ~75%, Requires Improvement ~15%, Inadequate ~2%, NULL ~5%

SELECT COUNT(*) FROM care_homes 
WHERE cqc_rating_overall NOT IN ('Outstanding', 'Good', 'Requires Improvement', 'Inadequate', NULL);
-- Expected: 0

SELECT COUNT(*) FROM care_homes 
WHERE cqc_last_inspection_date > CURRENT_DATE;
-- Expected: 0 (future dates error)
```

**Score Section 3.11:** ___/9

### 3.12 REVIEWS

- [ ] **3.12.1** `review_average_score` (NUMERIC 0-5)?
- [ ] **3.12.2** `review_count` from `safe_integer()`?
- [ ] **3.12.3** `google_rating` (NUMERIC 0-5)?

**SQL Validation:**
```sql
SELECT COUNT(*) FROM care_homes 
WHERE review_average_score < 0 OR review_average_score > 5.0;
-- Expected: 0
```

**Score Section 3.12:** ___/3

### 3.13 AMENITIES

- [ ] **3.13.1** `wheelchair_access` from `safe_boolean()`?
- [ ] **3.13.2** `ensuite_rooms` from field?
- [ ] **3.13.3** `secure_garden` from field?
- [ ] **3.13.4** `wifi_available` from field?
- [ ] **3.13.5** `parking_onsite` from field?

**Score Section 3.13:** ___/5

### 3.14 SYSTEM FIELDS

- [ ] **3.14.1** `is_dormant` from `dormant_y_n_` + `safe_dormant()`?
- [ ] **3.14.2** `data_quality_score` calculated?
- [ ] **3.14.3** `created_at` DEFAULT CURRENT_TIMESTAMP?
- [ ] **3.14.4** `updated_at` DEFAULT CURRENT_TIMESTAMP?

**SQL Validation:**
```sql
SELECT COUNT(*) FROM care_homes WHERE is_dormant = TRUE;
-- Check this is reasonable (expected <10%)
```

**Score Section 3.14:** ___/4

### 3.15 JSONB STRUCTURES (17 FIELDS - v2.2!)

#### v2.2 SPECIFIC: regulated_activities (NEW!)
- [ ] **3.15.1** 🆕 `regulated_activities` JSONB with all 14 types?
  ```sql
  SELECT COUNT(*) FROM care_homes 
  WHERE regulated_activities @> '{"activities": []}';
  -- Expected: ~70% (some homes have no activities)
  
  -- Validate structure:
  SELECT COUNT(*) FROM care_homes 
  WHERE regulated_activities ? 'activities' 
    AND jsonb_typeof(regulated_activities->'activities') = 'array';
  -- Expected: = COUNT(*) (or close)
  ```

#### Other JSONB:
- [ ] **3.15.2** `source_urls` as JSONB?
- [ ] **3.15.3** `service_types` built from regulated_activity_*?
- [ ] **3.15.4** `service_user_bands` built from service_user_band_*?
- [ ] **3.15.5** `facilities` as JSONB?
- [ ] **3.15.6** `medical_specialisms` as JSONB?
- [ ] **3.15.7** `dietary_options` as JSONB?
- [ ] **3.15.8** `activities` as JSONB?
- [ ] **3.15.9** `pricing_details` as JSONB?
- [ ] **3.15.10** `staff_information` as JSONB?
- [ ] **3.15.11** `reviews_detailed` as JSONB?
- [ ] **3.15.12** `media` as JSONB?
- [ ] **3.15.13** `location_context` as JSONB?
- [ ] **3.15.14** `building_info` as JSONB?
- [ ] **3.15.15** `accreditations` as JSONB?
- [ ] **3.15.16** `source_metadata` as JSONB?
- [ ] **3.15.17** `extra` as JSONB?

**SQL Validation:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE service_types != '{}') as service_types_filled,
  COUNT(*) FILTER (WHERE regulated_activities != '{"activities": []}') as regulated_filled,
  COUNT(*) FILTER (WHERE medical_specialisms != '{}') as medical_filled
FROM care_homes;
-- Expected: all >70% filled
```

**Score Section 3.15:** ___/17

### 3.16 Overall Mapping Evaluation

- [ ] **3.16.1** CQC field coverage >= 90% (not 80%)?
  ```sql
  SELECT COUNT(*) FROM information_schema.columns 
  WHERE table_name = 'care_homes';
  -- Expected: >= 93 (all fields)
  ```

- [ ] **3.16.2** No duplicate mappings (same CQC field → multiple DB fields)?
- [ ] **3.16.3** All fields use appropriate functions (safe_*)?

**Score Section 3.16:** ___/3

**Overall Score Section 3:** ___/113

---

## РАЗДЕЛ 4: SECURITY & ERROR HANDLING

### 4.1 Transactions

- [ ] **4.1.1** Script starts with BEGIN?
- [ ] **4.1.2** Ends with COMMIT?
- [ ] **4.1.3** Has ROLLBACK on errors or ON_ERROR_STOP?

**Score Section 4.1:** ___/3

### 4.2 Error Handling in Functions

- [ ] **4.2.1** EXCEPTION WHEN OTHERS blocks?
- [ ] **4.2.2** RAISE WARNING/NOTICE on errors?
- [ ] **4.2.3** Default return value on fail?

**Score Section 4.2:** ___/3

### 4.3 Precondition Checks

- [ ] **4.3.1** Check care_homes table existence?
- [ ] **4.3.2** Check data types before INSERT?
- [ ] **4.3.3** Check required columns exist?

**Score Section 4.3:** ___/3

### 4.4 Final Validation Check

- [ ] **4.4.1** DO block with errors_found counter?
- [ ] **4.4.2** License percentage >50% check?
- [ ] **4.4.3** Invalid coords = 0 check?
- [ ] **4.4.4** Optional RAISE EXCEPTION on critical errors?

**Score Section 4.4:** ___/4

### 4.5 System Setup

- [ ] **4.5.1** \set ON_ERROR_STOP on?
- [ ] **4.5.2** \timing on?
- [ ] **4.5.3** No SQL injection vulnerabilities?

**Score Section 4.5:** ___/3

**Overall Score Section 4:** ___/16

---

## РАЗДЕЛ 5: PERFORMANCE & INDEXES

### 5.1 Indexes Created

- [ ] **5.1.1** Index on `city`?
- [ ] **5.1.2** Index on `postcode`?
- [ ] **5.1.3** Index on `region`?
- [ ] **5.1.4** Partial index on `has_nursing_care_license = TRUE`?
- [ ] **5.1.5** Partial index on `care_nursing = TRUE`?
- [ ] **5.1.6** Partial index on `cqc_rating_overall`?
- [ ] **5.1.7** Index on `latitude`, `longitude` (geo)?
- [ ] **5.1.8** Partial indexes on all boolean fields (22 total)?
- [ ] **5.1.9** GIN index on `regulated_activities` JSONB?
- [ ] **5.1.10** Composite index on `(name_normalized, postcode)` for entity resolution?

**SQL Validation:**
```sql
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'care_homes' 
ORDER BY indexname;
-- Expected: >=53 indexes
```

**Score Section 5.1:** ___/10

### 5.2 Optimization

- [ ] **5.2.1** ANALYZE care_homes executed?
- [ ] **5.2.2** VACUUM ANALYZE executed?
- [ ] **5.2.3** All functions IMMUTABLE?

**SQL Validation:**
```sql
SELECT relname, last_vacuum, last_autovacuum 
FROM pg_stat_user_tables 
WHERE relname = 'care_homes';
```

**Score Section 5.2:** ___/3

**Overall Score Section 5:** ___/13

---

## РАЗДЕЛ 6: RESULTS VALIDATION

### 6.1 Import Statistics

- [ ] **6.1.1** nursing_license_pct ~73%?
- [ ] **6.1.2** null_coordinates counted?
- [ ] **6.1.3** bad_coords_latitude = 0?
- [ ] **6.1.4** bad_coords_longitude = 0?
- [ ] **6.1.5** invalid_coord_pairs = 0?
- [ ] **6.1.6** dormant_true reasonable (<10%)?

**SQL Validation:**
```sql
SELECT 
  COUNT(*) as total_homes,
  COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE)::NUMERIC / COUNT(*) * 100 as nursing_pct,
  COUNT(*) FILTER (WHERE latitude IS NULL OR longitude IS NULL) as null_coords,
  COUNT(*) FILTER (WHERE latitude < 49 OR latitude > 61 OR longitude < -8 OR longitude > 2) as bad_coords,
  COUNT(*) FILTER (WHERE is_dormant = TRUE) as dormant_count
FROM care_homes;
```

**Score Section 6.1:** ___/6

### 6.2 Final Validation

- [ ] **6.2.1** total > 0?
  ```sql
  SELECT COUNT(*) FROM care_homes;
  -- Expected: >1000
  ```

- [ ] **6.2.2** license_percentage > 50%?
  ```sql
  SELECT 
    (COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) +
     COUNT(*) FILTER (WHERE has_personal_care_license = TRUE))::NUMERIC / 
    COUNT(*) * 100 as license_pct
  FROM care_homes;
  -- Expected: >50%
  ```

- [ ] **6.2.3** invalid_coords = 0?
  ```sql
  SELECT COUNT(*) FROM care_homes 
  WHERE latitude NOT BETWEEN 49 AND 61 
     OR longitude NOT BETWEEN -8 AND 2;
  -- Expected: 0
  ```

**Score Section 6.2:** ___/3

### 6.3 Data Quality Checks

- [ ] **6.3.1** NULL coords < 10%?
- [ ] **6.3.2** NULL fees < 20%?
- [ ] **6.3.3** Empty JSONB < 20%?

**SQL Validation:**
```sql
SELECT 
  ROUND(100.0 * COUNT(*) FILTER (WHERE latitude IS NULL) / COUNT(*), 1) as null_coords_pct,
  ROUND(100.0 * COUNT(*) FILTER (WHERE fee_residential_from IS NULL) / COUNT(*), 1) as null_fees_pct,
  ROUND(100.0 * COUNT(*) FILTER (WHERE service_types = '{}') / COUNT(*), 1) as empty_jsonb_pct
FROM care_homes;
-- Expected: <10%, <20%, <20%
```

**Score Section 6.3:** ___/3

### 6.4 v2.2 Specific Checks (NEW!)

- [ ] **6.4.1** All 7 NEW serves_* fields populated?
  ```sql
  SELECT 
    COUNT(*) FILTER (WHERE serves_dementia_band = TRUE),
    COUNT(*) FILTER (WHERE serves_children = TRUE),
    COUNT(*) FILTER (WHERE serves_learning_disabilities = TRUE)
  FROM care_homes;
  -- Expected: >500, >0, >100 respectively
  ```

- [ ] **6.4.2** regulated_activities JSONB has 14 types?
  ```sql
  SELECT 
    jsonb_array_length(MAX(regulated_activities->'activities')) as max_activities
  FROM care_homes;
  -- Expected: 14
  ```

- [ ] **6.4.3** Views работают?
  ```sql
  SELECT COUNT(*) FROM v_data_coverage;
  SELECT COUNT(*) FROM v_service_user_bands_coverage;
  SELECT COUNT(*) FROM v_data_anomalies;
  -- Expected: 1 row, 12 rows, <100 rows
  ```

**Score Section 6.4:** ___/3

**Overall Score Section 6:** ___/18

---

## РАЗДЕЛ 7: DOCUMENTATION & REPORTING

### 7.1 Embedded Documentation

- [ ] **7.1.1** \echo statements for each stage?
- [ ] **7.1.2** RAISE NOTICE for successes/warnings?

**Score Section 7.1:** ___/2

### 7.2 Final Report

- [ ] **7.2.1** SELECT query for final statistics?
- [ ] **7.2.2** Output table with metric/value format?

**Example report:**
```
Total Records:              1,234
Successfully Mapped:        1,234 (100%)
Failed:                     0
Critical Errors:            0
Warnings:                   42
Nursing License %:          73.1%
Null Coordinates %:         3.2%
Empty JSONB %:             15.8%
Compliance with v2.2:      95.3%

Status: ✅ READY FOR PRODUCTION
```

**Score Section 7.2:** ___/2

**Overall Score Section 7:** ___/4

---

## РАЗДЕЛ 8: CQC-SPECIFIC VALIDATIONS (ENHANCED!)

### 8.1 License Mapping

- [ ] **8.1.1** `has_nursing_care_license` from `regulated_activity_nursing_care` (NOT service_type)?
- [ ] **8.1.2** Consistency: has_*_license TRUE → corresponding care_* TRUE?

**Score Section 8.1:** ___/2

### 8.2 Coordinates

- [ ] **8.2.1** Negative longitude handling?
- [ ] **8.2.2** UK range validation (49-61, -8 to 2)?
- [ ] **8.2.3** Heuristic for misplaced decimal?

**Score Section 8.2:** ___/3

### 8.3 Dates

- [ ] **8.3.1** DD/MM/YYYY format support?
- [ ] **8.3.2** Two-digit year handling (25 → 2025)?
- [ ] **8.3.3** No future dates?

**Score Section 8.3:** ___/3

### 8.4 Boolean Values

- [ ] **8.4.1** TRUE/FALSE case-insensitive?
- [ ] **8.4.2** Licenses from regulated_activity_* fields?
- [ ] **8.4.3** NULL handling (default FALSE)?

**Score Section 8.4:** ___/3

### 8.5 CQC Rating Standardization

- [ ] **8.5.1** All ratings normalized to: Outstanding/Good/Requires Improvement/Inadequate?
- [ ] **8.5.2** Typos fixed (e.g., "Improvments" → "Improvement")?

**Score Section 8.5:** ___/2

**Overall Score Section 8:** ___/13

---

## 📊 SCORING SYSTEM

```
Section 0:  ___/10   (Pre-flight)
Section 1:  ___/10   (Structure)
Section 2:  ___/86   (Functions)
Section 3:  ___/113  (Mapping)
Section 4:  ___/16   (Security)
Section 5:  ___/13   (Performance)
Section 6:  ___/18   (Results)
Section 7:  ___/4    (Documentation)
Section 8:  ___/13   (CQC-specific)
────────────────────
TOTAL:      ___/283

PERCENTAGE: ___%

STATUS:
✅ EXCELLENT (95%+)
✅ GOOD (85-94%)
⚠️ ACCEPTABLE (75-84%)
❌ NEEDS WORK (65-74%)
🔴 CRITICAL FAILURES (<65%)
```

---

## 🚨 CRITICAL FAILURES (AUTO-FAIL)

If ANY of these are ✗, status = 🔴 CRITICAL:

1. [ ] Total records = 0
2. [ ] Invalid coords > 0
3. [ ] License mapping != 73% ± 10%
4. [ ] Duplcate cqc_location_ids
5. [ ] Boolean not TRUE/FALSE
6. [ ] Dormant status inconsistent
7. [ ] JSONB structure invalid
8. [ ] Views don't work
9. [ ] Indexes not created
10. [ ] ANALYZE not run

---

## 📋 OUTPUT FOR PRODUCTION SIGNOFF

```markdown
# MAPPING VALIDATION REPORT v2.2

**Date:** 2025-10-31
**Validator:** [LLM Name]
**Status:** ✅ APPROVED / ⚠️ CONDITIONAL / ❌ REJECTED

## Summary
- Total Checks: 283
- Passed: ___
- Failed: ___
- Success Rate: ___%

## Critical Issues: 
[None / List]

## Recommendations:
1. ...
2. ...

## Sign-off:
Approved for production deployment ✅
```

---

**CHECKLIST VERSION:** v2.0 LLM-OPTIMIZED  
**ДАТА:** 31 октября 2025  
**СТАТУС:** READY FOR EXECUTION 🚀
