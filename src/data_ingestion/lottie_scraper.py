"""Lottie website scraper for regional averages."""

import re
import json
from pathlib import Path
from typing import Dict, Optional
import httpx
from selectolax.parser import HTMLParser
import structlog
from .config import config
from .exceptions import LottieScrapingError
from .database import get_db_connection

logger = structlog.get_logger(__name__)


class LottieScraper:
    """Scrape Lottie website for regional care home price averages."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize Lottie scraper.
        
        Args:
            cache_dir: Optional cache directory for HTML files
        """
        self.cache_dir = cache_dir or config.cache_dir / "lottie"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_page(self, url: str) -> str:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            LottieScrapingError: If fetch fails
        """
        logger.info("Fetching Lottie page", url=url)
        
        try:
            with httpx.Client(timeout=config.http_timeout) as client:
                response = client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()
                
                html_content = response.text
                logger.info("Fetched Lottie page", url=url, size_bytes=len(html_content))
                
                # Cache HTML
                cache_file = self.cache_dir / f"{url.split('/')[-2]}.html"
                cache_file.write_text(html_content, encoding='utf-8')
                
                return html_content
        except httpx.HTTPError as e:
            raise LottieScrapingError(f"Failed to fetch Lottie page {url}: {e}") from e
        except Exception as e:
            raise LottieScrapingError(f"Unexpected error fetching Lottie page {url}: {e}") from e
    
    def extract_regional_prices(self, html_content: str, care_type: str) -> Dict[str, float]:
        """
        Extract regional prices from HTML content.
        
        Args:
            html_content: HTML content from Lottie page
            care_type: Care type identifier (residential, nursing, dementia)
            
        Returns:
            Dict mapping: {region: price_per_week}
        """
        parser = HTMLParser(html_content)
        result: Dict[str, float] = {}
        
        # Check if page content is loaded (might be JavaScript-rendered)
        if len(html_content) < 1000:
            logger.warning("HTML content seems too short, might be JavaScript-rendered", 
                          content_length=len(html_content))
        
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
        
        # Debug: Check what we have
        pound_count = html_content.count('£')
        tables = parser.css("table")
        logger.debug("Parsing HTML", 
                    content_length=len(html_content),
                    pound_symbols=pound_count,
                    tables_found=len(tables))
        
        # Look for tables
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
                            if matched_region not in result:
                                result[matched_region] = prices_found[0]
                            else:
                                # If multiple prices found, use average
                                result[matched_region] = sum(prices_found) / len(prices_found)
        
        # Also try to find prices in divs/spans with specific classes
        price_elements = parser.css("div.price, span.price, [class*='price'], [class*='cost']")
        for elem in price_elements:
            text = elem.text(strip=True)
            price_matches = re.findall(r'£[\d,]+', text.replace(',', ''))
            for price_match in price_matches:
                price_str = price_match.replace('£', '').replace(',', '')
                try:
                    price = float(price_str)
                    if 500 <= price <= 3000:
                        # Try to find associated region in parent or sibling elements
                        parent = elem.parent
                        if parent:
                            parent_text = parent.text(strip=True)
                            for region, aliases in REGIONS.items():
                                if any(alias.lower() in parent_text.lower() for alias in aliases):
                                    if region not in result:
                                        result[region] = price
                                    break
                except ValueError:
                    pass
        
        # Try to extract from JSON-LD or script tags (common for JS-rendered content)
        script_tags = parser.css("script")
        for script in script_tags:
            script_text = script.text()
            if script_text and ('price' in script_text.lower() or 'cost' in script_text.lower()):
                # Try to find JSON data
                json_matches = re.findall(r'\{[^{}]*"price"[^{}]*\}', script_text)
                for json_match in json_matches:
                    try:
                        import json
                        data = json.loads(json_match)
                        if 'price' in data:
                            price = float(str(data['price']).replace('£', '').replace(',', ''))
                            if 500 <= price <= 3000:
                                # Try to find region in surrounding text
                                for region, aliases in REGIONS.items():
                                    if any(alias.lower() in script_text.lower() for alias in aliases):
                                        if region not in result:
                                            result[region] = price
                    except (json.JSONDecodeError, ValueError, KeyError):
                        pass
        
        # If no data found, log warning
        if len(result) == 0:
            logger.warning(
                "No regional prices extracted from Lottie page",
                care_type=care_type,
                content_length=len(html_content),
                pound_symbols=pound_count,
                tables_found=len(tables),
                hint="Page might be JavaScript-rendered. Consider using Selenium/Playwright."
            )
        else:
            logger.info("Extracted regional prices", care_type=care_type, regions=len(result), 
                       regions_list=list(result.keys()))
        
        return result
    
    def scrape_all_pages(self) -> Dict[str, Dict[str, float]]:
        """
        Scrape all Lottie pages and extract regional averages.
        
        Returns:
            Dict mapping: {care_type: {region: price}}
        """
        result: Dict[str, Dict[str, float]] = {}
        
        # Map URLs to care types
        url_map = {
            "residential": config.lottie_residential_url,
            "nursing": config.lottie_nursing_url,
            "dementia": config.lottie_dementia_url,
        }
        
        for care_type, url in url_map.items():
            try:
                logger.info("Scraping Lottie page", care_type=care_type, url=url)
                html_content = self.fetch_page(url)
                regional_prices = self.extract_regional_prices(html_content, care_type)
                
                if regional_prices:
                    result[care_type] = regional_prices
                    logger.info("Successfully scraped Lottie page", 
                               care_type=care_type, 
                               regions_found=len(regional_prices))
                else:
                    logger.warning("No prices extracted from Lottie page", 
                                  care_type=care_type,
                                  url=url,
                                  hint="Page might require JavaScript rendering")
            except Exception as e:
                logger.error("Failed to scrape Lottie page", 
                            care_type=care_type, 
                            error=str(e),
                            url=url,
                            exc_info=True)
                # Continue with other pages
                continue
        
        return result
    
    def save_to_database(self, data: Dict[str, Dict[str, float]]) -> int:
        """
        Save scraped Lottie data to database.
        
        Args:
            data: Scraped data mapping {care_type: {region: price}}
            
        Returns:
            Number of records updated
            
        Raises:
            DatabaseError: If database operation fails
        """
        logger.info("Saving Lottie data to database", care_types=len(data))
        
        if not data:
            logger.warning("No Lottie data to save")
            return 0
        
        records_updated = 0
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for care_type, regional_prices in data.items():
                    if not regional_prices:
                        logger.warning("No prices for care type", care_type=care_type)
                        continue
                    
                    for region, price in regional_prices.items():
                        try:
                            cursor.execute("""
                                INSERT INTO lottie_regional_averages (
                                    region, care_type, price_per_week, updated_at
                                ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (region, care_type) 
                                DO UPDATE SET
                                    price_per_week = EXCLUDED.price_per_week,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (region, care_type, price))
                            records_updated += 1
                        except Exception as e:
                            logger.error("Failed to save Lottie record", region=region, care_type=care_type, error=str(e))
                            continue
                
                conn.commit()
            
            logger.info("Lottie data saved to database", records=records_updated)
            return records_updated
        except Exception as e:
            logger.error("Failed to save Lottie data to database", error=str(e), exc_info=True)
            raise
    
    def load_lottie_data(self, use_fallback: bool = True) -> int:
        """
        Scrape and save Lottie regional averages.
        
        Args:
            use_fallback: If True, use fallback constants data if scraping fails
        
        Returns:
            Number of records updated
            
        Raises:
            LottieScrapingError: If scraping fails and use_fallback=False
        """
        logger.info("Loading Lottie data", use_fallback=use_fallback)
        
        try:
            # Scrape all pages
            data = self.scrape_all_pages()
            
            if not data:
                if use_fallback:
                    logger.info("No data scraped, using fallback constants data")
                    data = self._load_fallback_data()
                else:
                    error_msg = (
                        "No data scraped from Lottie pages. "
                        "Possible reasons: "
                        "1) Pages require JavaScript rendering (use Selenium/Playwright), "
                        "2) Website structure changed, "
                        "3) Network/access issues. "
                        "Check server logs for details."
                    )
                    logger.warning("No Lottie data scraped from any page", error=error_msg)
                    raise LottieScrapingError(error_msg)
            
            # Check if we have any valid data
            total_regions = sum(len(prices) for prices in data.values())
            if total_regions == 0:
                if use_fallback:
                    logger.info("No prices extracted, using fallback constants data")
                    data = self._load_fallback_data()
                    total_regions = sum(len(prices) for prices in data.values())
                else:
                    error_msg = (
                        "No regional prices extracted from Lottie pages. "
                        "Pages might require JavaScript rendering. "
                        "Consider using Selenium/Playwright for JS-rendered content."
                    )
                    logger.warning("No regional prices extracted from Lottie pages", error=error_msg)
                    raise LottieScrapingError(error_msg)
            
            logger.info("Scraped Lottie data", care_types=len(data), total_regions=total_regions)
            
            # Save to database
            records_updated = self.save_to_database(data)
            
            if records_updated == 0 and len(data) > 0:
                logger.warning(
                    "Lottie data parsed but not saved to database",
                    parsed_records=total_regions,
                    saved_records=records_updated,
                    hint="Database might be unavailable or psycopg2 not installed"
                )
                # Don't fail if we have fallback data - system can still work
                if not use_fallback:
                    raise LottieScrapingError("No records saved to database")
            
            return records_updated
        except LottieScrapingError:
            if use_fallback:
                logger.info("Scraping failed, using fallback constants data")
                try:
                    data = self._load_fallback_data()
                    records_updated = self.save_to_database(data)
                    logger.info("Loaded Lottie data from fallback", records=records_updated)
                    return records_updated
                except Exception as fallback_error:
                    logger.error("Failed to load fallback data", error=str(fallback_error))
                    raise
            raise
        except Exception as e:
            logger.error("Failed to load Lottie data", error=str(e), exc_info=True)
            if use_fallback:
                logger.info("Attempting to use fallback constants data")
                try:
                    data = self._load_fallback_data()
                    records_updated = self.save_to_database(data)
                    logger.info("Loaded Lottie data from fallback after error", records=records_updated)
                    return records_updated
                except Exception as fallback_error:
                    logger.error("Failed to load fallback data", error=str(fallback_error))
            raise LottieScrapingError(f"Failed to load Lottie data: {e}") from e
    
    def _load_fallback_data(self) -> Dict[str, Dict[str, float]]:
        """
        Load fallback Lottie data from constants.py.
        
        Returns:
            Dict mapping: {care_type: {region: price}}
        """
        try:
            from pricing_calculator.constants import LOTTIE_2025_REGIONAL_AVERAGES
            from pricing_calculator.models import CareType
            
            result: Dict[str, Dict[str, float]] = {}
            
            # Convert from constants format to scraper format
            for region, care_type_prices in LOTTIE_2025_REGIONAL_AVERAGES.items():
                for care_type_enum, price in care_type_prices.items():
                    # Convert CareType enum to string
                    care_type_str = care_type_enum.value if hasattr(care_type_enum, 'value') else str(care_type_enum)
                    
                    # Normalize care type names
                    if care_type_str == "residential":
                        care_type_str = "residential"
                    elif care_type_str == "nursing":
                        care_type_str = "nursing"
                    elif care_type_str == "residential_dementia":
                        care_type_str = "dementia"  # Lottie uses "dementia" as care type
                    elif care_type_str == "nursing_dementia":
                        care_type_str = "dementia"
                    elif care_type_str == "respite":
                        care_type_str = "respite"
                    
                    if care_type_str not in result:
                        result[care_type_str] = {}
                    
                    result[care_type_str][region] = price
            
            logger.info("Loaded fallback Lottie data", care_types=len(result), 
                       total_regions=sum(len(prices) for prices in result.values()))
            return result
        except ImportError as e:
            logger.error("Failed to import fallback constants", error=str(e))
            raise LottieScrapingError(f"Fallback data not available: {e}") from e

