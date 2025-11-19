"""Load and parse MSIF Fair Cost data from XLS files."""

import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import httpx
import structlog
from .exceptions import FairCostDataError

logger = structlog.get_logger(__name__)

# MSIF URLs
MSIF_2025_2026_URL = (
    "https://assets.publishing.service.gov.uk/media/68a3021cf49bec79d23d2940/"
    "market-sustainability-and-improvement-fund-fees-2025-to-2026.xlsx"
)
MSIF_2024_2025_URL = (
    "https://assets.publishing.service.gov.uk/media/6703d7cc3b919067bb482d39/"
    "market-sustainability-and-improvement-fund-fees-2024-to-2025.xlsx"
)

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "pricing_calculator"
DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache file path
CACHE_FILE_2025 = DEFAULT_CACHE_DIR / "msif_2025_2026.xlsx"
CACHE_FILE_2024 = DEFAULT_CACHE_DIR / "msif_2024_2025.xlsx"


def _download_file(url: str, destination: Path, timeout: int = 60) -> None:
    """Download file from URL to destination."""
    logger.info("Downloading MSIF file", url=url, destination=str(destination))
    
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "wb") as f:
                f.write(response.content)
            
            logger.info("Downloaded successfully", size=len(response.content))
    except Exception as e:
        logger.error("Failed to download MSIF file", error=str(e), url=url)
        raise FairCostDataError(f"Failed to download MSIF file: {e}") from e


def _is_file_stale(file_path: Path, max_age_days: int = 30) -> bool:
    """Check if file is older than max_age_days."""
    if not file_path.exists():
        return True
    
    file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
    return file_age > timedelta(days=max_age_days)


def _parse_msif_xls(file_path: Path) -> Dict[str, Dict[str, float]]:
    """
    Parse MSIF XLS file and extract median fees.
    
    MSIF 2025-2026 structure:
    - Sheet "Table A 2025-26" contains the main data
    - Column 1: ONS Code
    - Column 2: Local authority name
    - Column 6: Residential 65+ fee (2025-26 provisional)
    - Column 9: Nursing 65+ fee (2025-26 provisional)
    
    Returns:
        Dict mapping: {local_authority: {care_type: median_fee_gbp}}
    """
    logger.info("Parsing MSIF XLS file", file=str(file_path))
    
    try:
        xls = pd.ExcelFile(file_path)
        
        # Find Table A sheet (main data sheet)
        target_sheet = None
        for sheet_name in xls.sheet_names:
            if "table a" in sheet_name.lower() and "2025" in sheet_name.lower():
                target_sheet = sheet_name
                break
        
        if target_sheet is None:
            # Try alternative names
            for sheet_name in xls.sheet_names:
                if any(keyword in sheet_name.lower() for keyword in ["table a", "fees", "data"]):
                    target_sheet = sheet_name
                    break
        
        if target_sheet is None:
            raise FairCostDataError(f"Could not find Table A sheet in MSIF file. Available sheets: {xls.sheet_names}")
        
        logger.info("Using sheet", sheet=target_sheet)
        
        # Read with header row (row 1 contains column names)
        df = pd.read_excel(xls, sheet_name=target_sheet, header=1)
        
        result: Dict[str, Dict[str, float]] = {}
        
        # Column indices based on MSIF 2025-2026 structure:
        # Column 0: ONS Code
        # Column 1: Local authority name
        # Column 6: Residential 65+ fee 2025-26 (provisional) - index 6
        # Column 9: Nursing 65+ fee 2025-26 (provisional) - index 9
        
        # Find column indices dynamically
        la_col_idx = None
        residential_col_idx = None
        nursing_col_idx = None
        
        # Look for Local authority column (usually column 1)
        for idx, col in enumerate(df.columns):
            col_str = str(col).lower()
            if "local authority" in col_str or (idx == 1 and "unnamed" not in col_str.lower()):
                la_col_idx = idx
                break
        
        if la_col_idx is None:
            la_col_idx = 1  # Fallback to column 1
        
        # Look for residential and nursing columns by header text
        for idx, col in enumerate(df.columns):
            col_str = str(col).lower()
            if "care homes without nursing" in col_str and "65" in col_str and "2025" in col_str:
                residential_col_idx = idx
            elif "care homes with nursing" in col_str and "65" in col_str and "2025" in col_str:
                nursing_col_idx = idx
        
        # Fallback: use known positions (column 6 and 9 for 2025-26 provisional)
        if residential_col_idx is None:
            if len(df.columns) > 6:
                residential_col_idx = 6  # Column 7 (2025-26 provisional residential)
        
        if nursing_col_idx is None:
            if len(df.columns) > 9:
                nursing_col_idx = 9  # Column 10 (2025-26 provisional nursing)
        
        if residential_col_idx is None or nursing_col_idx is None:
            raise FairCostDataError(
                f"Could not find required fee columns. "
                f"Residential col: {residential_col_idx}, Nursing col: {nursing_col_idx}. "
                f"Available columns: {list(df.columns[:10])}"
            )
        
        logger.info(
            "Found columns",
            la_col=la_col_idx,
            residential_col=residential_col_idx,
            nursing_col=nursing_col_idx
        )
        
        # Extract data
        for idx, row in df.iterrows():
            # Skip header rows and empty rows
            if idx < 2:  # Skip first 2 rows (title and header)
                continue
            
            la_name = str(row.iloc[la_col_idx]).strip()
            
            # Skip invalid rows
            if (not la_name or 
                la_name.lower() in ["nan", "none", "", "this worksheet", "ons code"] or
                la_name.startswith("Table") or
                len(la_name) < 2):
                continue
            
            try:
                # Extract fees
                residential_fee_raw = row.iloc[residential_col_idx]
                nursing_fee_raw = row.iloc[nursing_col_idx]
                
                residential_fee = None
                nursing_fee = None
                
                if pd.notna(residential_fee_raw):
                    try:
                        residential_fee = float(residential_fee_raw)
                    except (ValueError, TypeError):
                        pass
                
                if pd.notna(nursing_fee_raw):
                    try:
                        nursing_fee = float(nursing_fee_raw)
                    except (ValueError, TypeError):
                        pass
                
                # Only add if we have at least one valid fee
                if residential_fee or nursing_fee:
                    if la_name not in result:
                        result[la_name] = {}
                    
                    if residential_fee and residential_fee > 0:
                        result[la_name]["residential"] = residential_fee
                        # Dementia care typically costs 10-15% more
                        result[la_name]["residential_dementia"] = residential_fee * 1.12
                        # Respite typically same as residential
                        result[la_name]["respite"] = residential_fee
                    
                    if nursing_fee and nursing_fee > 0:
                        result[la_name]["nursing"] = nursing_fee
                        # Dementia care typically costs 10-15% more
                        result[la_name]["nursing_dementia"] = nursing_fee * 1.12
                    
            except (ValueError, TypeError, IndexError) as e:
                logger.debug("Skipping row", la=la_name, error=str(e), row_idx=idx)
                continue
        
        logger.info("Parsed MSIF data", local_authorities=len(result))
        
        if len(result) == 0:
            raise FairCostDataError("No valid data extracted from MSIF file")
        
        return result
        
    except Exception as e:
        logger.error("Failed to parse MSIF XLS", error=str(e))
        raise FairCostDataError(f"Failed to parse MSIF XLS file: {e}") from e


def load_fair_cost_data(
    xls_path: Optional[Path] = None,
    max_age_days: int = 30,
    force_download: bool = False
) -> Dict[str, Dict[str, float]]:
    """
    Load MSIF fair cost data from XLS file.
    
    Automatically downloads if file not provided or older than max_age_days.
    
    Args:
        xls_path: Optional path to XLS file. If None, uses cache or downloads.
        max_age_days: Maximum age of cached file in days before re-downloading.
        force_download: Force download even if cached file exists.
        
    Returns:
        Dict mapping: {local_authority: {care_type: median_fee_gbp}}
    """
    # Determine file path
    if xls_path is None:
        xls_path = CACHE_FILE_2025
    
    # Download if needed
    if force_download or _is_file_stale(xls_path, max_age_days):
        try:
            _download_file(MSIF_2025_2026_URL, xls_path)
        except Exception as e:
            logger.warning("Failed to download 2025-2026 file, trying 2024-2025", error=str(e))
            # Fallback to 2024-2025
            if xls_path == CACHE_FILE_2025:
                xls_path = CACHE_FILE_2024
            if force_download or _is_file_stale(xls_path, max_age_days):
                _download_file(MSIF_2024_2025_URL, xls_path)
    
    # Parse file
    if not xls_path.exists():
        raise FairCostDataError(f"MSIF file not found: {xls_path}")
    
    return _parse_msif_xls(xls_path)

