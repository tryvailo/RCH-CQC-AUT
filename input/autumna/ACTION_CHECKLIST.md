# ✅ ACTION CHECKLIST: Следующие шаги после валидации

**Версия:** v2.4 → production  
**Статус:** ✅ Готово к использованию  
**Дата:** 31 октября 2025

---

## 🎯 НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ (v2.4 Production)

### [ ] 1. Утвердить текущую версию v2.4

**Статус:** ✅ Production-ready (97.7%)

**Файлы для утверждения:**
- ✅ `AUTUMNA_PARSING_PROMPT_v2_4.md` - системный промпт
- ✅ `response_format_v2_4.json` - JSON Schema
- ✅ `care_homes_db_v2_2.sql` - структура БД

**Проверено:**
- ✅ Все 4 обязательных поля корректны
- ✅ 0 критических блокеров
- ✅ 100% покрытие новых полей v2.2

---

### [ ] 2. Настроить OpenAI API integration

**Код для вызова:**

```python
import openai
import json

# Загрузить JSON Schema
with open('response_format_v2_4.json', 'r') as f:
    response_format = json.load(f)

# Загрузить System Prompt
with open('AUTUMNA_PARSING_PROMPT_v2_4.md', 'r') as f:
    system_prompt = f.read()

# Вызов OpenAI API
response = openai.chat.completions.create(
    model="gpt-4o-2024-08-06",  # Или новее
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Parse this HTML: {html_content}"}
    ],
    response_format=response_format
)

parsed_data = json.loads(response.choices[0].message.content)
```

**Параметры:**
- ✅ Model: `gpt-4o-2024-08-06` (или новее с Structured Outputs)
- ✅ Temperature: 0 (для consistency)
- ✅ response_format: используйте полный JSON Schema

---

### [ ] 3. Настроить staging таблицу ⭐ РЕКОМЕНДУЕТСЯ!

**Статус:** ⚠️ КРИТИЧНО для экономии средств при итерациях

**Подробности:** см. `STAGING_ARCHITECTURE_v2.4.md` - полное руководство по staging подходу

**Почему staging:**
- 💰 Экономия $53.52+ при 5 итерациях улучшения промпта
- 🔄 Возможность повторной обработки без перезагрузки HTML через Firecrawl
- 🧪 Тестирование разных версий промптов на одних данных
- 📊 История и версионирование результатов парсинга

**SQL для создания staging table (обновленная версия):**

```sql
CREATE TABLE autumna_staging (
    id BIGSERIAL PRIMARY KEY,
    
    -- ИДЕНТИФИКАЦИЯ
    source_url TEXT NOT NULL UNIQUE,
    cqc_location_id TEXT,  -- Извлечено из URL для быстрого поиска
    scraped_at TIMESTAMPTZ NOT NULL,
    
    -- ИСХОДНЫЕ ДАННЫЕ (сохраняются один раз)
    html_content TEXT NOT NULL,  -- ВЕСЬ HTML текст страницы
    firecrawl_metadata JSONB,   -- Метаданные от Firecrawl
    
    -- РЕЗУЛЬТАТЫ ПАРСИНГА (обновляются многократно)
    parsed_json JSONB,           -- Результат от ChatGPT (JSON Schema v2.4)
    extraction_confidence TEXT,  -- 'high', 'medium', 'low'
    data_quality_score INTEGER, -- Quality score (0-100)
    is_dormant BOOLEAN DEFAULT FALSE,
    
    -- ВЕРСИОНИРОВАНИЕ И ОТЛАДКА
    llm_model TEXT,             -- 'gpt-4o-2024-08-06', etc.
    llm_prompt_version TEXT,    -- 'v2.4', 'v2.5', 'experimental_1', etc.
    parsing_errors JSONB,       -- Ошибки парсинга
    mapping_errors JSONB,       -- Ошибки маппинга
    
    -- ФЛАГИ ОБРАБОТКИ
    needs_reparse BOOLEAN DEFAULT FALSE,     -- Нужно ли переобработать
    needs_validation BOOLEAN DEFAULT FALSE, -- Нужна ли ручная проверка
    processed BOOLEAN DEFAULT FALSE,         -- Обработан ли в care_homes
    processed_at TIMESTAMPTZ,
    
    -- СВЯЗЬ С ФИНАЛЬНОЙ БД
    care_homes_id BIGINT,                    -- FK на care_homes.id
    
    -- ВРЕМЕННЫЕ МЕТКИ
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ИНДЕКСЫ
CREATE INDEX idx_staging_url ON autumna_staging(source_url);
CREATE INDEX idx_staging_cqc_id ON autumna_staging(cqc_location_id) WHERE cqc_location_id IS NOT NULL;
CREATE INDEX idx_staging_processed ON autumna_staging(processed) WHERE processed = FALSE;
CREATE INDEX idx_staging_quality ON autumna_staging(data_quality_score DESC NULLS LAST);
CREATE INDEX idx_staging_reparse ON autumna_staging(needs_reparse) WHERE needs_reparse = TRUE;
CREATE INDEX idx_staging_prompt_version ON autumna_staging(llm_prompt_version);
```

**Workflow (3 фазы):**
1. **Фаза 1:** Firecrawl сохраняет HTML → `staging.html_content` ($15 один раз)
2. **Фаза 2:** OpenAI парсит → `staging.parsed_json` ($1.62 многократно, можно повторять!)
3. **Фаза 3:** Mapper переносит → `care_homes` (финальная таблица)

**Подробнее:** см. `STAGING_ARCHITECTURE_v2.4.md` - полное руководство с примерами кода и n8n workflows

---

### [ ] 4. Создать mapper function

**Пример Python mapper:**

```python
def map_autumna_to_db(parsed_json: dict) -> dict:
    """Map Autumna parsed JSON to care_homes DB structure"""
    
    return {
        # ГРУППА 1: ИДЕНТИФИКАТОРЫ
        'cqc_location_id': parsed_json['identity']['cqc_location_id'],
        'location_ods_code': parsed_json['identity']['location_ods_code'],
        
        # ГРУППА 2: БАЗОВАЯ ИНФОРМАЦИЯ
        'name': parsed_json['identity']['name'],
        'provider_name': parsed_json['identity']['provider_name'],
        'provider_id': parsed_json['identity']['provider_id'],
        'brand_name': parsed_json['identity']['brand_name'],
        
        # ГРУППА 3: КОНТАКТЫ
        'telephone': parsed_json['contact']['telephone'],
        'email': parsed_json['contact']['email'],
        'website': parsed_json['contact']['website'],
        
        # ГРУППА 4: ЛОКАЦИЯ
        'city': parsed_json['location']['city'],
        'county': parsed_json['location']['county'],
        'postcode': parsed_json['location']['postcode'],
        'latitude': parsed_json['location']['latitude'],
        'longitude': parsed_json['location']['longitude'],
        'region': parsed_json['location']['region'],
        'local_authority': parsed_json['location']['local_authority'],
        
        # ГРУППА 5: ВМЕСТИМОСТЬ
        'beds_total': parsed_json['capacity']['beds_total'],
        'beds_available': parsed_json['capacity']['beds_available'],
        'has_availability': parsed_json['capacity']['has_availability'],
        'availability_status': parsed_json['capacity']['availability_status'],
        'year_opened': parsed_json['capacity']['year_opened'],
        'year_registered': parsed_json['capacity']['year_registered'],
        
        # ГРУППА 6: ТИПЫ УХОДА
        'care_residential': parsed_json['care_services']['care_residential'],
        'care_nursing': parsed_json['care_services']['care_nursing'],
        'care_dementia': parsed_json['care_services']['care_dementia'],
        'care_respite': parsed_json['care_services']['care_respite'],
        
        # ГРУППА 7: ЛИЦЕНЗИИ (5 полей)
        'has_nursing_care_license': parsed_json['licenses']['has_nursing_care_license'],
        'has_personal_care_license': parsed_json['licenses']['has_personal_care_license'],
        'has_surgical_procedures_license': parsed_json['licenses']['has_surgical_procedures_license'],
        'has_treatment_license': parsed_json['licenses']['has_treatment_license'],
        'has_diagnostic_license': parsed_json['licenses']['has_diagnostic_license'],
        
        # ГРУППА 8: SERVICE USER BANDS (12 полей)
        'serves_older_people': parsed_json['user_categories']['serves_older_people'],
        'serves_younger_adults': parsed_json['user_categories']['serves_younger_adults'],
        'serves_mental_health': parsed_json['user_categories']['serves_mental_health'],
        'serves_physical_disabilities': parsed_json['user_categories']['serves_physical_disabilities'],
        'serves_sensory_impairments': parsed_json['user_categories']['serves_sensory_impairments'],
        'serves_dementia_band': parsed_json['user_categories']['serves_dementia_band'],
        'serves_children': parsed_json['user_categories']['serves_children'],
        'serves_learning_disabilities': parsed_json['user_categories']['serves_learning_disabilities'],
        'serves_detained_mha': parsed_json['user_categories']['serves_detained_mha'],
        'serves_substance_misuse': parsed_json['user_categories']['serves_substance_misuse'],
        'serves_eating_disorders': parsed_json['user_categories']['serves_eating_disorders'],
        'serves_whole_population': parsed_json['user_categories']['serves_whole_population'],
        
        # ГРУППА 9: ЦЕНООБРАЗОВАНИЕ
        'fee_residential_from': parsed_json['pricing']['fee_residential_from'],
        'fee_nursing_from': parsed_json['pricing']['fee_nursing_from'],
        'fee_dementia_from': parsed_json['pricing']['fee_dementia_from'],
        'fee_respite_from': parsed_json['pricing']['fee_respite_from'],
        
        # ГРУППА 10: ФИНАНСИРОВАНИЕ
        'accepts_self_funding': parsed_json['funding']['accepts_self_funding'],
        'accepts_local_authority': parsed_json['funding']['accepts_local_authority'],
        'accepts_nhs_chc': parsed_json['funding']['accepts_nhs_chc'],
        'accepts_third_party_topup': parsed_json['funding']['accepts_third_party_topup'],
        
        # ГРУППА 11: CQC РЕЙТИНГИ
        'cqc_rating_overall': parsed_json['cqc_ratings']['cqc_rating_overall'],
        'cqc_rating_safe': parsed_json['cqc_ratings']['cqc_rating_safe'],
        'cqc_rating_effective': parsed_json['cqc_ratings']['cqc_rating_effective'],
        'cqc_rating_caring': parsed_json['cqc_ratings']['cqc_rating_caring'],
        'cqc_rating_responsive': parsed_json['cqc_ratings']['cqc_rating_responsive'],
        'cqc_rating_well_led': parsed_json['cqc_ratings']['cqc_rating_well_led'],
        'cqc_last_inspection_date': parsed_json['cqc_ratings']['cqc_last_inspection_date'],
        'cqc_publication_date': parsed_json['cqc_ratings']['cqc_publication_date'],
        'cqc_latest_report_url': parsed_json['cqc_ratings']['cqc_latest_report_url'],
        
        # ГРУППА 12: ОТЗЫВЫ
        'review_average_score': parsed_json['reviews']['review_average_score'],
        'review_count': parsed_json['reviews']['review_count'],
        'google_rating': parsed_json['reviews']['google_rating'],
        
        # ГРУППА 13: УДОБСТВА (5 boolean полей)
        'wheelchair_access': parsed_json['building_and_facilities']['wheelchair_access'],
        'ensuite_rooms': parsed_json['building_and_facilities']['ensuite_rooms'],
        'secure_garden': parsed_json['building_and_facilities']['secure_garden'],
        'wifi_available': parsed_json['building_and_facilities']['wifi_available'],
        'parking_onsite': parsed_json['building_and_facilities']['parking_onsite'],
        
        # ГРУППА 14: СТАТУС
        'is_dormant': parsed_json['extraction_metadata']['is_dormant'],
        'data_quality_score': parsed_json['extraction_metadata']['data_quality_score'],
        
        # ГРУППА 15: JSONB ПОЛЯ (17 полей)
        'regulated_activities': json.dumps(parsed_json['licenses']['regulated_activities']),
        'source_urls': json.dumps(parsed_json['source_metadata']),
        'service_types': json.dumps(parsed_json['care_services'].get('service_types_list', [])),
        'service_user_bands': json.dumps(parsed_json['user_categories'].get('user_categories_list', [])),
        'facilities': json.dumps(parsed_json['building_and_facilities'].get('facilities_details', {})),
        'medical_specialisms': json.dumps(parsed_json['medical_specialisms']),
        'dietary_options': json.dumps(parsed_json['dietary_options']),
        'activities': json.dumps(parsed_json['activities']),
        'pricing_details': json.dumps(parsed_json['pricing']),
        'staff_information': json.dumps(parsed_json['staff_information']),
        'reviews_detailed': json.dumps(parsed_json['reviews']),
        'media': json.dumps(parsed_json['media']),
        'location_context': json.dumps(parsed_json['location']['location_context']),
        'building_info': json.dumps(parsed_json['building_and_facilities'].get('building_details', {})),
        'accreditations': json.dumps(parsed_json['accreditations']),
        
        # ВРЕМЕННЫЕ МЕТКИ
        'last_scraped_at': parsed_json['source_metadata']['scraped_at']
    }
```

---

### [ ] 5. Настроить мониторинг качества

**SQL для мониторинга:**

```sql
-- Проверка data quality
SELECT 
    AVG(data_quality_score) as avg_quality,
    MIN(data_quality_score) as min_quality,
    COUNT(*) FILTER (WHERE data_quality_score < 70) as low_quality_count,
    COUNT(*) FILTER (WHERE is_dormant = TRUE) as dormant_count
FROM care_homes
WHERE source = 'autumna';

-- Проверка критических полей
SELECT 
    COUNT(*) FILTER (WHERE cqc_location_id IS NULL) as missing_cqc_id,
    COUNT(*) FILTER (WHERE name IS NULL) as missing_name,
    COUNT(*) FILTER (WHERE city IS NULL) as missing_city,
    COUNT(*) FILTER (WHERE postcode IS NULL) as missing_postcode
FROM care_homes
WHERE source = 'autumna';

-- Покрытие новых полей v2.2
SELECT 
    COUNT(*) FILTER (WHERE serves_dementia_band = TRUE) as dementia_count,
    COUNT(*) FILTER (WHERE regulated_activities != '{"activities": []}'::jsonb) as has_licenses,
    COUNT(*) FILTER (WHERE wheelchair_access = TRUE) as wheelchair_count
FROM care_homes
WHERE source = 'autumna';
```

**Alert thresholds:**
- ⚠️ avg_quality < 80% → проверить промпт
- ⚠️ missing_cqc_id > 0 → критическая ошибка
- ⚠️ low_quality_count > 10% → проверить HTML источник

---

### [ ] 6. Запустить тестовый парсинг

**Test checklist:**
- [ ] Выбрать 10-20 страниц Autumna для теста
- [ ] Запустить парсинг с v2.4
- [ ] Проверить data_quality_score (ожидается 80-95)
- [ ] Проверить критические поля (100% заполнение)
- [ ] Проверить новые поля v2.2 (корректное извлечение)
- [ ] Проверить consistency (licenses vs care_services)

**Ожидаемые результаты:**
- ✅ 95%+ успешных парсингов
- ✅ Все критические поля заполнены
- ✅ Data quality score 80-95
- ✅ Нет validation errors

---

## 🔧 ОПЦИОНАЛЬНЫЕ УЛУЧШЕНИЯ (v2.5)

### [ ] 7. Реализовать улучшение #1: Regulated Activities

**Файл:** `improvement_recommendations.md` → секция "УЛУЧШЕНИЕ #1"

**Действия:**
1. Скопировать готовый текст из рекомендаций
2. Вставить в `AUTUMNA_PARSING_PROMPT_v2_5.md` после секции PRICING
3. Обновить версию в JSON Schema на 2.5

**Срок:** 3-4 часа

**Приоритет:** MEDIUM (улучшает точность на 15-20%)

---

### [ ] 8. Реализовать улучшение #2: Service Types List

**Файл:** `improvement_recommendations.md` → секция "УЛУЧШЕНИЕ #2"

**Действия:**
1. Скопировать готовый текст из рекомендаций
2. Вставить в `AUTUMNA_PARSING_PROMPT_v2_5.md`
3. Тестировать извлечение service_types_list

**Срок:** 2-3 часа

**Приоритет:** MEDIUM (улучшает полноту на 5-10%)

---

### [ ] 9. Добавить полный пример HTML → JSON

**Файл:** `improvement_recommendations.md` → секция "УЛУЧШЕНИЕ #3"

**Действия:**
1. Скопировать complete example из рекомендаций
2. Вставить в `AUTUMNA_PARSING_PROMPT_v2_5.md` перед OUTPUT CONTRACT

**Срок:** 1 час

**Приоритет:** LOW (образовательное)

---

### [ ] 10. Добавить documentation notes

**Файл:** `improvement_recommendations.md` → секция "УЛУЧШЕНИЕ #4"

**Действия:**
1. Добавить примечание про address_line_1/2
2. Обновить DB MAPPING QUICK REFERENCE

**Срок:** 15 минут

**Приоритет:** LOW (документационное)

---

## 📊 МЕТРИКИ ДЛЯ ОТСЛЕЖИВАНИЯ

### Week 1: Baseline metrics

**Собрать:**
- [ ] Успешность парсинга (% без errors)
- [ ] Средний data_quality_score
- [ ] % домов с заполненными критическими полями
- [ ] % домов с regulated_activities
- [ ] % домов с новыми service_user_bands

**Target:**
- ✅ Success rate: 95%+
- ✅ Avg quality: 85+
- ✅ Critical fields: 100%
- ✅ regulated_activities: 70%+

---

### Week 2-3: После v2.5 (если реализовано)

**Сравнить:**
- [ ] Улучшение regulated_activities coverage (+15-20%)
- [ ] Улучшение service_types_list coverage (+5-10%)
- [ ] Общее улучшение data_quality_score

---

## ✅ ГОТОВНОСТЬ К PRODUCTION

### Критерии готовности:

- [x] ✅ v2.4 утверждена (97.7%)
- [x] ✅ 0 критических блокеров
- [x] ✅ 100% покрытие БД v2.2
- [ ] ⏳ OpenAI API настроен
- [ ] ⏳ Staging table создана
- [ ] ⏳ Mapper function готов
- [ ] ⏳ Monitoring настроен
- [ ] ⏳ Test run завершен успешно

**Статус:** 2/7 готово (40%)

**До production:** Выполнить пункты 2-6

---

## 🚀 TIMELINE

### Немедленно (сегодня):
1. ✅ Утвердить v2.4
2. ⏳ Настроить OpenAI API (1 час)
3. ⏳ Создать staging table (30 минут)

### День 1-2:
4. ⏳ Написать mapper function (4 часа)
5. ⏳ Настроить monitoring (2 часа)
6. ⏳ Запустить test run (1 час)

### Неделя 1-2:
7. ⏳ Собрать baseline metrics
8. ⏳ Анализ результатов

### Опционально (неделя 2-3):
9. ⏳ Реализовать v2.5 улучшения (1-2 дня)

---

## 📞 SUPPORT

**При возникновении проблем:**

1. Проверьте `validation_report.md` (детальная валидация)
2. Проверьте `improvement_recommendations.md` (готовые решения)
3. Проверьте `EXECUTIVE_SUMMARY.md` (краткий обзор)

**Типичные проблемы и решения:**

**Проблема:** OpenAI returns validation error
**Решение:** Проверьте required fields (cqc_location_id, name, city, postcode)

**Проблема:** Low data_quality_score
**Решение:** Проверьте качество HTML от Firecrawl

**Проблема:** regulated_activities пустой
**Решение:** Реализуйте улучшение #1 из recommendations

---

**Создано:** 31 октября 2025  
**Статус:** Ready to use  
**Следующее обновление:** После реализации v2.5
