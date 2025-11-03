-- ============================================================================
-- УЛУЧШЕННЫЙ МИГРАЦИОННЫЙ СКРИПТ CQC → CARE HOMES v2.2 (IMPROVED)
-- ИСТОЧНИК: cqc_dataset_test
-- ЦЕЛЬ: care_homes
-- ВЕРСИЯ: v2.4 - ИСПРАВЛЕННАЯ С КРИТИЧЕСКИМИ ИЗМЕНЕНИЯМИ
-- ============================================================================

-- ИСПРАВЛЕНИЯ:
-- 1. Улучшена функция safe_boolean для явной обработки "TRUE"/"FALSE"
-- 2. Исправлена обработка координат с запятыми
-- 3. Добавлен маппинг service_types в JSONB
-- 4. Добавлен маппинг service_user_bands в JSONB
-- 5. Добавлены дополнительные поля в JSONB структуры
-- 6. КРИТИЧЕСКОЕ: Исправлена логика has_nursing_care_license (используется service_type вместо regulated_activity)
-- 7. КРИТИЧЕСКОЕ: year_opened остаётся NULL (location_hsca_start_date - это дата регистрации, не открытия)
-- ============================================================================

-- ============================================================================
-- ЧАСТЬ 0: ДОБАВЛЕНИЕ НОВЫХ ПОЛЕЙ В ТАБЛИЦУ (если не существуют)
-- ============================================================================

DO $$
BEGIN
  -- Добавление provider_telephone_number (если не существует)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'care_homes' 
      AND column_name = 'provider_telephone_number'
      AND table_schema = 'public'
  ) THEN
    ALTER TABLE care_homes ADD COLUMN provider_telephone_number TEXT;
    RAISE NOTICE '✅ Добавлено поле provider_telephone_number';
  ELSE
    RAISE NOTICE 'ℹ️  Поле provider_telephone_number уже существует';
  END IF;
  
  -- Добавление provider_hsca_start_date (если не существует)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'care_homes' 
      AND column_name = 'provider_hsca_start_date'
      AND table_schema = 'public'
  ) THEN
    ALTER TABLE care_homes ADD COLUMN provider_hsca_start_date DATE;
    RAISE NOTICE '✅ Добавлено поле provider_hsca_start_date';
  ELSE
    RAISE NOTICE 'ℹ️  Поле provider_hsca_start_date уже существует';
  END IF;
END $$;

-- ============================================================================
-- ЧАСТЬ 0.5: ОЧИСТКА HELPER FUNCTIONS (если нужно)
-- ============================================================================

-- Очистка старых версий функций (если есть конфликты)
DO $$
BEGIN
  RAISE NOTICE 'Проверка и очистка старых helper функций...';
END $$;

-- Удаление старых версий функций перед пересозданием
DROP FUNCTION IF EXISTS clean_text(TEXT);
DROP FUNCTION IF EXISTS safe_integer(TEXT, INTEGER);
DROP FUNCTION IF EXISTS safe_latitude(TEXT, NUMERIC);
DROP FUNCTION IF EXISTS safe_longitude(TEXT, NUMERIC);
DROP FUNCTION IF EXISTS safe_boolean(TEXT, BOOLEAN);
DROP FUNCTION IF EXISTS safe_date(TEXT, DATE);
DROP FUNCTION IF EXISTS safe_dormant(TEXT);
DROP FUNCTION IF EXISTS extract_year(TEXT);
DROP FUNCTION IF EXISTS normalize_cqc_rating(TEXT);
DROP FUNCTION IF EXISTS validate_uk_coordinates(NUMERIC, NUMERIC);
-- Удаление неиспользуемых функций (если были созданы ранее)
DROP FUNCTION IF EXISTS build_service_types_array();
DROP FUNCTION IF EXISTS build_service_user_bands_array();

-- ============================================================================
-- ЧАСТЬ 1: СОЗДАНИЕ УЛУЧШЕННЫХ HELPER FUNCTIONS
-- ============================================================================

-- 1. clean_text() - без изменений
CREATE OR REPLACE FUNCTION clean_text(input TEXT)
RETURNS TEXT AS $$
BEGIN
  IF input IS NULL OR TRIM(input) = '' THEN
    RETURN NULL;
  END IF;
  RETURN TRIM(input);
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 2. safe_integer() - без изменений
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
      RETURN default_value;
  END;
EXCEPTION
  WHEN OTHERS THEN
    RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. safe_latitude() - УЛУЧШЕНО для координат с запятыми
CREATE OR REPLACE FUNCTION safe_latitude(input TEXT, default_value NUMERIC DEFAULT NULL)
RETURNS NUMERIC AS $$
DECLARE
  result NUMERIC;
  cleaned TEXT;
  comma_count INT;
  numeric_val NUMERIC;
BEGIN
  IF input IS NULL OR TRIM(input) = '' THEN
    RETURN default_value;
  END IF;
  
  cleaned := TRIM(input);
  comma_count := LENGTH(cleaned) - LENGTH(REPLACE(cleaned, ',', ''));
  
  -- Если есть запятые (разделители тысяч)
  IF comma_count > 1 THEN
    cleaned := REPLACE(cleaned, ',', '');
    -- Попробуем разные варианты преобразования
    BEGIN
      numeric_val := cleaned::NUMERIC;
      -- Если значение очень большое (> 1000000), это может быть формат без запятой в десятичной части
      IF numeric_val > 1000000 THEN
        -- Попробуем разделить на 100000 (формат: 5252257 / 100000 = 52.52257)
        result := numeric_val / 100000.0;
        IF result >= 49.0 AND result <= 61.0 THEN
          RETURN ROUND(result, 7);
        END IF;
        -- Или на 1000000
        result := numeric_val / 1000000.0;
        IF result >= 49.0 AND result <= 61.0 THEN
          RETURN ROUND(result, 7);
        END IF;
      ELSE
        -- Если значение в разумном диапазоне, используем как есть
        IF numeric_val >= 49.0 AND numeric_val <= 61.0 THEN
          RETURN ROUND(numeric_val, 7);
        END IF;
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
  ELSIF comma_count = 1 THEN
    -- Одна запятая - возможно десятичный разделитель
    cleaned := REPLACE(cleaned, ',', '.');
    BEGIN
      result := cleaned::NUMERIC;
      IF result >= 49.0 AND result <= 61.0 THEN
        RETURN ROUND(result, 7);
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
  ELSIF comma_count = 0 THEN
    -- Нет запятых - пробуем как есть
    BEGIN
      result := cleaned::NUMERIC;
      -- Если слишком большое, делим
      IF result > 100 THEN
        result := result / 100000.0;
      END IF;
      IF result >= 49.0 AND result <= 61.0 THEN
        RETURN ROUND(result, 7);
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
  END IF;
  
  RETURN default_value;
EXCEPTION
  WHEN OTHERS THEN
    RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 4. safe_longitude() - УЛУЧШЕНО аналогично
CREATE OR REPLACE FUNCTION safe_longitude(input TEXT, default_value NUMERIC DEFAULT NULL)
RETURNS NUMERIC AS $$
DECLARE
  result NUMERIC;
  cleaned TEXT;
  comma_count INT;
  numeric_val NUMERIC;
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
  
  IF comma_count > 1 THEN
    cleaned := REPLACE(cleaned, ',', '');
    BEGIN
      numeric_val := cleaned::NUMERIC;
      IF ABS(numeric_val) > 1000000 THEN
        result := numeric_val / 100000.0;
        IF ABS(result) >= 0.0 AND ABS(result) <= 10.0 THEN
          IF is_negative THEN result := -result; END IF;
          RETURN ROUND(result, 7);
        END IF;
        result := numeric_val / 1000000.0;
        IF ABS(result) >= 0.0 AND ABS(result) <= 10.0 THEN
          IF is_negative THEN result := -result; END IF;
          RETURN ROUND(result, 7);
        END IF;
      ELSE
        IF ABS(numeric_val) >= 0.0 AND ABS(numeric_val) <= 10.0 THEN
          IF is_negative THEN result := -numeric_val; ELSE result := numeric_val; END IF;
          RETURN ROUND(result, 7);
        END IF;
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
  ELSIF comma_count = 1 THEN
    cleaned := REPLACE(cleaned, ',', '.');
    BEGIN
      result := cleaned::NUMERIC;
      IF is_negative THEN result := -result; END IF;
      IF ABS(result) >= 0.0 AND ABS(result) <= 10.0 THEN
        RETURN ROUND(result, 7);
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
  ELSIF comma_count = 0 THEN
    BEGIN
      result := cleaned::NUMERIC;
      IF ABS(result) > 10 THEN
        result := result / 100000.0;
      END IF;
      IF is_negative THEN result := -result; END IF;
      IF ABS(result) >= 0.0 AND ABS(result) <= 10.0 THEN
        RETURN ROUND(result, 7);
      END IF;
    EXCEPTION
      WHEN OTHERS THEN
        NULL;
    END;
  END IF;
  
  RETURN default_value;
EXCEPTION
  WHEN OTHERS THEN
    RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. safe_boolean() - УЛУЧШЕНО для явной обработки "TRUE"/"FALSE"
CREATE OR REPLACE FUNCTION safe_boolean(input TEXT, default_value BOOLEAN DEFAULT NULL)
RETURNS BOOLEAN AS $$
DECLARE
  cleaned TEXT;
  upper_cleaned TEXT;
BEGIN
  IF input IS NULL OR TRIM(input) = '' THEN
    RETURN default_value;
  END IF;
  
  cleaned := LOWER(TRIM(input));
  upper_cleaned := UPPER(TRIM(input));
  
  -- Явная проверка на "TRUE" и "FALSE" (заглавными)
  IF upper_cleaned = 'TRUE' THEN
    RETURN TRUE;
  END IF;
  IF upper_cleaned = 'FALSE' THEN
    RETURN FALSE;
  END IF;
  
  -- Стандартная обработка
  IF cleaned IN ('y', 'yes', 'true', '1', 't') THEN
    RETURN TRUE;
  END IF;
  IF cleaned IN ('n', 'no', 'false', '0', 'f') THEN
    RETURN FALSE;
  END IF;
  
  RETURN default_value;
EXCEPTION
  WHEN OTHERS THEN
    RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 6. validate_uk_coordinates()
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
    RETURN FALSE;
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
      RETURN default_value;
  END;
EXCEPTION
  WHEN OTHERS THEN
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

DO $$
BEGIN
  RAISE NOTICE '✅ Все 10 helper функций созданы (с улучшениями)';
END $$;

-- ============================================================================
-- ЧАСТЬ 2: УЛУЧШЕННЫЙ INSERT SELECT С ПОЛНЫМ МАППИНГОМ
-- ============================================================================

-- Проверка перед INSERT
DO $$
DECLARE
  source_count INTEGER;
  existing_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO source_count FROM cqc_dataset_test
  WHERE location_type_sector = 'Social Care Org' AND care_home_ = 'Y';
  RAISE NOTICE 'Найдено записей для миграции: %', source_count;
  
  -- Проверка существующих данных
  SELECT COUNT(*) INTO existing_count FROM care_homes;
  IF existing_count > 0 THEN
    RAISE WARNING '⚠️  Таблица care_homes не пуста (% записей)! Выполняю TRUNCATE...', existing_count;
    TRUNCATE care_homes RESTART IDENTITY CASCADE;
    RAISE NOTICE '✅ Таблица care_homes очищена';
  ELSE
    RAISE NOTICE '✅ Таблица care_homes пуста, готово к заполнению';
  END IF;
END $$;

BEGIN;

INSERT INTO care_homes (
  cqc_location_id, location_ods_code, name, name_normalized, provider_name, provider_id, brand_name,
  telephone, provider_telephone_number, email, website, city, county, postcode,
  latitude, longitude, region, local_authority, beds_total, beds_available, has_availability,
  availability_status, availability_last_checked, year_opened, year_registered, provider_hsca_start_date, care_residential,
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
  serves_dementia_band, serves_children, serves_learning_disabilities, serves_detained_mha,
  serves_substance_misuse, serves_eating_disorders, serves_whole_population,
  regulated_activities
)
SELECT
  -- Основные поля
  clean_text(location_id) AS cqc_location_id,
  clean_text(location_ods_code) AS location_ods_code,
  clean_text(location_name) AS name,
  LOWER(TRIM(location_name)) AS name_normalized,
  clean_text(provider_name) AS provider_name,
  clean_text(provider_id) AS provider_id,
  clean_text(brand_name) AS brand_name,
  clean_text(location_telephone_number) AS telephone,
  clean_text(provider_telephone_number) AS provider_telephone_number,
  NULL AS email,
  COALESCE(clean_text(location_web_address), clean_text(provider_web_address)) AS website,
  clean_text(location_city) AS city,
  clean_text(location_county) AS county,
  clean_text(location_postal_code) AS postcode,
  safe_latitude(location_latitude) AS latitude,
  safe_longitude(location_longitude) AS longitude,
  clean_text(location_region) AS region,
  clean_text(location_local_authority) AS local_authority,
  safe_integer(care_homes_beds) AS beds_total,
  NULL AS beds_available,
  FALSE AS has_availability,
  NULL AS availability_status,
  NULL AS availability_last_checked,
  -- ВАЖНО: location_hsca_start_date - это дата РЕГИСТРАЦИИ в CQC,
  -- а НЕ год открытия дома. Многие дома перерегистрировались в 2010 году
  -- при переходе на новую систему HSCA 2008, но работали десятилетиями ранее.
  -- Поэтому year_opened остаётся NULL до получения реальных данных о годе основания.
  NULL AS year_opened,
  extract_year(location_hsca_start_date) AS year_registered,
  safe_date(provider_hsca_start_date) AS provider_hsca_start_date,
  safe_boolean(service_type_care_home_service_without_nursing) AS care_residential,
  safe_boolean(service_type_care_home_service_with_nursing) AS care_nursing,
  safe_boolean(service_user_band_dementia) AS care_dementia,
  NULL AS care_respite,
  -- ВАЖНО: regulated_activity_nursing_care НЕ используется в данных CQC для care homes.
  -- Вместо него используется service_type_care_home_service_with_nursing.
  -- 73 nursing homes имеют service_type=TRUE, но regulated_activity=FALSE для всех.
  -- Поэтому используем service_type как официальный маркер наличия лицензии на nursing care.
  safe_boolean(service_type_care_home_service_with_nursing) AS has_nursing_care_license,
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
  TRUE AS accepts_self_funding,
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
  
  -- УЛУЧШЕНО: source_urls с дополнительными URL
  jsonb_build_object(
    'cqc_profile', 'https://www.cqc.org.uk/location/' || location_id,
    'carehome_url', clean_text(carehome_url),
    'lottie_url', clean_text(lottie_url)
  ) AS source_urls,
  
  -- УЛУЧШЕНО: service_types заполняется из всех service_type_* полей
  jsonb_build_object(
    'services', ARRAY_REMOVE(ARRAY[
      CASE WHEN service_type_care_home_service_with_nursing = 'TRUE' THEN 'Care home service with nursing' END,
      CASE WHEN service_type_care_home_service_without_nursing = 'TRUE' THEN 'Care home service without nursing' END,
      CASE WHEN service_type_acute_services_with_overnight_beds = 'TRUE' THEN 'Acute services with overnight beds' END,
      CASE WHEN service_type_acute_services_without_overnight_beds_listed_acute = 'TRUE' THEN 'Acute services without overnight beds' END,
      CASE WHEN service_type_ambulance_service = 'TRUE' THEN 'Ambulance service' END,
      CASE WHEN service_type_blood_and_transplant_service = 'TRUE' THEN 'Blood and transplant service' END,
      CASE WHEN service_type_community_based_services_for_people_who_misuse_sub = 'TRUE' THEN 'Community based services for people who misuse substances' END,
      CASE WHEN service_type_community_based_services_for_people_with_a_learnin = 'TRUE' THEN 'Community based services for people with learning disabilities' END,
      CASE WHEN service_type_community_based_services_for_people_with_mental_he = 'TRUE' THEN 'Community based services for people with mental health needs' END,
      CASE WHEN service_type_community_health_care_services_independent_midwive = 'TRUE' THEN 'Community health care services - independent midwives' END,
      CASE WHEN service_type_community_health_care_services_nurses_agency_only = 'TRUE' THEN 'Community health care services - nurses agency only' END,
      CASE WHEN service_type_community_healthcare_service = 'TRUE' THEN 'Community healthcare service' END,
      CASE WHEN service_type_dental_service = 'TRUE' THEN 'Dental service' END,
      CASE WHEN service_type_diagnostic_and_or_screening_service = 'TRUE' THEN 'Diagnostic and/or screening service' END,
      CASE WHEN service_type_diagnostic_and_or_screening_service_single_handed_ = 'TRUE' THEN 'Diagnostic and/or screening service - single handed' END,
      CASE WHEN service_type_doctors_consultation_service = 'TRUE' THEN 'Doctors consultation service' END,
      CASE WHEN service_type_doctors_treatment_service = 'TRUE' THEN 'Doctors treatment service' END,
      CASE WHEN service_type_domiciliary_care_service = 'TRUE' THEN 'Domiciliary care service' END,
      CASE WHEN service_type_extra_care_housing_services = 'TRUE' THEN 'Extra care housing services' END,
      CASE WHEN service_type_hospice_services = 'TRUE' THEN 'Hospice services' END,
      CASE WHEN service_type_hospice_services_at_home = 'TRUE' THEN 'Hospice services at home' END,
      CASE WHEN service_type_hospital_services_for_people_with_mental_health_ne = 'TRUE' THEN 'Hospital services for people with mental health needs' END,
      CASE WHEN service_type_hyperbaric_chamber = 'TRUE' THEN 'Hyperbaric chamber' END,
      CASE WHEN service_type_long_term_conditions_services = 'TRUE' THEN 'Long term conditions services' END,
      CASE WHEN service_type_mobile_doctors_service = 'TRUE' THEN 'Mobile doctors service' END,
      CASE WHEN service_type_prison_healthcare_services = 'TRUE' THEN 'Prison healthcare services' END,
      CASE WHEN service_type_rehabilitation_services = 'TRUE' THEN 'Rehabilitation services' END,
      CASE WHEN service_type_remote_clinical_advice_service = 'TRUE' THEN 'Remote clinical advice service' END,
      CASE WHEN service_type_residential_substance_misuse_treatment_and_or_reha = 'TRUE' THEN 'Residential substance misuse treatment and/or rehabilitation' END,
      CASE WHEN service_type_shared_lives = 'TRUE' THEN 'Shared lives' END,
      CASE WHEN service_type_specialist_college_service = 'TRUE' THEN 'Specialist college service' END,
      CASE WHEN service_type_supported_living_service = 'TRUE' THEN 'Supported living service' END,
      CASE WHEN service_type_urgent_care_services = 'TRUE' THEN 'Urgent care services' END
    ], NULL)
  ) AS service_types,
  
  -- УЛУЧШЕНО: service_user_bands заполняется из всех service_user_band_* полей
  jsonb_build_object(
    'bands', ARRAY_REMOVE(ARRAY[
    CASE WHEN service_user_band_children_0_18_years = 'TRUE' THEN 'Children (0-18 years)' END,
    CASE WHEN service_user_band_dementia = 'TRUE' THEN 'Dementia' END,
    CASE WHEN service_user_band_learning_disabilities_or_autistic_spectrum_di = 'TRUE' THEN 'Learning disabilities or autistic spectrum disorder' END,
    CASE WHEN service_user_band_mental_health = 'TRUE' THEN 'Mental health' END,
    CASE WHEN service_user_band_older_people = 'TRUE' THEN 'Older people' END,
    CASE WHEN service_user_band_people_detained_under_the_mental_health_act = 'TRUE' THEN 'People detained under the Mental Health Act' END,
    CASE WHEN service_user_band_people_who_misuse_drugs_and_alcohol = 'TRUE' THEN 'People who misuse drugs and alcohol' END,
    CASE WHEN service_user_band_people_with_an_eating_disorder = 'TRUE' THEN 'People with an eating disorder' END,
    CASE WHEN service_user_band_physical_disability = 'TRUE' THEN 'Physical disability' END,
    CASE WHEN service_user_band_sensory_impairment = 'TRUE' THEN 'Sensory impairment' END,
    CASE WHEN service_user_band_whole_population = 'TRUE' THEN 'Whole population' END,
    CASE WHEN service_user_band_younger_adults = 'TRUE' THEN 'Younger adults' END
  ], NULL)
  ) AS service_user_bands,
  
  '{}'::jsonb AS facilities,
  '{}'::jsonb AS medical_specialisms,
  '{}'::jsonb AS dietary_options,
  '{}'::jsonb AS activities,
  '{}'::jsonb AS pricing_details,
  
  -- УЛУЧШЕНО: staff_information с дополнительными полями
  jsonb_build_object(
    'registered_manager', clean_text(registered_manager),
    'nominated_individual', clean_text(provider_nominated_individual_name),
    'main_partner', clean_text(provider_main_partner_name)
  ) AS staff_information,
  
  '{}'::jsonb AS reviews_detailed,
  '{}'::jsonb AS media,
  
  -- УЛУЧШЕНО: location_context с дополнительными данными
  jsonb_build_object(
    'parliamentary_constituency', clean_text(location_parliamentary_constituency),
    'paf_id', clean_text(location_paf_id),
    'uprn_id', clean_text(location_uprn_id),
    'ccg_code', clean_text(location_onspd_ccg_code),
    'ccg_name', clean_text(location_onspd_ccg),
    'commissioning_ccg_code', clean_text(location_commissioning_ccg_code),
    'commissioning_ccg_name', clean_text(location_commissioning_ccg),
    'nhs_region', clean_text(location_nhs_region)
  ) AS location_context,
  
  -- УЛУЧШЕНО: building_info с адресными данными
  jsonb_build_object(
    'street_address', clean_text(location_street_address),
    'address_line_2', clean_text(location_address_line_2),
    'provider_street_address', clean_text(provider_street_address),
    'provider_address_line_2', clean_text(provider_address_line_2),
    'provider_city', clean_text(provider_city),
    'provider_county', clean_text(provider_county),
    'provider_postcode', clean_text(provider_postal_code)
  ) AS building_info,
  
  '{}'::jsonb AS accreditations,
  
  -- УЛУЧШЕНО: source_metadata с дополнительными данными
  jsonb_build_object(
    'inspection_directorate', clean_text(location_inspection_directorate),
    'primary_inspection_category', clean_text(location_primary_inspection_category),
    'provider_inspection_directorate', clean_text(provider_inspection_directorate),
    'provider_primary_inspection_category', clean_text(provider_primary_inspection_category),
    'inherited_rating', safe_boolean(inherited_rating_y_n_),
    'location_type_sector', clean_text(location_type_sector),
    'provider_type_sector', clean_text(provider_type_sector),
    'provider_ownership_type', clean_text(provider_ownership_type),
    'provider_companies_house_number', clean_text(provider_companies_house_number),
    'provider_charity_number', clean_text(provider_charity_number)
  ) AS source_metadata,
  
  '{}'::jsonb AS extra,
  
  -- Новые v2.2 поля
  safe_boolean(service_user_band_dementia) AS serves_dementia_band,
  safe_boolean(service_user_band_children_0_18_years) AS serves_children,
  safe_boolean(service_user_band_learning_disabilities_or_autistic_spectrum_di) AS serves_learning_disabilities,
  safe_boolean(service_user_band_people_detained_under_the_mental_health_act) AS serves_detained_mha,
  safe_boolean(service_user_band_people_who_misuse_drugs_and_alcohol) AS serves_substance_misuse,
  safe_boolean(service_user_band_people_with_an_eating_disorder) AS serves_eating_disorders,
  safe_boolean(service_user_band_whole_population) AS serves_whole_population,
  
  -- regulated_activities (без изменений, но теперь safe_boolean работает лучше)
  jsonb_build_object(
    'activities', ARRAY_REMOVE(ARRAY[
      CASE WHEN safe_boolean(regulated_activity_accommodation_for_persons_who_require_nursin) THEN 'accommodation_nursing' END,
      CASE WHEN safe_boolean(regulated_activity_accommodation_for_persons_who_require_treatm) THEN 'accommodation_treatment' END,
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
FROM cqc_dataset_test
WHERE location_type_sector = 'Social Care Org'
  AND care_home_ = 'Y';

COMMIT;

-- ============================================================================
-- ЧАСТЬ 3: ВАЛИДАЦИЯ И ОТЧЕТ
-- ============================================================================

DO $$
DECLARE
  inserted_count INTEGER;
  has_nursing_count INTEGER;
  has_regulated_activities_count INTEGER;
  has_service_types_count INTEGER;
  has_service_user_bands_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO inserted_count FROM care_homes;
  SELECT COUNT(*) INTO has_nursing_count FROM care_homes WHERE has_nursing_care_license = TRUE;
  SELECT COUNT(*) INTO has_regulated_activities_count FROM care_homes WHERE regulated_activities != '{"activities": []}'::jsonb;
  SELECT COUNT(*) INTO has_service_types_count FROM care_homes WHERE jsonb_array_length(COALESCE(service_types->'services', '[]'::jsonb)) > 0;
  SELECT COUNT(*) INTO has_service_user_bands_count FROM care_homes WHERE jsonb_array_length(COALESCE(service_user_bands->'bands', '[]'::jsonb)) > 0;
  
  RAISE NOTICE '========================================================================';
  RAISE NOTICE 'УЛУЧШЕННАЯ МИГРАЦИЯ ЗАВЕРШЕНА!';
  RAISE NOTICE '========================================================================';
  RAISE NOTICE 'Вставлено записей: %', inserted_count;
  RAISE NOTICE 'has_nursing_care_license=TRUE: % (%.1f%%) - ожидается ~73 записи (26.9%%)', has_nursing_count, (has_nursing_count::FLOAT / NULLIF(inserted_count, 0) * 100);
  RAISE NOTICE 'regulated_activities заполнено: % (%.1f%%)', has_regulated_activities_count, (has_regulated_activities_count::FLOAT / NULLIF(inserted_count, 0) * 100);
  RAISE NOTICE 'service_types заполнено: % (%.1f%%)', has_service_types_count, (has_service_types_count::FLOAT / NULLIF(inserted_count, 0) * 100);
  RAISE NOTICE 'service_user_bands заполнено: % (%.1f%%)', has_service_user_bands_count, (has_service_user_bands_count::FLOAT / NULLIF(inserted_count, 0) * 100);
  RAISE NOTICE '========================================================================';
  RAISE NOTICE 'ВАЖНО: Проверьте, что has_nursing_care_license=TRUE для всех домов с care_nursing=TRUE';
  RAISE NOTICE '========================================================================';
END $$;

