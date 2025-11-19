"""Map UK postcodes to Local Authority and Region."""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import httpx
import structlog
from .models import PostcodeInfo
from .exceptions import PostcodeMappingError

logger = structlog.get_logger(__name__)

# Postcodes.io API
POSTCODES_IO_API = "https://api.postcodes.io/postcodes/{postcode}"

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "pricing_calculator"
DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# SQLite cache database
CACHE_DB = DEFAULT_CACHE_DIR / "postcode_cache.db"

# Cache expiry (days)
CACHE_EXPIRY_DAYS = 90


class PostcodeMapper:
    """Postcode to Local Authority mapper with caching."""
    
    def __init__(self, cache_db_path: Optional[Path] = None):
        """
        Initialize PostcodeMapper.
        
        Args:
            cache_db_path: Optional path to SQLite cache database.
        """
        self.cache_db_path = cache_db_path or CACHE_DB
        self._init_cache_db()
    
    def _init_cache_db(self) -> None:
        """Initialize SQLite cache database."""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postcode_cache (
                postcode TEXT PRIMARY KEY,
                local_authority TEXT NOT NULL,
                region TEXT NOT NULL,
                county TEXT,
                country TEXT DEFAULT 'England',
                cached_at TIMESTAMP NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Initialized postcode cache database", db=str(self.cache_db_path))
    
    def _get_from_cache(self, postcode: str) -> Optional[PostcodeInfo]:
        """Get postcode info from cache."""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT local_authority, region, county, country, cached_at
            FROM postcode_cache
            WHERE postcode = ?
        """, (postcode.upper().replace(" ", ""),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            la, region, county, country, cached_at = row
            # Check if cache is still valid
            cache_date = datetime.fromisoformat(cached_at)
            if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                logger.debug("Cache hit", postcode=postcode)
                return PostcodeInfo(
                    postcode=postcode,
                    local_authority=la,
                    region=region,
                    county=county,
                    country=country or "England"
                )
        
        return None
    
    def _save_to_cache(self, postcode: str, info: PostcodeInfo) -> None:
        """Save postcode info to cache."""
        conn = sqlite3.connect(str(self.cache_db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO postcode_cache
            (postcode, local_authority, region, county, country, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            postcode.upper().replace(" ", ""),
            info.local_authority,
            info.region,
            info.county,
            info.country,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        logger.debug("Cached postcode", postcode=postcode)
    
    def _fetch_from_api(self, postcode: str) -> PostcodeInfo:
        """Fetch postcode info from postcodes.io API."""
        normalized_postcode = postcode.upper().replace(" ", "")
        url = POSTCODES_IO_API.format(postcode=normalized_postcode)
        
        logger.info("Fetching postcode from API", postcode=postcode, url=url)
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != 200:
                    raise PostcodeMappingError(f"API returned error: {data.get('error', 'Unknown error')}")
                
                result = data.get("result")
                if not result:
                    raise PostcodeMappingError(f"No result for postcode: {postcode}")
                
                # Extract data
                admin_district = result.get("admin_district", "")
                region = result.get("region", "")
                admin_county = result.get("admin_county")
                country = result.get("country", "England")
                
                # Normalize region names
                region = self._normalize_region(region)
                
                info = PostcodeInfo(
                    postcode=postcode,
                    local_authority=admin_district or region,
                    region=region,
                    county=admin_county,
                    country=country
                )
                
                # Cache it
                self._save_to_cache(postcode, info)
                
                return info
                
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching postcode", error=str(e), postcode=postcode)
            raise PostcodeMappingError(f"Failed to fetch postcode from API: {e}") from e
        except Exception as e:
            logger.error("Error fetching postcode", error=str(e), postcode=postcode)
            raise PostcodeMappingError(f"Failed to fetch postcode: {e}") from e
    
    def _normalize_region(self, region: str) -> str:
        """Normalize region name."""
        # Map common variations to standard names
        region_mapping = {
            "Greater London": "London",
            "London": "London",
            "South East England": "South East",
            "South East": "South East",
            "South West England": "South West",
            "South West": "South West",
            "East of England": "East of England",
            "East England": "East of England",
            "West Midlands": "West Midlands",
            "East Midlands": "East Midlands",
            "Yorkshire and the Humber": "Yorkshire and the Humber",
            "Yorkshire": "Yorkshire and the Humber",
            "North West England": "North West",
            "North West": "North West",
            "North East England": "North East",
            "North East": "North East",
        }
        return region_mapping.get(region, region)
    
    def get_postcode_info(self, postcode: str) -> PostcodeInfo:
        """
        Get postcode information (Local Authority, Region, etc.).
        
        Args:
            postcode: UK postcode
            
        Returns:
            PostcodeInfo object
            
        Raises:
            PostcodeMappingError: If postcode cannot be mapped
        """
        # Try cache first
        cached = self._get_from_cache(postcode)
        if cached:
            return cached
        
        # Fetch from API
        return self._fetch_from_api(postcode)


# Global instance
_default_mapper: Optional[PostcodeMapper] = None


def get_postcode_info(postcode: str) -> PostcodeInfo:
    """
    Convenience function to get postcode info.
    
    Args:
        postcode: UK postcode
        
    Returns:
        PostcodeInfo object
    """
    global _default_mapper
    if _default_mapper is None:
        _default_mapper = PostcodeMapper()
    return _default_mapper.get_postcode_info(postcode)

