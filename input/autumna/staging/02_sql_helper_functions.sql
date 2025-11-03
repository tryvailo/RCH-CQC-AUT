-- ============================================================================
-- SQL HELPER FUNCTIONS для нормализации данных при маппинге
-- ============================================================================
-- Дата: 3 ноября 2025
-- Версия: v2.4 FINAL
-- Назначение: Функции для безопасной нормализации данных из staging в care_homes
-- ============================================================================

-- ============================================================================
-- 1. clean_text() - Очистка текста
-- ============================================================================
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

-- ============================================================================
-- 2. safe_integer() - Безопасное преобразование в INTEGER
-- ============================================================================
CREATE OR REPLACE FUNCTION safe_integer(input TEXT, default_value INTEGER DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    result INTEGER;
    cleaned TEXT;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    -- Удалить все кроме цифр и минуса
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

-- ============================================================================
-- 3. safe_latitude() - Безопасное преобразование широты (КРИТИЧНО!)
-- ============================================================================
-- Обрабатывает координаты с запятой как десятичным разделителем
-- Примеры: "52,533398" → 52.533398, "-1,88634" → -1.88634
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
        BEGIN
            numeric_val := cleaned::NUMERIC;
            -- Если значение очень большое, делим
            IF numeric_val > 1000000 THEN
                result := numeric_val / 100000.0;
                IF result >= 49.0 AND result <= 61.0 THEN
                    RETURN ROUND(result, 7);
                END IF;
            ELSE
                IF numeric_val >= 49.0 AND numeric_val <= 61.0 THEN
                    RETURN ROUND(numeric_val, 7);
                END IF;
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                NULL;
        END;
    -- Одна запятая - возможно десятичный разделитель
    ELSIF comma_count = 1 THEN
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
    -- Нет запятых
    ELSIF comma_count = 0 THEN
        BEGIN
            result := cleaned::NUMERIC;
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

-- ============================================================================
-- 4. safe_longitude() - Безопасное преобразование долготы (КРИТИЧНО!)
-- ============================================================================
-- Обрабатывает координаты с запятой как десятичным разделителем
-- Примеры: "-1,989241" → -1.989241
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

-- ============================================================================
-- 5. safe_boolean() - Безопасное преобразование в BOOLEAN
-- ============================================================================
CREATE OR REPLACE FUNCTION safe_boolean(input TEXT, default_value BOOLEAN DEFAULT NULL)
RETURNS BOOLEAN AS $$
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    -- Попробовать как boolean
    BEGIN
        RETURN input::BOOLEAN;
    EXCEPTION
        WHEN OTHERS THEN
            -- Попробовать как текст
            CASE LOWER(TRIM(input))
                WHEN 'true' THEN RETURN TRUE;
                WHEN 'false' THEN RETURN FALSE;
                WHEN '1' THEN RETURN TRUE;
                WHEN '0' THEN RETURN FALSE;
                WHEN 'yes' THEN RETURN TRUE;
                WHEN 'no' THEN RETURN FALSE;
                ELSE RETURN default_value;
            END CASE;
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 6. safe_date() - Безопасное преобразование в DATE
-- ============================================================================
CREATE OR REPLACE FUNCTION safe_date(input TEXT, default_value DATE DEFAULT NULL)
RETURNS DATE AS $$
DECLARE
    v_date DATE;
BEGIN
    IF input IS NULL OR TRIM(input) = '' THEN
        RETURN default_value;
    END IF;
    
    -- Попробовать разные форматы
    BEGIN
        v_date := TO_DATE(input, 'YYYY-MM-DD');
        RETURN v_date;
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;
    
    BEGIN
        v_date := TO_DATE(input, 'DD/MM/YYYY');
        RETURN v_date;
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;
    
    BEGIN
        v_date := TO_DATE(input, 'DD-MM-YYYY');
        RETURN v_date;
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;
    
    RETURN default_value;
EXCEPTION
    WHEN OTHERS THEN
        RETURN default_value;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 7. normalize_cqc_rating() - Нормализация CQC рейтинга
-- ============================================================================
CREATE OR REPLACE FUNCTION normalize_cqc_rating(p_value TEXT)
RETURNS TEXT AS $$
BEGIN
    IF p_value IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN CASE LOWER(TRIM(p_value))
        WHEN 'outstanding' THEN 'Outstanding'
        WHEN 'good' THEN 'Good'
        WHEN 'requires improvement' THEN 'Requires Improvement'
        WHEN 'requires improvement' THEN 'Requires Improvement'
        WHEN 'ri' THEN 'Requires Improvement'
        WHEN 'inadequate' THEN 'Inadequate'
        ELSE NULL
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 8. extract_year() - Извлечение года из даты
-- ============================================================================
CREATE OR REPLACE FUNCTION extract_year(p_date DATE)
RETURNS INTEGER AS $$
BEGIN
    IF p_date IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN EXTRACT(YEAR FROM p_date)::INTEGER;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- ГОТОВО!
-- ============================================================================

