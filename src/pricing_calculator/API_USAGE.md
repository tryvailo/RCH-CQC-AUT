# API Usage Guide - Locations Table

## Overview

The pricing calculator module provides a FastAPI endpoint for retrieving pricing data for all UK Local Authorities, suitable for displaying in a table interface.

## API Endpoints

### 1. Get All Locations Pricing

**Endpoint:** `GET /api/pricing/locations`

**Query Parameters:**
- `care_type` (optional): Filter by care type (`residential`, `nursing`, `residential_dementia`, `nursing_dementia`, `respite`)
- `region` (optional): Filter by region (e.g., `London`, `South East`)
- `min_fair_cost` (optional): Minimum fair cost in GBP per week
- `max_fair_cost` (optional): Maximum fair cost in GBP per week
- `band` (optional): Filter by affordability band (`A`, `B`, `C`, `D`, `E`)

**Response:**
```json
{
  "total_locations": 755,
  "care_types": ["residential", "nursing", "residential_dementia", "nursing_dementia", "respite"],
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
    },
    ...
  ]
}
```

### 2. Get Pricing for Postcode

**Endpoint:** `GET /api/pricing/postcode/{postcode}`

**Query Parameters:**
- `care_type` (required): Type of care
- `cqc_rating` (optional): CQC rating
- `facilities_score` (optional): Facilities score (0-20)
- `bed_count` (optional): Number of beds
- `is_chain` (optional): Is part of a chain (boolean)

### 3. Get Regions

**Endpoint:** `GET /api/pricing/regions`

Returns list of all available regions.

### 4. Get Care Types

**Endpoint:** `GET /api/pricing/care-types`

Returns list of all available care types.

## Integration with FastAPI App

### Option 1: Include Router

```python
from fastapi import FastAPI
from pricing_calculator.api import router as pricing_router

app = FastAPI()
app.include_router(pricing_router)
```

### Option 2: Standalone App

```python
from pricing_calculator.example_api_usage import app

# Run with: uvicorn pricing_calculator.example_api_usage:app --reload
```

## Frontend Integration

### HTML Example

A complete HTML example is provided in `frontend_example.html`. It includes:

- ✅ Filterable table with all locations
- ✅ Filters: Care Type, Region, Affordability Band, Price Range
- ✅ Statistics: Total locations, Average prices
- ✅ Color-coded affordability bands
- ✅ Responsive design

### Usage

1. Start the API server:
```bash
uvicorn pricing_calculator.example_api_usage:app --reload
```

2. Open `frontend_example.html` in a browser

3. The frontend will automatically connect to `http://localhost:8000/api/pricing`

### React/Vue Example

```javascript
// Fetch all locations
const response = await fetch('http://localhost:8000/api/pricing/locations?care_type=residential&region=London');
const data = await response.json();

// data.data contains array of location pricing rows
data.data.forEach(row => {
  console.log(`${row.local_authority}: £${row.private_average_gbp}/week`);
});
```

## Example Response Structure

Each location row contains:

- `local_authority`: Name of Local Authority
- `region`: UK region name
- `care_type`: Type of care
- `fair_cost_lower_bound_gbp`: MSIF fair cost (may be null)
- `private_average_gbp`: Lottie regional average
- `affordability_band`: Band A-E
- `band_confidence_percent`: Confidence 60-100%
- `fair_cost_gap_gbp`: Difference between private and fair cost
- `fair_cost_gap_percent`: Gap as percentage

## Performance Notes

- First request may be slow as it loads MSIF data (cached afterwards)
- Postcode mapping is cached in SQLite database
- Consider pagination for large datasets (>1000 rows)

