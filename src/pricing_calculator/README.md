# Pricing Calculator Module

**Version:** 1.0.0  
**Status:** Production Ready

A comprehensive pricing calculator module for RightCareHome UK care homes matching service. This module provides unified pricing calculations and Affordability Bands (A-E) based on MSIF Fair Cost data, Lottie regional averages, and postcode mapping.

---

## Features

- ✅ **MSIF Fair Cost Integration**: Automatic download and parsing of MSIF 2025-2026 fees data
- ✅ **Lottie Regional Averages**: Scraping with fallback to hardcoded constants
- ✅ **Postcode Mapping**: Cached mapping to Local Authority and Region via postcodes.io API
- ✅ **Affordability Bands**: Calculates A-E bands with confidence scores (60-100%)
- ✅ **Comprehensive Factors**: Considers CQC rating, facilities score, bed count, chain status
- ✅ **Ready-to-Use Text**: Generates negotiation leverage text for PDF reports
- ✅ **Full Type Safety**: Pydantic v2 models with validation
- ✅ **High Test Coverage**: >95% test coverage with pytest

---

## Installation

```bash
pip install pandas openpyxl httpx beautifulsoup4 selectolax "pydantic[email]" structlog
```

For development:

```bash
pip install -e ".[dev]"
```

---

## Quick Start

```python
from pricing_calculator import PricingService, CareType

# Initialize service
service = PricingService()

# Calculate pricing for a postcode
result = service.get_pricing_for_postcode(
    postcode="B15 2HQ",
    care_type=CareType.NURSING_DEMENTIA,
    cqc_rating="Outstanding",
    facilities_score=18,
    bed_count=30,
    is_chain=True
)

# Print result
print(result.model_dump_json(indent=2))
```

---

## Usage Examples

### Basic Usage

```python
from pricing_calculator import PricingService, CareType

service = PricingService()

result = service.get_pricing_for_postcode(
    postcode="SW1A 1AA",
    care_type=CareType.RESIDENTIAL
)

print(f"Affordability Band: {result.affordability_band}")
print(f"Confidence: {result.band_confidence_percent}%")
print(f"Private Average: £{result.private_average_gbp:.0f}/week")
print(f"Fair Cost Lower Bound: £{result.fair_cost_lower_bound_gbp:.0f}/week" if result.fair_cost_lower_bound_gbp else "No fair cost data")
```

### With All Factors

```python
result = service.get_pricing_for_postcode(
    postcode="B15 2HQ",
    care_type=CareType.NURSING_DEMENTIA,
    cqc_rating="Outstanding",
    facilities_score=18,
    bed_count=30,
    is_chain=True
)

print(result.negotiation_leverage_text)
```

### Accessing Individual Components

```python
from pricing_calculator import (
    get_postcode_info,
    get_lottie_price_sync,
    calculate_band,
    CareType
)

# Get postcode info
postcode_info = get_postcode_info("SW1A 1AA")
print(f"Local Authority: {postcode_info.local_authority}")
print(f"Region: {postcode_info.region}")

# Get Lottie price
price = get_lottie_price_sync("London", CareType.NURSING)
print(f"Lottie average: £{price:.0f}/week")

# Calculate band
band_result = calculate_band(
    base_private_avg=1200.0,
    fair_cost_lower=1100.0,
    cqc_rating="Outstanding",
    facilities_score=18
)
print(f"Band: {band_result.band}, Confidence: {band_result.confidence_percent}%")
```

---

## Module Structure

```
src/pricing_calculator/
├── __init__.py              # Module exports
├── models.py                # Pydantic models
├── constants.py             # Hardcoded Lottie 2025 data
├── fair_cost_loader.py      # MSIF XLS loader
├── lottie_scraper.py        # Lottie scraping
├── postcode_mapper.py        # Postcode → LA mapping
├── band_calculator.py        # Affordability band logic
├── service.py               # Main PricingService facade
├── exceptions.py            # Custom exceptions
└── tests/                    # Test suite (>95% coverage)
```

---

## Data Sources

### MSIF Fair Cost Data

- **Source**: UK Government MSIF Fees 2025-2026 XLS
- **URL**: https://assets.publishing.service.gov.uk/media/68a3021cf49bec79d23d2940/market-sustainability-and-improvement-fund-fees-2025-to-2026.xlsx
- **Fallback**: 2024-2025 version
- **Caching**: Downloaded files cached in `~/.cache/pricing_calculator/`
- **Auto-refresh**: Re-downloads if file older than 30 days

### Lottie Regional Averages

- **Source**: Lottie.org 2025 regional averages
- **URLs**:
  - Main: https://lottie.org/fees-funding/care-home-costs/
  - Dementia: https://lottie.org/fees-funding/dementia-care-home-costs/
  - Respite: https://lottie.org/fees-funding/cost-of-respite-care/
- **Fallback**: Hardcoded constants in `constants.py`
- **Scraping**: Async scraping with BeautifulSoup/selectolax

### Postcode Mapping

- **Source**: postcodes.io API
- **URL**: https://api.postcodes.io/postcodes/{postcode}
- **Caching**: SQLite database in `~/.cache/pricing_calculator/postcode_cache.db`
- **Expiry**: 90 days cache expiry

---

## Affordability Bands

### Band Definitions

- **A**: Excellent value (≤5% above fair cost, or <£800/week)
- **B**: Good value (5-15% above fair cost, or £800-950/week)
- **C**: Fair value (15-25% above fair cost, or £950-1100/week)
- **D**: Premium pricing (25-40% above fair cost, or £1100-1300/week)
- **E**: Very expensive (>40% above fair cost, or >£1300/week)

### Confidence Adjustments

- Base confidence: 80%
- +10% if fair cost data available
- +5% if CQC rating is Outstanding
- +5% if facilities_score ≥ 15
- -5% if facilities_score < 10
- -5% if bed_count < 10
- +5% if is_chain = True

---

## API Reference

### PricingService

Main service class for pricing calculations.

#### `__init__(cache_dir: Optional[str] = None)`

Initialize PricingService.

#### `get_pricing_for_postcode(...) -> PricingResult`

Calculate complete pricing for a postcode and care type.

**Parameters:**
- `postcode: str` - UK postcode
- `care_type: CareType` - Type of care
- `cqc_rating: Optional[str]` - CQC rating (Outstanding/Good/Requires Improvement/Inadequate)
- `facilities_score: Optional[int]` - Facilities score (0-20)
- `bed_count: Optional[int]` - Number of beds
- `is_chain: bool` - Whether care home is part of a chain

**Returns:** `PricingResult`

### Models

#### `CareType` (Enum)

- `RESIDENTIAL`
- `NURSING`
- `RESIDENTIAL_DEMENTIA`
- `NURSING_DEMENTIA`
- `RESPITE`

#### `PricingResult` (Pydantic Model)

Complete pricing calculation result with all fields.

#### `PostcodeInfo` (Pydantic Model)

Postcode information (Local Authority, Region, County, Country).

#### `BandResult` (Pydantic Model)

Affordability band calculation result (band, confidence, reasoning).

---

## Testing

Run tests with pytest:

```bash
pytest src/pricing_calculator/tests/ -v
```

Run with coverage:

```bash
pytest src/pricing_calculator/tests/ --cov=src/pricing_calculator --cov-report=html
```

Coverage target: **>95%**

---

## Error Handling

All exceptions inherit from `PricingCalculatorError`:

- `FairCostDataError`: MSIF data loading/parsing errors
- `LottieScrapingError`: Lottie scraping errors
- `PostcodeMappingError`: Postcode mapping errors
- `BandCalculationError`: Band calculation errors
- `InvalidCareTypeError`: Invalid care type
- `InvalidPostcodeError`: Invalid postcode format

---

## Caching

The module uses local caching for:

1. **MSIF XLS files**: `~/.cache/pricing_calculator/msif_*.xlsx`
2. **Postcode mappings**: `~/.cache/pricing_calculator/postcode_cache.db`

Cache directories are created automatically.

---

## Future Enhancements

- [ ] Add per-home scraped pricing data integration
- [ ] Support for Scotland, Wales, Northern Ireland
- [ ] Historical pricing trends
- [ ] Batch processing API
- [ ] Redis caching option
- [ ] Async PricingService methods

---

## License

MIT License

---

## Support

For issues and questions, please open an issue on GitHub or contact the development team.

