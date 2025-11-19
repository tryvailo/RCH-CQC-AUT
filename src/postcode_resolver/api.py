"""FastAPI endpoints for postcode resolver module."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from .resolver import PostcodeResolver
from .batch_resolver import BatchPostcodeResolver
from .validator import validate_postcode, is_valid_postcode
from .models import PostcodeInfo

router = APIRouter(prefix="/api/postcode", tags=["postcode"])

# Global service instances
_resolver: Optional[PostcodeResolver] = None
_batch_resolver: Optional[BatchPostcodeResolver] = None


def get_resolver() -> PostcodeResolver:
    """Get or create PostcodeResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = PostcodeResolver()
    return _resolver


def get_batch_resolver() -> BatchPostcodeResolver:
    """Get or create BatchPostcodeResolver instance."""
    global _batch_resolver
    if _batch_resolver is None:
        _batch_resolver = BatchPostcodeResolver()
    return _batch_resolver


@router.get("/resolve/{postcode}", response_model=PostcodeInfo)
async def resolve_postcode(
    postcode: str,
    use_cache: bool = Query(True, description="Use cache")
):
    """
    Resolve a single UK postcode to Local Authority and Region.
    
    Returns postcode information including location, local authority, and coordinates.
    """
    try:
        if not is_valid_postcode(postcode):
            raise HTTPException(status_code=400, detail=f"Invalid postcode format: {postcode}")
        
        resolver = get_resolver()
        result = resolver.resolve(postcode, use_cache=use_cache)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/resolve-batch")
async def resolve_batch(
    postcodes: List[str] = Query(..., description="List of postcodes to resolve"),
    use_cache: bool = Query(True, description="Use cache"),
    validate: bool = Query(True, description="Validate postcode format")
):
    """
    Resolve multiple UK postcodes in batch.
    
    Returns batch results with found/not found counts and individual results.
    """
    try:
        if len(postcodes) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 postcodes per batch")
        
        batch_resolver = get_batch_resolver()
        result = batch_resolver.resolve_batch(
            postcodes,
            use_cache=use_cache,
            validate=validate
        )
        
        return {
            "total": result.total,
            "found": result.found,
            "not_found": result.not_found,
            "results": [r.model_dump() if r else None for r in result.results]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validate/{postcode}")
async def validate_postcode_format(postcode: str):
    """
    Validate UK postcode format.
    
    Returns whether the postcode format is valid.
    """
    is_valid = is_valid_postcode(postcode)
    return {
        "postcode": postcode,
        "is_valid": is_valid
    }

