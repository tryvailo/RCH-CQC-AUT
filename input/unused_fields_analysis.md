# Анализ неиспользованных полей из cqc_dataset_test

## Всего полей в cqc_dataset_test: 127

## ❌ НЕИСПОЛЬЗОВАННЫЕ ПОЛЯ (11):

### 1. Provider Location Data (6 полей):
- `provider_latitude` - широта провайдера (организации)
- `provider_longitude` - долгота провайдера (организации)
- `provider_paf_id` - PAF ID провайдера
- `provider_uprn_id` - UPRN ID провайдера
- `provider_local_authority` - местная администрация провайдера
- `provider_region` - регион провайдера
- `provider_nhs_region` - NHS регион провайдера
- `provider_parliamentary_constituency` - парламентский округ провайдера

### 2. Provider Additional Data (2 поля):
- `provider_hsca_start_date` - дата начала регистрации провайдера
- `provider_telephone_number` - телефон провайдера

### 3. Brand Data (1 поле):
- `brand_id` - ID бренда

---

## ✅ ИСПОЛЬЗУЕМЫЕ ПОЛЯ (116):

### Location Core Data (33 поля):
- location_id ✅
- location_name ✅
- location_ods_code ✅
- location_telephone_number ✅
- location_web_address ✅
- location_hsca_start_date ✅
- dormant_y_n_ ✅
- care_home_ ✅
- care_homes_beds ✅
- location_type_sector ✅
- location_inspection_directorate ✅
- location_primary_inspection_category ✅
- location_latest_overall_rating ✅
- publication_date ✅
- inherited_rating_y_n_ ✅
- location_region ✅
- location_nhs_region ✅
- location_local_authority ✅
- location_onspd_ccg_code ✅
- location_onspd_ccg ✅
- location_commissioning_ccg_code ✅
- location_commissioning_ccg ✅
- location_street_address ✅
- location_address_line_2 ✅
- location_city ✅
- location_county ✅
- location_postal_code ✅
- location_paf_id ✅
- location_uprn_id ✅
- location_latitude ✅
- location_longitude ✅
- location_parliamentary_constituency ✅
- registered_manager ✅

### Provider Data (11 полей):
- provider_id ✅
- provider_name ✅
- brand_name ✅
- provider_type_sector ✅
- provider_inspection_directorate ✅
- provider_primary_inspection_category ✅
- provider_ownership_type ✅
- provider_web_address ✅
- provider_companies_house_number ✅
- provider_charity_number ✅
- provider_nominated_individual_name ✅
- provider_main_partner_name ✅

### Provider Address (5 полей):
- provider_street_address ✅
- provider_address_line_2 ✅
- provider_city ✅
- provider_county ✅
- provider_postal_code ✅

### CQC Ratings (7 полей):
- cqc_report_url ✅
- cqc_rating_safe ✅
- cqc_rating_effective ✅
- cqc_rating_caring ✅
- cqc_rating_responsive ✅
- cqc_rating_well_led ✅
- cqc_rating_overall ✅

### Regulated Activities (14 полей):
- regulated_activity_accommodation_for_persons_who_require_nursin ✅
- regulated_activity_accommodation_for_persons_who_require_treatm ✅
- regulated_activity_assessment_or_medical_treatment_for_persons_ ✅
- regulated_activity_diagnostic_and_screening_procedures ✅
- regulated_activity_family_planning ✅
- regulated_activity_management_of_supply_of_blood_and_blood_deri ✅
- regulated_activity_maternity_and_midwifery_services ✅
- regulated_activity_nursing_care ✅
- regulated_activity_personal_care ✅
- regulated_activity_services_in_slimming_clinics ✅
- regulated_activity_surgical_procedures ✅
- regulated_activity_termination_of_pregnancies ✅
- regulated_activity_transport_services_triage_and_medical_advice ✅
- regulated_activity_treatment_of_disease_disorder_or_injury ✅

### Service Types (32 поля):
Все 32 поля service_type_* используются ✅

### Service User Bands (12 полей):
Все 12 полей service_user_band_* используются ✅

### Additional URLs (2 поля):
- carehome_url ✅
- lottie_url ✅

---

## 📊 Статистика:

- **Всего полей**: 127
- **Используемых**: 116 (91.3%)
- **Неиспользованных**: 11 (8.7%)

---

## 💡 Рекомендации:

### 1. Можно добавить в маппинг:
- `provider_telephone_number` → может быть полезен как альтернативный контакт
- `provider_hsca_start_date` → может показать опыт провайдера
- `brand_id` → для связи с брендом

### 2. Геолокация провайдера:
- `provider_latitude`, `provider_longitude` → можно добавить в JSONB поле `building_info` или `source_metadata`

### 3. Provider Context:
- `provider_local_authority`, `provider_region`, `provider_nhs_region`, `provider_parliamentary_constituency` → можно добавить в `building_info` или `source_metadata`

### 4. Provider IDs:
- `provider_paf_id`, `provider_uprn_id` → можно добавить в `building_info`

---

## 🎯 Приоритет добавления:

### Высокий приоритет:
1. `provider_telephone_number` - полезный контакт
2. `provider_hsca_start_date` - дата регистрации провайдера

### Средний приоритет:
3. `provider_latitude`, `provider_longitude` - геолокация офиса провайдера
4. `brand_id` - для связи с брендом

### Низкий приоритет:
5. `provider_local_authority`, `provider_region` и т.д. - дублируют location данные
6. `provider_paf_id`, `provider_uprn_id` - технические идентификаторы

