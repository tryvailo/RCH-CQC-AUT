#!/bin/bash

# Скрипт для полной проверки маппинга полей CQC → care_homes v2.2

CSV_FILE="../input/CQC-DataSet_rows.csv"
SQL_FILE="step2_run_migration.sql"
DOC_FILE="../input/Product_Manager_Guide_CQC.md"

echo "=== ПРОВЕРКА МАППИНГА ПОЛЕЙ CQC → care_homes v2.2 ==="
echo ""

# 1. Проверка критичных полей
echo "1. ПРОВЕРКА КРИТИЧНЫХ ПОЛЕЙ:"
echo ""

# Проверка beds_total
echo "✓ beds_total:"
if grep -q "safe_integer(care_homes_beds)" "$SQL_FILE"; then
    echo "  ✅ Использует care_homes_beds"
else
    echo "  ❌ ОШИБКА: Не найдено safe_integer(care_homes_beds)"
fi

# Проверка координат
echo "✓ latitude:"
if grep -q "safe_latitude(location_latitude)" "$SQL_FILE"; then
    echo "  ✅ Использует location_latitude"
else
    echo "  ❌ ОШИБКА: Не найдено safe_latitude(location_latitude)"
fi

echo "✓ longitude:"
if grep -q "safe_longitude(location_longitude)" "$SQL_FILE"; then
    echo "  ✅ Использует location_longitude"
else
    echo "  ❌ ОШИБКА: Не найдено safe_longitude(location_longitude)"
fi

# Проверка service_user_band полей
echo ""
echo "2. ПРОВЕРКА SERVICE_USER_BAND ПОЛЕЙ:"
echo ""

FIELDS=(
    "service_user_band_children_0_18_years"
    "service_user_band_people_detained_under_the_mental_health_act"
    "service_user_band_people_who_misuse_drugs_and_alcohol"
    "service_user_band_learning_disabilities_or_autistic_spectrum_di"
)

for field in "${FIELDS[@]}"; do
    if grep -q "$field" "$SQL_FILE"; then
        echo "  ✅ $field"
    else
        echo "  ❌ ОШИБКА: $field не найден"
    fi
done

# Проверка regulated_activity полей
echo ""
echo "3. ПРОВЕРКА REGULATED_ACTIVITY ПОЛЕЙ:"
echo ""

REGULATED=(
    "regulated_activity_nursing_care"
    "regulated_activity_personal_care"
    "regulated_activity_surgical_procedures"
    "regulated_activity_treatment_of_disease_disorder_or_injury"
    "regulated_activity_diagnostic_and_screening_procedures"
)

for field in "${REGULATED[@]}"; do
    if grep -q "$field" "$SQL_FILE"; then
        echo "  ✅ $field"
    else
        echo "  ❌ ОШИБКА: $field не найден"
    fi
done

# Проверка service_type полей
echo ""
echo "4. ПРОВЕРКА SERVICE_TYPE ПОЛЕЙ:"
echo ""

SERVICE_TYPES=(
    "service_type_care_home_service_without_nursing"
    "service_type_care_home_service_with_nursing"
)

for field in "${SERVICE_TYPES[@]}"; do
    if grep -q "$field" "$SQL_FILE"; then
        echo "  ✅ $field"
    else
        echo "  ❌ ОШИБКА: $field не найден"
    fi
done

# Проверка CQC рейтингов
echo ""
echo "5. ПРОВЕРКА CQC РЕЙТИНГОВ:"
echo ""

RATINGS=(
    "location_latest_overall_rating"
    "cqc_rating_safe"
    "cqc_rating_effective"
    "cqc_rating_caring"
    "cqc_rating_responsive"
    "cqc_rating_well_led"
)

for field in "${RATINGS[@]}"; do
    if grep -q "$field" "$SQL_FILE"; then
        echo "  ✅ $field"
    else
        echo "  ❌ ОШИБКА: $field не найден"
    fi
done

# Проверка телефона (должен быть TEXT)
echo ""
echo "6. ПРОВЕРКА ТЕЛЕФОНА:"
if grep -q "clean_text(location_telephone_number) AS telephone" "$SQL_FILE"; then
    echo "  ✅ Телефон правильно маппится как TEXT (clean_text)"
else
    echo "  ❌ ОШИБКА: Телефон должен быть TEXT!"
fi

# Проверка веб-сайта (COALESCE)
echo ""
echo "7. ПРОВЕРКА ВЕБ-САЙТА:"
if grep -q "COALESCE.*location_web_address.*provider_web_address" "$SQL_FILE"; then
    echo "  ✅ Веб-сайт использует COALESCE (fallback логика)"
else
    echo "  ❌ ОШИБКА: Веб-сайт должен использовать COALESCE!"
fi

echo ""
echo "=== ПРОВЕРКА ЗАВЕРШЕНА ==="

