"""Database connection and session management."""

import os
from typing import Generator
from contextlib import contextmanager
import structlog
from .config import config
from .exceptions import DatabaseError

logger = structlog.get_logger(__name__)

# Lazy import psycopg2 to avoid import errors if not installed
_psycopg2 = None

def _get_psycopg2():
    """Lazy import psycopg2."""
    global _psycopg2
    if _psycopg2 is None:
        try:
            import psycopg2
            _psycopg2 = psycopg2
        except ImportError:
            raise DatabaseError(
                "psycopg2 is not installed. Install it with: pip install psycopg2-binary"
            )
    return _psycopg2


@contextmanager
def get_db_connection() -> Generator:
    """
    Get PostgreSQL database connection context manager.
    
    Yields:
        psycopg2 connection object
        
    Raises:
        DatabaseError: If connection fails or psycopg2 is not installed
    """
    psycopg2 = _get_psycopg2()
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password
        )
        logger.debug("Database connection established")
        yield conn
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error("Database error", error=str(e))
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


def init_database() -> None:
    """Initialize database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # MSIF fees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS msif_fees_2025 (
                id SERIAL PRIMARY KEY,
                local_authority TEXT NOT NULL,
                ons_code TEXT,
                residential_fee_65_plus NUMERIC(10, 2),
                nursing_fee_65_plus NUMERIC(10, 2),
                residential_dementia_fee NUMERIC(10, 2),
                nursing_dementia_fee NUMERIC(10, 2),
                respite_fee NUMERIC(10, 2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(local_authority)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS msif_fees_2024 (
                id SERIAL PRIMARY KEY,
                local_authority TEXT NOT NULL,
                ons_code TEXT,
                residential_fee_65_plus NUMERIC(10, 2),
                nursing_fee_65_plus NUMERIC(10, 2),
                residential_dementia_fee NUMERIC(10, 2),
                nursing_dementia_fee NUMERIC(10, 2),
                respite_fee NUMERIC(10, 2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(local_authority)
            )
        """)
        
        # Lottie regional averages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lottie_regional_averages (
                id SERIAL PRIMARY KEY,
                region TEXT NOT NULL,
                care_type TEXT NOT NULL,
                price_per_week NUMERIC(10, 2) NOT NULL,
                source_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(region, care_type)
            )
        """)
        
        # Data update log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_update_log (
                id SERIAL PRIMARY KEY,
                data_source TEXT NOT NULL,
                status TEXT NOT NULL,
                records_updated INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                duration_seconds INTEGER
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_msif_2025_la 
            ON msif_fees_2025(local_authority)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lottie_region_care 
            ON lottie_regional_averages(region, care_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_update_log_source_status 
            ON data_update_log(data_source, status, started_at DESC)
        """)
        
        conn.commit()
        logger.info("Database tables initialized")

