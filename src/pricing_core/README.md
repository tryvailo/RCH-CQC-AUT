# Pricing Core Module

Основной сервис для расчета цен и Affordability Bands версии 5.

## Функционал

1. **PricingService с методом get_full_pricing**
   - Полный расчет цены с учетом всех факторов
   - Поддержка scraped price override
   - Интеграция с postcode_resolver и data_ingestion

2. **Логика Band v5**
   - Base = Lottie 2025 regional average
   - Lower bound = MSIF 2025 median fee
   - Корректировки: CQC + nursing + dementia + facilities + size + chain
   - Band Score = (final_price - MSIF_lower) / (Lottie_average - MSIF_lower)
   - Confidence scoring с MSIF validation

3. **Price Adjustments**
   - CQC Rating: Outstanding (+15%), Good (+5%), Requires Improvement (-5%), Inadequate (-15%)
   - Nursing: +25%
   - Dementia: +12%
   - Facilities Score (0-20): Linear от -10% до +10%
   - Size: Small (<20 beds) +5%, Large (>60 beds) -5%
   - Chain: -8%

4. **Streamlit интерфейс**
   - Форма с полями
   - Мгновенный вывод Band A-E
   - Expected range
   - Confidence meter
   - Кнопка "Save as scraped price"

5. **Тесты и бенчмарк**
   - Полные тесты всех компонентов
   - Бенчмарк на 100 реальных домов

## Установка

```bash
pip install -e .
```

## Использование

### Basic Usage

```python
from pricing_core import PricingService, CareType

service = PricingService()

result = service.get_full_pricing(
    postcode="B15 2HQ",
    care_type=CareType.RESIDENTIAL,
    cqc_rating="Good",
    facilities_score=12,
    bed_count=30,
    is_chain=False
)

print(f"Final Price: £{result.final_price_gbp:.2f}/week")
print(f"Band: {result.affordability_band}")
print(f"Confidence: {result.band_confidence_percent}%")
```

### With Scraped Price

```python
result = service.get_full_pricing(
    postcode="B15 2HQ",
    care_type=CareType.RESIDENTIAL,
    scraped_price=950.0  # Overrides calculation
)
```

## Streamlit интерфейс

```bash
streamlit run src/pricing_core/streamlit_calculator.py
```

## Тестирование

```bash
pytest src/pricing_core/tests/ -v --cov=src/pricing_core
```

### Бенчмарк

```bash
pytest src/pricing_core/tests/test_benchmark.py -v --benchmark
```

## Структура модуля

```
src/pricing_core/
├── __init__.py
├── models.py              # Pydantic модели
├── service.py             # PricingService
├── adjustments.py         # Price adjustments logic
├── band_calculator.py     # Band v5 calculation
├── streamlit_calculator.py # Streamlit интерфейс
├── exceptions.py          # Исключения
└── tests/
    ├── test_adjustments.py
    ├── test_band_calculator.py
    ├── test_service.py
    └── test_benchmark.py  # Бенчмарк на 100 домов
```

## Band v5 Logic

### Band Score Formula

```
band_score = (final_price - MSIF_lower) / (Lottie_average - MSIF_lower)
```

### Band Thresholds

- **Band A**: ≤5% above MSIF lower bound
- **Band B**: 5-15% above MSIF lower bound
- **Band C**: 15-25% above MSIF lower bound
- **Band D**: 25-40% above MSIF lower bound
- **Band E**: >40% above MSIF lower bound

### Confidence Scoring

- Base: 100%
- MSIF missing: -20%
- No adjustments: -10%
- CQC rating available: +5%
- Clamped to [60%, 100%]

## Production Ready

- ✅ Полная валидация входных данных
- ✅ Обработка ошибок
- ✅ Логирование через structlog
- ✅ Интеграция с postcode_resolver и data_ingestion
- ✅ Тесты с высокой покрываемостью
- ✅ Бенчмарк на 100 реальных домов
- ✅ Streamlit интерфейс

