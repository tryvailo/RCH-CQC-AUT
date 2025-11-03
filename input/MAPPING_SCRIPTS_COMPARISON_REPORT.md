# ОТЧЕТ: СРАВНЕНИЕ СКРИПТОВ МАППИНГА CQC → CARE_HOMES

**Дата анализа:** 2025-11-03  
**Текущий скрипт:** `input/cqc-to-care_homes_grok.sql` (v7.3.1 FULL)  
**Улучшенный скрипт:** `input/mapping_improved_script.sql` (v2.3)  
**Анализ неиспользованных полей:** `input/unused_fields_analysis.md`

---

## 1. ОБЩАЯ СТАТИСТИКА

| Параметр | Текущий скрипт | Улучшенный скрипт |
|----------|----------------|-------------------|
| **Версия** | v7.3.1 FULL | v2.3 IMPROVED |
| **Метод загрузки** | Через staging таблицу `temp_cqc_raw` | Прямая загрузка из `cqc_dataset_test` |
| **Helper функций** | 10 функций | 10 функций (улучшенные) |
| **Поля в INSERT** | 93 поля | 93 поля + дополнительные |

---

## 2. КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ

### ✅ 2.1. Маппинг `publication_date` → `cqc_publication_date`

**Статус:** ✅ **ОБА СКРИПТА ИМЕЮТ ЭТОТ МАППИНГ**

- **Текущий скрипт:**
  ```sql
  safe_date(publication_date) AS cqc_publication_date,
  ```

- **Улучшенный скрипт:**
  ```sql
  safe_date(publication_date) AS cqc_publication_date,
  ```

**Вывод:** ✅ Оба скрипта корректно маппят `publication_date`. Проблема уже решена в текущем скрипте.

---

### ⚠️ 2.2. Маппинг `location_hsca_start_date` → `year_opened`

**Статус:** ❌ **ОБА СКРИПТА НЕ ИСПРАВЛЯЮТ ЭТУ ПРОБЛЕМУ**

- **Текущий скрипт:**
  ```sql
  NULL AS year_opened,
  extract_year(location_hsca_start_date) AS year_registered,
  ```

- **Улучшенный скрипт:**
  ```sql
  NULL AS year_opened,
  extract_year(location_hsca_start_date) AS year_registered,
  ```

**Вывод:** ❌ **ПРОБЛЕМА НЕ РЕШЕНА** - оба скрипта используют `location_hsca_start_date` только для `year_registered`, но не для `year_opened`. 

**Рекомендация:** Добавить маппинг:
```sql
extract_year(location_hsca_start_date) AS year_opened,
```

---

### ⚠️ 2.3. Логика `has_nursing_care_license`

**Статус:** ⚠️ **ОБА СКРИПТА ИСПОЛЬЗУЮТ ОДИНАКОВУЮ ЛОГИКУ**

- **Текущий скрипт:**
  ```sql
  safe_boolean(regulated_activity_nursing_care) AS has_nursing_care_license,
  ```

- **Улучшенный скрипт:**
  ```sql
  safe_boolean(regulated_activity_nursing_care) AS has_nursing_care_license,
  ```

**Проблема:** В исходных данных `regulated_activity_nursing_care` всегда `FALSE`, даже для домов с nursing care (73 дома).

**Анализ из unused_fields_analysis.md:**
- `service_type_care_home_service_with_nursing = TRUE` для 73 домов
- `regulated_activity_nursing_care = TRUE` для 0 домов

**Рекомендация:** Изменить логику на:
```sql
safe_boolean(service_type_care_home_service_with_nursing) AS has_nursing_care_license,
```
ИЛИ использовать комбинацию:
```sql
COALESCE(
  safe_boolean(regulated_activity_nursing_care),
  safe_boolean(service_type_care_home_service_with_nursing)
) AS has_nursing_care_license,
```

---

## 3. НОВЫЕ ПОЛЯ В УЛУЧШЕННОМ СКРИПТЕ

### 3.1. `provider_telephone_number`

**Статус:** ✅ **ДОБАВЛЕНО В УЛУЧШЕННОМ СКРИПТЕ**

- **Улучшенный скрипт:**
  ```sql
  -- ЧАСТЬ 0: Добавление поля (если не существует)
  ALTER TABLE care_homes ADD COLUMN provider_telephone_number TEXT;
  
  -- В INSERT:
  clean_text(provider_telephone_number) AS provider_telephone_number,
  ```

- **Текущий скрипт:** ❌ Нет

**Приоритет:** Высокий (из unused_fields_analysis.md)

---

### 3.2. `provider_hsca_start_date`

**Статус:** ✅ **ДОБАВЛЕНО В УЛУЧШЕННОМ СКРИПТЕ**

- **Улучшенный скрипт:**
  ```sql
  -- ЧАСТЬ 0: Добавление поля (если не существует)
  ALTER TABLE care_homes ADD COLUMN provider_hsca_start_date DATE;
  
  -- В INSERT:
  safe_date(provider_hsca_start_date) AS provider_hsca_start_date,
  ```

- **Текущий скрипт:** ❌ Нет

**Приоритет:** Высокий (из unused_fields_analysis.md)

---

## 4. УЛУЧШЕНИЯ ФУНКЦИЙ

### 4.1. `safe_boolean()` - Улучшенная обработка TRUE/FALSE

**Текущий скрипт:**
```sql
-- Стандартная обработка
IF cleaned IN ('y', 'yes', 'true', '1', 't') THEN RETURN TRUE;
IF cleaned IN ('n', 'no', 'false', '0', 'f') THEN RETURN FALSE;
```

**Улучшенный скрипт:**
```sql
-- Явная проверка на "TRUE" и "FALSE" (заглавными)
IF upper_cleaned = 'TRUE' THEN RETURN TRUE;
IF upper_cleaned = 'FALSE' THEN RETURN FALSE;
-- + стандартная обработка
```

**Преимущество:** Явная обработка заглавных TRUE/FALSE, что важно для данных CQC.

---

### 4.2. `safe_latitude()` и `safe_longitude()` - Улучшенная обработка запятых

**Текущий скрипт:**
- Базовая обработка запятых как десятичного разделителя
- Эвристика для больших чисел

**Улучшенный скрипт:**
- Детальная обработка запятых как разделителей тысяч
- Поддержка разных форматов: `52,533,398` → `52.533398`
- Обработка отрицательных значений для longitude
- Более точное определение формата координат

**Пример из улучшенного скрипта:**
```sql
-- Если есть запятые (разделители тысяч)
IF comma_count > 1 THEN
  cleaned := REPLACE(cleaned, ',', '');
  -- Если значение очень большое (> 1000000), делим на 100000
  IF numeric_val > 1000000 THEN
    result := numeric_val / 100000.0;
  END IF;
END IF;
```

---

### 4.3. `safe_date()` - Обработка дат

**Оба скрипта:** Используют одинаковую логику с поддержкой:
- `DD/MM/YYYY` формата
- Двузначных годов (20YY для <= 50, 19YY для > 50)
- ISO формата `YYYY-MM-DD`

---

## 5. СТРУКТУРНЫЕ РАЗЛИЧИЯ

### 5.1. Метод загрузки данных

**Текущий скрипт:**
1. Создает staging таблицу `temp_cqc_raw` со всеми полями CSV
2. Загружает CSV через `\copy`
3. Выполняет INSERT SELECT из staging таблицы

**Улучшенный скрипт:**
1. Использует существующую таблицу `cqc_dataset_test`
2. Прямой INSERT SELECT без промежуточных таблиц

**Преимущество улучшенного:** Меньше шагов, проще поддержка.

**Недостаток:** Требует предварительной загрузки данных в `cqc_dataset_test`.

---

### 5.2. Обработка JSON полей

**Оба скрипта:** Используют одинаковую логику для:
- `service_types` - маппинг всех 33 `service_type_*` полей
- `service_user_bands` - маппинг всех 12 `service_user_band_*` полей
- `regulated_activities` - маппинг всех 14 `regulated_activity_*` полей
- `location_context`, `building_info`, `source_metadata` - одинаковые поля

**Улучшенный скрипт:** Имеет дополнительные поля в JSON структурах:
- `staff_information` - добавляет `registered_manager`, `nominated_individual`, `main_partner`
- `location_context` - добавляет `parliamentary_constituency`, `ccg_code`, `nhs_region`
- `building_info` - добавляет адресные данные провайдера

---

## 6. НЕИСПОЛЬЗОВАННЫЕ ПОЛЯ (из unused_fields_analysis.md)

### 6.1. Поля, которые можно добавить

**Высокий приоритет:**
1. ✅ `provider_telephone_number` - **ДОБАВЛЕНО в улучшенном скрипте**
2. ✅ `provider_hsca_start_date` - **ДОБАВЛЕНО в улучшенном скрипте**
3. ❌ `brand_id` - не добавлено (низкий приоритет)

**Средний приоритет:**
4. ❌ `provider_latitude`, `provider_longitude` - можно добавить в `building_info` JSON
5. ❌ `provider_local_authority`, `provider_region`, `provider_nhs_region`, `provider_parliamentary_constituency` - можно добавить в `building_info` JSON
6. ❌ `provider_paf_id`, `provider_uprn_id` - можно добавить в `building_info` JSON

---

## 7. КРИТИЧЕСКИЕ РАЗЛИЧИЯ И РЕКОМЕНДАЦИИ

### ✅ Что уже исправлено в обоих скриптах:

1. ✅ `publication_date` → `cqc_publication_date` - маппинг есть
2. ✅ `location_hsca_start_date` → `year_registered` - маппинг есть
3. ✅ Координаты - улучшенная обработка (в улучшенном скрипте лучше)
4. ✅ Булевы значения - улучшенная обработка (в улучшенном скрипте лучше)

### ❌ Что нужно исправить в обоих скриптах:

1. ❌ **`year_opened`** - должен маппиться из `location_hsca_start_date`:
   ```sql
   extract_year(location_hsca_start_date) AS year_opened,
   ```

2. ❌ **`has_nursing_care_license`** - логика должна использовать `service_type_care_home_service_with_nursing`:
   ```sql
   COALESCE(
     safe_boolean(regulated_activity_nursing_care),
     safe_boolean(service_type_care_home_service_with_nursing)
   ) AS has_nursing_care_license,
   ```

### ✅ Что добавлено в улучшенном скрипте (рекомендуется):

1. ✅ `provider_telephone_number` - полезный контакт
2. ✅ `provider_hsca_start_date` - дата регистрации провайдера
3. ✅ Улучшенные функции `safe_latitude()`, `safe_longitude()`, `safe_boolean()`

---

## 8. ИТОГОВЫЕ РЕКОМЕНДАЦИИ

### Для немедленного применения:

1. **Исправить `year_opened`** в обоих скриптах:
   ```sql
   extract_year(location_hsca_start_date) AS year_opened,
   ```

2. **Исправить логику `has_nursing_care_license`**:
   ```sql
   COALESCE(
     safe_boolean(regulated_activity_nursing_care),
     safe_boolean(service_type_care_home_service_with_nursing)
   ) AS has_nursing_care_license,
   ```

### Для улучшения (из улучшенного скрипта):

3. **Добавить `provider_telephone_number`**:
   - Добавить поле в таблицу (если не существует)
   - Добавить маппинг: `clean_text(provider_telephone_number) AS provider_telephone_number`

4. **Добавить `provider_hsca_start_date`**:
   - Добавить поле в таблицу (если не существует)
   - Добавить маппинг: `safe_date(provider_hsca_start_date) AS provider_hsca_start_date`

5. **Обновить функции**:
   - Скопировать улучшенные `safe_latitude()`, `safe_longitude()`, `safe_boolean()` из улучшенного скрипта

### Опционально (низкий приоритет):

6. Добавить provider геолокацию в JSON `building_info`
7. Добавить `brand_id` для связи с брендом

---

## 9. ВЫВОДЫ

### Положительные моменты:
- ✅ Оба скрипта имеют маппинг `publication_date` → `cqc_publication_date`
- ✅ Улучшенный скрипт имеет дополнительные поля (`provider_telephone_number`, `provider_hsca_start_date`)
- ✅ Улучшенный скрипт имеет более продвинутые функции обработки данных

### Критические проблемы:
- ❌ Оба скрипта **НЕ маппят** `year_opened` из `location_hsca_start_date`
- ❌ Оба скрипта используют **неправильную логику** для `has_nursing_care_license`

### Рекомендация:
**Использовать улучшенный скрипт как основу**, но **добавить исправления**:
1. Маппинг `year_opened`
2. Исправленная логика `has_nursing_care_license`

---

**Дата создания отчета:** 2025-11-03  
**Автор:** Анализ скриптов маппинга

