"""MSIF data loader - downloads and parses MSIF XLS files."""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import httpx
import structlog
from .config import config
from .exceptions import MSIFDownloadError, MSIFParseError
from .database import get_db_connection

logger = structlog.get_logger(__name__)


class MSIFLoader:
    """Load and parse MSIF XLS files."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize MSIF loader.
        
        Args:
            cache_dir: Optional cache directory for downloaded files
        """
        self.cache_dir = cache_dir or config.cache_dir / "msif"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_msif_file(self, url: str, year: int) -> Path:
        """
        Download MSIF XLS file.
        
        Args:
            url: URL to download from
            year: Year for filename (2024 or 2025)
            
        Returns:
            Path to downloaded file
            
        Raises:
            MSIFDownloadError: If download fails
        """
        file_path = self.cache_dir / f"msif_{year}.xlsx"
        
        logger.info("Downloading MSIF file", url=url, year=year, target=str(file_path))
        
        try:
            with httpx.Client(timeout=config.http_timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                
                file_path.write_bytes(response.content)
                logger.info("MSIF file downloaded", file=str(file_path), size_bytes=len(response.content))
                
                return file_path
        except httpx.HTTPError as e:
            raise MSIFDownloadError(f"Failed to download MSIF {year}: {e}") from e
        except Exception as e:
            raise MSIFDownloadError(f"Unexpected error downloading MSIF {year}: {e}") from e
    
    def parse_msif_xls(self, file_path: Path, year: int) -> Dict[str, Dict[str, float]]:
        """
        Parse MSIF XLS file and extract fee data.
        
        Args:
            file_path: Path to XLS file
            year: Year (2024 or 2025)
            
        Returns:
            Dict mapping: {local_authority: {care_type: fee}}
            
        Raises:
            MSIFParseError: If parsing fails
        """
        logger.info("Parsing MSIF XLS file", file=str(file_path), year=year)
        
        try:
            xls = pd.ExcelFile(file_path)
            
            # Find Table A sheet
            target_sheet = None
            for sheet_name in xls.sheet_names:
                sheet_lower = sheet_name.lower()
                if "table a" in sheet_lower and str(year) in sheet_lower:
                    target_sheet = sheet_name
                    break
            
            if target_sheet is None:
                # Try alternative names
                for sheet_name in xls.sheet_names:
                    if any(keyword in sheet_name.lower() for keyword in ["table a", "fees", "data"]):
                        target_sheet = sheet_name
                        break
            
            if target_sheet is None:
                raise MSIFParseError(
                    f"Could not find Table A sheet in MSIF {year} file. "
                    f"Available sheets: {xls.sheet_names}"
                )
            
            logger.info("Using sheet", sheet=target_sheet)
            
            # Read with header row
            df = pd.read_excel(xls, sheet_name=target_sheet, header=1)
            
            result: Dict[str, Dict[str, float]] = {}
            
            # Find column indices dynamically
            la_col_idx = None
            residential_col_idx = None
            nursing_col_idx = None
            
            # Look for Local Authority column
            for idx, col in enumerate(df.columns):
                col_str = str(col).lower()
                if "local authority" in col_str or (idx == 1 and "unnamed" not in col_str.lower()):
                    la_col_idx = idx
                    break
            
            if la_col_idx is None:
                la_col_idx = 1  # Fallback
            
            # Look for residential and nursing columns
            for idx, col in enumerate(df.columns):
                col_str = str(col).lower()
                if "care homes without nursing" in col_str and "65" in col_str and str(year) in col_str:
                    residential_col_idx = idx
                elif "care homes with nursing" in col_str and "65" in col_str and str(year) in col_str:
                    nursing_col_idx = idx
            
            # Fallback to known positions
            if residential_col_idx is None and len(df.columns) > 6:
                residential_col_idx = 6
            
            if nursing_col_idx is None and len(df.columns) > 9:
                nursing_col_idx = 9
            
            if residential_col_idx is None or nursing_col_idx is None:
                raise MSIFParseError(
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
                if idx < 2:  # Skip header rows
                    continue
                
                la_name = str(row.iloc[la_col_idx]).strip()
                
                # Skip invalid rows
                if (not la_name or 
                    la_name.lower() in ["nan", "none", "", "this worksheet", "ons code"] or
                    la_name.startswith("Table") or
                    len(la_name) < 2):
                    continue
                
                try:
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
                    
                    if residential_fee or nursing_fee:
                        if la_name not in result:
                            result[la_name] = {}
                        
                        if residential_fee and residential_fee > 0:
                            result[la_name]["residential"] = residential_fee
                            result[la_name]["residential_dementia"] = residential_fee * 1.12
                            result[la_name]["respite"] = residential_fee
                        
                        if nursing_fee and nursing_fee > 0:
                            result[la_name]["nursing"] = nursing_fee
                            result[la_name]["nursing_dementia"] = nursing_fee * 1.12
                
                except (ValueError, TypeError, IndexError) as e:
                    logger.debug("Skipping row", la=la_name, error=str(e), row_idx=idx)
                    continue
            
            logger.info("Parsed MSIF data", local_authorities=len(result), year=year)
            
            if len(result) == 0:
                raise MSIFParseError(f"No valid data extracted from MSIF {year} file")
            
            return result
            
        except Exception as e:
            logger.error("Failed to parse MSIF XLS", error=str(e), year=year)
            raise MSIFParseError(f"Failed to parse MSIF {year} XLS file: {e}") from e
    
    def save_to_database(self, data: Dict[str, Dict[str, float]], year: int) -> int:
        """
        Save parsed MSIF data to database.
        
        Args:
            data: Parsed MSIF data
            year: Year (2024 or 2025)
            
        Returns:
            Number of records updated
        """
        table_name = f"msif_fees_{year}"
        logger.info("Saving MSIF data to database", table=table_name, records=len(data))
        
        try:
            records_updated = 0
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for la_name, fees in data.items():
                    cursor.execute(f"""
                        INSERT INTO {table_name} (
                            local_authority,
                            residential_fee_65_plus,
                            nursing_fee_65_plus,
                            residential_dementia_fee,
                            nursing_dementia_fee,
                            respite_fee,
                            updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (local_authority) 
                        DO UPDATE SET
                            residential_fee_65_plus = EXCLUDED.residential_fee_65_plus,
                            nursing_fee_65_plus = EXCLUDED.nursing_fee_65_plus,
                            residential_dementia_fee = EXCLUDED.residential_dementia_fee,
                            nursing_dementia_fee = EXCLUDED.nursing_dementia_fee,
                            respite_fee = EXCLUDED.respite_fee,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        la_name,
                        fees.get("residential"),
                        fees.get("nursing"),
                        fees.get("residential_dementia"),
                        fees.get("nursing_dementia"),
                        fees.get("respite")
                    ))
                    records_updated += 1
                
                conn.commit()
            
            logger.info("MSIF data saved to database", records=records_updated, year=year)
            return records_updated
        except Exception as e:
            logger.warning(
                "Could not save MSIF data to database",
                error=str(e),
                year=year,
                records_parsed=len(data)
            )
            # Return 0 to indicate no records were saved, but don't fail the entire operation
            return 0
    
    def load_msif_from_csv(self, csv_path: Optional[Path] = None, year: int = 2025) -> Dict[str, Dict[str, float]]:
        """
        Load MSIF data from pre-processed CSV file.
        
        Args:
            csv_path: Path to CSV file. If None, uses default path from input/other
            year: Year (2024 or 2025) - used for validation
            
        Returns:
            Dict mapping: {local_authority: {care_type: fee}}
            
        Raises:
            MSIFParseError: If CSV file not found or parsing fails
        """
        if csv_path is None:
            # Use default CSV path from input/other
            # __file__ is src/data_ingestion/msif_loader.py
            # .parent = src/data_ingestion/
            # .parent.parent = src/
            # .parent.parent.parent = project root
            project_root = Path(__file__).parent.parent.parent
            csv_path = project_root / "input" / "other" / f"msif_{year}_{year+1}_processed.csv"
            
            # Fallback to 2025-2026 if year-specific file doesn't exist
            if not csv_path.exists() and year == 2025:
                csv_path = project_root / "input" / "other" / "msif_2025_2026_processed.csv"
        
        if not csv_path.exists():
            raise MSIFParseError(f"CSV file not found: {csv_path}")
        
        logger.info("Loading MSIF data from CSV", csv_path=str(csv_path), year=year)
        
        try:
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_cols = ['local_authority', 'residential_65_median', 'nursing_65_median']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise MSIFParseError(
                    f"CSV file missing required columns: {missing_cols}. "
                    f"Found columns: {list(df.columns)}"
                )
            
            result: Dict[str, Dict[str, float]] = {}
            
            for _, row in df.iterrows():
                la_name = str(row['local_authority']).strip()
                
                # Skip invalid rows
                if not la_name or la_name.lower() in ["nan", "none", ""]:
                    continue
                
                residential_fee = None
                nursing_fee = None
                
                # Extract fees with validation
                if pd.notna(row['residential_65_median']):
                    try:
                        residential_fee = float(row['residential_65_median'])
                    except (ValueError, TypeError):
                        pass
                
                if pd.notna(row['nursing_65_median']):
                    try:
                        nursing_fee = float(row['nursing_65_median'])
                    except (ValueError, TypeError):
                        pass
                
                # Only add if we have at least one valid fee
                if residential_fee or nursing_fee:
                    result[la_name] = {}
                    
                    if residential_fee and residential_fee > 0:
                        result[la_name]["residential"] = residential_fee
                        result[la_name]["residential_dementia"] = residential_fee * 1.12
                        result[la_name]["respite"] = residential_fee
                    
                    if nursing_fee and nursing_fee > 0:
                        result[la_name]["nursing"] = nursing_fee
                        result[la_name]["nursing_dementia"] = nursing_fee * 1.12
            
            logger.info("Loaded MSIF data from CSV", local_authorities=len(result), year=year)
            
            if len(result) == 0:
                raise MSIFParseError(f"No valid data extracted from CSV file: {csv_path}")
            
            return result
            
        except pd.errors.EmptyDataError:
            raise MSIFParseError(f"CSV file is empty: {csv_path}")
        except Exception as e:
            logger.error("Failed to load MSIF from CSV", error=str(e), csv_path=str(csv_path))
            raise MSIFParseError(f"Failed to load MSIF data from CSV: {e}") from e
    
    def load_msif_data(
        self, 
        year: int, 
        prefer_csv: bool = False,
        csv_path: Optional[Path] = None,
        fallback_to_csv: bool = True
    ) -> int:
        """
        Download, parse and save MSIF data for a given year.
        
        Supports loading from CSV file (faster) or Excel file (official source).
        Can use CSV as fallback if Excel parsing fails.
        
        Args:
            year: Year (2024 or 2025)
            prefer_csv: If True, try CSV first, then Excel if CSV fails
            csv_path: Optional path to CSV file. If None, uses default from input/other
            fallback_to_csv: If True, use CSV as fallback if Excel parsing fails
            
        Returns:
            Number of records updated
        """
        url = config.msif_2025_url if year == 2025 else config.msif_2024_url
        
        logger.info(
            "Loading MSIF data",
            year=year,
            url=url,
            prefer_csv=prefer_csv,
            fallback_to_csv=fallback_to_csv
        )
        
        # Try CSV first if preferred
        if prefer_csv:
            try:
                logger.info("Attempting to load from CSV", year=year)
                data = self.load_msif_from_csv(csv_path=csv_path, year=year)
                logger.info("Parsed MSIF CSV file", year=year, local_authorities=len(data))
                records_updated = self.save_to_database(data, year)
                
                if records_updated == 0 and len(data) > 0:
                    logger.warning(
                        "MSIF data parsed but not saved to database",
                        year=year,
                        parsed_records=len(data),
                        saved_records=records_updated,
                        hint="Database might be unavailable or psycopg2 not installed"
                    )
                
                logger.info("Successfully loaded MSIF from CSV", records=records_updated, parsed=len(data), year=year)
                return records_updated
            except Exception as e:
                logger.warning("Failed to load from CSV, falling back to Excel", error=str(e), year=year)
                if not fallback_to_csv:
                    raise
        
        # Try Excel (official source)
        try:
            # Download
            file_path = self.download_msif_file(url, year)
            
            # Parse
            data = self.parse_msif_xls(file_path, year)
            logger.info("Parsed MSIF Excel file", year=year, local_authorities=len(data))
            
            # Save to database
            records_updated = self.save_to_database(data, year)
            
            if records_updated == 0 and len(data) > 0:
                logger.warning(
                    "MSIF data parsed but not saved to database",
                    year=year,
                    parsed_records=len(data),
                    saved_records=records_updated,
                    hint="Database might be unavailable or psycopg2 not installed"
                )
            
            logger.info("Successfully loaded MSIF from Excel", records=records_updated, parsed=len(data), year=year)
            return records_updated
            
        except Exception as e:
            logger.error("Failed to load MSIF from Excel", error=str(e), year=year)
            
            # Fallback to CSV if enabled
            if fallback_to_csv:
                try:
                    logger.info("Falling back to CSV", year=year)
                    data = self.load_msif_from_csv(csv_path=csv_path, year=year)
                    records_updated = self.save_to_database(data, year)
                    logger.info("Successfully loaded MSIF from CSV (fallback)", records=records_updated, year=year)
                    return records_updated
                except Exception as csv_error:
                    logger.error("CSV fallback also failed", error=str(csv_error), year=year)
                    raise MSIFParseError(
                        f"Failed to load MSIF {year} from both Excel and CSV. "
                        f"Excel error: {e}. CSV error: {csv_error}"
                    ) from csv_error
            else:
                raise

