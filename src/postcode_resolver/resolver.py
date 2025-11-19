"""Postcode resolver - resolves UK postcodes to Local Authority and Region."""

import httpx
from typing import Optional
import structlog
from .config import config
from .models import PostcodeInfo
from .validator import validate_postcode, normalize_postcode
from .cache import get_cache_backend
from .exceptions import InvalidPostcodeError, PostcodeNotFoundError, APIError

logger = structlog.get_logger(__name__)


class PostcodeResolver:
    """Resolve UK postcodes to Local Authority and Region."""
    
    def __init__(self):
        """Initialize postcode resolver."""
        self.cache = get_cache_backend()
        self.api_url = config.postcodes_io_api
    
    def resolve(self, postcode: str, use_cache: bool = True) -> PostcodeInfo:
        """
        Resolve postcode to Local Authority and Region.
        
        Args:
            postcode: UK postcode string
            use_cache: Whether to use cache
            
        Returns:
            PostcodeInfo object
            
        Raises:
            InvalidPostcodeError: If postcode format is invalid
            PostcodeNotFoundError: If postcode not found
            APIError: If API call fails
        """
        # Validate format
        try:
            validate_postcode(postcode)
        except InvalidPostcodeError as e:
            logger.warning("Invalid postcode format", postcode=postcode, error=str(e))
            raise
        
        # Normalize
        normalized = normalize_postcode(postcode)
        
        # Check cache
        if use_cache:
            cached = self.cache.get(normalized)
            if cached:
                logger.debug("Using cached result", postcode=normalized)
                return cached
        
        # Call API
        try:
            result = self._call_api(normalized)
            
            # Cache result
            if use_cache:
                try:
                    self.cache.set(normalized, result, config.cache_expiry_days)
                except Exception as e:
                    logger.warning("Failed to cache result", postcode=normalized, error=str(e))
            
            return result
        except PostcodeNotFoundError:
            raise
        except Exception as e:
            logger.error("API call failed", postcode=normalized, error=str(e))
            raise APIError(f"Failed to resolve postcode: {e}") from e
    
    def _call_api(self, postcode: str) -> PostcodeInfo:
        """
        Call postcodes.io API.
        
        Args:
            postcode: Normalized postcode
            
        Returns:
            PostcodeInfo object
            
        Raises:
            PostcodeNotFoundError: If postcode not found
            APIError: If API call fails
        """
        url = self.api_url.format(postcode=postcode)
        
        logger.info("Calling postcodes.io API", postcode=postcode, url=url)
        
        try:
            with httpx.Client(timeout=config.http_timeout) as client:
                response = client.get(url)
                
                if response.status_code == 404:
                    raise PostcodeNotFoundError(f"Postcode not found: {postcode}")
                
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != 200:
                    error = data.get("error", "Unknown error")
                    if "not found" in error.lower():
                        raise PostcodeNotFoundError(f"Postcode not found: {postcode}")
                    raise APIError(f"API error: {error}")
                
                result_data = data.get("result")
                if not result_data:
                    raise PostcodeNotFoundError(f"Postcode not found: {postcode}")
                
                # Map API response to PostcodeInfo
                return self._map_api_response(postcode, result_data)
        
        except httpx.HTTPError as e:
            raise APIError(f"HTTP error calling postcodes.io: {e}") from e
        except PostcodeNotFoundError:
            raise
        except Exception as e:
            raise APIError(f"Unexpected error calling API: {e}") from e
    
    def _map_api_response(self, postcode: str, api_data: dict) -> PostcodeInfo:
        """
        Map postcodes.io API response to PostcodeInfo.
        
        Args:
            postcode: Normalized postcode
            api_data: API response data
            
        Returns:
            PostcodeInfo object
        """
        # Map region names to standard UK regions
        region_mapping = {
            "East of England": "East of England",
            "East Midlands": "East Midlands",
            "London": "London",
            "North East": "North East",
            "North West": "North West",
            "South East": "South East",
            "South West": "South West",
            "West Midlands": "West Midlands",
            "Yorkshire and the Humber": "Yorkshire and the Humber",
            "Scotland": "Scotland",
            "Wales": "Wales",
            "Northern Ireland": "Northern Ireland",
        }
        
        # Get region from admin_district or region
        region = api_data.get("region") or api_data.get("admin_district")
        if region:
            region = region_mapping.get(region, region)
        
        # Get local authority
        local_authority = (
            api_data.get("admin_district") or 
            api_data.get("parliamentary_constituency") or
            api_data.get("admin_county") or
            region or
            "Unknown"
        )
        
        return PostcodeInfo(
            postcode=postcode,
            local_authority=local_authority,
            region=region or "Unknown",
            lat=api_data.get("latitude", 0.0),
            lon=api_data.get("longitude", 0.0),
            country=api_data.get("country"),
            county=api_data.get("admin_county"),
            district=api_data.get("admin_district"),
            ward=api_data.get("admin_ward")
        )

