"""
Example FastAPI application using pricing_calculator endpoints.

To use this, add to your main FastAPI app:

    from pricing_calculator.api import router as pricing_router
    app.include_router(pricing_router)

Or run standalone:

    uvicorn pricing_calculator.example_api_usage:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from .api import router as pricing_router

# Import pricing_core API
try:
    from pricing_core.api import router as pricing_core_router
    PRICING_CORE_AVAILABLE = True
except ImportError:
    PRICING_CORE_AVAILABLE = False

# Import funding_calculator API
try:
    from funding_calculator.api import router as funding_router
    FUNDING_AVAILABLE = True
except ImportError:
    FUNDING_AVAILABLE = False

# Import postcode_resolver API
try:
    from postcode_resolver.api import router as postcode_router
    POSTCODE_AVAILABLE = True
except ImportError:
    POSTCODE_AVAILABLE = False

# Import data_ingestion API
try:
    from data_ingestion.api import router as data_admin_router
    DATA_ADMIN_AVAILABLE = True
except ImportError:
    DATA_ADMIN_AVAILABLE = False

app = FastAPI(
    title="Pricing Calculator API",
    description="API for UK care homes pricing calculations and Affordability Bands",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include pricing router
app.include_router(pricing_router)

# Include pricing_core router if available
if PRICING_CORE_AVAILABLE:
    app.include_router(pricing_core_router)

# Include funding router if available
if FUNDING_AVAILABLE:
    app.include_router(funding_router)

# Include postcode router if available
if POSTCODE_AVAILABLE:
    app.include_router(postcode_router)

# Include data admin router if available
if DATA_ADMIN_AVAILABLE:
    app.include_router(data_admin_router)

# Mount static files (HTML frontend)
static_dir = Path(__file__).parent
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception:
    # If static files can't be mounted, continue without it
    pass


@app.get("/frontend")
async def serve_frontend():
    """Serve the HTML frontend."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not found"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pricing Calculator API",
        "version": "1.0.0",
        "frontend": "http://localhost:8001/frontend",
        "endpoints": {
            "postcode": "/api/pricing/postcode/{postcode}",
            "locations": "/api/pricing/locations",
            "regions": "/api/pricing/regions",
            "care-types": "/api/pricing/care-types",
            "pricing-core": "/api/pricing-core/calculate" if PRICING_CORE_AVAILABLE else None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

