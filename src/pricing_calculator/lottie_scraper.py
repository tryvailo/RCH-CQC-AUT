"""Scrape Lottie 2025 regional averages from website."""

from typing import Dict, Optional
from pathlib import Path
import httpx
import structlog
from selectolax.parser import HTMLParser
from .models import CareType
from .constants import LOTTIE_2025_REGIONAL_AVERAGES, get_lottie_average
from .exceptions import LottieScrapingError

logger = structlog.get_logger(__name__)

# Lottie URLs
LOTTIE_MAIN_URL = "https://lottie.org/fees-funding/care-home-costs/"
LOTTIE_DEMENTIA_URL = "https://lottie.org/fees-funding/dementia-care-home-costs/"
LOTTIE_RESPITE_URL = "https://lottie.org/fees-funding/cost-of-respite-care/"


def _extract_prices_from_html(html_content: str, care_type: str) -> Dict[str, float]:
    """
    Extract regional prices from HTML content.
    
    Args:
        html_content: HTML content from Lottie page
        care_type: Care type identifier (residential, nursing, etc.)
        
    Returns:
        Dict mapping: {region: price_per_week}
    """
    import re
    
    parser = HTMLParser(html_content)
    result: Dict[str, float] = {}
    
    # Region name mapping
    REGIONS = {
        "London": ["London", "Greater London"],
        "South East": ["South East", "South East England"],
        "South West": ["South West", "South West England"],
        "West Midlands": ["West Midlands"],
        "East Midlands": ["East Midlands"],
        "Yorkshire and the Humber": ["Yorkshire", "Yorkshire and the Humber"],
        "North West": ["North West", "North West England"],
        "North East": ["North East", "North East England"],
        "East of England": ["East of England", "East England"],
    }
    
    # Look for tables
    tables = parser.css("table")
    
    for table in tables:
        rows = table.css("tr")
        
        for row in rows:
            cells = [cell.text(strip=True) for cell in row.css("td, th")]
            
            if len(cells) < 2:
                continue
            
            # Look for region names and prices
            for i, cell in enumerate(cells):
                cell_lower = cell.lower()
                
                # Check if this cell contains a region name
                matched_region = None
                for region, aliases in REGIONS.items():
                    if any(alias.lower() in cell_lower for alias in aliases):
                        matched_region = region
                        break
                
                if matched_region:
                    # Look for prices in nearby cells
                    prices_found = []
                    for j in range(max(0, i-2), min(len(cells), i+3)):
                        price_cell = cells[j]
                        # Look for £ amount
                        price_matches = re.findall(r'£[\d,]+', price_cell.replace(',', ''))
                        for price_match in price_matches:
                            price_str = price_match.replace('£', '').replace(',', '')
                            try:
                                price = float(price_str)
                                # Filter reasonable prices (between £500 and £3000 per week)
                                if 500 <= price <= 3000:
                                    prices_found.append(price)
                            except ValueError:
                                pass
                    
                    # Use the first reasonable price found
                    if prices_found:
                        # For main page, typically first price is residential, second is nursing
                        # But we'll take average or first depending on care_type
                        if matched_region not in result:
                            result[matched_region] = prices_found[0]
                        else:
                            # If multiple prices found, use average
                            result[matched_region] = sum(prices_found) / len(prices_found)
    
    return result


async def fetch_lottie_averages(
    use_fallback: bool = True,
    save_to_constants: bool = False
) -> Dict[str, Dict[str, float]]:
    """
    Fetch Lottie 2025 regional averages from website.
    
    Args:
        use_fallback: If True, fallback to constants.py if scraping fails.
        save_to_constants: If True, save scraped data to constants.py (not implemented).
        
    Returns:
        Dict mapping: {region: {care_type: price_per_week}}
    """
    logger.info("Fetching Lottie averages")
    
    result: Dict[str, Dict[str, float]] = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch main page (residential and nursing)
            try:
                response = await client.get(LOTTIE_MAIN_URL)
                response.raise_for_status()
                html = response.text
                
                # Extract residential prices (typically first price in table)
                residential_prices = _extract_prices_from_html(html, "residential")
                
                # For main page, we need to distinguish residential vs nursing
                # Typically tables have two columns: residential and nursing
                # We'll extract both
                parser = HTMLParser(html)
                tables = parser.css("table")
                
                for table in tables:
                    rows = table.css("tr")
                    for row in rows:
                        cells = [cell.text(strip=True) for cell in row.css("td, th")]
                        if len(cells) >= 3:  # Region + Residential + Nursing
                            # Try to identify region
                            region = None
                            for i, cell in enumerate(cells):
                                cell_lower = cell.lower()
                                if "london" in cell_lower:
                                    region = "London"
                                elif "south east" in cell_lower:
                                    region = "South East"
                                elif "south west" in cell_lower:
                                    region = "South West"
                                elif "west midlands" in cell_lower:
                                    region = "West Midlands"
                                elif "east midlands" in cell_lower:
                                    region = "East Midlands"
                                elif "yorkshire" in cell_lower:
                                    region = "Yorkshire and the Humber"
                                elif "north west" in cell_lower:
                                    region = "North West"
                                elif "north east" in cell_lower:
                                    region = "North East"
                                elif "east of england" in cell_lower or "east england" in cell_lower:
                                    region = "East of England"
                                
                                if region:
                                    # Extract prices from remaining cells
                                    import re
                                    prices = []
                                    for j in range(i+1, min(len(cells), i+4)):
                                        price_matches = re.findall(r'£[\d,]+', cells[j].replace(',', ''))
                                        for pm in price_matches:
                                            try:
                                                p = float(pm.replace('£', '').replace(',', ''))
                                                if 500 <= p <= 3000:
                                                    prices.append(p)
                                            except ValueError:
                                                pass
                                    
                                    if prices and region:
                                        if region not in result:
                                            result[region] = {}
                                        # First price is typically residential, second is nursing
                                        if len(prices) >= 1:
                                            result[region]["residential"] = prices[0]
                                        if len(prices) >= 2:
                                            result[region]["nursing"] = prices[1]
                                        elif len(prices) == 1:
                                            # If only one price, use for both (with nursing premium)
                                            result[region]["nursing"] = prices[0] * 1.15
                
                logger.info("Scraped Lottie main page", regions=len(result))
                
            except Exception as e:
                logger.warning("Failed to scrape main page", error=str(e))
                if not use_fallback:
                    raise LottieScrapingError(f"Failed to scrape Lottie: {e}") from e
            
            # Fetch dementia page
            try:
                response = await client.get(LOTTIE_DEMENTIA_URL)
                response.raise_for_status()
                html = response.text
                dementia_prices = _extract_prices_from_html(html, "dementia")
                
                for region, price in dementia_prices.items():
                    if region not in result:
                        result[region] = {}
                    result[region]["residential_dementia"] = price
                    result[region]["nursing_dementia"] = price * 1.1  # Estimate
                
                logger.info("Scraped Lottie dementia page")
            except Exception as e:
                logger.warning("Failed to scrape dementia page", error=str(e))
            
            # Fetch respite page
            try:
                response = await client.get(LOTTIE_RESPITE_URL)
                response.raise_for_status()
                html = response.text
                respite_prices = _extract_prices_from_html(html, "respite")
                
                for region, price in respite_prices.items():
                    if region not in result:
                        result[region] = {}
                    result[region]["respite"] = price
                
                logger.info("Scraped Lottie respite page")
            except Exception as e:
                logger.warning("Failed to scrape respite page", error=str(e))
        
        # Fill in missing care types with estimates
        for region in result:
            if "residential" in result[region] and "residential_dementia" not in result[region]:
                result[region]["residential_dementia"] = result[region]["residential"] * 1.12
            if "nursing" in result[region] and "nursing_dementia" not in result[region]:
                result[region]["nursing_dementia"] = result[region]["nursing"] * 1.12
            if "residential" in result[region] and "respite" not in result[region]:
                result[region]["respite"] = result[region]["residential"]
        
        # If scraping failed or incomplete, use fallback
        if not result and use_fallback:
            logger.info("Using fallback constants data")
            return LOTTIE_2025_REGIONAL_AVERAGES
        
        return result
        
    except Exception as e:
        logger.error("Lottie scraping failed", error=str(e))
        if use_fallback:
            logger.info("Falling back to constants data")
            return LOTTIE_2025_REGIONAL_AVERAGES
        raise LottieScrapingError(f"Failed to scrape Lottie: {e}") from e


def get_lottie_price_sync(region: str, care_type: CareType) -> float:
    """
    Synchronous wrapper to get Lottie price.
    Uses constants fallback.
    
    Args:
        region: UK region name
        care_type: Care type
        
    Returns:
        Average price per week in GBP
    """
    return get_lottie_average(region, care_type)

