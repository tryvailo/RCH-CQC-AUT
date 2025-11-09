-- ============================================================================
-- ДОБАВЛЕНИЕ ПОЛЯ markdown_content В autumna_staging
-- ============================================================================
-- Дата: 3 ноября 2025
-- Версия: v2.4 → v2.5 (Markdown support)
-- Назначение: Добавить поддержку Markdown формата для экономии токенов
-- ============================================================================

-- Добавить поле markdown_content (NULL для обратной совместимости)
ALTER TABLE autumna_staging 
ADD COLUMN IF NOT EXISTS markdown_content TEXT;

-- Обновить комментарии
COMMENT ON COLUMN autumna_staging.markdown_content IS 'Markdown версия страницы - сохраняется через Firecrawl для экономии токенов при парсинге';

-- Создать индекс для быстрого поиска записей с markdown
CREATE INDEX IF NOT EXISTS idx_staging_markdown_null ON autumna_staging(id) WHERE markdown_content IS NULL;

-- Обновить представления для поддержки markdown_content
DROP VIEW IF EXISTS v_staging_stats;
CREATE OR REPLACE VIEW v_staging_stats AS
SELECT 
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE html_content IS NOT NULL OR markdown_content IS NOT NULL) as content_loaded,
    COUNT(*) FILTER (WHERE html_content IS NOT NULL) as html_loaded,
    COUNT(*) FILTER (WHERE markdown_content IS NOT NULL) as markdown_loaded,
    COUNT(*) FILTER (WHERE parsed_json IS NOT NULL) as parsed,
    COUNT(*) FILTER (WHERE processed = TRUE) as synced_to_production,
    COUNT(*) FILTER (WHERE needs_reparse = TRUE) as needs_reparse,
    COUNT(*) FILTER (WHERE needs_validation = TRUE) as needs_validation,
    COUNT(*) FILTER (WHERE processed = FALSE AND parsed_json IS NOT NULL) as ready_for_mapping,
    AVG(data_quality_score)::INTEGER as avg_quality_score,
    COUNT(*) FILTER (WHERE data_quality_score >= 90) as high_quality_count,
    COUNT(*) FILTER (WHERE data_quality_score < 60 AND data_quality_score IS NOT NULL) as low_quality_count
FROM autumna_staging;

-- Обновить представление проблемных записей
DROP VIEW IF EXISTS v_staging_problems;
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
        WHEN html_content IS NULL AND markdown_content IS NULL THEN 'Missing content'
        WHEN parsed_json IS NULL THEN 'Not parsed'
        WHEN data_quality_score < 60 THEN 'Low quality'
        WHEN parsing_errors IS NOT NULL THEN 'Parsing errors'
        WHEN mapping_errors IS NOT NULL THEN 'Mapping errors'
        ELSE 'Other'
    END as problem_type
FROM autumna_staging
WHERE 
    (html_content IS NULL AND markdown_content IS NULL)
    OR (parsed_json IS NULL AND needs_reparse = FALSE)
    OR (data_quality_score < 60 OR data_quality_score IS NULL)
    OR needs_validation = TRUE
    OR parsing_errors IS NOT NULL
    OR mapping_errors IS NOT NULL
ORDER BY 
    CASE 
        WHEN html_content IS NULL AND markdown_content IS NULL THEN 1
        WHEN parsed_json IS NULL THEN 2
        WHEN data_quality_score < 60 THEN 3
        ELSE 4
    END,
    data_quality_score ASC NULLS LAST;

-- ============================================================================
-- ГОТОВО!
-- ============================================================================
-- После выполнения этого скрипта:
-- 1. phase1_load_html.py будет сохранять markdown_content
-- 2. phase2_parse_llm.py будет использовать markdown_content для парсинга
-- 3. Старые записи с html_content продолжат работать (обратная совместимость)
-- ============================================================================

