"""Cache implementation for postcode resolver (Redis/SQLite)."""

import json
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import structlog
from .config import config
from .models import PostcodeInfo
from .exceptions import CacheError

logger = structlog.get_logger(__name__)


class CacheBackend:
    """Base cache backend interface."""
    
    def get(self, key: str) -> Optional[PostcodeInfo]:
        """Get value from cache."""
        raise NotImplementedError
    
    def set(self, key: str, value: PostcodeInfo, expiry_days: int) -> None:
        """Set value in cache."""
        raise NotImplementedError
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        raise NotImplementedError
    
    def clear(self) -> None:
        """Clear all cache."""
        raise NotImplementedError


class SQLiteCache(CacheBackend):
    """SQLite cache backend."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize SQLite cache.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or config.cache_dir / "postcode_cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postcode_cache (
                postcode TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at 
            ON postcode_cache(expires_at)
        """)
        
        conn.commit()
        conn.close()
        logger.info("SQLite cache initialized", db=str(self.db_path))
    
    def get(self, key: str) -> Optional[PostcodeInfo]:
        """Get value from SQLite cache."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data, expires_at 
                FROM postcode_cache 
                WHERE postcode = ? AND expires_at > datetime('now')
            """, (key.upper(),))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                data_json, expires_at = row
                data = json.loads(data_json)
                logger.debug("Cache hit", postcode=key)
                return PostcodeInfo(**data)
            
            logger.debug("Cache miss", postcode=key)
            return None
        except Exception as e:
            logger.error("Cache get error", postcode=key, error=str(e))
            return None
    
    def set(self, key: str, value: PostcodeInfo, expiry_days: int) -> None:
        """Set value in SQLite cache."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(days=expiry_days)
            data_json = json.dumps(value.model_dump())
            
            cursor.execute("""
                INSERT OR REPLACE INTO postcode_cache 
                (postcode, data, cached_at, expires_at)
                VALUES (?, ?, datetime('now'), ?)
            """, (key.upper(), data_json, expires_at.isoformat()))
            
            conn.commit()
            conn.close()
            logger.debug("Cache set", postcode=key)
        except Exception as e:
            logger.error("Cache set error", postcode=key, error=str(e))
            raise CacheError(f"Failed to set cache: {e}") from e
    
    def delete(self, key: str) -> None:
        """Delete value from SQLite cache."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM postcode_cache WHERE postcode = ?", (key.upper(),))
            
            conn.commit()
            conn.close()
            logger.debug("Cache delete", postcode=key)
        except Exception as e:
            logger.error("Cache delete error", postcode=key, error=str(e))
    
    def clear(self) -> None:
        """Clear all SQLite cache."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM postcode_cache")
            
            conn.commit()
            conn.close()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error("Cache clear error", error=str(e))
            raise CacheError(f"Failed to clear cache: {e}") from e


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self):
        """Initialize Redis cache."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=config.redis_db,
                password=config.redis_password,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized", host=config.redis_host, port=config.redis_port)
        except ImportError:
            raise CacheError("Redis not installed. Install with: pip install redis")
        except Exception as e:
            raise CacheError(f"Failed to connect to Redis: {e}") from e
    
    def get(self, key: str) -> Optional[PostcodeInfo]:
        """Get value from Redis cache."""
        try:
            data_json = self.redis_client.get(f"postcode:{key.upper()}")
            if data_json:
                data = json.loads(data_json)
                logger.debug("Cache hit", postcode=key)
                return PostcodeInfo(**data)
            logger.debug("Cache miss", postcode=key)
            return None
        except Exception as e:
            logger.error("Cache get error", postcode=key, error=str(e))
            return None
    
    def set(self, key: str, value: PostcodeInfo, expiry_days: int) -> None:
        """Set value in Redis cache."""
        try:
            data_json = json.dumps(value.model_dump())
            expiry_seconds = expiry_days * 24 * 60 * 60
            self.redis_client.setex(
                f"postcode:{key.upper()}",
                expiry_seconds,
                data_json
            )
            logger.debug("Cache set", postcode=key)
        except Exception as e:
            logger.error("Cache set error", postcode=key, error=str(e))
            raise CacheError(f"Failed to set cache: {e}") from e
    
    def delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        try:
            self.redis_client.delete(f"postcode:{key.upper()}")
            logger.debug("Cache delete", postcode=key)
        except Exception as e:
            logger.error("Cache delete error", postcode=key, error=str(e))
    
    def clear(self) -> None:
        """Clear all Redis cache."""
        try:
            keys = self.redis_client.keys("postcode:*")
            if keys:
                self.redis_client.delete(*keys)
            logger.info("Cache cleared", keys_deleted=len(keys))
        except Exception as e:
            logger.error("Cache clear error", error=str(e))
            raise CacheError(f"Failed to clear cache: {e}") from e


def get_cache_backend() -> CacheBackend:
    """
    Get cache backend based on configuration.
    
    Returns:
        Cache backend instance
        
    Raises:
        CacheError: If cache backend cannot be initialized
    """
    if config.cache_type.lower() == "redis":
        try:
            return RedisCache()
        except CacheError:
            logger.warning("Redis cache failed, falling back to SQLite")
            return SQLiteCache()
    else:
        return SQLiteCache()

