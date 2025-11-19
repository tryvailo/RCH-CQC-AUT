"""Batch postcode resolver for processing multiple postcodes."""

import time
from typing import List, Optional
import httpx
import structlog
from .config import config
from .models import PostcodeInfo, BatchPostcodeResponse
from .validator import normalize_postcode, is_valid_postcode
from .cache import get_cache_backend
from .exceptions import InvalidPostcodeError, APIError

logger = structlog.get_logger(__name__)


class BatchPostcodeResolver:
    """Batch resolver for multiple postcodes."""
    
    def __init__(self):
        """Initialize batch resolver."""
        self.cache = get_cache_backend()
        self.api_url = config.postcodes_io_batch_api
        self.batch_size = config.batch_size
        self.batch_delay = config.batch_delay_seconds
    
    def resolve_batch(
        self, 
        postcodes: List[str], 
        use_cache: bool = True,
        validate: bool = True
    ) -> BatchPostcodeResponse:
        """
        Resolve multiple postcodes in batch.
        
        Args:
            postcodes: List of postcode strings
            use_cache: Whether to use cache
            validate: Whether to validate postcode format
            
        Returns:
            BatchPostcodeResponse object
        """
        if not postcodes:
            return BatchPostcodeResponse(
                results=[],
                total=0,
                found=0,
                not_found=0
            )
        
        # Normalize and validate postcodes
        normalized_postcodes = []
        invalid_indices = []
        
        for i, postcode in enumerate(postcodes):
            try:
                if validate and not is_valid_postcode(postcode):
                    invalid_indices.append(i)
                    normalized_postcodes.append(None)
                else:
                    normalized = normalize_postcode(postcode) if postcode else None
                    normalized_postcodes.append(normalized)
            except Exception:
                invalid_indices.append(i)
                normalized_postcodes.append(None)
        
        # Check cache for valid postcodes
        cached_results: List[Optional[PostcodeInfo]] = [None] * len(postcodes)
        uncached_indices: List[int] = []
        
        if use_cache:
            for i, normalized in enumerate(normalized_postcodes):
                if normalized and i not in invalid_indices:
                    cached = self.cache.get(normalized)
                    if cached:
                        cached_results[i] = cached
                    else:
                        uncached_indices.append(i)
        else:
            uncached_indices = [i for i in range(len(postcodes)) if i not in invalid_indices]
        
        # Resolve uncached postcodes in batches
        if uncached_indices:
            uncached_postcodes = [normalized_postcodes[i] for i in uncached_indices]
            api_results = self._resolve_via_api(uncached_postcodes)
            
            # Map API results back to original indices
            for idx, api_result in enumerate(api_results):
                original_idx = uncached_indices[idx]
                cached_results[original_idx] = api_result
                
                # Cache successful results
                if api_result and use_cache:
                    try:
                        self.cache.set(
                            normalized_postcodes[original_idx],
                            api_result,
                            config.cache_expiry_days
                        )
                    except Exception as e:
                        logger.warning("Failed to cache result", error=str(e))
        
        # Set None for invalid postcodes
        for i in invalid_indices:
            cached_results[i] = None
        
        # Count results
        found = sum(1 for r in cached_results if r is not None)
        not_found = len(cached_results) - found
        
        return BatchPostcodeResponse(
            results=cached_results,
            total=len(postcodes),
            found=found,
            not_found=not_found
        )
    
    def _resolve_via_api(self, postcodes: List[str]) -> List[Optional[PostcodeInfo]]:
        """
        Resolve postcodes via postcodes.io batch API.
        
        Args:
            postcodes: List of normalized postcodes
            
        Returns:
            List of PostcodeInfo objects (None if not found)
        """
        if not postcodes:
            return []
        
        # Split into batches
        batches = [
            postcodes[i:i + self.batch_size]
            for i in range(0, len(postcodes), self.batch_size)
        ]
        
        all_results: List[Optional[PostcodeInfo]] = []
        
        for batch_idx, batch in enumerate(batches):
            logger.info("Processing batch", batch_idx=batch_idx + 1, total_batches=len(batches), batch_size=len(batch))
            
            try:
                batch_results = self._call_batch_api(batch)
                all_results.extend(batch_results)
                
                # Delay between batches (except last)
                if batch_idx < len(batches) - 1:
                    time.sleep(self.batch_delay)
            
            except Exception as e:
                logger.error("Batch API call failed", batch_idx=batch_idx, error=str(e))
                # Add None for all postcodes in failed batch
                all_results.extend([None] * len(batch))
        
        return all_results
    
    def _call_batch_api(self, postcodes: List[str]) -> List[Optional[PostcodeInfo]]:
        """
        Call postcodes.io batch API.
        
        Args:
            postcodes: List of normalized postcodes
            
        Returns:
            List of PostcodeInfo objects (None if not found)
        """
        try:
            with httpx.Client(timeout=config.http_timeout * 2) as client:
                response = client.post(
                    self.api_url,
                    json={"postcodes": postcodes}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != 200:
                    raise APIError(f"API error: {data.get('error', 'Unknown error')}")
                
                results = data.get("result", [])
                mapped_results: List[Optional[PostcodeInfo]] = []
                
                for result_item in results:
                    if result_item and result_item.get("result"):
                        # Map API response
                        api_data = result_item["result"]
                        postcode = api_data.get("postcode", "")
                        
                        # Use same mapping logic as single resolver
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
                        
                        region = api_data.get("region") or api_data.get("admin_district")
                        if region:
                            region = region_mapping.get(region, region)
                        
                        local_authority = (
                            api_data.get("admin_district") or 
                            api_data.get("parliamentary_constituency") or
                            api_data.get("admin_county") or
                            region or
                            "Unknown"
                        )
                        
                        mapped_results.append(PostcodeInfo(
                            postcode=postcode,
                            local_authority=local_authority,
                            region=region or "Unknown",
                            lat=api_data.get("latitude", 0.0),
                            lon=api_data.get("longitude", 0.0),
                            country=api_data.get("country"),
                            county=api_data.get("admin_county"),
                            district=api_data.get("admin_district"),
                            ward=api_data.get("admin_ward")
                        ))
                    else:
                        mapped_results.append(None)
                
                return mapped_results
        
        except httpx.HTTPError as e:
            raise APIError(f"HTTP error calling batch API: {e}") from e
        except Exception as e:
            raise APIError(f"Unexpected error calling batch API: {e}") from e

