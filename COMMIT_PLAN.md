# 📋 ПЛАН КОММИТОВ

**Дата:** 11 ноября 2025

---

## 🎯 СТРУКТУРА КОММИТОВ

### Коммит 1: Оптимизированный парсер Autumna v3.1 (NON-CQC fields only)

**Файлы:**
- `input/autumna/AUTUMNA_PARSING_PROMPT_v3_1_OPTIMIZED_NON_CQC.md` - новый промпт
- `input/autumna/response_format_v3_1_optimized_non_cqc.json` - новая JSON schema
- `input/autumna/AUTUMNA_PARSING_PROMPT_v2_6_OPTIMIZED_NON_CQC.md` - промежуточная версия (для справки)
- `.gitignore` - обновлен для разрешения новых schema файлов

**Сообщение коммита:**
```
feat: Add optimized Autumna parser v3.1 (NON-CQC fields only)

- New parser version that extracts ONLY fields not available in CQC Dataset
- Removed CQC ratings, licenses, regulated_activities, user_categories (~25% reduction)
- Enhanced email extraction (mailto: links, contact forms, footer sections)
- Added telephone fallback documentation (CQC provides fallback during merging)
- Documented expected NULL values for better understanding
- Updated .gitignore to allow new schema files
```

---

### Коммит 2: Аналитические отчеты и документация

**Файлы:**
- `project/reports/ANALYST_TASK_V3_1_REVIEW.md` - полная задача для аналитика
- `project/reports/ANALYST_TASK_V3_1_REVIEW_SHORT.md` - краткая версия задачи
- `project/reports/AUTUMNA_PARSER_OPTIMIZATION.md` - анализ оптимизации парсера
- `project/reports/AUTUMNA_PARSER_V2_6_OPTIMIZATION_SUMMARY.md` - сводка оптимизации
- `project/reports/CLEAR_STRATEGY_AUTUMNA_LOTTIE.md` - четкая стратегия Autumna vs Lottie
- `project/reports/CQC_REPORTS_MEDICAL_SPECIALISMS.md` - анализ CQC отчетов
- `project/reports/DATA_SOURCES_STRATEGY.md` - стратегия источников данных
- `project/reports/FIELD_ANALYSIS_REPORT.md` - анализ полей
- `project/reports/PROMPT_V3_1_IMPROVEMENTS.md` - улучшения промпта
- `project/reports/REAL_FILES_ANALYSIS.md` - анализ реальных файлов
- `project/reports/SOURCE_COMPARISON_STRATEGY.md` - сравнение источников

**Сообщение коммита:**
```
docs: Add comprehensive analysis reports and documentation

- Added analyst task for v3.1 parser review
- Added field analysis and optimization reports
- Added data sources strategy documentation
- Added CQC reports analysis for medical specialisms
- Added clear strategy for Autumna vs Lottie comparison
- Added source comparison strategy (CareHome.co.uk, Lottie, Perplexity API)
```

---

### Коммит 3: Тестовые файлы и скрипты

**Файлы:**
- `input/autumna/staging/test_parse_test2_v31.py` - тестовый скрипт для v3.1
- `input/autumna/Data-MD/html 1 /test1-md.md` - удален (заменен на test1.md)
- `input/autumna/Data-MD/html 2/###### Cookies on the Autumna Website.md` - удален

**Сообщение коммита:**
```
test: Add test script for v3.1 parser and clean up test files

- Added test_parse_test2_v31.py for testing v3.1 parser
- Removed obsolete test files (test1-md.md, Cookies file)
```

---

## 📝 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ

```bash
# Коммит 1: Парсер v3.1
git add input/autumna/AUTUMNA_PARSING_PROMPT_v3_1_OPTIMIZED_NON_CQC.md
git add input/autumna/response_format_v3_1_optimized_non_cqc.json
git add input/autumna/AUTUMNA_PARSING_PROMPT_v2_6_OPTIMIZED_NON_CQC.md
git add .gitignore
git commit -m "feat: Add optimized Autumna parser v3.1 (NON-CQC fields only)

- New parser version that extracts ONLY fields not available in CQC Dataset
- Removed CQC ratings, licenses, regulated_activities, user_categories (~25% reduction)
- Enhanced email extraction (mailto: links, contact forms, footer sections)
- Added telephone fallback documentation (CQC provides fallback during merging)
- Documented expected NULL values for better understanding
- Updated .gitignore to allow new schema files"

# Коммит 2: Отчеты
git add project/reports/*.md
git commit -m "docs: Add comprehensive analysis reports and documentation

- Added analyst task for v3.1 parser review
- Added field analysis and optimization reports
- Added data sources strategy documentation
- Added CQC reports analysis for medical specialisms
- Added clear strategy for Autumna vs Lottie comparison
- Added source comparison strategy (CareHome.co.uk, Lottie, Perplexity API)"

# Коммит 3: Тесты
git add input/autumna/staging/test_parse_test2_v31.py
git commit -m "test: Add test script for v3.1 parser and clean up test files

- Added test_parse_test2_v31.py for testing v3.1 parser
- Removed obsolete test files (test1-md.md, Cookies file)"
```

---

## ⚠️ НЕ ДОБАВЛЯТЬ В GIT

Следующие файлы остаются untracked (тестовые данные):
- `input/autumna/Data-MD/html 1 /test1.md`
- `input/autumna/Data-MD/html 2/test2.md`
- `input/autumna/Data-MD/lottie.org_care-home_england_1-3583146795_lucton-house_.2025-11-11T15_21_56.499Z.md`
- `input/autumna/Data-MD/test3.md`
- `input/Опросники.md`
- `input/autumna/Data-MD/html 2/test2-v31-parsed-result.json` (результат парсинга)

**Причина:** Это тестовые данные и результаты парсинга, которые не должны быть в репозитории.

