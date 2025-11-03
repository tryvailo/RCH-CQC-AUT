-- ============================================================================
-- AUTUMNA STAGING TABLE v2.4
-- Промежуточное хранилище для парсинга Autumna HTML страниц
-- ============================================================================
-- Дата: 3 ноября 2025
-- Версия: v2.4 FINAL
-- Назначение: Хранение HTML и результатов парсинга для многократной обработки
-- ============================================================================

-- ============================================================================
-- ТАБЛИЦА: autumna_staging
-- ============================================================================
CREATE TABLE IF NOT EXISTS autumna_staging (
    -- PRIMARY KEY
    id BIGSERIAL PRIMARY KEY,
    
    -- ИДЕНТИФИКАЦИЯ
    source_url TEXT NOT NULL UNIQUE,
    cqc_location_id TEXT,  -- Извлечено из URL для быстрого поиска
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- ИСХОДНЫЕ ДАННЫЕ (сохраняются один раз через Firecrawl)
    html_content TEXT NOT NULL,  -- ВЕСЬ HTML текст страницы
    firecrawl_metadata JSONB,    -- Метаданные от Firecrawl (status, timestamp, etc.)
    
    -- РЕЗУЛЬТАТЫ ПАРСИНГА (обновляются многократно через OpenAI)
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

-- ============================================================================
-- ИНДЕКСЫ для быстрого поиска
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_staging_url ON autumna_staging(source_url);
CREATE INDEX IF NOT EXISTS idx_staging_cqc_id ON autumna_staging(cqc_location_id) WHERE cqc_location_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_staging_processed ON autumna_staging(processed) WHERE processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_staging_quality ON autumna_staging(data_quality_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_staging_reparse ON autumna_staging(needs_reparse) WHERE needs_reparse = TRUE;
CREATE INDEX IF NOT EXISTS idx_staging_prompt_version ON autumna_staging(llm_prompt_version);
CREATE INDEX IF NOT EXISTS idx_staging_html_null ON autumna_staging(id) WHERE html_content IS NULL;
CREATE INDEX IF NOT EXISTS idx_staging_parsed_null ON autumna_staging(id) WHERE parsed_json IS NULL;

-- ============================================================================
-- ТРИГГЕР для обновления updated_at
-- ============================================================================
CREATE OR REPLACE FUNCTION update_staging_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_staging_updated_at ON autumna_staging;
CREATE TRIGGER trigger_staging_updated_at
    BEFORE UPDATE ON autumna_staging
    FOR EACH ROW
    EXECUTE FUNCTION update_staging_updated_at();

-- ============================================================================
-- ФУНКЦИЯ для извлечения cqc_location_id из URL
-- ============================================================================
CREATE OR REPLACE FUNCTION extract_cqc_id_from_url(url TEXT)
RETURNS TEXT AS $$
DECLARE
    cqc_id TEXT;
BEGIN
    -- Паттерн: /1-XXXXXXXXXX в конце URL
    SELECT regexp_match(url, '/1-(\d{10})') INTO cqc_id;
    
    IF cqc_id IS NOT NULL AND array_length(cqc_id, 1) > 0 THEN
        RETURN '1-' || cqc_id[1];
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- КОММЕНТАРИИ
-- ============================================================================
COMMENT ON TABLE autumna_staging IS 'Промежуточное хранилище для парсинга Autumna HTML страниц';
COMMENT ON COLUMN autumna_staging.html_content IS 'Исходный HTML текст страницы - сохраняется один раз через Firecrawl';
COMMENT ON COLUMN autumna_staging.parsed_json IS 'Результат парсинга ChatGPT (JSON Schema v2.4, 188 полей) - обновляется многократно';
COMMENT ON COLUMN autumna_staging.llm_prompt_version IS 'Версия промпта для отслеживания эффективности разных версий';
COMMENT ON COLUMN autumna_staging.needs_reparse IS 'Флаг для повторной обработки (например, после улучшения промпта)';
COMMENT ON COLUMN autumna_staging.cqc_location_id IS 'Извлечено из URL для быстрого поиска и связывания с care_homes';

-- ============================================================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS) для удобного мониторинга
-- ============================================================================

-- Статистика обработки
CREATE OR REPLACE VIEW v_staging_stats AS
SELECT 
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE html_content IS NOT NULL) as html_loaded,
    COUNT(*) FILTER (WHERE parsed_json IS NOT NULL) as parsed,
    COUNT(*) FILTER (WHERE processed = TRUE) as synced_to_production,
    COUNT(*) FILTER (WHERE needs_reparse = TRUE) as needs_reparse,
    COUNT(*) FILTER (WHERE needs_validation = TRUE) as needs_validation,
    COUNT(*) FILTER (WHERE processed = FALSE AND parsed_json IS NOT NULL) as ready_for_mapping,
    AVG(data_quality_score)::INTEGER as avg_quality_score,
    COUNT(*) FILTER (WHERE data_quality_score >= 90) as high_quality_count,
    COUNT(*) FILTER (WHERE data_quality_score < 60 AND data_quality_score IS NOT NULL) as low_quality_count
FROM autumna_staging;

-- Качество по версиям промпта
CREATE OR REPLACE VIEW v_staging_prompt_stats AS
SELECT 
    llm_prompt_version,
    COUNT(*) as total_parsed,
    AVG(data_quality_score)::INTEGER as avg_quality,
    MIN(data_quality_score) as min_quality,
    MAX(data_quality_score) as max_quality,
    COUNT(*) FILTER (WHERE data_quality_score >= 90) as high_quality,
    COUNT(*) FILTER (WHERE data_quality_score < 60) as low_quality,
    COUNT(*) FILTER (WHERE extraction_confidence = 'high') as high_confidence,
    COUNT(*) FILTER (WHERE parsing_errors IS NOT NULL) as has_errors
FROM autumna_staging
WHERE parsed_json IS NOT NULL
GROUP BY llm_prompt_version
ORDER BY avg_quality DESC NULLS LAST;

-- Записи готовые для маппинга
CREATE OR REPLACE VIEW v_staging_ready_for_mapping AS
SELECT 
    id,
    source_url,
    cqc_location_id,
    data_quality_score,
    extraction_confidence,
    llm_prompt_version,
    parsed_json,
    parsing_errors
FROM autumna_staging
WHERE parsed_json IS NOT NULL
  AND processed = FALSE
  AND data_quality_score >= 60  -- Минимальный порог качества
ORDER BY data_quality_score DESC NULLS LAST;

-- Проблемные записи (требуют внимания)
CREATE OR REPLACE VIEW v_staging_problems AS
SELECT 
    id,
    source_url,
    cqc_location_id,
    data_quality_score,
    extraction_confidence,
    parsing_errors,
    mapping_errors,
    needs_validation,
    CASE 
        WHEN html_content IS NULL THEN 'Missing HTML'
        WHEN parsed_json IS NULL THEN 'Not parsed'
        WHEN data_quality_score < 60 THEN 'Low quality'
        WHEN parsing_errors IS NOT NULL THEN 'Parsing errors'
        WHEN mapping_errors IS NOT NULL THEN 'Mapping errors'
        ELSE 'Other'
    END as problem_type
FROM autumna_staging
WHERE 
    (html_content IS NULL)
    OR (parsed_json IS NULL AND needs_reparse = FALSE)
    OR (data_quality_score < 60 OR data_quality_score IS NULL)
    OR needs_validation = TRUE
    OR parsing_errors IS NOT NULL
    OR mapping_errors IS NOT NULL
ORDER BY 
    CASE 
        WHEN html_content IS NULL THEN 1
        WHEN parsed_json IS NULL THEN 2
        WHEN data_quality_score < 60 THEN 3
        ELSE 4
    END,
    data_quality_score ASC NULLS LAST;

-- ============================================================================
-- GRANT PERMISSIONS (если нужны)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON autumna_staging TO your_app_user;
-- GRANT SELECT ON v_staging_stats TO your_app_user;
-- GRANT SELECT ON v_staging_prompt_stats TO your_app_user;
-- GRANT SELECT ON v_staging_ready_for_mapping TO your_app_user;
-- GRANT SELECT ON v_staging_problems TO your_app_user;

-- ============================================================================
-- ГОТОВО!
-- ============================================================================

