"""Pydantic models for postcode resolver."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PostcodeInfo(BaseModel):
    """Postcode information model."""
    
    postcode: str = Field(..., description="UK postcode")
    local_authority: str = Field(..., description="Local authority name")
    region: str = Field(..., description="UK region")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    country: Optional[str] = Field(None, description="Country (England, Scotland, Wales, Northern Ireland)")
    county: Optional[str] = Field(None, description="County")
    district: Optional[str] = Field(None, description="District")
    ward: Optional[str] = Field(None, description="Ward")
    
    @field_validator("lat", "lon")
    @classmethod
    def validate_coordinates(cls, v: float) -> float:
        """Validate coordinates are within UK bounds."""
        if not (-90 <= v <= 90 if abs(v) <= 90 else -180 <= v <= 180):
            raise ValueError(f"Invalid coordinate: {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "postcode": "B15 2HQ",
                "local_authority": "Birmingham",
                "region": "West Midlands",
                "lat": 52.475,
                "lon": -1.920,
                "country": "England",
                "county": "West Midlands",
                "district": "Birmingham",
                "ward": "Edgbaston"
            }
        }


class BatchPostcodeRequest(BaseModel):
    """Batch postcode request model."""
    
    postcodes: list[str] = Field(..., min_length=1, max_length=100, description="List of postcodes")
    
    @field_validator("postcodes")
    @classmethod
    def validate_postcodes(cls, v: list[str]) -> list[str]:
        """Validate postcodes list."""
        if len(v) > 100:
            raise ValueError("Maximum 100 postcodes per batch request")
        return v


class BatchPostcodeResponse(BaseModel):
    """Batch postcode response model."""
    
    results: list[Optional[PostcodeInfo]] = Field(..., description="List of postcode info (None if not found)")
    total: int = Field(..., description="Total postcodes requested")
    found: int = Field(..., description="Number of postcodes found")
    not_found: int = Field(..., description="Number of postcodes not found")

