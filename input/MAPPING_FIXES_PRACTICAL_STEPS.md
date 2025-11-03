# ПРАКТИЧНЫЕ ШАГИ ДЛЯ ИСПРАВЛЕНИЯ МАППИНГА CQC → CARE_HOMES

**Дата:** 2025-11-03  
**Основано на:** Детальном анализе маппинга CQC  
**Версия:** v2.3 - ИСПРАВЛЕННАЯ

---

## КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ (ОБЯЗАТЕЛЬНО)

### ❌ ШАГ 1: НЕ МАППИТЬ `location_hsca_start_date` → `year_opened`

**Проблема:** В текущих скриптах используется `location_hsca_start_date` для `year_opened`, но это **НЕПРАВИЛЬНО**.

**Причина:**
- `location_hsca_start_date` = дата регистрации в CQC (административная дата)
- `year_opened` = фактический год открытия дома
- Многие дома перерегистрировались в 2010 году при переходе на новую систему CQC
- Реальные дома могли работать десятилетиями до регистрации

**Действие:**
```sql
-- ❌ НЕПРАВИЛЬНО (удалить из скрипта):
extract_year(location_hsca_start_date) AS year_opened,

-- ✅ ПРАВИЛЬНО:
NULL AS year_opened,  -- Оставить пустым, данных нет в CQC
```

**Где исправить:**
- `input/cqc-to-care_homes_grok.sql` - строка ~707
- `input/mapping_improved_script.sql` - строка ~495

---

### ✅ ШАГ 2: ИСПРАВИТЬ ЛОГИКУ `has_nursing_care_license`

**Проблема:** Используется `regulated_activity_nursing_care`, но это поле **ВСЕГДА FALSE** в данных CQC.

**Статистика:**
- `service_type_care_home_service_with_nursing = TRUE`: 73 дома
- `regulated_activity_nursing_care = TRUE`: **0 домов** (все FALSE!)
- Все 73 дома с nursing имеют `has_nursing_care_license = FALSE` (неправильно!)

**Действие:**
```sql
-- ❌ НЕПРАВИЛЬНО (удалить из скрипта):
safe_boolean(regulated_activity_nursing_care) AS has_nursing_care_license,

-- ✅ ПРАВИЛЬНО:
safe_boolean(service_type_care_home_service_with_nursing) AS has_nursing_care_license,
```

**Обоснование:**
- `regulated_activity_nursing_care` не используется для care homes в данных CQC
- `service_type_care_home_service_with_nursing` - официальный маркер nursing homes
- 98.6% nursing homes имеют `regulated_activity_treatment_of_disease_disorder_or_injury = TRUE`

**Где исправить:**
- `input/cqc-to-care_homes_grok.sql` - найти строку с `has_nursing_care_license`
- `input/mapping_improved_script.sql` - строка ~502

---

### ✅ ШАГ 3: ПОДТВЕРДИТЬ МАППИНГ `publication_date` → `cqc_publication_date`

**Статус:** ✅ Уже правильно реализовано в обоих скриптах

**Проверка:**
```sql
-- Должно быть (уже есть в скриптах):
safe_date(publication_date) AS cqc_publication_date,
```

**Где проверить:**
- `input/cqc-to-care_homes_grok.sql` - строка ~737
- `input/mapping_improved_script.sql` - строка ~526

**Функция `safe_date()` должна обрабатывать:**
- Формат `DD/MM/YYYY` (например: `26/04/2022`)
- Формат `D/M/YY` (например: `1/10/20` → `2020-10-01`)
- ISO формат `YYYY-MM-DD`

---

## ДОПОЛНИТЕЛЬНЫЕ УЛУЧШЕНИЯ (РЕКОМЕНДУЕТСЯ)

### ✅ ШАГ 4: ДОБАВИТЬ `provider_telephone_number`

**Статус:** ✅ Уже добавлено в улучшенном скрипте

**Действие:**
```sql
-- 1. Добавить поле в таблицу (если не существует):
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'care_homes' 
      AND column_name = 'provider_telephone_number'
  ) THEN
    ALTER TABLE care_homes ADD COLUMN provider_telephone_number TEXT;
  END IF;
END $$;

-- 2. Добавить в INSERT:
clean_text(provider_telephone_number) AS provider_telephone_number,
```

**Где добавить:**
- Если используете улучшенный скрипт - уже есть
- Если используете текущий скрипт - добавить вручную

---

### ✅ ШАГ 5: ДОБАВИТЬ `provider_hsca_start_date`

**Статус:** ✅ Уже добавлено в улучшенном скрипте

**Действие:**
```sql
-- 1. Добавить поле в таблицу (если не существует):
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'care_homes' 
      AND column_name = 'provider_hsca_start_date'
  ) THEN
    ALTER TABLE care_homes ADD COLUMN provider_hsca_start_date DATE;
  END IF;
END $$;

-- 2. Добавить в INSERT:
safe_date(provider_hsca_start_date) AS provider_hsca_start_date,
```

**Где добавить:**
- Если используете улучшенный скрипт - уже есть
- Если используете текущий скрипт - добавить вручную

---

### ✅ ШАГ 6: ПРОВЕРИТЬ МАППИНГ ДРУГИХ ЛИЦЕНЗИЙ

**Текущий маппинг (правильный):**
```sql
safe_boolean(regulated_activity_personal_care) AS has_personal_care_license,
safe_boolean(regulated_activity_surgical_procedures) AS has_surgical_procedures_license,
safe_boolean(regulated_activity_treatment_of_disease_disorder_or_injury) AS has_treatment_license,
safe_boolean(regulated_activity_diagnostic_and_screening_procedures) AS has_diagnostic_license,
```

**Статистика использования:**
- `has_treatment_license` (75 домов, 27.7%) - ✅ активно используется
- `has_diagnostic_license` (10 домов, 3.7%) - ✅ активно используется
- `has_personal_care_license` (6 домов, 2.2%) - ✅ активно используется
- `has_surgical_procedures_license` (0 домов) - ⚠️ не используется, но логика правильная

**Вывод:** ✅ Текущий маппинг других лицензий **ПРАВИЛЬНЫЙ**, менять не нужно.

---

## ЧЕКЛИСТ ИСПРАВЛЕНИЙ

### Критические исправления (обязательно):

- [ ] **ШАГ 1:** Удалить маппинг `location_hsca_start_date` → `year_opened`
  - [ ] В `input/cqc-to-care_homes_grok.sql`
  - [ ] В `input/mapping_improved_script.sql`
  - [ ] Заменить на `NULL AS year_opened,`

- [ ] **ШАГ 2:** Исправить логику `has_nursing_care_license`
  - [ ] В `input/cqc-to-care_homes_grok.sql`
  - [ ] В `input/mapping_improved_script.sql`
  - [ ] Заменить `regulated_activity_nursing_care` на `service_type_care_home_service_with_nursing`

- [ ] **ШАГ 3:** Проверить маппинг `publication_date` → `cqc_publication_date`
  - [ ] Убедиться, что используется `safe_date(publication_date)`
  - [ ] Проверить функцию `safe_date()` на обработку форматов DD/MM/YYYY и D/M/YY

### Дополнительные улучшения (рекомендуется):

- [ ] **ШАГ 4:** Добавить `provider_telephone_number` (если нет в текущем скрипте)
- [ ] **ШАГ 5:** Добавить `provider_hsca_start_date` (если нет в текущем скрипте)
- [ ] **ШАГ 6:** Проверить другие лицензии (уже правильно)

---

## ИТОГОВАЯ ТАБЛИЦА МАППИНГА (ИСПРАВЛЕННАЯ)

| Целевое поле | Исходное поле | Функция | Статус |
|--------------|---------------|---------|--------|
| `year_opened` | ❌ **НЕТ** | `NULL` | ✅ Оставить пустым |
| `year_registered` | `location_hsca_start_date` | `extract_year()` | ✅ Правильно |
| `has_nursing_care_license` | `service_type_care_home_service_with_nursing` | `safe_boolean()` | ✅ **ИСПРАВЛЕНО** |
| `has_treatment_license` | `regulated_activity_treatment_of_disease_disorder_or_injury` | `safe_boolean()` | ✅ Правильно |
| `has_diagnostic_license` | `regulated_activity_diagnostic_and_screening_procedures` | `safe_boolean()` | ✅ Правильно |
| `has_personal_care_license` | `regulated_activity_personal_care` | `safe_boolean()` | ✅ Правильно |
| `has_surgical_procedures_license` | `regulated_activity_surgical_procedures` | `safe_boolean()` | ✅ Правильно |
| `cqc_publication_date` | `publication_date` | `safe_date()` | ✅ Правильно |
| `provider_telephone_number` | `provider_telephone_number` | `clean_text()` | ✅ Добавить |
| `provider_hsca_start_date` | `provider_hsca_start_date` | `safe_date()` | ✅ Добавить |

---

## КОД ДЛЯ КОПИРОВАНИЯ

### Исправление ШАГ 1: year_opened

```sql
-- Заменить в INSERT SELECT:
-- ❌ БЫЛО:
extract_year(location_hsca_start_date) AS year_opened,

-- ✅ СТАЛО:
NULL AS year_opened,  -- Данных о фактическом годе открытия нет в CQC
```

### Исправление ШАГ 2: has_nursing_care_license

```sql
-- Заменить в INSERT SELECT:
-- ❌ БЫЛО:
safe_boolean(regulated_activity_nursing_care) AS has_nursing_care_license,

-- ✅ СТАЛО:
safe_boolean(service_type_care_home_service_with_nursing) AS has_nursing_care_license,
```

### Добавление ШАГ 4-5: provider_telephone_number и provider_hsca_start_date

```sql
-- Добавить в начало скрипта (ЧАСТЬ 0):
DO $$
BEGIN
  -- provider_telephone_number
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'care_homes' 
      AND column_name = 'provider_telephone_number'
  ) THEN
    ALTER TABLE care_homes ADD COLUMN provider_telephone_number TEXT;
    RAISE NOTICE '✅ Добавлено поле provider_telephone_number';
  END IF;
  
  -- provider_hsca_start_date
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'care_homes' 
      AND column_name = 'provider_hsca_start_date'
  ) THEN
    ALTER TABLE care_homes ADD COLUMN provider_hsca_start_date DATE;
    RAISE NOTICE '✅ Добавлено поле provider_hsca_start_date';
  END IF;
END $$;

-- Добавить в INSERT (в список колонок):
INSERT INTO care_homes (
  ...
  provider_telephone_number,
  provider_hsca_start_date,
  ...
)

-- Добавить в SELECT (в список значений):
SELECT
  ...
  clean_text(provider_telephone_number) AS provider_telephone_number,
  safe_date(provider_hsca_start_date) AS provider_hsca_start_date,
  ...
```

---

## ВАЛИДАЦИЯ ПОСЛЕ ИСПРАВЛЕНИЙ

После применения исправлений выполните проверку:

```sql
-- Проверка 1: year_opened должен быть NULL для всех записей
SELECT COUNT(*) as total, 
       COUNT(year_opened) as with_year_opened
FROM care_homes;
-- Ожидаемый результат: with_year_opened = 0

-- Проверка 2: has_nursing_care_license должен быть TRUE для домов с nursing
SELECT 
  COUNT(*) FILTER (WHERE care_nursing = TRUE) as nursing_homes,
  COUNT(*) FILTER (WHERE care_nursing = TRUE AND has_nursing_care_license = TRUE) as with_license
FROM care_homes;
-- Ожидаемый результат: nursing_homes = with_license (все должны иметь лицензию)

-- Проверка 3: cqc_publication_date должен быть заполнен для ~91.5% записей
SELECT 
  COUNT(*) as total,
  COUNT(cqc_publication_date) as with_date,
  ROUND(100.0 * COUNT(cqc_publication_date) / COUNT(*), 1) as percentage
FROM care_homes;
-- Ожидаемый результат: percentage ≈ 91.5%
```

---

## РЕЗЮМЕ

### Критические изменения (обязательно):
1. ❌ **НЕ маппить** `location_hsca_start_date` → `year_opened` (оставить NULL)
2. ✅ **Использовать** `service_type_care_home_service_with_nursing` для `has_nursing_care_license`
3. ✅ **Подтвердить** маппинг `publication_date` → `cqc_publication_date` (уже правильно)

### Дополнительные улучшения (рекомендуется):
4. ✅ Добавить `provider_telephone_number`
5. ✅ Добавить `provider_hsca_start_date`

### Что уже правильно:
- ✅ Все остальные лицензии (`has_treatment_license`, `has_diagnostic_license`, etc.)
- ✅ Маппинг `year_registered` из `location_hsca_start_date`
- ✅ Маппинг `publication_date` → `cqc_publication_date`

---

**Дата создания:** 2025-11-03  
**Версия:** v2.3 - ИСПРАВЛЕННАЯ

