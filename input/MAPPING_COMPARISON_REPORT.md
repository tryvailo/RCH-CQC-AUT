# ОТЧЕТ: СРАВНЕНИЕ ИСХОДНОЙ И ИТОГОВОЙ БАЗЫ ДАННЫХ

**Дата анализа:** 2025-11-03 12:08:12
**Исходный файл:** cqc_dataset_test_initalDB.csv
**Итоговый файл:** care_homes_rows_after_mapping.csv

---

## 1. ОБЩАЯ СТАТИСТИКА

- **Исходный файл:** 129 полей, 271 записей
- **Итоговый файл:** 93 полей, 271 записей
- **Разница:** 36 полей (исходник больше)

## 2. ПОЛЯ, ПРИСУТСТВУЮЩИЕ В ИСХОДНИКЕ, НО ОТСУТСТВУЮЩИЕ В ИТОГОВОЙ БАЗЕ

**Всего уникальных полей в исходнике:** 119

### Даты (3 полей)

- `location_hsca_start_date` - заполнено 271 (100.0%)
- `provider_hsca_start_date` - заполнено 271 (100.0%)
- `publication_date` - заполнено 248 (91.5%)

### Regulated Activities (14 полей)

- `regulated_activity_accommodation_for_persons_who_require_nursin` - заполнено 0 (0.0%)
- `regulated_activity_accommodation_for_persons_who_require_treatm` - заполнено 0 (0.0%)
- `regulated_activity_assessment_or_medical_treatment_for_persons_` - заполнено 0 (0.0%)
- `regulated_activity_diagnostic_and_screening_procedures` - заполнено 271 (100.0%)
- `regulated_activity_family_planning` - заполнено 271 (100.0%)
- `regulated_activity_management_of_supply_of_blood_and_blood_deri` - заполнено 0 (0.0%)
- `regulated_activity_maternity_and_midwifery_services` - заполнено 271 (100.0%)
- `regulated_activity_nursing_care` - заполнено 271 (100.0%)
- `regulated_activity_personal_care` - заполнено 271 (100.0%)
- `regulated_activity_services_in_slimming_clinics` - заполнено 271 (100.0%)
- ... и еще 4 полей

### Service Types (33 полей)

- `service_type_acute_services_with_overnight_beds` - заполнено 271 (100.0%)
- `service_type_acute_services_without_overnight_beds_listed_acute` - заполнено 0 (0.0%)
- `service_type_ambulance_service` - заполнено 271 (100.0%)
- `service_type_blood_and_transplant_service` - заполнено 271 (100.0%)
- `service_type_care_home_service_with_nursing` - заполнено 271 (100.0%)
- `service_type_care_home_service_without_nursing` - заполнено 271 (100.0%)
- `service_type_community_based_services_for_people_who_misuse_sub` - заполнено 0 (0.0%)
- `service_type_community_based_services_for_people_with_a_learnin` - заполнено 0 (0.0%)
- `service_type_community_based_services_for_people_with_mental_he` - заполнено 0 (0.0%)
- `service_type_community_health_care_services_independent_midwive` - заполнено 0 (0.0%)
- ... и еще 23 полей

### Service User Bands (12 полей)

- `service_user_band_children_0_18_years` - заполнено 271 (100.0%)
- `service_user_band_dementia` - заполнено 271 (100.0%)
- `service_user_band_learning_disabilities_or_autistic_spectrum_di` - заполнено 0 (0.0%)
- `service_user_band_mental_health` - заполнено 271 (100.0%)
- `service_user_band_older_people` - заполнено 271 (100.0%)
- `service_user_band_people_detained_under_the_mental_health_act` - заполнено 271 (100.0%)
- `service_user_band_people_who_misuse_drugs_and_alcohol` - заполнено 271 (100.0%)
- `service_user_band_people_with_an_eating_disorder` - заполнено 271 (100.0%)
- `service_user_band_physical_disability` - заполнено 271 (100.0%)
- `service_user_band_sensory_impairment` - заполнено 271 (100.0%)
- ... и еще 2 полей

### Provider данные (23 полей)

- `provider_address_line_2` - заполнено 221 (81.5%)
- `provider_charity_number` - заполнено 43 (15.9%)
- `provider_city` - заполнено 271 (100.0%)
- `provider_companies_house_number` - заполнено 250 (92.3%)
- `provider_county` - заполнено 142 (52.4%)
- `provider_inspection_directorate` - заполнено 271 (100.0%)
- `provider_latitude` - заполнено 271 (100.0%)
- `provider_local_authority` - заполнено 271 (100.0%)
- `provider_longitude` - заполнено 271 (100.0%)
- `provider_main_partner_name` - заполнено 271 (100.0%)
- ... и еще 13 полей

### Location данные (24 полей)

- `location_address_line_2` - заполнено 188 (69.4%)
- `location_city` - заполнено 271 (100.0%)
- `location_commissioning_ccg` - заполнено 0 (0.0%)
- `location_commissioning_ccg_code` - заполнено 0 (0.0%)
- `location_county` - заполнено 231 (85.2%)
- `location_inspection_directorate` - заполнено 271 (100.0%)
- `location_latest_overall_rating` - заполнено 248 (91.5%)
- `location_latitude` - заполнено 271 (100.0%)
- `location_local_authority` - заполнено 271 (100.0%)
- `location_longitude` - заполнено 271 (100.0%)
- ... и еще 14 полей

### Другое (10 полей)

- `brand_id` - заполнено 271 (100.0%)
- `care_home_` - заполнено 271 (100.0%)
- `care_homes_beds` - заполнено 271 (100.0%)
- `carehome_url` - заполнено 68 (25.1%)
- `cqc_report_url` - заполнено 271 (100.0%)
- `dormant_y_n_` - заполнено 271 (100.0%)
- `inherited_rating_y_n_` - заполнено 249 (91.9%)
- `location_id` - заполнено 271 (100.0%)
- `lottie_url` - заполнено 100 (36.9%)
- `registered_manager` - заполнено 271 (100.0%)


## 3. КРИТИЧНЫЕ ПРОПУЩЕННЫЕ МАППИНГИ

### ⚠️ Поля, которые были в исходнике с данными, но НЕ замаплены в итоговую базу:

| Исходное поле | Целевое поле | Заполнено в исходнике | Описание |
|---------------|--------------|----------------------|----------|
| `publication_date` | `cqc_publication_date` | 248 (91.5%) | Дата публикации CQC отчета |
| `location_hsca_start_date` | `year_opened` | 271 (100.0%) | Дата начала регистрации (HSCA) |

## 4. АНАЛИЗ ПУСТЫХ ПОЛЕЙ ИТОГОВОЙ БАЗЫ

| Поле итоговой базы | Статус в исходнике |
|-------------------|-------------------|
| `email` | Email не собирается |
| `beds_available` | Не было в исходнике |
| `availability_status` | Не было в исходнике |
| `availability_last_checked` | Не было в исходнике |
| `year_opened` | БЫЛО: location_hsca_start_date - заполнено 100%! |
| `care_respite` | Не было в исходнике |
| `serves_learning_disabilities` | БЫЛО: service_user_band_learning_disabilities - пусто (0%) |
| `fee_residential_from` | Не было в исходнике |
| `fee_nursing_from` | Не было в исходнике |
| `fee_dementia_from` | Не было в исходнике |
| `fee_respite_from` | Не было в исходнике |
| `cqc_publication_date` | БЫЛО: publication_date - заполнено 91.5%! |
| `review_average_score` | Не было в исходнике |
| `review_count` | Не было в исходнике |
| `google_rating` | Не было в исходнике |
| `last_scraped_at` | Не было в исходнике |

## 5. КЛЮЧЕВЫЕ ВЫВОДЫ

### ✅ Что было правильно замаплено:

1. **Regulated Activities** - преобразованы в JSON структуру `regulated_activities`
2. **Service Types** - преобразованы в JSON структуру `service_types`
3. **Service User Bands** - преобразованы в JSON структуру `service_user_bands`
4. **Provider данные** - преобразованы в JSON структуру `building_info` и `source_metadata`
5. **Location данные** - преобразованы в JSON структуру `location_context`

### ⚠️ Критические пропуски в маппинге:

1. **`publication_date` → `cqc_publication_date`**:
   - Было в исходнике: **ДА** (91.5% заполнено)
   - В итоговой базе: **ПУСТО**
   - **Рекомендация:** Добавить маппинг `publication_date` → `cqc_publication_date`

2. **`location_hsca_start_date` → `year_opened`**:
   - Было в исходнике: **ДА** (100% заполнено)
   - В итоговой базе: **ПУСТО**
   - **Рекомендация:** Добавить маппинг `location_hsca_start_date` → `year_opened`
   - **Примечание:** Также возможно использовать для `year_registered`, если это разные даты

### 📋 Поля, которых не было в исходнике:

Следующие поля пусты в итоговой базе, потому что их **не было** в исходной базе:
- `email` - Email не собирается
- `beds_available` - Данные о доступных кроватях
- `availability_status`, `availability_last_checked` - Статус доступности
- `care_respite` - Respite care
- `fee_*` - Поля цен
- `review_*`, `google_rating` - Рейтинги
- `last_scraped_at` - Дата скрапинга

Эти поля **предназначены для будущего заполнения** из других источников.

### 🔍 Интересные находки:

1. **`service_user_band_learning_disabilities`** - было в исходнике, но пусто (0%), поэтому и в итоговой пусто
2. **Regulated Activities** были преобразованы в JSON, но также можно было создать булевы поля для лицензий
3. **Много Provider и Location данных** были преобразованы в JSON структуры вместо отдельных полей

### ⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: Лицензии для Nursing Care

**Обнаружена проблема с маппингом лицензий:**

- В исходнике: `service_type_care_home_service_with_nursing = TRUE` для 73 домов
- В исходнике: `regulated_activity_nursing_care = TRUE` для **0 домов** (все FALSE!)
- В итоговой базе: `care_nursing = TRUE` для 73 домов
- В итоговой базе: `has_nursing_care_license = FALSE` для **всех 73 домов**

**Вывод:**
- `regulated_activity_nursing_care` в исходнике **всегда FALSE**, даже для домов с nursing care
- Это означает, что либо:
  1. `regulated_activity_nursing_care` не означает наличие лицензии на nursing care
  2. Логика маппинга должна использовать другое поле
  3. Нужно использовать `service_type_care_home_service_with_nursing = TRUE` для определения `has_nursing_care_license`

**Рекомендация:** Проверить логику маппинга лицензий. Возможно, `has_nursing_care_license` должен определяться на основе `service_type_care_home_service_with_nursing`, а не `regulated_activity_nursing_care`.

---

*Отчет сгенерирован автоматически 2025-11-03 12:08:12*