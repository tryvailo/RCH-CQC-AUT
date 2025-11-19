# Funding Calculator Module

Модуль для расчета финансирования ухода и потенциальной экономии.

## Функционал

1. **FundingEligibilityCalculator**
   - Расчет CHC (Continuing Healthcare) probability
   - Расчет LA top-up probability
   - Определение Deferred Payment eligibility
   - Расчет потенциальной экономии

2. **FairCostGapCalculator**
   - Расчет Fair Cost Gap (weekly/yearly/5-year)
   - Генерация эмоционального текста для отчетов
   - HTML и Markdown блоки для вставки в отчеты

3. **Streamlit интерфейс "Savings Calculator"**
   - Квиз из 7 вопросов
   - Большой красный блок Fair Cost Gap
   - Зеленый блок потенциальной экономии
   - CTA "Получить полный отчёт £119"

4. **PDF генератор**
   - Jinja шаблоны для HTML и Markdown
   - Генерация отчетов из результатов расчетов

## Установка

```bash
pip install -e .
```

## Использование

### Funding Eligibility

```python
from funding_calculator import FundingEligibilityCalculator, PatientProfile

calculator = FundingEligibilityCalculator()

profile = PatientProfile(
    age=85,
    has_primary_health_need=True,
    has_dementia=True,
    requires_nursing_care=True,
    capital_assets=100000.0,
    care_cost_per_week=1200.0
)

result = calculator.calculate_full_eligibility(profile)

print(f"CHC Probability: {result.chc_eligibility.probability_percent}%")
print(f"Potential Savings: £{result.potential_savings_per_year:,.0f}/year")
```

### Fair Cost Gap

```python
from funding_calculator import FairCostGapCalculator

calculator = FairCostGapCalculator()

result = calculator.calculate_gap(weekly_gap=150.0, emotional_tone="empathetic")

print(result.emotional_text)
print(result.report_block_html)  # For HTML reports
print(result.report_block_markdown)  # For Markdown reports
```

### PDF Report Generation

```python
from funding_calculator import PDFReportGenerator

generator = PDFReportGenerator()

html_report = generator.generate_html_report(eligibility_result, fair_cost_result)
markdown_report = generator.generate_markdown_report(eligibility_result, fair_cost_result)
```

## Streamlit интерфейс

```bash
streamlit run src/funding_calculator/streamlit_savings.py
```

## CHC Eligibility Factors

- Primary Health Need: 40 points
- Nursing Care: 25 points
- Dementia: 15 points
- Parkinson's: 15 points
- Stroke: 10 points
- Heart Condition: 10 points
- Bedbound: 20 points
- Wheelchair: 10 points
- Medication Management: 10 points

## LA Funding Thresholds (2025-2026)

- **Fully Funded**: Capital < £23,250
- **Partial Funding**: Capital £23,250 - £186,000
- **Self-Funding**: Capital > £186,000 (eligible for Deferred Payment)

## Структура модуля

```
src/funding_calculator/
├── __init__.py
├── models.py                  # Pydantic модели
├── chc_calculator.py         # CHC и LA funding calculator
├── fair_cost_gap.py          # Fair Cost Gap calculator
├── pdf_generator.py          # PDF report generator
├── streamlit_savings.py      # Streamlit интерфейс
├── exceptions.py             # Исключения
├── templates/
│   ├── report_template.html  # HTML шаблон
│   └── report_template.md    # Markdown шаблон
└── tests/
    ├── test_chc_calculator.py
    ├── test_fair_cost_gap.py
    └── test_pdf_generator.py
```

## Production Ready

- ✅ Правило-базированная логика CHC eligibility
- ✅ Расчет LA funding с учетом thresholds
- ✅ Эмоциональный текст для конверсии
- ✅ Jinja шаблоны для PDF генерации
- ✅ Streamlit интерфейс с квизом
- ✅ Тесты всех компонентов

