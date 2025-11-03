# Исправление ошибок в именах полей CQC

**Дата:** 2025-01-27  
**Аналитик:** Обнаружены 4 ошибки в именах полей CQC  
**Статус:** ✅ ИСПРАВЛЕНО

---

## 🔴 ОБНАРУЖЕННЫЕ ОШИБКИ

### Ошибка 1: `service_user_band_children_0_17_years`
- **Неправильно:** `service_user_band_children_0_17_years`
- **Правильно:** `service_user_band_children_0_18_years`
- **Источник:** `Product_Manager_Guide_CQC.md` строка 338, 444
- **Местоположение в коде:**
  - Создание временной таблицы `temp_cqc_raw` (строка 228)
  - SELECT запрос (строка 767)

### Ошибка 2: `service_user_band_detained_under_the_mental_health_act`
- **Неправильно:** `service_user_band_detained_under_the_mental_health_act`
- **Правильно:** `service_user_band_people_detained_under_the_mental_health_act`
- **Источник:** `Product_Manager_Guide_CQC.md` строка 340, 458
- **Местоположение в коде:**
  - Создание временной таблицы `temp_cqc_raw` (строка 229)
  - SELECT запрос (строка 769)

### Ошибка 3: `service_user_band_people_misusing_drugs_and_alcohol`
- **Неправильно:** `service_user_band_people_misusing_drugs_and_alcohol`
- **Правильно:** `service_user_band_people_who_misuse_drugs_and_alcohol`
- **Источник:** `Product_Manager_Guide_CQC.md` строка 341, 465
- **Местоположение в коде:**
  - Создание временной таблицы `temp_cqc_raw` (строка 235)
  - SELECT запрос (строка 770)

### Ошибка 4: `service_user_band_learning_disabilities_or_autistic_spectrum_d` (обнаружена при проверке)
- **Неправильно:** `service_user_band_learning_disabilities_or_autistic_spectrum_d` (отсутствует `i` в конце)
- **Правильно:** `service_user_band_learning_disabilities_or_autistic_spectrum_di`
- **Источник:** 
  - `Product_Manager_Guide_CQC.md` строка 339, 451
  - Реальный CSV файл: `CQC-DataSet_rows.csv`
- **Местоположение в коде:**
  - Создание временной таблицы `temp_cqc_raw` (строка 232)
  - SELECT запрос (строка 768)

---

## ✅ ИСПРАВЛЕНИЯ

### Файл 1: `step2_run_migration.sql`

**Изменения:**
1. ✅ Строка 228: `service_user_band_children_0_17_years` → `service_user_band_children_0_18_years`
2. ✅ Строка 229: `service_user_band_detained_under_the_mental_health_act` → `service_user_band_people_detained_under_the_mental_health_act`
3. ✅ Строка 232: `service_user_band_learning_disabilities_or_autistic_spectrum_d` → `service_user_band_learning_disabilities_or_autistic_spectrum_di`
4. ✅ Строка 235: `service_user_band_people_misusing_drugs_and_alcohol` → `service_user_band_people_who_misuse_drugs_and_alcohol`
5. ✅ Строка 767: обновлено использование `service_user_band_children_0_18_years`
6. ✅ Строка 768: обновлено использование `service_user_band_learning_disabilities_or_autistic_spectrum_di`
7. ✅ Строка 769: обновлено использование `service_user_band_people_detained_under_the_mental_health_act`
8. ✅ Строка 770: обновлено использование `service_user_band_people_who_misuse_drugs_and_alcohol`

### Файл 2: `step2_run_migration_SUPABASE.sql`

**Изменения:**
1. ✅ Строка 241: `service_user_band_children_0_17_years` → `service_user_band_children_0_18_years`
2. ✅ Строка 242: `service_user_band_detained_under_the_mental_health_act` → `service_user_band_people_detained_under_the_mental_health_act`
3. ✅ Строка 245: `service_user_band_learning_disabilities_or_autistic_spectrum_d` → `service_user_band_learning_disabilities_or_autistic_spectrum_di`
4. ✅ Строка 248: `service_user_band_people_misusing_drugs_and_alcohol` → `service_user_band_people_who_misuse_drugs_and_alcohol`
5. ✅ Строка 800: обновлено использование `service_user_band_children_0_18_years`
6. ✅ Строка 801: обновлено использование `service_user_band_learning_disabilities_or_autistic_spectrum_di`
7. ✅ Строка 802: обновлено использование `service_user_band_people_detained_under_the_mental_health_act`
8. ✅ Строка 803: обновлено использование `service_user_band_people_who_misuse_drugs_and_alcohol`

---

## 📋 ПРОВЕРКА СООТВЕТСТВИЯ ДОКУМЕНТАЦИИ

Согласно `Product_Manager_Guide_CQC.md` (строки 333-343):

| Поле v2.2 | Источник CQC | Статус |
|-----------|-------------|--------|
| `serves_children` | `service_user_band_children_0_18_years` | ✅ ИСПРАВЛЕНО |
| `serves_learning_disabilities` | `service_user_band_learning_disabilities_or_autistic_spectrum_di` | ✅ ИСПРАВЛЕНО |
| `serves_detained_mha` | `service_user_band_people_detained_under_the_mental_health_act` | ✅ ИСПРАВЛЕНО |
| `serves_substance_misuse` | `service_user_band_people_who_misuse_drugs_and_alcohol` | ✅ ИСПРАВЛЕНО |

---

## ⚠️ ВАЖНОЕ ЗАМЕЧАНИЕ

Исходный файл `/input/cqc-to-care_homes_grok.sql` **НЕ БЫЛ ИЗМЕНЕН**, так как пользователь работает с копиями в `/execution/`. Если необходимо обновить исходный файл, это нужно сделать отдельно.

---

## ✅ РЕЗУЛЬТАТ

Все 4 ошибки исправлены в обоих файлах миграции:
- ✅ `step2_run_migration.sql`
- ✅ `step2_run_migration_SUPABASE.sql`

Маппинг теперь соответствует документации CQC и реальным именам колонок в CSV файле.

