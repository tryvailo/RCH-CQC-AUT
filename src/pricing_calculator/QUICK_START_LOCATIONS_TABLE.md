# 🚀 Quick Start: Locations Table Interface

## Что создано

✅ **API Endpoint** для получения данных по всем локациям  
✅ **HTML интерфейс** с таблицей и фильтрами  
✅ **Метод в PricingService** для генерации данных  

---

## Быстрый старт

### 1. Установить зависимости

```bash
pip install fastapi uvicorn
```

### 2. Запустить API сервер

```bash
cd src/pricing_calculator
python -m uvicorn example_api_usage:app --reload --port 8000
```

Или из корня проекта:

```bash
python -m uvicorn pricing_calculator.example_api_usage:app --reload --port 8000
```

### 3. Открыть HTML интерфейс

Откройте файл `src/pricing_calculator/frontend_example.html` в браузере.

Интерфейс автоматически подключится к `http://localhost:8000/api/pricing`

---

## API Endpoints

### Получить все локации

```
GET /api/pricing/locations?care_type=residential&region=London
```

**Параметры фильтрации:**
- `care_type`: `residential`, `nursing`, `residential_dementia`, `nursing_dementia`, `respite`
- `region`: `London`, `South East`, `West Midlands`, etc.
- `band`: `A`, `B`, `C`, `D`, `E`
- `min_fair_cost`: минимальная цена (GBP/week)
- `max_fair_cost`: максимальная цена (GBP/week)

**Пример ответа:**
```json
{
  "total_locations": 151,
  "care_types": ["residential", "nursing", ...],
  "data": [
    {
      "local_authority": "Birmingham",
      "region": "West Midlands",
      "care_type": "residential",
      "fair_cost_lower_bound_gbp": 813.87,
      "private_average_gbp": 750.0,
      "affordability_band": "A",
      "band_confidence_percent": 90,
      "fair_cost_gap_gbp": -63.87,
      "fair_cost_gap_percent": -7.8
    }
  ]
}
```

---

## Интеграция в существующее FastAPI приложение

```python
from fastapi import FastAPI
from pricing_calculator.api import router as pricing_router

app = FastAPI(title="Your App")
app.include_router(pricing_router)
```

---

## Что показывает таблица

- **Local Authority** - название местного органа власти
- **Region** - регион UK
- **Care Type** - тип ухода
- **Fair Cost** - справедливая стоимость (MSIF)
- **Private Avg** - средняя частная цена (Lottie)
- **Gap** - разница между частной и справедливой ценой
- **Band** - Affordability Band (A-E) с цветовой кодировкой
- **Confidence** - уверенность в расчете (%)

---

## Фильтры

Таблица поддерживает фильтрацию по:
- ✅ Типу ухода (Care Type)
- ✅ Региону (Region)
- ✅ Affordability Band
- ✅ Диапазону цен (Min/Max Fair Cost)

---

## Статистика

В верхней части таблицы отображается:
- Общее количество локаций
- Средняя справедливая стоимость
- Средняя частная стоимость

---

## Примеры использования

### Получить только London residential care

```
GET /api/pricing/locations?care_type=residential&region=London
```

### Получить только Band A (excellent value)

```
GET /api/pricing/locations?band=A
```

### Получить локации с ценой от £800 до £1000

```
GET /api/pricing/locations?min_fair_cost=800&max_fair_cost=1000
```

---

## Готово к использованию!

Интерфейс полностью готов. Просто запустите API сервер и откройте HTML файл.

