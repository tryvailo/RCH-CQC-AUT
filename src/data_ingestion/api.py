"""FastAPI endpoints for data ingestion module."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from .service import DataIngestionService
from .database import init_database

router = APIRouter(prefix="/api/data-admin", tags=["data-admin"])

# Global service instance
_service: DataIngestionService = None


def get_service() -> DataIngestionService:
    """Get or create DataIngestionService instance."""
    global _service
    if _service is None:
        _service = DataIngestionService()
    return _service


@router.post("/init-database")
async def initialize_database():
    """Initialize database tables."""
    try:
        init_database()
        return {"status": "success", "message": "Database tables initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-msif/{year}")
async def refresh_msif_data(
    year: int,
    prefer_csv: bool = Query(False, description="Prefer CSV over Excel (faster, good for development)"),
    csv_path: Optional[str] = Query(None, description="Custom CSV file path. If None, uses default from input/other")
):
    """
    Refresh MSIF data for a specific year.
    
    Year should be 2024 or 2025.
    
    Supports loading from CSV file (faster) or Excel file (official source).
    Can use CSV as fallback if Excel parsing fails.
    """
    try:
        if year not in [2024, 2025]:
            return {
                "status": "error",
                "data_source": f"MSIF {year}",
                "error": "Year must be 2024 or 2025"
            }
        
        service = get_service()
        result = service.refresh_msif_data(year=year, prefer_csv=prefer_csv, csv_path=csv_path)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        
        # Log full error for debugging
        import logging
        logging.error(f"Error refreshing MSIF {year}: {error_detail}\n{error_traceback}")
        
        # Return error in same format as service
        return {
            "status": "error",
            "data_source": f"MSIF {year}",
            "error": error_detail
        }


@router.post("/refresh-lottie")
async def refresh_lottie_data(
    use_fallback: bool = Query(True, description="Use fallback constants data if scraping fails")
):
    """
    Refresh Lottie regional averages data.
    
    If scraping fails and use_fallback=True, will use hardcoded constants from pricing_calculator.constants.
    """
    try:
        service = get_service()
        result = service.refresh_lottie_data(use_fallback=use_fallback)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        
        # Log full error for debugging
        import logging
        logging.error(f"Error refreshing Lottie data: {error_detail}\n{error_traceback}")
        
        # Return error in same format as service
        return {
            "status": "error",
            "data_source": "Lottie",
            "error": error_detail,
            "hint": "System can still work using fallback constants data from pricing_calculator.constants"
        }


@router.get("/update-status")
async def get_update_status():
    """Get update status log."""
    try:
        service = get_service()
        updates = service.get_update_status()
        
        # Convert to serializable format
        result = []
        for update in updates:
            result.append({
                "id": update["id"],
                "data_source": update["data_source"],
                "status": update["status"],
                "records_updated": update["records_updated"],
                "started_at": update["started_at"].isoformat() if update["started_at"] else None,
                "completed_at": update["completed_at"].isoformat() if update["completed_at"] else None,
                "duration_seconds": update["duration_seconds"],
                "error_message": update["error_message"]
            })
        
        return {
            "total": len(result),
            "updates": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

