# ЧЕКЛИСТ ПРОВЕРКИ LLM ПАРСИНГА: System Prompt + Response Format

**Версия:** 1.0  
**Дата:** 30 октября 2025 г.  
**Назначение:** Проверка качества системного промпта и JSON Schema для парсинга HTML страниц Autumna с помощью OpenAI LLM

---

## 📋 О ЧЕМ ЭТОТ ЧЕКЛИСТ

Этот чеклист фокусируется **ТОЛЬКО** на проверке:
1. **System Prompt** (инструкции для LLM)
2. **Response Format** (JSON Schema для OpenAI `response_format.type = "json_schema"`)

**НЕ включает:** Python mapper, SQL functions, валидацию (для этого используйте основной чеклист маппинга).

---

## КАК ИСПОЛЬЗОВАТЬ

1. Откройте файлы:
   - `AUTUMNA_PARSING_PROMPT_v2_3_HYBRID_ULTIMATE.md` (или аналогичный)
   - `response_format_v2_3_FIXED.json` (или аналогичный)

2. Пройдите ВСЕ пункты по порядку, отмечая ✅ или ❌

3. Запишите найденные проблемы в раздел "Найденные ошибки"

4. Подсчитайте итоговую оценку

5. Проверьте **КРИТИЧЕСКИЕ БЛОКЕРЫ** (если >= 1 → переделать промпт!)

---

## РАЗДЕЛ 1: БАЗОВАЯ СТРУКТУРА RESPONSE FORMAT (JSON SCHEMA)

### 1.1 Метаданные схемы

- [ ] **1.1.1** Есть поле `"name"` (например, `"autumna_care_home_extraction"`)
- [ ] **1.1.2** Есть поле `"description"` с описанием схемы
- [ ] **1.1.3** Есть поле `"strict": true` (для Structured Outputs)
- [ ] **1.1.4** Корневой тип: `"type": "object"`
- [ ] **1.1.5** Есть секция `"properties"` с полями
- [ ] **1.1.6** Есть секция `"required"` со списком обязательных полей
- [ ] **1.1.7** Есть `"additionalProperties": false` (для strict mode)

**Пример правильной структуры:**
```json
{
  "name": "autumna_care_home_extraction",
  "description": "Extract care home data from Autumna HTML",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": { ... },
    "required": [...],
    "additionalProperties": false
  }
}
```

**Оценка раздела 1.1:** ___/7

---

### 1.2 Иерархическая структура (топ-уровень)

- [ ] **1.2.1** Есть секция `identity` (идентификаторы и названия)
- [ ] **1.2.2** Есть секция `contact` (телефон, email, website)
- [ ] **1.2.3** Есть секция `location` (адрес, координаты)
- [ ] **1.2.4** Есть секция `capacity` (beds, years)
- [ ] **1.2.5** Есть секция `care_services` (типы ухода)
- [ ] **1.2.6** Есть секция `licenses` (официальные лицензии CQC)
- [ ] **1.2.7** Есть секция `user_categories` (категории пользователей)
- [ ] **1.2.8** Есть секция `pricing` (ценообразование)
- [ ] **1.2.9** Есть секция `funding` (финансирование)
- [ ] **1.2.10** Есть секция `building_and_facilities` (здание и удобства)
- [ ] **1.2.11** Есть секция `medical_specialisms` (медицинские специализации)
- [ ] **1.2.12** Есть секция `dietary_options` (диетические опции)
- [ ] **1.2.13** Есть секция `activities` (активности)
- [ ] **1.2.14** Есть секция `staff_information` (информация о персонале)
- [ ] **1.2.15** Есть секция `cqc_ratings` (CQC рейтинги)
- [ ] **1.2.16** Есть секция `reviews` (отзывы)
- [ ] **1.2.17** Есть секция `media` (изображения, видео)
- [ ] **1.2.18** Есть секция `availability` (доступность)
- [ ] **1.2.19** Есть секция `accreditations` (аккредитации)
- [ ] **1.2.20** Есть секция `source_metadata` (метаданные источника)

**Важно:** Все секции должны быть на **верхнем уровне** (не вложенные друг в друга).

**Оценка раздела 1.2:** ___/20

---

## РАЗДЕЛ 2: КРИТИЧЕСКИЕ ПОЛЯ (ОБЯЗАТЕЛЬНЫЕ) 🔴

### 2.1 identity.cqc_location_id (КРИТИЧНО!)

- [ ] **2.1.1** ✅ **БЛОКЕР:** Поле `identity.cqc_location_id` существует
- [ ] **2.1.2** ✅ **БЛОКЕР:** Тип: `"type": "string"` (НЕ `["string", "null"]`)
- [ ] **2.1.3** ✅ **БЛОКЕР:** Есть `"pattern": "^1-\\d{10}$"`
- [ ] **2.1.4** ✅ **БЛОКЕР:** Есть `"description"` с объяснением формата
- [ ] **2.1.5** Поле включено в `"required"` массив секции `identity`

**Проверка:**
```bash
grep -A 5 '"cqc_location_id"' response_format.json
```

**Ожидается:**
```json
"cqc_location_id": {
  "type": "string",  // НЕ ["string", "null"]!
  "pattern": "^1-\\d{10}$",
  "description": "CQC Location ID in format 1-XXXXXXXXXX"
}
```

**❌ КРИТИЧЕСКАЯ ОШИБКА ЕСЛИ:**
```json
"cqc_location_id": {
  "type": ["string", "null"]  // ❌ Система упадет!
}
```

**Оценка раздела 2.1:** ___/5

---

### 2.2 identity.name (КРИТИЧНО!)

- [ ] **2.2.1** ✅ **БЛОКЕР:** Поле `identity.name` существует
- [ ] **2.2.2** ✅ **БЛОКЕР:** Тип: `"type": "string"` (НЕ `["string", "null"]`)
- [ ] **2.2.3** Есть `"description"` с объяснением
- [ ] **2.2.4** Поле включено в `"required"` массив секции `identity`

**Оценка раздела 2.2:** ___/4

---

### 2.3 location.city (КРИТИЧНО!)

- [ ] **2.3.1** ✅ **БЛОКЕР:** Поле `location.city` существует
- [ ] **2.3.2** ✅ **БЛОКЕР:** Тип: `"type": "string"` (НЕ `["string", "null"]`)
- [ ] **2.3.3** Есть `"description"` с объяснением
- [ ] **2.3.4** Поле включено в `"required"` массив секции `location`

**Оценка раздела 2.3:** ___/4

---

### 2.4 location.postcode (КРИТИЧНО!)

- [ ] **2.4.1** ✅ **БЛОКЕР:** Поле `location.postcode` существует
- [ ] **2.4.2** ✅ **БЛОКЕР:** Тип: `"type": "string"` (НЕ `["string", "null"]`)
- [ ] **2.4.3** Есть `"pattern"` для UK postcode (regex)
- [ ] **2.4.4** Есть `"description"` с объяснением формата
- [ ] **2.4.5** Поле включено в `"required"` массив секции `location`

**Рекомендуемый regex:**
```json
"pattern": "^[A-Z]{1,2}\\d{1,2}[A-Z]?\\s?\\d[A-Z]{2}$"
```

**Оценка раздела 2.4:** ___/5

---

### 2.5 Проверка "required" массивов

- [ ] **2.5.1** ✅ **БЛОКЕР:** `identity` имеет `"required": ["cqc_location_id", "name"]`
- [ ] **2.5.2** ✅ **БЛОКЕР:** `location` имеет `"required": ["city", "postcode"]`
- [ ] **2.5.3** `source_metadata` имеет `"required": ["source_url", "scraped_at"]`

**Проверка:**
```bash
grep -A 2 '"required"' response_format.json | grep -E "(cqc_location_id|name|city|postcode)"
```

**Оценка раздела 2.5:** ___/3

---

## РАЗДЕЛ 3: СЕКЦИЯ identity

### 3.1 Основные поля identity

- [ ] **3.1.1** `cqc_location_id` - string, pattern `^1-\\d{10}$`, REQUIRED
- [ ] **3.1.2** `name` - string, REQUIRED
- [ ] **3.1.3** `provider_name` - string или null
- [ ] **3.1.4** `provider_id` - string или null, pattern `^1-\\d{9}$`
- [ ] **3.1.5** `brand_name` - string или null
- [ ] **3.1.6** `location_ods_code` - string или null
- [ ] **3.1.7** `registered_manager` - string или null

**Оценка раздела 3.1:** ___/7

---

## РАЗДЕЛ 4: СЕКЦИЯ contact

### 4.1 Поля contact

- [ ] **4.1.1** `telephone` - string или null
- [ ] **4.1.2** `email` - string или null, с email pattern
- [ ] **4.1.3** `website` - string или null, с URL pattern

**Важно:** Все поля должны быть `["string", "null"]` (опциональные).

**Оценка раздела 4.1:** ___/3

---

## РАЗДЕЛ 5: СЕКЦИЯ location

### 5.1 Адрес (КРИТИЧНО!)

- [ ] **5.1.1** `address_line_1` - string или null
- [ ] **5.1.2** `address_line_2` - string или null
- [ ] **5.1.3** ✅ **БЛОКЕР:** `city` - string (НЕ null), REQUIRED
- [ ] **5.1.4** `county` - string или null
- [ ] **5.1.5** ✅ **БЛОКЕР:** `postcode` - string (НЕ null), pattern, REQUIRED
- [ ] **5.1.6** `region` - string или null
- [ ] **5.1.7** ✅ **ВАЖНО:** `local_authority` - string или null (ДОЛЖНО присутствовать!)

**Оценка раздела 5.1:** ___/7

---

### 5.2 Координаты

- [ ] **5.2.1** `latitude` - number или null
- [ ] **5.2.2** `longitude` - number или null
- [ ] **5.2.3** Есть `"description"` с упоминанием UK диапазонов

**Важно:** Тип должен быть `["number", "null"]`, НЕ `["string", "null"]`!

**Оценка раздела 5.2:** ___/3

---

### 5.3 Контекст локации

- [ ] **5.3.1** Есть вложенная секция `location_context` (объект)
- [ ] **5.3.2** `location_context.nearby_amenities` - array или null
- [ ] **5.3.3** `location_context.transport_links` - array или null
- [ ] **5.3.4** `location_context.area_description` - string или null

**Оценка раздела 5.3:** ___/4

---

## РАЗДЕЛ 6: СЕКЦИЯ capacity

### 6.1 Поля capacity

- [ ] **6.1.1** `beds_total` - integer или null
- [ ] **6.1.2** `beds_available` - integer или null
- [ ] **6.1.3** `year_opened` - integer или null
- [ ] **6.1.4** `year_registered` - integer или null

**Важно:** Тип должен быть `["integer", "null"]`, НЕ `["number", "null"]` и НЕ `["string", "null"]`!

**Оценка раздела 6.1:** ___/4

---

## РАЗДЕЛ 7: СЕКЦИЯ care_services (КРИТИЧНО!)

### 7.1 Основные типы ухода

- [ ] **7.1.1** ✅ **ВАЖНО:** `residential_care` - boolean или null
- [ ] **7.1.2** ✅ **ВАЖНО:** `nursing_care` - boolean или null
- [ ] **7.1.3** ✅ **ВАЖНО:** `dementia_care` - boolean или null
- [ ] **7.1.4** `respite_care` - boolean или null
- [ ] **7.1.5** `palliative_care` - boolean или null
- [ ] **7.1.6** `day_care` - boolean или null

**Важно:** Секция `care_services` должна быть **ОТДЕЛЬНОЙ** от `licenses`!

**Оценка раздела 7.1:** ___/6

---

## РАЗДЕЛ 8: СЕКЦИЯ licenses (КРИТИЧНО!) 🔴

### 8.1 Структура licenses

- [ ] **8.1.1** ✅ **БЛОКЕР:** Секция `licenses` существует и **ОТДЕЛЬНА** от `care_services`
- [ ] **8.1.2** ✅ **БЛОКЕР:** `licenses` находится на **верхнем уровне** (не вложена в care_services)

**Проверка:**
```bash
grep -n '"licenses"' response_format.json
grep -n '"care_services"' response_format.json
# Должны быть на одном уровне вложенности!
```

**Оценка раздела 8.1:** ___/2

---

### 8.2 Поля licenses

- [ ] **8.2.1** ✅ **КРИТИЧНО:** `nursing_care` - boolean или null
- [ ] **8.2.2** ✅ **КРИТИЧНО:** `personal_care` - boolean или null
- [ ] **8.2.3** `surgical_procedures` - boolean или null
- [ ] **8.2.4** `treatment_of_disease` - boolean или null
- [ ] **8.2.5** `diagnostic_procedures` - boolean или null

**Важно:** Эти поля отражают **официальные лицензии CQC** (regulated activities), а НЕ типы услуг!

**Оценка раздела 8.2:** ___/5

---

### 8.3 Описания полей licenses

- [ ] **8.3.1** `licenses.nursing_care` имеет `"description"` с упоминанием "CQC regulated activity"
- [ ] **8.3.2** `licenses.personal_care` имеет `"description"` с упоминанием "CQC regulated activity"
- [ ] **8.3.3** В description есть отличие от `care_services.*`

**Пример правильного description:**
```json
"nursing_care": {
  "type": ["boolean", "null"],
  "description": "Official CQC license for Nursing Care (regulated activity). NOT the same as care_services.nursing_care which is marketing."
}
```

**Оценка раздела 8.3:** ___/3

---

## РАЗДЕЛ 9: СЕКЦИЯ user_categories (КРИТИЧНО!) 🔴

### 9.1 Названия полей (КРИТИЧНО!)

**🆕 v2.2 UPDATE:** БД v2.2 требует ВСЕ 12 полей Service User Bands (5 старых + 7 новых)

**Старые 5 полей (v2.1):**
- [ ] **9.1.1** ✅ **БЛОКЕР:** Есть поле `serves_older_people` (НЕ `serves_elderly`!)
- [ ] **9.1.2** Есть поле `serves_younger_adults`
- [ ] **9.1.3** Есть поле `serves_mental_health`
- [ ] **9.1.4** Есть поле `serves_physical_disabilities`
- [ ] **9.1.5** Есть поле `serves_sensory_impairments`

**🆕 НОВЫЕ 7 полей (v2.2) - КРИТИЧНО:**
- [ ] **9.1.6** ✅ **БЛОКЕР:** Есть поле `serves_dementia_band` (NEW v2.2)
- [ ] **9.1.7** ✅ **БЛОКЕР:** Есть поле `serves_children` (NEW v2.2)
- [ ] **9.1.8** ✅ **БЛОКЕР:** Есть поле `serves_learning_disabilities` (NEW v2.2)
- [ ] **9.1.9** ✅ **БЛОКЕР:** Есть поле `serves_detained_mha` (NEW v2.2)
- [ ] **9.1.10** ✅ **БЛОКЕР:** Есть поле `serves_substance_misuse` (NEW v2.2)
- [ ] **9.1.11** ✅ **БЛОКЕР:** Есть поле `serves_eating_disorders` (NEW v2.2)
- [ ] **9.1.12** ✅ **БЛОКЕР:** Есть поле `serves_whole_population` (NEW v2.2)

**Проверка:**
```bash
grep '"serves_' response_format.json | grep -o '"serves_[a-z_]*"' | sort -u
```

**Ожидается (12 полей):**
```
"serves_children"
"serves_dementia_band"
"serves_detained_mha"
"serves_eating_disorders"
"serves_learning_disabilities"
"serves_mental_health"
"serves_older_people"
"serves_physical_disabilities"
"serves_sensory_impairments"
"serves_substance_misuse"
"serves_whole_population"
"serves_younger_adults"
```

**❌ КРИТИЧЕСКАЯ ОШИБКА ЕСЛИ:**
```json
"serves_elderly"  // ❌ Неправильное название!
"serves_dementia" // ❌ Это не категория пользователей!
// ❌ Отсутствуют 7 новых полей v2.2
```

**Оценка раздела 9.1:** ___/12

---

### 9.2 Типы полей user_categories

- [ ] **9.2.1** Все поля имеют тип `["boolean", "null"]`
- [ ] **9.2.2** Все поля имеют `"description"`
- [ ] **9.2.3** 🆕 Новые поля v2.2 помечены как "NEW v2.2" в description

**Оценка раздела 9.2:** ___/3

---

## РАЗДЕЛ 10: СЕКЦИЯ pricing

### 10.1 Структура pricing

- [ ] **10.1.1** Есть вложенная секция `residential_care` (объект)
- [ ] **10.1.2** Есть вложенная секция `nursing_care` (объект)
- [ ] **10.1.3** Есть вложенная секция `dementia_care` (объект)
- [ ] **10.1.4** Есть вложенная секция `respite_care` (объект)

**Оценка раздела 10.1:** ___/4

---

### 10.2 Поля внутри каждого типа pricing

Для каждой секции (residential_care, nursing_care, и т.д.):

- [ ] **10.2.1** `fee_from` - number или null
- [ ] **10.2.2** `fee_to` - number или null
- [ ] **10.2.3** `fee_period` - string или null (enum: "per week", "per month")
- [ ] **10.2.4** `notes` - string или null

**Оценка раздела 10.2:** ___/4

---

## РАЗДЕЛ 11: СЕКЦИЯ funding

### 11.1 Поля funding

- [ ] **11.1.1** `self_funding` - boolean или null
- [ ] **11.1.2** `local_authority` - boolean или null
- [ ] **11.1.3** `nhs_continuing_healthcare` - boolean или null
- [ ] **11.1.4** `third_party_topup` - boolean или null

**Оценка раздела 11.1:** ___/4

---

## РАЗДЕЛ 12: СЕКЦИЯ building_and_facilities (КРИТИЧНО!)

### 12.1 Плоские поля (НЕ вложенные!)

- [ ] **12.1.1** ✅ **КРИТИЧНО:** `wheelchair_access` находится на **верхнем уровне** секции (НЕ в `accessibility.wheelchair_access`)
- [ ] **12.1.2** ✅ **КРИТИЧНО:** `ensuite_rooms` находится на **верхнем уровне** (boolean)
- [ ] **12.1.3** `secure_garden` находится на верхнем уровне
- [ ] **12.1.4** `wifi_available` находится на верхнем уровне
- [ ] **12.1.5** `parking_onsite` находится на верхнем уровне

**Правильная структура:**
```json
"building_and_facilities": {
  "type": "object",
  "properties": {
    "wheelchair_access": {"type": ["boolean", "null"]},  // Верхний уровень!
    "ensuite_rooms": {"type": ["boolean", "null"]},      // Верхний уровень!
    "building_details": {                                 // Вложенный объект для JSONB
      "type": "object",
      "properties": {
        "number_of_ensuite_rooms": {"type": ["integer", "null"]}
      }
    }
  }
}
```

**❌ НЕПРАВИЛЬНАЯ структура:**
```json
"building_and_facilities": {
  "accessibility": {  // ❌ Лишний уровень вложенности!
    "wheelchair_access": {...}
  }
}
```

**Оценка раздела 12.1:** ___/5

---

### 12.2 Вложенная секция building_details

- [ ] **12.2.1** Есть вложенная секция `building_details` (объект для JSONB)
- [ ] **12.2.2** `building_details.number_of_ensuite_rooms` - integer или null
- [ ] **12.2.3** `building_details.number_of_floors` - integer или null
- [ ] **12.2.4** `building_details.lift_available` - boolean или null
- [ ] **12.2.5** `building_details.garden_available` - boolean или null
- [ ] **12.2.6** `building_details.outdoor_space` - boolean или null
- [ ] **12.2.7** `building_details.communal_areas` - array или null
- [ ] **12.2.8** `building_details.safety_features` - array или null
- [ ] **12.2.9** `building_details.infection_control` - string или null
- [ ] **12.2.10** `building_details.sustainability` - string или null

**Оценка раздела 12.2:** ___/10

---

## РАЗДЕЛ 13: СЕКЦИЯ medical_specialisms

### 13.1 Структура medical_specialisms

- [ ] **13.1.1** Есть вложенная секция `nursing_specialisms` (объект)
- [ ] **13.1.2** Есть вложенная секция `dementia_types` (объект)
- [ ] **13.1.3** Есть вложенная секция `dementia_behaviour` (объект)
- [ ] **13.1.4** Есть вложенная секция `disability_support` (объект)
- [ ] **13.1.5** Есть вложенная секция `medication_support` (объект)
- [ ] **13.1.6** Есть вложенная секция `special_support` (объект)

**Оценка раздела 13.1:** ___/6

---

### 13.2 nursing_specialisms (минимум 13 полей)

- [ ] **13.2.1** `parkinsons_care` - boolean или null
- [ ] **13.2.2** `stroke_rehabilitation` - boolean или null
- [ ] **13.2.3** `diabetes_management` - boolean или null
- [ ] **13.2.4** `heart_conditions` - boolean или null
- [ ] **13.2.5** `respiratory_conditions` - boolean или null
- [ ] **13.2.6** `cancer_care` - boolean или null
- [ ] **13.2.7** `palliative_end_of_life` - boolean или null
- [ ] **13.2.8** `catheter_care` - boolean или null
- [ ] **13.2.9** `stoma_care` - boolean или null
- [ ] **13.2.10** `peg_feeding` - boolean или null
- [ ] **13.2.11** `wound_care` - boolean или null
- [ ] **13.2.12** `pressure_sore_management` - boolean или null
- [ ] **13.2.13** `pain_management` - boolean или null

**Оценка раздела 13.2:** ___/13

---

### 13.3 dementia_types (минимум 5 полей)

- [ ] **13.3.1** `alzheimers` - boolean или null
- [ ] **13.3.2** `vascular_dementia` - boolean или null
- [ ] **13.3.3** `lewy_body_dementia` - boolean или null
- [ ] **13.3.4** `frontotemporal_dementia` - boolean или null
- [ ] **13.3.5** `mixed_dementia` - boolean или null

**Оценка раздела 13.3:** ___/5

---

### 13.4 dementia_behaviour (минимум 5 полей)

- [ ] **13.4.1** `challenging_behaviour` - boolean или null
- [ ] **13.4.2** `wandering` - boolean или null
- [ ] **13.4.3** `aggression` - boolean или null
- [ ] **13.4.4** `sundowning` - boolean или null
- [ ] **13.4.5** `memory_loss` - boolean или null

**Оценка раздела 13.4:** ___/5

---

### 13.5 disability_support (минимум 8 полей)

- [ ] **13.5.1** `physical_disabilities` - boolean или null
- [ ] **13.5.2** `learning_disabilities` - boolean или null
- [ ] **13.5.3** `visual_impairment` - boolean или null
- [ ] **13.5.4** `hearing_impairment` - boolean или null
- [ ] **13.5.5** `mobility_issues` - boolean или null
- [ ] **13.5.6** `wheelchair_users` - boolean или null
- [ ] **13.5.7** `multiple_sclerosis` - boolean или null
- [ ] **13.5.8** `motor_neurone_disease` - boolean или null

**Оценка раздела 13.5:** ___/8

---

### 13.6 medication_support (минимум 4 полей)

- [ ] **13.6.1** `medication_management` - boolean или null
- [ ] **13.6.2** `complex_medication` - boolean или null
- [ ] **13.6.3** `medication_administration` - boolean или null
- [ ] **13.6.4** `controlled_drugs` - boolean или null

**Оценка раздела 13.6:** ___/4

---

### 13.7 special_support (минимум 8 полей)

- [ ] **13.7.1** `mental_health_conditions` - boolean или null
- [ ] **13.7.2** `depression` - boolean или null
- [ ] **13.7.3** `anxiety` - boolean или null
- [ ] **13.7.4** `bipolar_disorder` - boolean или null
- [ ] **13.7.5** `schizophrenia` - boolean или null
- [ ] **13.7.6** `eating_disorders` - boolean или null
- [ ] **13.7.7** `substance_misuse` - boolean или null
- [ ] **13.7.8** `acquired_brain_injury` - boolean или null

**Оценка раздела 13.7:** ___/8

---

## РАЗДЕЛ 14: СЕКЦИЯ dietary_options

### 14.1 Структура dietary_options

- [ ] **14.1.1** Есть вложенная секция `special_diets` (объект)
- [ ] **14.1.2** Есть вложенная секция `cultural_religious` (объект)
- [ ] **14.1.3** Есть вложенная секция `food_standards` (объект)

**Оценка раздела 14.1:** ___/3

---

### 14.2 special_diets (минимум 8 полей)

- [ ] **14.2.1** `vegetarian` - boolean или null
- [ ] **14.2.2** `vegan` - boolean или null
- [ ] **14.2.3** `gluten_free` - boolean или null
- [ ] **14.2.4** `dairy_free` - boolean или null
- [ ] **14.2.5** `diabetic_diet` - boolean или null
- [ ] **14.2.6** `low_sodium` - boolean или null
- [ ] **14.2.7** `pureed_food` - boolean или null
- [ ] **14.2.8** `soft_food` - boolean или null

**Оценка раздела 14.2:** ___/8

---

### 14.3 cultural_religious (минимум 4 полей)

- [ ] **14.3.1** `halal` - boolean или null
- [ ] **14.3.2** `kosher` - boolean или null
- [ ] **14.3.3** `hindu` - boolean или null
- [ ] **14.3.4** `sikh` - boolean или null

**Оценка раздела 14.3:** ___/4

---

### 14.4 food_standards (минимум 4 полей)

- [ ] **14.4.1** `food_hygiene_rating` - integer или null (0-5)
- [ ] **14.4.2** `fresh_food_daily` - boolean или null
- [ ] **14.4.3** `choice_of_meals` - boolean или null
- [ ] **14.4.4** `resident_input_menu` - boolean или null

**Оценка раздела 14.4:** ___/4

---

## РАЗДЕЛ 15: СЕКЦИЯ activities

### 15.1 Структура activities

- [ ] **15.1.1** Есть вложенная секция `physical_activities` (объект)
- [ ] **15.1.2** Есть вложенная секция `creative_activities` (объект)
- [ ] **15.1.3** Есть вложенная секция `social_activities` (объект)
- [ ] **15.1.4** Есть вложенная секция `cognitive_activities` (объект)

**Оценка раздела 15.1:** ___/4

---

### 15.2 Поля activities (минимум 14 полей всего)

- [ ] **15.2.1** `physical_activities.exercise_classes` - boolean или null
- [ ] **15.2.2** `physical_activities.walking_groups` - boolean или null
- [ ] **15.2.3** `physical_activities.gardening` - boolean или null
- [ ] **15.2.4** `creative_activities.arts_crafts` - boolean или null
- [ ] **15.2.5** `creative_activities.music_therapy` - boolean или null
- [ ] **15.2.6** `creative_activities.singing` - boolean или null
- [ ] **15.2.7** `social_activities.group_outings` - boolean или null
- [ ] **15.2.8** `social_activities.entertainment` - boolean или null
- [ ] **15.2.9** `social_activities.visiting_speakers` - boolean или null
- [ ] **15.2.10** `social_activities.religious_services` - boolean или null
- [ ] **15.2.11** `cognitive_activities.memory_games` - boolean или null
- [ ] **15.2.12** `cognitive_activities.reading_groups` - boolean или null
- [ ] **15.2.13** `cognitive_activities.puzzles` - boolean или null
- [ ] **15.2.14** `cognitive_activities.reminiscence_therapy` - boolean или null

**Оценка раздела 15.2:** ___/14

---

## РАЗДЕЛ 16: СЕКЦИЯ staff_information

### 16.1 Поля staff_information (минимум 4 полей)

- [ ] **16.1.1** `staff_ratio` - string или null
- [ ] **16.1.2** `nurse_on_duty` - string или null (enum: "24/7", "day only", "on call")
- [ ] **16.1.3** `staff_training` - array или null
- [ ] **16.1.4** `staff_qualifications` - array или null

**Оценка раздела 16.1:** ___/4

---

## РАЗДЕЛ 16.5: СЕКЦИЯ regulated_activities (🆕 v2.2 - КРИТИЧНО!) 🔴

### 16.5.1 Структура regulated_activities

- [ ] **16.5.1** ✅ **БЛОКЕР:** Секция `regulated_activities` существует
- [ ] **16.5.2** ✅ **БЛОКЕР:** Есть вложенная секция `activities` (массив)
- [ ] **16.5.3** ✅ **БЛОКЕР:** Каждый элемент массива имеет поля `activity_id`, `activity_name`, `is_active`

**Оценка раздела 16.5.1:** ___/3

---

### 16.5.2 Поля regulated_activities

- [ ] **16.5.4** ✅ **БЛОКЕР:** Поле `activity_id` имеет `enum` с 14 значениями
- [ ] **16.5.5** Поле `activity_name` - string
- [ ] **16.5.6** Поле `is_active` - boolean или null

**Ожидаемые activity_id enum значения (14):**
```
"nursing_care"
"personal_care"
"accommodation_nursing"
"accommodation_treatment"
"assessment_medical"
"diagnostic_screening"
"family_planning"
"blood_management"
"maternity_midwifery"
"surgical_procedures"
"termination_pregnancies"
"transport_triage"
"treatment_disease"
"slimming_clinics"
```

**Оценка раздела 16.5.2:** ___/3

---

### 16.5.3 Описания regulated_activities

- [ ] **16.5.7** Секция имеет description с упоминанием "v2.2" и "JSONB"
- [ ] **16.5.8** Description указывает маппинг в `regulated_activities JSONB field`

**Оценка раздела 16.5.3:** ___/2

---

## РАЗДЕЛ 17: СЕКЦИЯ cqc_ratings (КРИТИЧНО!) 🔴

### 17.1 Основные рейтинги (6 категорий)

- [ ] **17.1.1** ✅ **КРИТИЧНО:** `overall` - string или null
- [ ] **17.1.2** `safe` - string или null
- [ ] **17.1.3** `effective` - string или null
- [ ] **17.1.4** `caring` - string или null
- [ ] **17.1.5** `responsive` - string или null
- [ ] **17.1.6** `well_led` - string или null

**Оценка раздела 17.1:** ___/6

---

### 17.2 Enum для рейтингов

- [ ] **17.2.1** Все рейтинги имеют `"enum"` с допустимыми значениями
- [ ] **17.2.2** Enum включает: `"outstanding"`, `"good"`, `"requires improvement"`, `"inadequate"`, `"not rated"`, `null`

**Пример:**
```json
"overall": {
  "type": ["string", "null"],
  "enum": ["outstanding", "good", "requires improvement", "inadequate", "not rated", null],
  "description": "Overall CQC rating"
}
```

**Оценка раздела 17.2:** ___/2

---

### 17.3 Даты и отчеты

- [ ] **17.3.1** `last_inspection_date` - string или null (ISO 8601 date)
- [ ] **17.3.2** `publication_date` - string или null (ISO 8601 date)
- [ ] **17.3.3** `latest_report_url` - string или null (URL)

**Оценка раздела 17.3:** ___/3

---

## РАЗДЕЛ 18: СЕКЦИЯ reviews (КРИТИЧНО!) 🔴

### 18.1 Поля reviews (минимум 3 полей)

- [ ] **18.1.1** ✅ **КРИТИЧНО:** `average_score` - number или null
- [ ] **18.1.2** ✅ **КРИТИЧНО:** `count` - integer или null
- [ ] **18.1.3** ✅ **КРИТИЧНО:** `google_rating` - number или null

**Важно:** Эти поля ДОЛЖНЫ присутствовать! Они были пропущены в ранних версиях.

**Оценка раздела 18.1:** ___/3

---

## РАЗДЕЛ 19: СЕКЦИЯ media (КРИТИЧНО!) 🔴

### 19.1 Поля media (минимум 3 полей)

- [ ] **19.1.1** ✅ **КРИТИЧНО:** `images` - array или null (массив URL изображений)
- [ ] **19.1.2** ✅ **КРИТИЧНО:** `virtual_tour` - string или null (URL виртуального тура)
- [ ] **19.1.3** ✅ **КРИТИЧНО:** `video_url` - string или null (URL видео)

**Важно:** Эти поля ДОЛЖНЫ присутствовать! Они были пропущены в ранних версиях.

**Оценка раздела 19.1:** ___/3

---

## РАЗДЕЛ 20: СЕКЦИЯ availability

### 20.1 Поля availability

- [ ] **20.1.1** `status` - string или null (enum: "available", "limited", "full", "closed")
- [ ] **20.1.2** `last_checked` - string или null (ISO 8601 date)
- [ ] **20.1.3** `is_dormant` - boolean или null

**Оценка раздела 20.1:** ___/3

---

## РАЗДЕЛ 21: СЕКЦИЯ accreditations

### 21.1 Поля accreditations

- [ ] **21.1.1** `accreditations` - array или null (массив объектов)
- [ ] **21.1.2** Каждый объект в массиве имеет поля: `name`, `issuer`, `date_awarded`

**Оценка раздела 21.1:** ___/2

---

## РАЗДЕЛ 22: СЕКЦИЯ source_metadata

### 22.1 Поля source_metadata

- [ ] **22.1.1** `source` - string, REQUIRED (значение: "autumna")
- [ ] **22.1.2** `source_url` - string, REQUIRED (URL страницы)
- [ ] **22.1.3** `scraped_at` - string, REQUIRED (ISO 8601 timestamp)
- [ ] **22.1.4** `extraction_confidence` - number или null (0.0-1.0)

**Оценка раздела 22.1:** ___/4

---

## РАЗДЕЛ 23: SYSTEM PROMPT - БАЗОВАЯ СТРУКТУРА

### 23.1 Метаданные промпта

- [ ] **23.1.1** Есть заголовок с названием промпта
- [ ] **23.1.2** Есть версия промпта (например, v2.3)
- [ ] **23.1.3** Есть дата последнего обновления
- [ ] **23.1.4** Есть краткое описание задачи

**Оценка раздела 23.1:** ___/4

---

### 23.2 Структура промпта

- [ ] **23.2.1** Есть секция "TASK" или "OBJECTIVE" с описанием задачи
- [ ] **23.2.2** Есть секция "INPUT" с описанием входных данных (HTML)
- [ ] **23.2.3** Есть секция "OUTPUT" с описанием выходных данных (JSON)
- [ ] **23.2.4** Есть секция "GOLDEN RULES" или "KEY PRINCIPLES"
- [ ] **23.2.5** Есть секция "PRIORITY FIELDS" или "CRITICAL FIELDS"
- [ ] **23.2.6** Есть секция "EXTRACTION GUIDELINES" или "INSTRUCTIONS"
- [ ] **23.2.7** Есть секция "EXAMPLES" с примерами HTML → JSON

**Оценка раздела 23.2:** ___/7

---

## РАЗДЕЛ 24: SYSTEM PROMPT - КРИТИЧЕСКИЕ ИНСТРУКЦИИ 🔴

### 24.1 Обязательные поля (GOLDEN RULE #1)

- [ ] **24.1.1** ✅ **БЛОКЕР:** Есть ЯВНАЯ инструкция о том, что `cqc_location_id` ОБЯЗАТЕЛЕН
- [ ] **24.1.2** ✅ **БЛОКЕР:** Есть инструкция о том, что система упадет без `cqc_location_id`
- [ ] **24.1.3** ✅ **БЛОКЕР:** Есть инструкция о том, что `name`, `city`, `postcode` ОБЯЗАТЕЛЬНЫ
- [ ] **24.1.4** Есть инструкция о том, что делать если обязательное поле отсутствует

**Пример правильной инструкции:**
```markdown
GOLDEN RULE #1: Critical Fields (SYSTEM WILL FAIL WITHOUT THESE!)

The following fields are ABSOLUTELY REQUIRED:
- identity.cqc_location_id (format: 1-XXXXXXXXXX)
- identity.name
- location.city
- location.postcode

If any of these fields cannot be extracted, the system will REJECT the record.
DO NOT leave these fields as null or empty string!
```

**Оценка раздела 24.1:** ___/4

---

### 24.2 Извлечение cqc_location_id (GOLDEN RULE #2)

- [ ] **24.2.1** ✅ **БЛОКЕР:** Есть инструкция по извлечению `cqc_location_id` из URL
- [ ] **24.2.2** Есть пример URL паттерна: `autumna.co.uk/care-homes/{slug}/1-XXXXXXXXXX`
- [ ] **24.2.3** Есть инструкция по извлечению из текста страницы
- [ ] **24.2.4** Есть инструкция по извлечению из structured data (schema.org)
- [ ] **24.2.5** Есть приоритет источников (URL > structured data > visible text)

**Пример правильной инструкции:**
```markdown
GOLDEN RULE #2: Extracting cqc_location_id

Priority order:
1. URL pattern: autumna.co.uk/care-homes/{slug}/1-XXXXXXXXXX
2. Structured data: <meta property="cqc:locationId" content="1-XXXXXXXXXX">
3. Visible text: "CQC Location ID: 1-XXXXXXXXXX"

Format: MUST be 1-XXXXXXXXXX (1 + dash + 10 digits)
```

**Оценка раздела 24.2:** ___/5

---

### 24.3 Различие licenses vs care_services (GOLDEN RULE #3) 🔴

- [ ] **24.3.1** ✅ **БЛОКЕР:** Есть ЯВНОЕ объяснение различия `licenses` vs `care_services`
- [ ] **24.3.2** ✅ **БЛОКЕР:** Есть объяснение что `licenses` = "what home is LEGALLY ALLOWED to do"
- [ ] **24.3.3** ✅ **БЛОКЕР:** Есть объяснение что `care_services` = "what home OFFERS (marketing)"
- [ ] **24.3.4** ✅ **БЛОКЕР:** Есть примеры HTML паттернов для `licenses`
- [ ] **24.3.5** ✅ **БЛОКЕР:** Есть примеры HTML паттернов для `care_services`
- [ ] **24.3.6** ✅ **БЛОКЕР:** Есть предупреждение "NEVER map service types to license fields!"

**Пример правильной инструкции:**
```markdown
GOLDEN RULE #3: Licenses vs Care Services (CRITICAL LEGAL DISTINCTION!)

licenses.* = What the home is LEGALLY ALLOWED to do (CQC regulated activities)
care_services.* = What the home OFFERS (marketing, positioning)

Example HTML patterns:
- "Regulated Activities: Nursing Care" → licenses.nursing_care = true
- "Services: Nursing Care" → care_services.nursing_care = true
- "We provide nursing care" → care_services.nursing_care = true (NOT licenses!)

NEVER map service types to license fields! This is a LEGAL issue.
```

**Оценка раздела 24.3:** ___/6

---

### 24.4 user_categories (GOLDEN RULE #4)

**🆕 v2.2 UPDATE:** Проверить инструкции для ВСЕХ 12 полей (5 старых + 7 новых)

- [ ] **24.4.1** ✅ **КРИТИЧНО:** Есть инструкция по деривации `serves_older_people`
- [ ] **24.4.2** Есть пример: "If age 65+ mentioned → serves_older_people = true"
- [ ] **24.4.3** Есть инструкция по деривации из `medical_specialisms`
- [ ] **24.4.4** Есть пример: "If dementia care → serves_older_people = true"
- [ ] **24.4.5** Есть инструкция по деривации `serves_younger_adults`
- [ ] **24.4.6** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_dementia_band` (NEW v2.2)
- [ ] **24.4.7** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_children` (NEW v2.2)
- [ ] **24.4.8** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_learning_disabilities` (NEW v2.2)
- [ ] **24.4.9** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_detained_mha` (NEW v2.2)
- [ ] **24.4.10** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_substance_misuse` (NEW v2.2)
- [ ] **24.4.11** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_eating_disorders` (NEW v2.2)
- [ ] **24.4.12** 🆕 ✅ **БЛОКЕР:** Есть инструкция по деривации `serves_whole_population` (NEW v2.2)

**Оценка раздела 24.4:** ___/12

---

### 24.5 local_authority (GOLDEN RULE #5)

- [ ] **24.5.1** ✅ **ВАЖНО:** Есть инструкция по извлечению `local_authority`
- [ ] **24.5.2** Есть примеры паттернов: "Birmingham City Council", "Royal Borough of..."
- [ ] **24.5.3** Есть приоритет источников (structured data > visible text > address parsing)

**Пример правильной инструкции:**
```markdown
GOLDEN RULE #5: Extracting local_authority

Priority order:
1. Structured data: <meta property="localAuthority" content="...">
2. Visible text: "Registered with Birmingham City Council"
3. Address parsing: Extract from county/region

Examples:
- "Birmingham City Council"
- "Royal Borough of Kensington and Chelsea"
- "London Borough of Camden"
```

**Оценка раздела 24.5:** ___/3

---

## РАЗДЕЛ 25: SYSTEM PROMPT - EXTRACTION GUIDELINES

### 25.1 Координаты

- [ ] **25.1.1** Есть инструкция по извлечению `latitude` и `longitude`
- [ ] **25.1.2** Есть упоминание UK диапазонов (lat 49-61, lon -8 to 2)
- [ ] **25.1.3** Есть инструкция по извлечению из schema.org
- [ ] **25.1.4** Есть инструкция по извлечению из Google Maps embed
- [ ] **25.1.5** Есть приоритет источников

**Оценка раздела 25.1:** ___/5

---

### 25.2 CQC ratings

- [ ] **25.2.1** Есть инструкция по извлечению 6 категорий рейтингов
- [ ] **25.2.2** Есть список допустимых значений (outstanding, good, requires improvement, inadequate, not rated)
- [ ] **25.2.3** Есть инструкция по извлечению дат инспекций
- [ ] **25.2.4** Есть инструкция по извлечению URL отчета CQC

**Оценка раздела 25.2:** ___/4

---

### 25.3 Reviews

- [ ] **25.3.1** Есть инструкция по извлечению `average_score`
- [ ] **25.3.2** Есть инструкция по извлечению `count`
- [ ] **25.3.3** Есть инструкция по извлечению `google_rating`
- [ ] **25.3.4** Есть примеры HTML паттернов для отзывов

**Оценка раздела 25.3:** ___/4

---

### 25.4 Media

- [ ] **25.4.1** Есть инструкция по извлечению изображений (images[])
- [ ] **25.4.2** Есть инструкция по извлечению virtual tour URL
- [ ] **25.4.3** Есть инструкция по извлечению video URL
- [ ] **25.4.4** Есть примеры HTML паттернов для media

**Оценка раздела 25.4:** ___/4

---

### 25.5 Pricing

- [ ] **25.5.1** Есть инструкция по извлечению `fee_from` и `fee_to`
- [ ] **25.5.2** Есть инструкция по определению `fee_period` (per week / per month)
- [ ] **25.5.3** Есть инструкция по обработке диапазонов цен
- [ ] **25.5.4** Есть примеры: "£1,200 - £1,500 per week"

**Оценка раздела 25.5:** ___/4

---

### 25.6 Medical specialisms

- [ ] **25.6.1** Есть инструкция по извлечению nursing_specialisms
- [ ] **25.6.2** Есть инструкция по извлечению dementia_types
- [ ] **25.6.3** Есть инструкция по извлечению disability_support
- [ ] **25.6.4** Есть примеры HTML паттернов

**Оценка раздела 25.6:** ___/4

---

### 25.7 Dietary options

- [ ] **25.7.1** Есть инструкция по извлечению special_diets
- [ ] **25.7.2** Есть инструкция по извлечению cultural_religious
- [ ] **25.7.3** Есть инструкция по извлечению food_standards

**Оценка раздела 25.7:** ___/3

---

### 25.8 Activities

- [ ] **25.8.1** Есть инструкция по категоризации activities (physical, creative, social, cognitive)
- [ ] **25.8.2** Есть примеры для каждой категории

**Оценка раздела 25.8:** ___/2

---

### 25.9 Staff information

- [ ] **25.9.1** Есть инструкция по извлечению `staff_ratio`
- [ ] **25.9.2** Есть инструкция по извлечению `nurse_on_duty`
- [ ] **25.9.3** Есть примеры паттернов

**Оценка раздела 25.9:** ___/3

---

### 25.10 Regulated Activities JSONB (🆕 v2.2)

- [ ] **25.10.1** 🆕 ✅ **БЛОКЕР:** Есть инструкция по извлечению `regulated_activities` JSONB
- [ ] **25.10.2** 🆕 ✅ **БЛОКЕР:** Есть список всех 14 CQC regulated activities
- [ ] **25.10.3** 🆕 Есть описание структуры `{"activities": [{"activity_id": ..., "activity_name": ..., "is_active": ...}]}`
- [ ] **25.10.4** 🆕 Есть инструкция по определению `is_active` (true/false/omit)
- [ ] **25.10.5** 🆕 Есть примеры HTML паттернов для regulated activities

**Оценка раздела 25.10:** ___/5

---

## РАЗДЕЛ 26: SYSTEM PROMPT - DATA QUALITY

### 26.1 Обработка отсутствующих данных

- [ ] **26.1.1** Есть инструкция о том, что делать если поле не найдено
- [ ] **26.1.2** Есть инструкция о том, когда использовать `null`
- [ ] **26.1.3** Есть инструкция о том, когда использовать пустой массив `[]`
- [ ] **26.1.4** Есть предупреждение "DO NOT hallucinate data!"

**Оценка раздела 26.1:** ___/4

---

### 26.2 Extraction confidence

- [ ] **26.2.1** Есть инструкция по вычислению `extraction_confidence` (0.0-1.0)
- [ ] **26.2.2** Есть критерии для разных уровней confidence
- [ ] **26.2.3** Есть примеры

**Пример:**
```markdown
extraction_confidence:
- 1.0: All critical fields present, data clearly visible
- 0.8: Critical fields present, some optional fields missing
- 0.6: Some critical fields missing or ambiguous
- 0.4: Many fields missing, low quality HTML
- 0.2: Minimal data extracted
```

**Оценка раздела 26.2:** ___/3

---

### 26.3 is_dormant

- [ ] **26.3.1** Есть инструкция по определению `is_dormant`
- [ ] **26.3.2** Есть критерии: "closed", "no contact info", "outdated data"

**Оценка раздела 26.3:** ___/2

---

## РАЗДЕЛ 27: SYSTEM PROMPT - ПРИМЕРЫ

### 27.1 Примеры HTML → JSON

- [ ] **27.1.1** Есть минимум 1 полный пример HTML → JSON
- [ ] **27.1.2** Пример включает критические поля
- [ ] **27.1.3** Пример показывает различие licenses vs care_services
- [ ] **27.1.4** Пример показывает обработку отсутствующих данных

**Оценка раздела 27.1:** ___/4

---

### 27.2 Примеры HTML паттернов

- [ ] **27.2.1** Есть примеры HTML для `cqc_location_id`
- [ ] **27.2.2** Есть примеры HTML для `licenses` vs `care_services`
- [ ] **27.2.3** Есть примеры HTML для `local_authority`
- [ ] **27.2.4** Есть примеры HTML для координат
- [ ] **27.2.5** Есть примеры HTML для CQC ratings

**Оценка раздела 27.2:** ___/5

---

## РАЗДЕЛ 28: SYSTEM PROMPT - ТАБЛИЦА МАППИНГА

### 28.1 Таблица маппинга полей

- [ ] **28.1.1** Есть таблица с маппингом JSON → БД (опционально, но рекомендуется)
- [ ] **28.1.2** Таблица включает критические поля
- [ ] **28.1.3** Таблица показывает приоритет полей

**Оценка раздела 28.1:** ___/3

---

## ИТОГОВАЯ ОЦЕНКА

### Подсчет баллов

| Раздел | Описание | Максимум | Получено | % |
|:---|:---|---:|---:|---:|
| 1 | Базовая структура JSON Schema | 7 | ___ | ___% |
| 2 | Иерархическая структура | 20 | ___ | ___% |
| 3-5 | Критические поля (identity, location) | 21 | ___ | ___% |
| 6 | capacity | 4 | ___ | ___% |
| 7-8 | care_services + licenses | 16 | ___ | ___% |
| 9 | user_categories | 7 | ___ | ___% |
| 10-11 | pricing + funding | 8 | ___ | ___% |
| 12 | building_and_facilities | 15 | ___ | ___% |
| 13 | medical_specialisms | 49 | ___ | ___% |
| 14 | dietary_options | 15 | ___ | ___% |
| 15 | activities | 18 | ___ | ___% |
| 16 | staff_information | 4 | ___ | ___% |
| 17 | cqc_ratings | 11 | ___ | ___% |
| 18 | reviews | 3 | ___ | ___% |
| 19 | media | 3 | ___ | ___% |
| 20-22 | availability, accreditations, source_metadata | 9 | ___ | ___% |
| 16.5 | 🆕 regulated_activities (v2.2) | 8 | ___ | ___% |
| 23-24 | System Prompt: структура + критические инструкции | 43 | ___ | ___% | (was 31, +12 for new fields)
| 25 | System Prompt: extraction guidelines | 34 | ___ | ___% | (was 29, +5 for regulated_activities)
| 26 | System Prompt: data quality | 9 | ___ | ___% |
| 27-28 | System Prompt: примеры + таблица | 12 | ___ | ___% |
| **ИТОГО** | | **310** | **___** | **___%** | (was 291, +19 for v2.2 fields)

---

### Критерии оценки

| Оценка | Процент | Статус | Рекомендация |
|:---|:---:|:---|:---|
| **A+ (Отлично)** | >= 95% | ✅ Production-ready | Можно использовать |
| **A (Очень хорошо)** | 90-94% | ✅ Почти готово | Исправить мелкие недочеты |
| **B (Хорошо)** | 80-89% | ⚠️ Требуются улучшения | Исправить средние проблемы |
| **C (Удовлетворительно)** | 70-79% | ⚠️ Много проблем | Требуется доработка |
| **D (Неудовлетворительно)** | 60-69% | ❌ Критические проблемы | Серьезная доработка |
| **F (Провал)** | < 60% | ❌ Не готово | Полная переработка |

---

## 🔴 КРИТИЧЕСКИЕ БЛОКЕРЫ (если >= 1 → ПЕРЕДЕЛАТЬ!)

- [ ] ❌ **БЛОКЕР #1:** `cqc_location_id`, `city` или `postcode` nullable в JSON Schema
- [ ] ❌ **БЛОКЕР #2:** Отсутствует секция `licenses` (отдельная от `care_services`)
- [ ] ❌ **БЛОКЕР #3:** Неправильные названия в `user_categories` (`serves_elderly` вместо `serves_older_people`)
- [ ] ❌ **БЛОКЕР #3.1:** Отсутствуют 7 новых полей Service User Bands v2.2 в `user_categories`
- [ ] ❌ **БЛОКЕР #3.2:** Отсутствует секция `regulated_activities` JSONB (новое поле v2.2)
- [ ] ❌ **БЛОКЕР #4:** Отсутствуют поля `cqc_ratings` (9 полей)
- [ ] ❌ **БЛОКЕР #5:** Отсутствуют поля `reviews` (3 поля)
- [ ] ❌ **БЛОКЕР #6:** Отсутствуют поля `media` (3 поля)
- [ ] ❌ **БЛОКЕР #7:** Отсутствует поле `local_authority`
- [ ] ❌ **БЛОКЕР #8:** Неправильная структура `building_and_facilities` (лишняя вложенность)
- [ ] ❌ **БЛОКЕР #9:** Нет инструкции о различии `licenses` vs `care_services` в промпте
- [ ] ❌ **БЛОКЕР #10:** Нет инструкции о том, что `cqc_location_id` ОБЯЗАТЕЛЕН в промпте
- [ ] ❌ **БЛОКЕР #11:** 🆕 Отсутствуют инструкции для 7 новых полей Service User Bands v2.2 в промпте
- [ ] ❌ **БЛОКЕР #12:** 🆕 Нет инструкции по извлечению `regulated_activities` JSONB в промпте

**Количество блокеров:** ___

**Если >= 1 → СТАТУС: ❌ НЕ ГОТОВО, ПЕРЕДЕЛАТЬ ПРОМПТ И СХЕМУ!**

---

## НАЙДЕННЫЕ ОШИБКИ

### Критические (🔴 БЛОКЕРЫ)

1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Важные (⚠️ HIGH)

1. _______________________________________________________________
2. _______________________________________________________________
3. _______________________________________________________________

### Средние (🟡 MEDIUM)

1. _______________________________________________________________
2. _______________________________________________________________

### Мелкие (🟢 LOW)

1. _______________________________________________________________
2. _______________________________________________________________

---

## ФИНАЛЬНОЕ РЕШЕНИЕ

**Итоговая оценка:** ___% (**___** из 291)

**Статус:** 
- [ ] ✅ Production-ready (>= 95%)
- [ ] ⚠️ Требуются исправления (80-94%)
- [ ] ❌ Не готово (< 80%)

**Критические блокеры:** ___ (если >= 1 → ПЕРЕДЕЛАТЬ!)

**Рекомендация:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

**Дата проверки:** _______________

**Проверил:** _______________

---

**Конец чеклиста LLM парсинга**
