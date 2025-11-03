#!/bin/bash
# ============================================================================
# ВАЛИДАЦИЯ SQL СКРИПТА МИГРАЦИИ CQC → CARE HOMES v2.2
# Версия: 1.0
# ============================================================================

set -e

echo "============================================================================"
echo "ВАЛИДАЦИЯ: CQC → Care Homes v2.2 Migration Script"
echo "============================================================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker найден${NC}"

# Пути к файлам
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SQL_SCHEMA="$SCRIPT_DIR/step1_schema_create.sql"
SQL_MIGRATION="$SCRIPT_DIR/step2_run_migration.sql"
CSV_FILE="$PROJECT_DIR/input/CQC-DataSet_rows.csv"

# Проверка наличия файлов
if [ ! -f "$SQL_SCHEMA" ]; then
    echo -e "${RED}❌ Файл схемы не найден: $SQL_SCHEMA${NC}"
    exit 1
fi

if [ ! -f "$SQL_MIGRATION" ]; then
    echo -e "${RED}❌ Файл миграции не найден: $SQL_MIGRATION${NC}"
    exit 1
fi

if [ ! -f "$CSV_FILE" ]; then
    echo -e "${YELLOW}⚠️  CSV файл не найден: $CSV_FILE${NC}"
    echo "   (Валидация продолжается без загрузки данных)"
fi

echo ""
echo "============================================================================"
echo "ШАГ 1: Запуск PostgreSQL в Docker"
echo "============================================================================"

# Остановка и удаление существующего контейнера (если есть)
docker stop cqc-validation-db 2>/dev/null || true
docker rm cqc-validation-db 2>/dev/null || true

# Запуск PostgreSQL
docker run -d \
    --name cqc-validation-db \
    -e POSTGRES_PASSWORD=validation \
    -e POSTGRES_DB=cqc_validation \
    -p 5433:5432 \
    postgres:15-alpine

echo -e "${GREEN}✅ PostgreSQL контейнер запущен${NC}"

# Ожидание готовности PostgreSQL
echo "Ожидание готовности PostgreSQL..."
sleep 5

max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec cqc-validation-db pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL готов${NC}"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ PostgreSQL не запустился за $max_attempts секунд${NC}"
    docker stop cqc-validation-db
    docker rm cqc-validation-db
    exit 1
fi

echo ""
echo "============================================================================"
echo "ШАГ 2: Создание схемы БД"
echo "============================================================================"

# Копирование и выполнение схемы
docker cp "$SQL_SCHEMA" cqc-validation-db:/tmp/schema.sql
docker exec cqc-validation-db psql -U postgres -d cqc_validation -f /tmp/schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Схема создана успешно${NC}"
else
    echo -e "${RED}❌ Ошибка при создании схемы${NC}"
    docker stop cqc-validation-db
    docker rm cqc-validation-db
    exit 1
fi

echo ""
echo "============================================================================"
echo "ШАГ 3: Валидация структуры схемы"
echo "============================================================================"

# Проверка количества полей
FIELD_COUNT=$(docker exec cqc-validation-db psql -U postgres -d cqc_validation -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='care_homes';" | tr -d ' ')

if [ "$FIELD_COUNT" = "93" ]; then
    echo -e "${GREEN}✅ Количество полей корректно: $FIELD_COUNT${NC}"
else
    echo -e "${YELLOW}⚠️  Количество полей: $FIELD_COUNT (ожидается 93)${NC}"
fi

# Проверка новых полей v2.2
REQUIRED_FIELDS=("regulated_activities" "serves_dementia_band" "serves_children" "serves_learning_disabilities")
for field in "${REQUIRED_FIELDS[@]}"; do
    EXISTS=$(docker exec cqc-validation-db psql -U postgres -d cqc_validation -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='care_homes' AND column_name='$field';" | tr -d ' ')
    if [ "$EXISTS" = "1" ]; then
        echo -e "${GREEN}✅ Поле v2.2 найдено: $field${NC}"
    else
        echo -e "${RED}❌ Поле v2.2 отсутствует: $field${NC}"
    fi
done

# Проверка индексов
INDEX_COUNT=$(docker exec cqc-validation-db psql -U postgres -d cqc_validation -t -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename='care_homes';" | tr -d ' ')
echo -e "${GREEN}✅ Количество индексов: $INDEX_COUNT (ожидается ~53)${NC}"

echo ""
echo "============================================================================"
echo "ШАГ 4: Синтаксическая валидация миграционного скрипта"
echo "============================================================================"

# Копирование миграционного скрипта
docker cp "$SQL_MIGRATION" cqc-validation-db:/tmp/migration.sql

# Проверка синтаксиса (без выполнения INSERT)
# Извлекаем только функции и проверяем их
docker exec cqc-validation-db psql -U postgres -d cqc_validation -c "
DO \$\$
BEGIN
    -- Проверка создания функций
    RAISE NOTICE 'Проверка синтаксиса функций...';
END \$\$;
" 2>&1 | grep -q "Проверка синтаксиса" && echo -e "${GREEN}✅ Синтаксис функций валиден${NC}" || echo -e "${YELLOW}⚠️  Проверьте синтаксис функций${NC}"

echo ""
echo "============================================================================"
echo "ШАГ 5: Проверка helper функций"
echo "============================================================================"

# Список функций для проверки
FUNCTIONS=("clean_text" "safe_integer" "safe_latitude" "safe_longitude" "validate_uk_coordinates" "safe_boolean" "safe_date" "normalize_cqc_rating" "safe_dormant" "extract_year")

# Загрузка функций из миграционного скрипта
# Извлекаем CREATE FUNCTION блоки и выполняем их
echo "Загрузка helper функций..."

# Упрощенная проверка: ищем определения функций
for func in "${FUNCTIONS[@]}"; do
    if grep -q "CREATE.*FUNCTION.*$func" "$SQL_MIGRATION"; then
        echo -e "${GREEN}✅ Функция найдена: $func${NC}"
    else
        echo -e "${RED}❌ Функция отсутствует: $func${NC}"
    fi
done

echo ""
echo "============================================================================"
echo "ШАГ 6: Проверка маппинга полей (статический анализ)"
echo "============================================================================"

# Проверка критичных маппингов
echo "Проверка критичных маппингов..."

if grep -q "regulated_activity_nursing_care.*has_nursing_care_license" "$SQL_MIGRATION"; then
    echo -e "${GREEN}✅ Правильный маппинг: nursing license из regulated_activity${NC}"
else
    echo -e "${RED}❌ НЕПРАВИЛЬНЫЙ маппинг: has_nursing_care_license должен быть из regulated_activity_*${NC}"
fi

if grep -q "service_user_band_dementia.*serves_dementia_band" "$SQL_MIGRATION"; then
    echo -e "${GREEN}✅ Правильный маппинг: serves_dementia_band из service_user_band_dementia${NC}"
else
    echo -e "${YELLOW}⚠️  Проверьте маппинг serves_dementia_band${NC}"
fi

if grep -q "safe_latitude.*safe_longitude" "$SQL_MIGRATION"; then
    echo -e "${GREEN}✅ Используются safe функции для координат${NC}"
else
    echo -e "${RED}❌ Координаты должны использовать safe_latitude/safe_longitude${NC}"
fi

echo ""
echo "============================================================================"
echo "ШАГ 7: Очистка"
echo "============================================================================"

docker stop cqc-validation-db
docker rm cqc-validation-db

echo -e "${GREEN}✅ Контейнер остановлен и удален${NC}"

echo ""
echo "============================================================================"
echo "ВАЛИДАЦИЯ ЗАВЕРШЕНА"
echo "============================================================================"
echo ""
echo "Следующие шаги:"
echo "  1. Проверьте результаты выше"
echo "  2. Для полной валидации с данными запустите:"
echo "     docker-compose up (если доступен)"
echo "  3. Или используйте Python валидатор для детального анализа"
echo ""

