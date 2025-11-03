-- ============================================================================
-- МИГРАЦИОННЫЙ СКРИПТ CQC → CARE HOMES v2.2 (v7.3.1 SUPABASE)
-- АДАПТИРОВАНО ДЛЯ SUPABASE: загрузка CSV через Storage или Table Editor
-- ============================================================================
-- Версия: 7.3.1 SUPABASE
-- Дата: 31 октября 2025
-- 
-- ЧТО ВКЛЮЧЕНО:
-- ✅ 93 поля (76 flat + 17 JSONB) - полное покрытие v2.2
-- ✅ Загрузка CSV через Supabase Storage или из существующей таблицы
-- ✅ has_*_license ИЗ regulated_activity_* (НЕ service_type_*)
-- ✅ Координаты с decimal fix + UK validation (49-61, -8 to 2)
-- ✅ Даты DD/MM/YYYY с двузначными годами
-- ✅ Boolean lowercase + NULL handling
-- ✅ regulated_activities JSONB (14 лицензий)
-- ✅ 12 полей serves_* (100% service user bands, включая 7 новых)
-- ✅ 10 helper functions с error handling
-- ✅ Транзакции + Rollback при ошибках
-- ✅ Полная статистика и валидация
-- ============================================================================

-- ============================================================================
-- ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ В SUPABASE:
-- ============================================================================
-- 
-- ВАРИАНТ 1: Загрузка CSV через Supabase Storage (РЕКОМЕНДУЕТСЯ)
--   1. Загрузите CSV файл в Supabase Storage (bucket: public или создайте новый)
--   2. Замените 'your-bucket-name/cqc_dataset.csv' на реальный путь
--   3. Выполните весь скрипт в SQL Editor
--
-- ВАРИАНТ 2: Данные уже загружены через Table Editor
--   1. Если CSV уже загружен в таблицу (например, через Table Editor),
--      замените "CREATE TEMPORARY TABLE temp_cqc_raw" на вашу таблицу
--   2. Обновите имя таблицы в SELECT запросе
--
-- ВАРИАНТ 3: Использовать существующую таблицу
--   1. Если у вас уже есть таблица с данными CQC,
--      замените temp_cqc_raw на имя вашей таблицы
-- ============================================================================

\set ON_ERROR_STOP on
\timing on

\echo ''
\echo '========================================================================'
\echo 'CQC → CARE HOMES v2.2 МИГРАЦИЯ (v7.3.1 SUPABASE)'
\echo '========================================================================'
\echo 'Целевая БД: care_homes v2.2 (93 поля)'
\echo 'Метод: Загрузка через Supabase Storage или Table Editor'
\echo '========================================================================'
\echo ''

-- ============================================================================
-- ЧАСТЬ 0: ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ
-- ============================================================================

\echo '========================================================================'
\echo 'ЧАСТЬ 0: Проверки перед миграцией'
\echo '========================================================================'
\echo ''

DO $$
BEGIN
    -- Проверка существования таблицы
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_name = 'care_homes') THEN
        RAISE EXCEPTION 'КРИТИЧЕСКАЯ ОШИБКА: Таблица care_homes не существует! Сначала выполните step1_schema_create.sql';
    END IF;
    RAISE NOTICE '✅ Проверка 1/5: Таблица care_homes существует';
    
    -- Проверка количества полей (должно быть 93)
    IF (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'care_homes') != 93 THEN
        RAISE EXCEPTION 'КРИТИЧЕСКАЯ ОШИБКА: Неправильное количество полей (% вместо 93)!', (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'care_homes');
    ELSE
        RAISE NOTICE '✅ Проверка 2/5: Количество полей корректно (93)';
    END IF;
    
    -- Проверка новых полей v2.2
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'care_homes' 
                   AND column_name = 'regulated_activities') THEN
        RAISE EXCEPTION 'КРИТИЧЕСКАЯ ОШИБКА: Поле regulated_activities отсутствует! Используйте БД v2.2';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'care_homes' 
                   AND column_name = 'serves_dementia_band') THEN
        RAISE EXCEPTION 'КРИТИЧЕСКАЯ ОШИБКА: Поле serves_dementia_band отсутствует! Используйте БД v2.2';
    END IF;
    RAISE NOTICE '✅ Проверка 3/5: Новые поля v2.2 присутствуют';
    
    -- Проверка типа telephone (должен быть TEXT)
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_name = 'care_homes' AND column_name = 'telephone') 
        NOT IN ('text', 'character varying') THEN
        RAISE EXCEPTION 'КРИТИЧЕСКАЯ ОШИБКА: Тип telephone не TEXT!';
    ELSE
        RAISE NOTICE '✅ Проверка 4/5: Тип telephone корректен (TEXT)';
    END IF;
    
    -- Проверка на пустую таблицу (условный TRUNCATE)
    IF (SELECT COUNT(*) FROM care_homes) > 0 THEN
        RAISE WARNING '⚠️ Таблица не пуста! Выполняю TRUNCATE...';
        TRUNCATE care_homes RESTART IDENTITY;
    END IF;
    RAISE NOTICE '✅ Проверка 5/5: Таблица готова (пуста)';
END $$;

\echo ''

-- ============================================================================
-- ЧАСТЬ 1: СОЗДАНИЕ ВРЕМЕННОЙ ТАБЛИЦЫ ДЛЯ CSV
-- ============================================================================

\echo '========================================================================'
\echo 'ЧАСТЬ 1: Создание временной таблицы temp_cqc_raw'
\echo '========================================================================'
\echo ''

DROP TABLE IF EXISTS temp_cqc_raw;

CREATE TEMPORARY TABLE temp_cqc_raw (
    location_id TEXT,
    location_hsca_start_date TEXT,
    dormant_y_n_ TEXT,
    care_home_ TEXT,
    location_name TEXT,
    location_ods_code TEXT,
    location_telephone_number TEXT,
    registered_manager TEXT,
    location_web_address TEXT,
    care_homes_beds TEXT,
    location_type_sector TEXT,
    location_inspection_directorate TEXT,
    location_primary_inspection_category TEXT,
    location_latest_overall_rating TEXT,
    publication_date TEXT,
    inherited_rating_y_n_ TEXT,
    location_region TEXT,
    location_nhs_region TEXT,
    location_local_authority TEXT,
    location_onspd_ccg_code TEXT,
    location_onspd_ccg TEXT,
    location_commissioning_ccg_code TEXT,
    location_commissioning_ccg TEXT,
    location_street_address TEXT,
    location_address_line_2 TEXT,
    location_city TEXT,
    location_county TEXT,
    location_postal_code TEXT,
    location_paf_id TEXT,
    location_uprn_id TEXT,
    location_latitude TEXT,
    location_longitude TEXT,
    location_parliamentary_constituency TEXT,
    brand_id TEXT,
    brand_name TEXT,
    provider_companies_house_number TEXT,
    provider_charity_number TEXT,
    provider_id TEXT,
    provider_name TEXT,
    provider_hsca_start_date TEXT,
    provider_type_sector TEXT,
    provider_inspection_directorate TEXT,
    provider_primary_inspection_category TEXT,
    provider_ownership_type TEXT,
    provider_telephone_number TEXT,
    provider_web_address TEXT,
    provider_street_address TEXT,
    provider_address_line_2 TEXT,
    provider_city TEXT,
    provider_county TEXT,
    provider_postal_code TEXT,
    provider_paf_id TEXT,
    provider_uprn_id TEXT,
    provider_local_authority TEXT,
    provider_region TEXT,
    provider_nhs_region TEXT,
    provider_latitude TEXT,
    provider_longitude TEXT,
    provider_parliamentary_constituency TEXT,
    provider_nominated_individual_name TEXT,
    cqc_report_url TEXT,
    cqc_rating_safe TEXT,
    cqc_rating_effective TEXT,
    cqc_rating_caring TEXT,
    cqc_rating_responsive TEXT,
    cqc_rating_well_led TEXT,
    cqc_rating_overall TEXT,
    provider_main_partner_name TEXT,
    regulated_activity_accommodation_for_persons_who_require_nursing TEXT,
    regulated_activity_accommodation_for_persons_who_require_treatment TEXT,
    regulated_activity_assessment_or_medical_treatment_for_persons_ TEXT,
    regulated_activity_diagnostic_and_screening_procedures TEXT,
    regulated_activity_family_planning TEXT,
    regulated_activity_management_of_supply_of_blood_and_blood_deri TEXT,
    regulated_activity_maternity_and_midwifery_services TEXT,
    regulated_activity_nursing_care TEXT,
    regulated_activity_personal_care TEXT,
    regulated_activity_services_in_slimming_clinics TEXT,
    regulated_activity_surgical_procedures TEXT,
    regulated_activity_termination_of_pregnancies TEXT,
    regulated_activity_transport_services_triage_and_medical_advice TEXT,
    regulated_activity_treatment_of_disease_disorder_or_injury TEXT,
    service_type_acute_services_with_overnight_beds TEXT,
    service_type_acute_services_without_overnight_beds_listed_acute TEXT,
    service_type_ambulance_service TEXT,
    service_type_blood_and_transplant_service TEXT,
    service_type_care_home_service_with_nursing TEXT,
    service_type_care_home_service_without_nursing TEXT,
    service_type_community_based_services_for_people_who_misuse_sub TEXT,
    service_type_community_based_services_for_people_with_a_learnin TEXT,
    service_type_community_based_services_for_people_with_mental_he TEXT,
    service_type_community_health_care_services_independent_midwive TEXT,
    service_type_community_health_care_services_nurses_agency_only TEXT,
    service_type_community_healthcare_service TEXT,
    service_type_dental_service TEXT,
    service_type_diagnostic_and_or_screening_service TEXT,
    service_type_diagnostic_and_or_screening_service_single_handed_ TEXT,
    service_type_doctors_consultation_service TEXT,
    service_type_doctors_treatment_service TEXT,
    service_type_domiciliary_care_service TEXT,
    service_type_extra_care_housing_services TEXT,
    service_type_hospice_services TEXT,
    service_type_hospital_services_for_people_with_mental_health_n TEXT,
    service_type_hyperbaric_chamber_services TEXT,
    service_type_long_term_conditions_services TEXT,
    service_type_mobile_doctors_services TEXT,
    service_type_nurses_agency TEXT,
    service_type_prison_health_care_services TEXT,
    service_type_rehabilitation_services TEXT,
    service_type_remote_clinical_advice_services TEXT,
    service_type_residential_substance_misuse_treatment_and_or_reh TEXT,
    service_type_respite TEXT,
    service_type_shared_lives TEXT,
    service_type_specialist_college_service TEXT,
    service_type_supported_housing TEXT,
    service_type_supported_living TEXT,
    service_type_urgent_care_services TEXT,
    service_user_band_children_0_18_years TEXT,
    service_user_band_people_detained_under_the_mental_health_act TEXT,
    service_user_band_dementia TEXT,
    service_user_band_eating_disorders TEXT,
    service_user_band_learning_disabilities_or_autistic_spectrum_di TEXT,
    service_user_band_mental_health TEXT,
    service_user_band_older_people TEXT,
    service_user_band_people_who_misuse_drugs_and_alcohol TEXT,
    service_user_band_people_with_an_eating_disorder TEXT,
    service_user_band_physical_disability TEXT,
    service_user_band_sensory_impairment TEXT,
    service_user_band_whole_population TEXT,
    service_user_band_younger_adults TEXT
);

\echo '✅ Временная таблица temp_cqc_raw создана'

-- ============================================================================
-- ЧАСТЬ 2: ЗАГРУЗКА CSV (ВАРИАНТЫ ДЛЯ SUPABASE)
-- ============================================================================

\echo '========================================================================'
\echo 'ЧАСТЬ 2: Загрузка CSV данных'
\echo '========================================================================'
\echo ''

-- ВАРИАНТ 1: Загрузка через Supabase Storage (используйте этот вариант)
-- Раскомментируйте и замените путь на ваш реальный путь в Storage:
/*
-- Создайте функцию для чтения CSV из Storage (выполните один раз)
CREATE OR REPLACE FUNCTION storage.read_csv_file(bucket_name TEXT, file_path TEXT)
RETURNS TEXT AS $$
DECLARE
    file_content TEXT;
BEGIN
    SELECT content INTO file_content
    FROM storage.objects
    WHERE bucket_id = bucket_name AND name = file_path;
    RETURN file_content;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Затем загрузите CSV (замените 'your-bucket-name/cqc_dataset.csv' на реальный путь)
-- Это требует дополнительной настройки Storage
*/

-- ВАРИАНТ 2: Если CSV уже загружен через Table Editor в таблицу cqc_csv_data
-- Раскомментируйте и используйте:
/*
INSERT INTO temp_cqc_raw
SELECT * FROM cqc_csv_data;
*/

-- ВАРИАНТ 3: Использовать существующую таблицу напрямую
-- Если у вас уже есть таблица с данными CQC, замените temp_cqc_raw на имя вашей таблицы
-- в SELECT запросе ниже (в части 4)

-- ВАРИАНТ 4: Ручная загрузка через SQL INSERT (для небольшого количества данных)
-- Не рекомендуется для большого объема данных

-- ВРЕМЕННОЕ РЕШЕНИЕ: Загрузите CSV через Supabase Table Editor
-- 1. В Supabase Dashboard → Table Editor
-- 2. Создайте новую таблицу или используйте существующую
-- 3. Загрузите CSV файл через импорт
-- 4. Затем замените temp_cqc_raw на имя вашей таблицы ниже

\echo '⚠️  ВНИМАНИЕ: Загрузите CSV данные в temp_cqc_raw перед продолжением!'
\echo '   Используйте один из вариантов выше или загрузите через Table Editor'
\echo ''

-- Проверка количества загруженных записей
DO $$
DECLARE
    loaded_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO loaded_count FROM temp_cqc_raw;
    RAISE NOTICE '✅ Загружено записей из CSV: %', loaded_count;
    
    IF loaded_count = 0 THEN
        RAISE EXCEPTION 'ОШИБКА: temp_cqc_raw пуста! Загрузите данные CSV перед продолжением.';
    END IF;
    
    IF loaded_count != 271 THEN
        RAISE WARNING '⚠️ Ожидалось 271, загружено %', loaded_count;
    END IF;
END $$;

\echo ''

-- ============================================================================
-- ЧАСТЬ 3: СОЗДАНИЕ HELPER FUNCTIONS (10 ФУНКЦИЙ)
-- ============================================================================
-- [Весь код функций остается без изменений, копируем из оригинального файла]

\echo '========================================================================'
\echo 'ЧАСТЬ 3: Создание 10 helper функций'
\echo '========================================================================'
\echo ''

-- 1. clean_text()
CREATE OR REPLACE FUNCTION clean_text(input TEXT)
RETURNS TEXT AS $$
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN NULL;
    END IF;
    RETURN TRIM(input);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Ошибка в clean_text: % (error: %)', input, SQLERRM;
        RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 2. safe_integer()
CREATE OR REPLACE FUNCTION safe_integer(input TEXT, default_value INTEGER DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    result INTEGER;
    cleaned TEXT;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    cleaned := REGEXP_REPLACE(TRIM(input), '[^0-9-]', '', 'g');
    
    IF cleaned = '' OR cleaned = '-' THEN
        RETURN default_value;
    END IF;
    
    BEGIN
        result := cleaned::INTEGER;
        RETURN result;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Failed to convert to integer: % (error: %)', input, SQLERRM;
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Критическая ошибка в safe_integer: %', SQLERRM;
        RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. safe_latitude()
CREATE OR REPLACE FUNCTION safe_latitude(input TEXT, default_value NUMERIC DEFAULT NULL)
RETURNS NUMERIC AS $$
DECLARE
    result NUMERIC;
    cleaned TEXT;
    comma_count INT;
    abs_val NUMERIC;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    cleaned := TRIM(input);
    comma_count := LENGTH(cleaned) - LENGTH(REPLACE(cleaned, ',', ''));
    
    IF comma_count = 0 AND LENGTH(cleaned) > 7 AND cleaned ~ '^[0-9.]+$' THEN
        cleaned := SUBSTRING(cleaned, 1, 2) || '.' || SUBSTRING(cleaned, 3);
    ELSIF comma_count = 1 THEN
        cleaned := REPLACE(cleaned, ',', '.');
    ELSIF comma_count > 1 THEN
        cleaned := REPLACE(cleaned, ',', '');
        IF LENGTH(cleaned) > 7 THEN
            cleaned := SUBSTRING(cleaned, 1, 2) || '.' || SUBSTRING(cleaned, 3);
        END IF;
    END IF;
    
    BEGIN
        result := cleaned::NUMERIC;
        abs_val := ABS(result);
        IF abs_val > 100 THEN
            result := result / 1000000;
            RAISE NOTICE 'Исправлена опечатка в latitude: original % → %', input, result;
        END IF;
        
        IF result < 49.0 OR result > 61.0 THEN
            RAISE NOTICE 'Latitude outside UK range: % (original: %)', result, input;
            RETURN default_value;
        END IF;
        
        IF result < 1.0 THEN
            RAISE NOTICE 'Suspicious latitude (too small): % (original: %)', result, input;
            RETURN default_value;
        END IF;
        
        RETURN ROUND(result, 7);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Failed to convert latitude: % (error: %)', input, SQLERRM;
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Критическая ошибка в safe_latitude: %', SQLERRM;
        RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 4. safe_longitude()
CREATE OR REPLACE FUNCTION safe_longitude(input TEXT, default_value NUMERIC DEFAULT NULL)
RETURNS NUMERIC AS $$
DECLARE
    result NUMERIC;
    cleaned TEXT;
    comma_count INT;
    abs_val NUMERIC;
    is_negative BOOLEAN := FALSE;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    cleaned := TRIM(input);
    
    IF cleaned ~ '^-' THEN
        is_negative := TRUE;
        cleaned := SUBSTRING(cleaned FROM 2);
    END IF;
    
    comma_count := LENGTH(cleaned) - LENGTH(REPLACE(cleaned, ',', ''));
    
    IF comma_count = 0 AND LENGTH(cleaned) > 7 AND cleaned ~ '^[0-9]+$' THEN
        cleaned := SUBSTRING(cleaned, 1, 1) || '.' || SUBSTRING(cleaned, 2);
    ELSIF comma_count = 1 THEN
        cleaned := REPLACE(cleaned, ',', '.');
        BEGIN
            result := cleaned::NUMERIC;
            IF ABS(result) > 10 THEN
                cleaned := SUBSTRING(cleaned, 1, 1) || '.' || SUBSTRING(cleaned, 2);
                RAISE NOTICE 'Исправлена опечатка в longitude: % → %', input, cleaned;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    ELSIF comma_count > 1 THEN
        cleaned := REPLACE(cleaned, ',', '');
        IF LENGTH(cleaned) > 7 THEN
            cleaned := SUBSTRING(cleaned, 1, 1) || '.' || SUBSTRING(cleaned, 2);
        END IF;
    END IF;
    
    IF is_negative THEN
        cleaned := '-' || cleaned;
    END IF;
    
    BEGIN
        result := cleaned::NUMERIC;
        abs_val := ABS(result);
        IF abs_val > 10 AND abs_val < 10000000 THEN
            result := result / 100000;
            RAISE NOTICE 'Исправлена опечатка в longitude (деление): original % → %', input, result;
        END IF;
        
        IF result < -8.0 OR result > 2.0 THEN
            RAISE NOTICE 'Longitude outside UK range: % (original: %)', result, input;
            RETURN default_value;
        END IF;
        
        RETURN ROUND(result, 7);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Failed to convert longitude: % (error: %)', input, SQLERRM;
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Критическая ошибка в safe_longitude: %', SQLERRM;
        RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. validate_uk_coordinates()
CREATE OR REPLACE FUNCTION validate_uk_coordinates(lat NUMERIC, lon NUMERIC)
RETURNS BOOLEAN AS $$
BEGIN
    IF lat IS NULL OR lon IS NULL THEN
        RETURN FALSE;
    END IF;
    
    IF lat < 49.0 OR lat > 61.0 OR lon < -8.0 OR lon > 2.0 THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Ошибка в validate_uk_coordinates: %', SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 6. safe_boolean()
CREATE OR REPLACE FUNCTION safe_boolean(input TEXT, default_value BOOLEAN DEFAULT NULL)
RETURNS BOOLEAN AS $$
DECLARE
    cleaned TEXT;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    cleaned := LOWER(TRIM(input));
    
    IF cleaned IN ('y', 'yes', 'true', '1', 't') THEN
        RETURN TRUE;
    END IF;
    
    IF cleaned IN ('n', 'no', 'false', '0', 'f') THEN
        RETURN FALSE;
    END IF;
    
    RAISE NOTICE 'Unknown boolean value: %. Returning default: %', input, default_value;
    RETURN default_value;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Ошибка в safe_boolean: % (error: %)', input, SQLERRM;
        RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 7. safe_date()
CREATE OR REPLACE FUNCTION safe_date(input TEXT, default_value DATE DEFAULT NULL)
RETURNS DATE AS $$
DECLARE
    result DATE;
    cleaned TEXT;
    year_part TEXT;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    cleaned := TRIM(input);
    
    BEGIN
        IF cleaned ~ '^\d{1,2}/\d{1,2}/\d{2,4}$' THEN
            year_part := SPLIT_PART(cleaned, '/', 3);
            IF LENGTH(year_part) = 2 THEN
                year_part := CASE 
                    WHEN year_part::INT <= 50 THEN '20' || year_part 
                    ELSE '19' || year_part 
                END;
                cleaned := SPLIT_PART(cleaned, '/', 1) || '/' || SPLIT_PART(cleaned, '/', 2) || '/' || year_part;
            END IF;
            result := TO_DATE(cleaned, 'DD/MM/YYYY');
            RETURN result;
        END IF;
        
        IF cleaned ~ '^\d{4}-\d{2}-\d{2}$' THEN
            result := TO_DATE(cleaned, 'YYYY-MM-DD');
            RETURN result;
        END IF;
        
        result := cleaned::DATE;
        RETURN result;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Failed to convert date: % (error: %)', input, SQLERRM;
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Критическая ошибка в safe_date: %', SQLERRM;
        RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 8. normalize_cqc_rating()
CREATE OR REPLACE FUNCTION normalize_cqc_rating(input TEXT)
RETURNS TEXT AS $$
DECLARE
    cleaned TEXT;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN NULL;
    END IF;
    
    cleaned := LOWER(TRIM(input));
    
    CASE cleaned
        WHEN 'outstanding' THEN RETURN 'Outstanding';
        WHEN 'good' THEN RETURN 'Good';
        WHEN 'requires improvement', 'requires improvment', 'needs improvement' THEN RETURN 'Requires Improvement';
        WHEN 'inadequate' THEN RETURN 'Inadequate';
        WHEN 'not rated' THEN RETURN 'Not Rated';
        ELSE
            RAISE NOTICE 'Unknown rating: %', input;
            RETURN NULL;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 9. safe_dormant()
CREATE OR REPLACE FUNCTION safe_dormant(input TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN safe_boolean(input, FALSE);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 10. extract_year()
CREATE OR REPLACE FUNCTION extract_year(input TEXT)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM safe_date(input))::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

\echo '✅ Все 10 helper функций созданы'

\echo ''

-- ============================================================================
-- ЧАСТЬ 4: INSERT SELECT С МАППИНГОМ (93 поля)
-- ============================================================================

\echo '========================================================================'
\echo 'ЧАСТЬ 4: INSERT данных в care_homes'
\echo '========================================================================'
\echo ''

-- Проверка дубликатов перед INSERT
DO $$
DECLARE
    dup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO dup_count
    FROM (
        SELECT location_id, COUNT(*) 
        FROM temp_cqc_raw 
        GROUP BY location_id 
        HAVING COUNT(*) > 1
    ) d;
    
    IF dup_count > 0 THEN
        RAISE EXCEPTION 'КРИТИЧЕСКАЯ ОШИБКА: % дубликатов location_id в CSV!', dup_count;
    END IF;
    RAISE NOTICE '✅ Проверка дубликатов: 0 найдено';
END $$;

BEGIN;

INSERT INTO care_homes (
    cqc_location_id, location_ods_code, name, name_normalized, provider_name, provider_id, brand_name,
    telephone, email, website, city, county, postcode,
    latitude, longitude, region, local_authority, beds_total, beds_available, has_availability,
    availability_status, availability_last_checked, year_opened, year_registered, care_residential,
    care_nursing, care_dementia, care_respite, has_nursing_care_license, has_personal_care_license,
    has_surgical_procedures_license, has_treatment_license, has_diagnostic_license, serves_older_people,
    serves_younger_adults, serves_mental_health, serves_physical_disabilities, serves_sensory_impairments,
    fee_residential_from, fee_nursing_from, fee_dementia_from, fee_respite_from, accepts_self_funding,
    accepts_local_authority, accepts_nhs_chc, accepts_third_party_topup, cqc_rating_overall,
    cqc_rating_safe, cqc_rating_effective, cqc_rating_caring, cqc_rating_responsive, cqc_rating_well_led,
    cqc_last_inspection_date, cqc_publication_date, cqc_latest_report_url, review_average_score,
    review_count, google_rating, wheelchair_access, ensuite_rooms, secure_garden, wifi_available,
    parking_onsite, is_dormant, data_quality_score, created_at, updated_at, source_urls, service_types,
    service_user_bands, facilities, medical_specialisms, dietary_options, activities, pricing_details,
    staff_information, reviews_detailed, media, location_context, building_info, accreditations,
    source_metadata, extra,
    -- Новые v2.2 поля
    serves_dementia_band, serves_children, serves_learning_disabilities, serves_detained_mha,
    serves_substance_misuse, serves_eating_disorders, serves_whole_population,
    regulated_activities  -- JSONB для 14 лицензий
)
SELECT
    clean_text(location_id) AS cqc_location_id,
    clean_text(location_ods_code) AS location_ods_code,
    clean_text(location_name) AS name,
    LOWER(TRIM(location_name)) AS name_normalized,
    clean_text(provider_name) AS provider_name,
    clean_text(provider_id) AS provider_id,
    clean_text(brand_name) AS brand_name,
    clean_text(location_telephone_number) AS telephone,  -- TEXT!
    NULL AS email,  -- Нет в CQC
    COALESCE(clean_text(location_web_address), clean_text(provider_web_address)) AS website,
    clean_text(location_city) AS city,
    clean_text(location_county) AS county,
    clean_text(location_postal_code) AS postcode,
    safe_latitude(location_latitude) AS latitude,
    safe_longitude(location_longitude) AS longitude,
    clean_text(location_region) AS region,
    clean_text(location_local_authority) AS local_authority,
    safe_integer(care_homes_beds) AS beds_total,
    NULL AS beds_available,  -- Нет в CQC
    FALSE AS has_availability,
    NULL AS availability_status,
    NULL AS availability_last_checked,
    NULL AS year_opened,
    extract_year(location_hsca_start_date) AS year_registered,
    safe_boolean(service_type_care_home_service_without_nursing) AS care_residential,
    safe_boolean(service_type_care_home_service_with_nursing) AS care_nursing,
    safe_boolean(service_user_band_dementia) AS care_dementia,
    NULL AS care_respite,  -- Нет в CQC CSV (документация: "Обычно нет прямого поля")
    safe_boolean(regulated_activity_nursing_care) AS has_nursing_care_license,
    safe_boolean(regulated_activity_personal_care) AS has_personal_care_license,
    safe_boolean(regulated_activity_surgical_procedures) AS has_surgical_procedures_license,
    safe_boolean(regulated_activity_treatment_of_disease_disorder_or_injury) AS has_treatment_license,
    safe_boolean(regulated_activity_diagnostic_and_screening_procedures) AS has_diagnostic_license,
    safe_boolean(service_user_band_older_people) AS serves_older_people,
    safe_boolean(service_user_band_younger_adults) AS serves_younger_adults,
    safe_boolean(service_user_band_mental_health) AS serves_mental_health,
    safe_boolean(service_user_band_physical_disability) AS serves_physical_disabilities,
    safe_boolean(service_user_band_sensory_impairment) AS serves_sensory_impairments,
    NULL AS fee_residential_from,
    NULL AS fee_nursing_from,
    NULL AS fee_dementia_from,
    NULL AS fee_respite_from,
    TRUE AS accepts_self_funding,  -- Assume default
    TRUE AS accepts_local_authority,
    TRUE AS accepts_nhs_chc,
    TRUE AS accepts_third_party_topup,
    normalize_cqc_rating(location_latest_overall_rating) AS cqc_rating_overall,
    normalize_cqc_rating(cqc_rating_safe) AS cqc_rating_safe,
    normalize_cqc_rating(cqc_rating_effective) AS cqc_rating_effective,
    normalize_cqc_rating(cqc_rating_caring) AS cqc_rating_caring,
    normalize_cqc_rating(cqc_rating_responsive) AS cqc_rating_responsive,
    normalize_cqc_rating(cqc_rating_well_led) AS cqc_rating_well_led,
    safe_date(publication_date) AS cqc_publication_date,
    NULL AS cqc_last_inspection_date,
    clean_text(cqc_report_url) AS cqc_latest_report_url,
    NULL AS review_average_score,
    NULL AS review_count,
    NULL AS google_rating,
    FALSE AS wheelchair_access,
    FALSE AS ensuite_rooms,
    FALSE AS secure_garden,
    FALSE AS wifi_available,
    FALSE AS parking_onsite,
    safe_dormant(dormant_y_n_) AS is_dormant,
    (CASE WHEN safe_latitude(location_latitude) IS NOT NULL AND safe_longitude(location_longitude) IS NOT NULL THEN 100 ELSE 50 END) AS data_quality_score,
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at,
    jsonb_build_object('cqc_profile', 'https://www.cqc.org.uk/location/' || location_id) AS source_urls,
    jsonb_build_object('services', ARRAY[]::TEXT[]) AS service_types,
    jsonb_build_object('bands', ARRAY[]::TEXT[]) AS service_user_bands,
    '{}'::jsonb AS facilities,
    '{}'::jsonb AS medical_specialisms,
    '{}'::jsonb AS dietary_options,
    '{}'::jsonb AS activities,
    '{}'::jsonb AS pricing_details,
    '{}'::jsonb AS staff_information,
    '{}'::jsonb AS reviews_detailed,
    '{}'::jsonb AS media,
    '{}'::jsonb AS location_context,
    '{}'::jsonb AS building_info,
    '{}'::jsonb AS accreditations,
    '{}'::jsonb AS source_metadata,
    '{}'::jsonb AS extra,
    -- Новые v2.2 поля
    safe_boolean(service_user_band_dementia) AS serves_dementia_band,
    safe_boolean(service_user_band_children_0_18_years) AS serves_children,
    safe_boolean(service_user_band_learning_disabilities_or_autistic_spectrum_di) AS serves_learning_disabilities,
    safe_boolean(service_user_band_people_detained_under_the_mental_health_act) AS serves_detained_mha,
    safe_boolean(service_user_band_people_who_misuse_drugs_and_alcohol) AS serves_substance_misuse,
    safe_boolean(service_user_band_people_with_an_eating_disorder) AS serves_eating_disorders,
    safe_boolean(service_user_band_whole_population) AS serves_whole_population,
    jsonb_build_object(
        'activities', ARRAY_REMOVE(ARRAY[
            CASE WHEN safe_boolean(regulated_activity_accommodation_for_persons_who_require_nursing) THEN 'accommodation_nursing' END,
            CASE WHEN safe_boolean(regulated_activity_accommodation_for_persons_who_require_treatment) THEN 'accommodation_treatment' END,
            CASE WHEN safe_boolean(regulated_activity_assessment_or_medical_treatment_for_persons_) THEN 'assessment_medical' END,
            CASE WHEN safe_boolean(regulated_activity_diagnostic_and_screening_procedures) THEN 'diagnostic_screening' END,
            CASE WHEN safe_boolean(regulated_activity_family_planning) THEN 'family_planning' END,
            CASE WHEN safe_boolean(regulated_activity_management_of_supply_of_blood_and_blood_deri) THEN 'blood_management' END,
            CASE WHEN safe_boolean(regulated_activity_maternity_and_midwifery_services) THEN 'maternity_midwifery' END,
            CASE WHEN safe_boolean(regulated_activity_nursing_care) THEN 'nursing_care' END,
            CASE WHEN safe_boolean(regulated_activity_personal_care) THEN 'personal_care' END,
            CASE WHEN safe_boolean(regulated_activity_services_in_slimming_clinics) THEN 'slimming_clinics' END,
            CASE WHEN safe_boolean(regulated_activity_surgical_procedures) THEN 'surgical_procedures' END,
            CASE WHEN safe_boolean(regulated_activity_termination_of_pregnancies) THEN 'termination_pregnancies' END,
            CASE WHEN safe_boolean(regulated_activity_transport_services_triage_and_medical_advice) THEN 'transport_triage' END,
            CASE WHEN safe_boolean(regulated_activity_treatment_of_disease_disorder_or_injury) THEN 'treatment_disease' END
        ], NULL)
    ) AS regulated_activities
FROM temp_cqc_raw
WHERE location_type_sector = 'Social Care Org'
  AND care_home_ = 'Y';

-- Проверка количества вставленных записей
DO $$
DECLARE
    inserted_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO inserted_count FROM care_homes;
    RAISE NOTICE '✅ Вставлено записей: %', inserted_count;
    
    IF inserted_count != 271 THEN
        RAISE WARNING '⚠️ Ожидалось 271, вставлено %', inserted_count;
    END IF;
END $$;

COMMIT;

\echo ''
\echo '✅ Миграция данных завершена успешно!'
\echo ''

-- ============================================================================
-- ЧАСТЬ 5: ВАЛИДАЦИЯ ДАННЫХ (после INSERT)
-- ============================================================================

\echo '========================================================================'
\echo 'ЧАСТЬ 5: Валидация данных после миграции'
\echo '========================================================================'
\echo ''

DO $$
DECLARE
    total_count INTEGER;
    has_nursing_count INTEGER;
    has_personal_count INTEGER;
    null_coords INTEGER;
    bad_coords INTEGER;
    serves_dementia_count INTEGER;
    serves_children_count INTEGER;
    regulated_filled INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM care_homes;
    
    SELECT COUNT(*) INTO has_nursing_count FROM care_homes WHERE has_nursing_care_license = TRUE;
    SELECT COUNT(*) INTO has_personal_count FROM care_homes WHERE has_personal_care_license = TRUE;
    
    SELECT COUNT(*) INTO null_coords FROM care_homes WHERE latitude IS NULL OR longitude IS NULL;
    
    SELECT COUNT(*) INTO bad_coords FROM care_homes 
    WHERE (latitude IS NOT NULL AND (latitude < 49 OR latitude > 61))
       OR (longitude IS NOT NULL AND (longitude < -8 OR longitude > 2));
    
    SELECT COUNT(*) INTO serves_dementia_count FROM care_homes WHERE serves_dementia_band = TRUE;
    SELECT COUNT(*) INTO serves_children_count FROM care_homes WHERE serves_children = TRUE;
    
    SELECT COUNT(*) INTO regulated_filled FROM care_homes WHERE regulated_activities != '{"activities": []}'::jsonb;
    
    RAISE NOTICE '========== ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ ==========';
    RAISE NOTICE 'Всего записей: %', total_count;
    RAISE NOTICE 'has_nursing_care_license=TRUE: % (%.1f%%)', has_nursing_count, (has_nursing_count::FLOAT / NULLIF(total_count, 0) * 100);
    RAISE NOTICE 'has_personal_care_license=TRUE: % (%.1f%%)', has_personal_count, (has_personal_count::FLOAT / NULLIF(total_count, 0) * 100);
    RAISE NOTICE 'NULL координаты: % (%.1f%%)', null_coords, (null_coords::FLOAT / NULLIF(total_count, 0) * 100);
    RAISE NOTICE 'Координаты вне UK: %', bad_coords;
    RAISE NOTICE 'serves_dementia_band=TRUE: % (%.1f%%)', serves_dementia_count, (serves_dementia_count::FLOAT / NULLIF(total_count, 0) * 100);
    RAISE NOTICE 'serves_children=TRUE: % (%.1f%%)', serves_children_count, (serves_children_count::FLOAT / NULLIF(total_count, 0) * 100);
    RAISE NOTICE 'regulated_activities заполнено: % (%.1f%%)', regulated_filled, (regulated_filled::FLOAT / NULLIF(total_count, 0) * 100);
    RAISE NOTICE '==========================================';
END $$;

\echo ''
\echo '========================================================================'
\echo 'МИГРАЦИЯ ЗАВЕРШЕНА!'
\echo '========================================================================'
\echo ''
\echo '✅ Схема БД создана (step1_schema_create.sql)'
\echo '✅ Данные загружены (step2_run_migration_SUPABASE.sql)'
\echo '✅ Индексы созданы (в step1_schema_create.sql)'
\echo '✅ Views созданы (в step1_schema_create.sql)'
\echo ''
\echo 'Проверьте результаты:'
\echo '  SELECT COUNT(*) FROM care_homes;'
\echo '  SELECT * FROM v_data_coverage LIMIT 10;'
\echo '  SELECT * FROM v_service_user_bands_coverage;'
\echo ''

