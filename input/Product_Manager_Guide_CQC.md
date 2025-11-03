# 📚 ПАМЯТКА ДЛЯ PRODUCT MANAGER: Маппинг CQC → Care Homes v2.2

**Версия:** 2.2 UPDATED  
**Дата:** 31 октября 2025  
**Назначение:** Руководство по маппингу CQC данных в БД v2.2 с полной поддержкой новых полей

---

## 📋 СОДЕРЖАНИЕ

1. [Ключевые концепции](#ключевые-концепции)
2. [ЧТО ИЗМЕНИЛОСЬ В v2.2](#что-изменилось-в-v22)
3. [Критические различия в данных CQC](#критические-различия-в-данных-cqc)
4. [Полная таблица маппинга](#полная-таблица-маппинга)
5. [7 новых полей Service User Bands](#7-новых-полей-service-user-bands)
6. [Regulated Activities JSONB](#regulated-activities-jsonb)
7. [Чеклист проверки маппинга](#чеклист-проверки-маппинга)
8. [Типичные ошибки и решения](#типичные-ошибки-и-решения)
9. [Валидация после миграции](#валидация-после-миграции)

---

## 🎯 КЛЮЧЕВЫЕ КОНЦЕПЦИИ

### Структура данных CQC

[translate:CQC] (Care Quality Commission) предоставляет данные о домах престарелых в структурированном формате с 5 основными категориями полей:

1. **Location fields** (`location_*`) — данные о конкретном доме
2. **Provider fields** (`provider_*`) — данные о компании-владельце
3. **Service Type fields** (`service_type_*`) — категория/тип ухода
4. **Regulated Activity fields** (`regulated_activity_*`) — официальные лицензии
5. **Service User Band fields** (`service_user_band_*`) — категории пациентов

### Три уровня данных

```
УРОВЕНЬ 1: LOCATION (конкретный дом)
├─ location_name → name
├─ location_city → city
├─ location_postcode → postcode
└─ location_latitude/longitude → координаты

УРОВЕНЬ 2: PROVIDER (компания-владелец)
├─ provider_name → provider_name
└─ provider_id → provider_id

УРОВЕНЬ 3: РЕГУЛЯЦИИ (лицензии и классификация)
├─ service_type_* → care_residential, care_nursing
├─ regulated_activity_* → has_nursing_care_license (🔴 КРИТИЧНО!)
└─ service_user_band_* → serves_dementia_band, serves_children, etc.
```

---

## 🆕 ЧТО ИЗМЕНИЛОСЬ В v2.2

### РАСШИРЕНИЕ: +8 новых полей

| Что | v2.1 | v2.2 | Статус |
|-----|------|------|--------|
| **Плоских полей** | 69 | 76 | +7 ✅ |
| **JSONB полей** | 16 | 17 | +1 ✅ |
| **Всего полей** | 85 | 93 | +8 ✅ |
| **Индексов** | 39 | 53 | +14 ✅ |

### НОВЫЕ КОМПОНЕНТЫ v2.2:

#### 1️⃣ **7 новых Service User Bands** (boolean)

Теперь поддерживаются ВСЕ 12 категорий пациентов:

**Старые 5 полей (v2.1):**
- ✅ `serves_older_people` (65+)
- ✅ `serves_younger_adults` (18-64)
- ✅ `serves_mental_health`
- ✅ `serves_physical_disabilities`
- ✅ `serves_sensory_impairments`

**НОВЫЕ 7 полей (v2.2):** 🆕
- 🆕 `serves_dementia_band` — принимает пациентов с деменцией
- 🆕 `serves_children` — принимает детей (редко < 1%)
- 🆕 `serves_learning_disabilities` — умственная инвалидность/аутизм
- 🆕 `serves_detained_mha` — психиатрия (Mental Health Act)
- 🆕 `serves_substance_misuse` — наркозависимость/алкоголизм
- 🆕 `serves_eating_disorders` — расстройства питания
- 🆕 `serves_whole_population` — смешанные категории

#### ⚠️ ВАЖНОЕ РАЗЛИЧИЕ:

```
care_dementia = TRUE          → дом СПЕЦИАЛИЗИРУЕТСЯ на деменции
serves_dementia_band = TRUE   → дом ПРИНИМАЕТ пациентов с деменцией

Пример: Обычный дом может care_dementia=FALSE, но serves_dementia_band=TRUE
```

#### 2️⃣ **Новое JSONB поле: regulated_activities** 🆕

Все 14 официальных CQC regulated activities теперь в одном JSONB поле:

```json
{
  "activities": [
    {"id": "nursing_care", "name": "Nursing care", "active": true},
    {"id": "personal_care", "name": "Personal care", "active": true},
    {"id": "surgical_procedures", "name": "Surgical procedures", "active": false},
    ...
    {"всего 14 типов}
  ]
}
```

**Преимущества:**
- ✅ Гибкость (можно добавить новые типы без миграции)
- ✅ Быстрый поиск через GIN индекс
- ✅ 100% покрытие CQC лицензий (было 36%, стало 100%)

#### 3️⃣ **Три новых Views** для аналитики

```sql
-- v_data_coverage — мониторинг качества данных
SELECT * FROM v_data_coverage;

-- v_service_user_bands_coverage — анализ рыночного покрытия
SELECT * FROM v_service_user_bands_coverage;

-- v_data_anomalies — выявление ошибок в данных
SELECT * FROM v_data_anomalies;
```

#### 4️⃣ **14 новых индексов**

- ✅ 22 partial индекса на boolean полях (7 новых)
- ✅ GIN индекс на `regulated_activities` JSONB
- ✅ Composite индекс на `(name_normalized, postcode)` для entity resolution

---

## 🔴 КРИТИЧЕСКИЕ РАЗЛИЧИЯ В ДАННЫХ CQC

### 1. service_type_* vs regulated_activity_* (САМОЕ ВАЖНОЕ!)

Это различие часто приводит к критическим ошибкам:

#### ❌ `service_type_*` = Категория/Классификация (НЕ лицензия!)

**Что это:**
- Описание типа услуг, которые учреждение предоставляет
- Классификация для административных целей
- **НЕ официальная лицензия**

**Примеры полей:**
- `service_type_care_home_service_with_nursing`
- `service_type_care_home_service_without_nursing`

**Когда использовать:**
- ✅ Для полей `care_nursing`, `care_residential` (тип ухода)
- ✅ Для фильтрации по типу учреждения
- ❌ **НИКОГДА для полей `has_*_license`** (лицензии)

#### ✅ `regulated_activity_*` = Официальная лицензия CQC

**Что это:**
- Официальное разрешение CQC на медицинскую деятельность
- Правовой статус учреждения
- **Обязательно для оказания соответствующей деятельности**

**Примеры полей:**
- `regulated_activity_nursing_care`
- `regulated_activity_personal_care`
- `regulated_activity_surgical_procedures`
- `regulated_activity_treatment_of_disease_disorder_or_injury`
- `regulated_activity_diagnostic_and_screening_procedures`

**Когда использовать:**
- ✅ **ТОЛЬКО для полей `has_*_license`** (лицензии)
- ✅ Для проверки юридического права на медицинскую деятельность
- ❌ **НИКОГДА для полей `care_*`** (типы ухода)

#### 📊 ПОЧЕМУ ЭТО КРИТИЧНО?

**Реальный пример:**

```
Дом "Sunset Care Home"
├─ service_type_care_home_service_with_nursing = TRUE
│  (Категория: "Дом с медсестрами")
│
└─ regulated_activity_nursing_care = FALSE
   (Лицензия на nursing: НЕТ)

Что это означает:
• Дом позиционирует себя как дом с медсестрами
• НО НЕ ИМЕЕТ официальной лицензии на nursing care
• Это ЛЕГАЛЬНО, если они не оказывают медицинские услуги
```

#### 🚨 ПОСЛЕДСТВИЯ ОШИБКИ:

**❌ Если использовать `service_type_*` для `has_nursing_care_license`:**
- Отметите 73 дома как имеющих лицензию (неправильно!)
- Пользователи будут ожидать медицинские услуги, которых нет
- Юридические риски для платформы
- Нарушение соответствия CQC

**✅ Если использовать `regulated_activity_*` для `has_nursing_care_license`:**
- Точная информация о наличии лицензии (198 из 271)
- Соответствие официальным данным CQC
- Юридическая защита платформы
- Доверие пользователей

### 2. location_* vs provider_*

#### ✅ `location_*` = Данные конкретного ДОМА (ПРИОРИТЕТ!)

**Когда использовать:**
- ✅ **ПРИОРИТЕТ** для всех полей о доме
- ✅ Всегда проверяйте сначала `location_*` поля

#### 🔄 `provider_*` = Данные компании-владельца (FALLBACK)

**Когда использовать:**
- ✅ Для полей о владельце (`provider_name`, `provider_id`)
- ✅ Как **FALLBACK** если location поле пусто
- ❌ **НЕ как основной источник**

#### 📝 Логика COALESCE:

```sql
-- ✅ ПРАВИЛЬНО: Сначала location, потом provider
COALESCE(location_web_address, provider_web_address) as website

-- ❌ НЕПРАВИЛЬНО: Только location (может быть пусто)
location_web_address as website

-- ❌ НЕПРАВИЛЬНО: Только provider (не специфично)
provider_web_address as website
```

---

## 📋 ПОЛНАЯ ТАБЛИЦА МАППИНГА

### ГРУППА 1: ИДЕНТИФИКАТОРЫ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `cqc_location_id` | `location_id` | `clean_text()` | Уникальный ID CQC |
| `location_ods_code` | `location_ods_code` | `clean_text()` | ODS код NHS |

### ГРУППА 2: БАЗОВАЯ ИНФОРМАЦИЯ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `name` | `location_name` | `clean_text()` | Название дома |
| `name_normalized` | `location_name` | `LOWER(TRIM())` | Для поиска |
| `provider_name` | `provider_name` | `clean_text()` | Компания-владелец |
| `provider_id` | `provider_id` | `clean_text()` | ID компании |
| `brand_name` | `brand_name` | `clean_text()` | Торговая марка |

### ГРУППА 3: КОНТАКТЫ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `telephone` | `location_telephone_number` | `clean_text()` | ⚠️ TEXT, НЕ NUMERIC! |
| `email` | — | NULL | Нет в CQC |
| `website` | `COALESCE(location_web_address, provider_web_address)` | `clean_text()` | ✅ Логика fallback |

### ГРУППА 4: АДРЕС И ЛОКАЦИЯ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `city` | `location_city` | `clean_text()` | NOT NULL |
| `county` | `location_county` | `clean_text()` | Графство |
| `postcode` | `location_postal_code` | `clean_text()` | Формат: "B31 2TX" |
| `latitude` | `location_latitude` | `safe_latitude()` | ✅ UK: 49-61°N |
| `longitude` | `location_longitude` | `safe_longitude()` | ✅ UK: -8 to 2°E |
| `region` | `location_region` | `clean_text()` | UK регион |
| `local_authority` | `location_local_authority` | `clean_text()` | Местный орган власти |

### ГРУППА 5: ВМЕСТИМОСТЬ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `beds_total` | `location_number_of_beds` | `safe_integer()` | CHECK: > 0 |
| `beds_available` | — | NULL | Нет в CQC (добавляется вручную) |
| `has_availability` | — | TRIGGER | Автоматически из `beds_available` |
| `year_opened` | — | NULL | Обычно нет в CQC |
| `year_registered` | `location_hsca_start_date` | `extract_year()` | Год регистрации в CQC |

### ГРУППА 6: ТИПЫ УХОДА (используют service_type_*)

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `care_residential` | `service_type_care_home_service_without_nursing` | `safe_boolean()` | ✅ Уход БЕЗ медсестер |
| `care_nursing` | `service_type_care_home_service_with_nursing` | `safe_boolean()` | ✅ Уход С медсестрами |
| `care_dementia` | `service_user_band_dementia` | `safe_boolean()` | Специализация на деменции |
| `care_respite` | — | NULL | Обычно нет прямого поля |

**Почему здесь service_type правильно:**
- Это КЛАССИФИКАЦИЯ типа ухода, а не лицензия
- Пользователи ищут дома по типу услуг
- Это категория, а не правовой статус

### ГРУППА 7: МЕДИЦИНСКИЕ ЛИЦЕНЗИИ 🔴 КРИТИЧНО!

**⚠️ Используют regulated_activity_* (ОБЯЗАТЕЛЬНО!)**

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `has_nursing_care_license` | `regulated_activity_nursing_care` | `safe_boolean()` | 🔴 НЕ service_type! |
| `has_personal_care_license` | `regulated_activity_personal_care` | `safe_boolean()` | Официальная лицензия |
| `has_surgical_procedures_license` | `regulated_activity_surgical_procedures` | `safe_boolean()` | Официальная лицензия |
| `has_treatment_license` | `regulated_activity_treatment_of_disease_disorder_or_injury` | `safe_boolean()` | Официальная лицензия |
| `has_diagnostic_license` | `regulated_activity_diagnostic_and_screening_procedures` | `safe_boolean()` | Официальная лицензия |

**Почему здесь regulated_activity ОБЯЗАТЕЛЬНО:**
- Это ОФИЦИАЛЬНЫЕ ЛИЦЕНЗИИ CQC
- Юридическое право на медицинскую деятельность
- Критично для регуляторного соответствия

### ГРУППА 8: КАТЕГОРИИ ПАЦИЕНТОВ (старые 5)

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `serves_older_people` | `service_user_band_older_people` | `safe_boolean()` | Пожилые 65+ |
| `serves_younger_adults` | `service_user_band_younger_adults` | `safe_boolean()` | Молодые 18-64 |
| `serves_mental_health` | `service_user_band_mental_health` | `safe_boolean()` | Психическое здоровье |
| `serves_physical_disabilities` | `service_user_band_physical_disability` | `safe_boolean()` | Физические нарушения |
| `serves_sensory_impairments` | `service_user_band_sensory_impairment` | `safe_boolean()` | Сенсорные нарушения |

### 🆕 ГРУППА 8B: НОВЫЕ КАТЕГОРИИ ПАЦИЕНТОВ v2.2 (+7)

| Поле v2.2 | Источник CQC | Функция | Комментарий | Частота |
|-----------|-------------|---------|-----------|---------|
| `serves_dementia_band` 🆕 | `service_user_band_dementia` | `safe_boolean()` | Принимают пациентов с деменцией | ~68% |
| `serves_children` 🆕 | `service_user_band_children_0_18_years` | `safe_boolean()` | Принимают детей | <1% |
| `serves_learning_disabilities` 🆕 | `service_user_band_learning_disabilities_or_autistic_spectrum_di` | `safe_boolean()` | Learning disabilities/аутизм | ~17% |
| `serves_detained_mha` 🆕 | `service_user_band_people_detained_under_the_mental_health_act` | `safe_boolean()` | Психиатрия (Mental Health Act) | <1% |
| `serves_substance_misuse` 🆕 | `service_user_band_people_who_misuse_drugs_and_alcohol` | `safe_boolean()` | Наркозависимость/алкоголизм | <2% |
| `serves_eating_disorders` 🆕 | `service_user_band_people_with_an_eating_disorder` | `safe_boolean()` | Расстройства питания | <1% |
| `serves_whole_population` 🆕 | `service_user_band_whole_population` | `safe_boolean()` | Смешанные категории | ~12% |

### ГРУППА 9: ФИНАНСИРОВАНИЕ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `accepts_self_funding` | `funding_* поля` | `safe_boolean()` | Частное финансирование |
| `accepts_local_authority` | `funding_* поля` | `safe_boolean()` | LA финансирование |
| `accepts_nhs_chc` | `funding_* поля` | `safe_boolean()` | NHS Continuing Healthcare |
| `accepts_third_party_topup` | — | NULL | Обычно нет прямого поля |

### ГРУППА 10: CQC РЕЙТИНГИ

| Поле v2.2 | Источник CQC | Функция | Комментарий |
|-----------|-------------|---------|-----------|
| `cqc_rating_overall` | `location_latest_overall_rating` | `normalize_cqc_rating()` | Общий рейтинг |
| `cqc_rating_safe` | `location_latest_rating_safe` | `normalize_cqc_rating()` | Рейтинг безопасности ⭐⭐⭐ |
| `cqc_rating_effective` | `location_latest_rating_effective` | `normalize_cqc_rating()` | Рейтинг эффективности |
| `cqc_rating_caring` | `location_latest_rating_caring` | `normalize_cqc_rating()` | Рейтинг заботы |
| `cqc_rating_responsive` | `location_latest_rating_responsive` | `normalize_cqc_rating()` | Рейтинг отзывчивости |
| `cqc_rating_well_led` | `location_latest_rating_well_led` | `normalize_cqc_rating()` | Рейтинг лидерства |
| `cqc_last_inspection_date` | `location_last_inspection_date` | `safe_date()` | Дата инспекции |
| `cqc_publication_date` | `publication_date` | `safe_date()` | Дата публикации |
| `cqc_latest_report_url` | `cqc_report_url` | `clean_text()` | Ссылка на отчёт |

### ГРУППА 11: ОТЗЫВЫ

| Поле v2.2 | Источник | Функция | Комментарий |
|-----------|---------|---------|-----------|
| `review_average_score` | Google/Carehome.co.uk | `safe_numeric()` | 0-5 stars |
| `review_count` | Google/Carehome.co.uk | `safe_integer()` | Количество отзывов |
| `google_rating` | Google Maps | `safe_numeric()` | Google рейтинг |

### ГРУППА 12: УДОБСТВА

| Поле v2.2 | Источник | Функция | Комментарий |
|-----------|---------|---------|-----------|
| `wheelchair_access` | CQC/Другое | `safe_boolean()` | Доступ для инвалидных колясок |
| `ensuite_rooms` | CQC/Другое | `safe_boolean()` | Комнаты с личной ванной |
| `secure_garden` | CQC/Другое | `safe_boolean()` | Безопасный огороженный сад |
| `wifi_available` | CQC/Другое | `safe_boolean()` | WiFi для резидентов |
| `parking_onsite` | CQC/Другое | `safe_boolean()` | Парковка на территории |

### ГРУППА 13: СИСТЕМА

| Поле v2.2 | Источник | Функция | Комментарий |
|-----------|---------|---------|-----------|
| `is_dormant` | `dormant_y_n` | `safe_dormant()` | Закрыт/приостановлен |
| `data_quality_score` | Вычисляется | — | 0-100 (%) |
| `created_at` | БД | DEFAULT CURRENT_TIMESTAMP | Дата создания |
| `updated_at` | БД | DEFAULT CURRENT_TIMESTAMP | Дата обновления |

### 🆕 ГРУППА 14: JSONB СТРУКТУРЫ v2.2 (+1)

| Поле v2.2 | Источник | Комментарий |
|-----------|---------|-----------|
| `service_types` | `service_type_*` поля | Типы услуг |
| `service_user_bands` | `service_user_band_*` поля | Категории пациентов |
| 🆕 `regulated_activities` | `regulated_activity_*` поля (14 типов) | ✅ ВСЕ 14 CQC лицензий! |
| `facilities` | Различные источники | Удобства |
| `medical_specialisms` | Различные источники | Медицинские специализации |
| `dietary_options` | Различные источники | Диетические опции |
| `activities` | Различные источники | Программы досуга |
| `pricing_details` | Различные источники | Детали ценообразования |
| `staff_information` | Различные источники | Информация о персонале |
| `reviews_detailed` | Google, Carehome.co.uk | Детальные отзывы |
| `media` | Различные источники | Фото/видео |
| `location_context` | Вычисляется | Контекст локации |
| `building_info` | Различные источники | Информация о здании |
| `accreditations` | Различные источники | Сертификаты |
| `source_urls` | Различные источники | Коллекция URL |
| `source_metadata` | Различные источники | Метаданные источников |
| `extra` | Гибкое поле | Дополнительная информация |

---

## 7 НОВЫХ ПОЛЕЙ SERVICE USER BANDS

### ⚠️ ВАЖНОЕ РАЗЛИЧИЕ

```
care_dementia = TRUE         → дом СПЕЦИАЛИЗИРУЕТСЯ на деменции
serves_dementia_band = TRUE  → дом ПРИНИМАЕТ пациентов с деменцией

Они НЕ обязательно совпадают!
Пример: care_dementia=FALSE, serves_dementia_band=TRUE = общий дом, 
но принимает людей с деменцией
```

### НОВЫЕ ПОЛЯ И ИХ ЗНАЧЕНИЕ

#### 1️⃣ `serves_dementia_band` ⭐ ВЫСОКИЙ ПРИОРИТЕТ

- **CQC поле:** `service_user_band_dementia`
- **Тип:** BOOLEAN
- **Частота:** ~68% домов принимают (ожидаемо)
- **Использование в матчинге:** Критично для Q9 (пациент с деменцией)
- **Consistency check:** если `care_dementia=TRUE` то `serves_dementia_band` должен быть TRUE

#### 2️⃣ `serves_children`

- **CQC поле:** `service_user_band_children_0_18_years`
- **Тип:** BOOLEAN
- **Частота:** <1% (редко)
- **Комментарий:** Специализированное предложение для домов престарелых

#### 3️⃣ `serves_learning_disabilities`

- **CQC поле:** `service_user_band_learning_disabilities_or_autistic_spectrum_di`
- **Тип:** BOOLEAN
- **Частота:** ~17% домов
- **Комментарий:** Умственная инвалидность / аутизм

#### 4️⃣ `serves_detained_mha`

- **CQC поле:** `service_user_band_people_detained_under_the_mental_health_act`
- **Тип:** BOOLEAN
- **Частота:** <1% (редко)
- **Комментарий:** Психиатрия под Mental Health Act (высокий уровень безопасности)

#### 5️⃣ `serves_substance_misuse`

- **CQC поле:** `service_user_band_people_who_misuse_drugs_and_alcohol`
- **Тип:** BOOLEAN
- **Частота:** <2% (редко)
- **Комментарий:** Реабилитация, медицинский надзор

#### 6️⃣ `serves_eating_disorders`

- **CQC поле:** `service_user_band_people_with_an_eating_disorder`
- **Тип:** BOOLEAN
- **Частота:** <1% (редко)
- **Комментарий:** Питание под контролем, психологическая поддержка

#### 7️⃣ `serves_whole_population`

- **CQC поле:** `service_user_band_whole_population`
- **Тип:** BOOLEAN
- **Частота:** ~12% домов
- **Комментарий:** Смешанные категории, без специализации

---

## REGULATED ACTIVITIES JSONB

### ЧТО ЭТО НОВОЕ ПОЛЕ?

В v2.2 добавлено **новое JSONB поле** `regulated_activities` которое содержит **ВСЕ 14 официальных CQC regulated activities**:

```json
{
  "activities": [
    {
      "id": "nursing_care",
      "name": "Nursing care",
      "cqc_field": "regulated_activity_nursing_care",
      "active": true
    },
    {
      "id": "personal_care",
      "name": "Personal care",
      "cqc_field": "regulated_activity_personal_care",
      "active": true
    },
    {
      "id": "surgical_procedures",
      "name": "Surgical procedures",
      "active": false
    },
    ...всего 14 типов
  ]
}
```

### КАКИЕ ЛИЦЕНЗИИ ВКЛЮЧЕНЫ?

| ID | Тип | Активный | Частота |
|----|-----|---------|---------|
| 1 | `accommodation_nursing` | Often | 🟢 Часто |
| 2 | `accommodation_treatment` | Rare | 🔴 Редко |
| 3 | `assessment_detained` | Rare | 🔴 Редко |
| 4 | `diagnostic_screening` | Often | 🟢 Активно используется |
| 5 | `family_planning` | Rare | 🔴 Редко |
| 6 | `blood_management` | Rare | 🔴 Редко |
| 7 | `maternity_midwifery` | Rare | 🔴 Редко |
| 8 | `nursing_care` | Often | 🟢 Часто (73% домов) |
| 9 | `personal_care` | Often | 🟢 Часто (92% домов) |
| 10 | `slimming_clinics` | Rare | 🔴 Редко |
| 11 | `surgical_procedures` | Rare | 🔴 Редко |
| 12 | `termination_pregnancies` | Rare | 🔴 Редко |
| 13 | `transport_triage` | Rare | 🔴 Редко |
| 14 | `treatment_disease` | Often | 🟢 Часто |

### КАК ИСПОЛЬЗОВАТЬ В ЗАПРОСАХ?

```sql
-- Найти дома с nursing care
SELECT name FROM care_homes 
WHERE regulated_activities @> '[{"id": "nursing_care", "active": true}]'::jsonb;

-- Подсчитать активные лицензии
SELECT 
  name,
  jsonb_array_length(regulated_activities->'activities') as license_count
FROM care_homes
WHERE regulated_activities != '{"activities": []}'::jsonb
ORDER BY license_count DESC;

-- Быстрый поиск через GIN индекс
EXPLAIN (ANALYZE) 
SELECT COUNT(*) FROM care_homes 
WHERE regulated_activities @> '[{"id": "nursing_care"}]'::jsonb;
```

### ПРЕИМУЩЕСТВА vs СТАРОЙ СИСТЕМЫ

| Аспект | v2.1 (5 полей) | v2.2 (JSONB + 14 типов) |
|--------|----------------|------------------------|
| **Покрытие** | 5/14 (36%) | 14/14 (100%) ✅ |
| **Гибкость** | Требуется миграция | Добавляем новые без миграции |
| **Поиск** | Медленно (5 WHERE) | Быстро (GIN индекс) |
| **Новые типы** | Нужна ALTER TABLE | Просто добавляем в JSON |
| **Синхронизация** | Требуется обновление | Автоматическая через JSONB |

---

## ✅ ЧЕКЛИСТ ПРОВЕРКИ МАППИНГА

### 1. ПРОВЕРКА ЛИЦЕНЗИЙ (КРИТИЧНО!)

- [ ] `has_nursing_care_license` использует `regulated_activity_nursing_care` ✅
- [ ] `has_personal_care_license` использует `regulated_activity_personal_care` ✅
- [ ] `has_surgical_procedures_license` использует `regulated_activity_surgical_procedures` ✅
- [ ] `has_treatment_license` использует `regulated_activity_treatment_of_disease_disorder_or_injury` ✅
- [ ] `has_diagnostic_license` использует `regulated_activity_diagnostic_and_screening_procedures` ✅
- [ ] **НИ ОДНО поле** `has_*_license` НЕ использует `service_type_*` ❌

**Ожидаемый результат:**
```sql
SELECT COUNT(*) FROM care_homes WHERE has_nursing_care_license = TRUE;
-- Ожидается: ~198 (73%), а НЕ 73 (27%)!
```

### 2. ПРОВЕРКА ТИПОВ УХОДА

- [ ] `care_residential` использует `service_type_care_home_service_without_nursing` ✅
- [ ] `care_nursing` использует `service_type_care_home_service_with_nursing` ✅
- [ ] `care_dementia` использует `service_user_band_dementia` ✅
- [ ] Порядок полей в SELECT соответствует INSERT

### 3. ПРОВЕРКА 7 НОВЫХ ПОЛЕЙ v2.2

- [ ] `serves_dementia_band` маппирован и заполнен
- [ ] `serves_children` маппирован и заполнен
- [ ] `serves_learning_disabilities` маппирован и заполнен
- [ ] `serves_detained_mha` маппирован и заполнен
- [ ] `serves_substance_misuse` маппирован и заполнен
- [ ] `serves_eating_disorders` маппирован и заполнен
- [ ] `serves_whole_population` маппирован и заполнен

**Ожидаемые результаты:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE serves_dementia_band = TRUE) as dementia,
  COUNT(*) FILTER (WHERE serves_children = TRUE) as children,
  COUNT(*) FILTER (WHERE serves_learning_disabilities = TRUE) as learning_dis
FROM care_homes;

-- Ожидается: dementia ~900+, children <10, learning_dis ~400+
```

### 4. ПРОВЕРКА REGULATED_ACTIVITIES JSONB

- [ ] Поле `regulated_activities` создано как JSONB
- [ ] Содержит все 14 типов лицензий
- [ ] GIN индекс создан на `regulated_activities`
- [ ] Структура валидна: `{"activities": [...]}`

**Проверка:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE regulated_activities IS NOT NULL) as with_data,
  COUNT(*) FILTER (WHERE regulated_activities != '{"activities": []}'::jsonb) as with_activities
FROM care_homes;

-- Ожидается: ~100% с данными, ~70-80% с заполненными activities
```

### 5. ПРОВЕРКА ТИПОВ ДАННЫХ

- [ ] `telephone` имеет тип TEXT (НЕ NUMERIC)
- [ ] `telephone` использует `clean_text()` (НЕ `safe_numeric()`)
- [ ] `latitude` и `longitude` имеют тип NUMERIC(10,7)
- [ ] Все boolean поля используют `safe_boolean()`

### 6. ПРОВЕРКА КООРДИНАТ

- [ ] `latitude` использует `safe_latitude()` с валидацией 49-61
- [ ] `longitude` использует `safe_longitude()` с валидацией -8 to 2
- [ ] Обработаны отрицательные значения
- [ ] Обработаны запятые как десятичный разделитель

```sql
SELECT COUNT(*) FROM care_homes 
WHERE latitude NOT BETWEEN 49 AND 61 
   OR longitude NOT BETWEEN -8 AND 2;
-- Ожидается: 0 (ноль!)
```

### 7. ПРОВЕРКА COALESCE ЛОГИКИ

- [ ] `website` использует `COALESCE(location_web_address, provider_web_address)`
- [ ] Другие поля используют `location_*` как приоритет

### 8. ПРОВЕРКА ФУНКЦИЙ

- [ ] Все 12+ helper функций созданы ДО INSERT
- [ ] `safe_boolean()` обрабатывает: Y, YES, TRUE, 1, T, N, NO, FALSE, 0, F
- [ ] `normalize_cqc_rating()` валидирует 4 значения: Outstanding/Good/RI/Inadequate
- [ ] `safe_latitude()`, `safe_longitude()` с UK валидацией

---

## ⚠️ ТИПИЧНЫЕ ОШИБКИ И РЕШЕНИЯ

### Ошибка #1: Путаница service_type_* vs regulated_activity_*

**Симптомы:**
- Неверное количество домов с лицензиями
- Пользователи жалуются на отсутствие заявленных услуг

**Причина:**
```sql
-- ❌ НЕПРАВИЛЬНО
has_nursing_care_license ← service_type_care_home_service_with_nursing
```

**Решение:**
```sql
-- ✅ ПРАВИЛЬНО
has_nursing_care_license ← regulated_activity_nursing_care
```

### Ошибка #2: Забыли новые 7 полей v2.2

**Симптомы:**
- Views не работают (expecting 12 bands, got 5)
- Аналитика incomplete

**Решение:**
- Добавить все 7 полей в INSERT
- Маппировать из `service_user_band_*` полей CQC
- Использовать `safe_boolean()` для преобразования

### Ошибка #3: Неправильная структура regulated_activities

**Симптомы:**
```json
// ❌ НЕПРАВИЛЬНО
{"nursing_care": true, "personal_care": false}

// ✅ ПРАВИЛЬНО
{"activities": [
  {"id": "nursing_care", "active": true},
  {"id": "personal_care", "active": false}
]}
```

**Решение:**
- Использовать `jsonb_build_object()` и `jsonb_agg()`
- Соответствовать структуре: `{"activities": [...]}`
- Протестировать CHECK constraint

### Ошибка #4: Потеря целой части у negative координат

**Симптомы:**
- -1.88634 → -0.188634
- Дома на неправильных местах

**Решение:**
- Использовать `safe_longitude()` с heuristic для запятых
- Проверить обработку отрицательных чисел

### Ошибка #5: telephone как NUMERIC

**Симптомы:**
- 01234567890 → 1234567890.0 (потеря leading zero!)
- Телефоны не правильные

**Решение:**
```sql
-- ✅ Только TEXT!
telephone TEXT
clean_text(location_telephone_number)
```

---

## 🔍 ВАЛИДАЦИЯ ПОСЛЕ МИГРАЦИИ

### Проверка 1: Количество записей

```sql
SELECT COUNT(*) FROM care_homes;
-- Ожидается: 271 (или ваше количество)
```

### Проверка 2: Лицензии (КРИТИЧНО!)

```sql
SELECT COUNT(*) FROM care_homes WHERE has_nursing_care_license = TRUE;
-- Ожидается: ~198 (73%), а НЕ 73!

-- Детальный анализ
SELECT 
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) as nursing_true,
  COUNT(*) FILTER (WHERE has_personal_care_license = TRUE) as personal_true,
  ROUND(100.0 * COUNT(*) FILTER (WHERE has_nursing_care_license = TRUE) / COUNT(*), 1) as nursing_pct
FROM care_homes;
```

### Проверка 3: Координаты

```sql
-- Валидация диапазона
SELECT COUNT(*) 
FROM care_homes 
WHERE latitude NOT BETWEEN 49 AND 61 
   OR longitude NOT BETWEEN -8 AND 2;
-- Ожидается: 0

-- NULL координаты
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE latitude IS NULL) / COUNT(*), 1) as null_pct
FROM care_homes;
-- Ожидается: <5%
```

### Проверка 4: Тип данных telephone

```sql
-- Проверка типа
SELECT data_type FROM information_schema.columns
WHERE table_name = 'care_homes' AND column_name = 'telephone';
-- Ожидается: text

-- Примеры телефонов
SELECT telephone FROM care_homes 
WHERE telephone IS NOT NULL LIMIT 10;
-- НЕ должно быть формата: 1212740588.0
```

### Проверка 5: Новые 7 полей v2.2

```sql
SELECT 
  COUNT(*) FILTER (WHERE serves_dementia_band = TRUE) as dementia,
  COUNT(*) FILTER (WHERE serves_children = TRUE) as children,
  COUNT(*) FILTER (WHERE serves_learning_disabilities = TRUE) as learning_dis,
  COUNT(*) FILTER (WHERE serves_detained_mha = TRUE) as detained_mha,
  COUNT(*) FILTER (WHERE serves_substance_misuse = TRUE) as substance_misuse,
  COUNT(*) FILTER (WHERE serves_eating_disorders = TRUE) as eating_disorders,
  COUNT(*) FILTER (WHERE serves_whole_population = TRUE) as whole_population
FROM care_homes;

-- Ожидается:
-- dementia ~180-200
-- children 0-5
-- learning_dis ~40-50
-- detained_mha 0-2
-- substance_misuse 0-3
-- eating_disorders 0-1
-- whole_population ~30-40
```

### Проверка 6: regulated_activities JSONB

```sql
-- Структура валидна
SELECT COUNT(*) 
FROM care_homes 
WHERE regulated_activities ? 'activities'
  AND jsonb_typeof(regulated_activities->'activities') = 'array';
-- Ожидается: = COUNT(*)

-- Распределение
SELECT 
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE regulated_activities != '{"activities": []}'::jsonb) as with_activities,
  ROUND(100.0 * COUNT(*) FILTER (WHERE regulated_activities != '{"activities": []}'::jsonb) / COUNT(*), 1) as fill_pct
FROM care_homes;
-- Ожидается: fill_pct > 70%
```

### Проверка 7: Views

```sql
-- Все 3 view работают
SELECT * FROM v_data_coverage;
SELECT COUNT(*) FROM v_service_user_bands_coverage;
SELECT COUNT(*) FROM v_data_anomalies;

-- Ожидается:
-- v_data_coverage: 1 row
-- v_service_user_bands_coverage: 12 rows
-- v_data_anomalies: <100 rows (errors only)
```

---

## 📊 ЭТАЛОННЫЕ ЗНАЧЕНИЯ

| Метрика | Ожидаемое | Коммент |
|---------|----------|---------|
| **Всего записей** | 271 | Или ваше количество |
| **has_nursing_care_license = TRUE** | ~198 (73%) | НЕ 73! |
| **has_personal_care_license = TRUE** | ~250 (92%) | Большинство |
| **Координаты (не NULL)** | ~260-270 (96-99%) | Почти все |
| **Координаты вне UK** | 0 | Ноль ошибок! |
| **telephone тип TEXT** | 100% | Не NUMERIC |
| **year_registered 1950-2025** | 100% | Разумные годы |
| **serves_dementia_band = TRUE** | ~180-200 | ~68% |
| **serves_children = TRUE** | 0-5 | Редко <1% |
| **regulated_activities заполнено** | >70% | Хорошее покрытие |

---

## 🎓 ВАЖНЫЕ МОМЕНТЫ ИНТЕГРАЦИИ v2.2

### Для разработчиков:

1. ✅ **ВСЕГДА** проверяйте тип источника (service_type vs regulated_activity)
2. ✅ Используйте **правильные функции** для каждого типа
3. ✅ Включайте **все 7 новых полей** в INSERT
4. ✅ Тестируйте на **реальных данных** перед production
5. ✅ Валидируйте **JSONB структуру** перед INSERT

### Для QA:

1. ✅ Проверяйте **количество с лицензиями** (~73%, а не 27%)
2. ✅ Проверяйте **формат телефонов** (TEXT, не 1212740588.0)
3. ✅ Проверяйте **координаты на карте** (правильные места)
4. ✅ Проверяйте **новые 7 полей** (все заполнены)
5. ✅ Проверяйте **Views работают** (3 views с данными)

### Для Product Managers:

1. ✅ Убедитесь в **соответствии CQC** (точные лицензии)
2. ✅ Убедитесь в **юридической корректности** (regulated_activity)
3. ✅ Убедитесь в **качестве UX** (правильные координаты, телефоны)
4. ✅ Убедитесь в **полноте данных** (новые 7 полей)
5. ✅ Убедитесь в **Views работают** (аналитика доступна)

---

## 📞 КОНТАКТЫ И ПОДДЕРЖКА

При вопросах:

1. ✅ Сначала проверьте этот документ
2. ✅ Используйте чеклист проверки
3. ✅ Сравните с эталонными значениями
4. ✅ Проверьте SQL queries в разделе Валидация
5. ✅ Обратитесь к эксперту БД для сложных случаев

---

## 📝 ИСТОРИЯ ВЕРСИЙ

| Версия | Дата | Изменения |
|--------|------|----------|
| **2.2 UPDATED** | 31.10.2025 | ✅ Полная поддержка v2.2 БД |
| | | ✅ 7 новых Service User Bands |
| | | ✅ regulated_activities JSONB (14 типов) |
| | | ✅ 3 Views для аналитики |
| | | ✅ Чеклисты и примеры v2.2 |
| **2.1 FINAL** | 28.10.2025 | Первая полная версия |

---

**✅ Эта памятка является ОБЯЗАТЕЛЬНОЙ для всех, кто работает с маппингом CQC в v2.2!**

**Статус:** PRODUCTION READY  
**Дата обновления:** 31 октября 2025  
**Версия БД:** v2.2 FINAL
