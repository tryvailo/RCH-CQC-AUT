-- Извлеченные функции из step2_run_migration.sql для валидации

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
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
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
        END IF;
        
        IF result < 49.0 OR result > 61.0 THEN
            RETURN default_value;
        END IF;
        
        IF result < 1.0 THEN
            RETURN default_value;
        END IF;
        
        RETURN ROUND(result, 7);
    EXCEPTION
        WHEN OTHERS THEN
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
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
            END IF;
        EXCEPTION WHEN OTHERS THEN NULL;
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
        END IF;
        
        IF result < -8.0 OR result > 2.0 THEN
            RETURN default_value;
        END IF;
        
        RETURN ROUND(result, 7);
    EXCEPTION
        WHEN OTHERS THEN
            RETURN default_value;
    END;
EXCEPTION
    WHEN OTHERS THEN
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
    
    RETURN default_value;
EXCEPTION
    WHEN OTHERS THEN
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

