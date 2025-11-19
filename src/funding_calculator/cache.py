"""Caching module for Funding Eligibility Calculator results.

Uses Redis for primary caching with SQLite fallback.
Caches results by user_id + hash(patient_profile).
"""

import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pickle
import base64

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    sqlite3 = None

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration."""
    
    # Redis settings
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    REDIS_SOCKET_TIMEOUT = 5
    
    # Cache settings
    DEFAULT_TTL_SECONDS = 3600 * 24 * 7  # 7 days
    CACHE_PREFIX = "funding_calc:"
    
    # SQLite fallback
    SQLITE_DB_PATH = "funding_cache.db"


class FundingCache:
    """
    Cache manager for funding eligibility calculations.
    
    Uses Redis as primary cache with SQLite fallback.
    """
    
    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = None,
        redis_password: str = None,
        sqlite_db_path: str = None,
        default_ttl: int = None
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_host: Redis host (default from config)
            redis_port: Redis port (default from config)
            redis_db: Redis database number (default from config)
            redis_password: Redis password (optional)
            sqlite_db_path: SQLite database path (default from config)
            default_ttl: Default TTL in seconds (default from config)
        """
        self.config = CacheConfig()
        
        # Override config if provided
        if redis_host:
            self.config.REDIS_HOST = redis_host
        if redis_port:
            self.config.REDIS_PORT = redis_port
        if redis_db is not None:
            self.config.REDIS_DB = redis_db
        if redis_password:
            self.config.REDIS_PASSWORD = redis_password
        if sqlite_db_path:
            self.config.SQLITE_DB_PATH = sqlite_db_path
        if default_ttl:
            self.config.DEFAULT_TTL_SECONDS = default_ttl
        
        # Initialize Redis
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=self.config.REDIS_HOST,
                    port=self.config.REDIS_PORT,
                    db=self.config.REDIS_DB,
                    password=self.config.REDIS_PASSWORD,
                    socket_timeout=self.config.REDIS_SOCKET_TIMEOUT,
                    decode_responses=False  # We'll handle encoding ourselves
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected", host=self.config.REDIS_HOST, port=self.config.REDIS_PORT)
            except Exception as e:
                logger.warning("Redis not available, using SQLite fallback", error=str(e))
                self.redis_client = None
        
        # Initialize SQLite fallback
        self.sqlite_conn = None
        if SQLITE_AVAILABLE and not self.redis_client:
            try:
                self.sqlite_conn = sqlite3.connect(
                    self.config.SQLITE_DB_PATH,
                    check_same_thread=False,
                    timeout=5.0
                )
                self._init_sqlite_db()
                logger.info("SQLite cache initialized", db_path=self.config.SQLITE_DB_PATH)
            except Exception as e:
                logger.warning("SQLite not available", error=str(e))
    
    def _init_sqlite_db(self):
        """Initialize SQLite database schema."""
        if not self.sqlite_conn:
            return
        
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funding_cache (
                cache_key TEXT PRIMARY KEY,
                cache_value BLOB NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                profile_hash TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON funding_cache(expires_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON funding_cache(user_id)
        """)
        self.sqlite_conn.commit()
    
    def _generate_cache_key(
        self,
        user_id: str,
        profile_hash: str,
        override: bool = False
    ) -> str:
        """
        Generate cache key.
        
        Args:
            user_id: User identifier
            profile_hash: Hash of patient profile
            override: Whether this is an admin override
            
        Returns:
            Cache key string
        """
        prefix = self.config.CACHE_PREFIX
        if override:
            prefix += "override:"
        return f"{prefix}{user_id}:{profile_hash}"
    
    def _hash_profile(self, profile: Dict[str, Any]) -> str:
        """
        Generate hash of patient profile.
        
        Args:
            profile: Patient profile dict
            
        Returns:
            SHA256 hash string
        """
        # Normalize profile for hashing (remove None values, sort keys)
        normalized = {}
        for key, value in sorted(profile.items()):
            if value is not None:
                normalized[key] = value
        
        profile_json = json.dumps(normalized, sort_keys=True, default=str)
        return hashlib.sha256(profile_json.encode()).hexdigest()
    
    def get(
        self,
        user_id: str,
        profile: Dict[str, Any],
        check_override: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            user_id: User identifier
            profile: Patient profile dict
            check_override: Whether to check for admin override first
            
        Returns:
            Cached result dict or None
        """
        profile_hash = self._hash_profile(profile)
        
        # Check override first if requested
        if check_override:
            override_key = self._generate_cache_key(user_id, profile_hash, override=True)
            override_result = self._get_from_cache(override_key)
            if override_result:
                logger.info("Cache hit (override)", user_id=user_id, profile_hash=profile_hash[:8])
                return override_result
        
        # Check regular cache
        cache_key = self._generate_cache_key(user_id, profile_hash, override=False)
        result = self._get_from_cache(cache_key)
        
        if result:
            logger.info("Cache hit", user_id=user_id, profile_hash=profile_hash[:8])
        else:
            logger.debug("Cache miss", user_id=user_id, profile_hash=profile_hash[:8])
        
        return result
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache (Redis or SQLite)."""
        # Try Redis first
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return self._deserialize(cached_data)
            except Exception as e:
                logger.warning("Redis get error, trying SQLite", error=str(e))
        
        # Fallback to SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("""
                    SELECT cache_value, expires_at 
                    FROM funding_cache 
                    WHERE cache_key = ? AND expires_at > datetime('now')
                """, (cache_key,))
                row = cursor.fetchone()
                if row:
                    cache_value, expires_at = row
                    return self._deserialize(cache_value)
                else:
                    # Clean up expired entries
                    cursor.execute("DELETE FROM funding_cache WHERE expires_at <= datetime('now')")
                    self.sqlite_conn.commit()
            except Exception as e:
                logger.warning("SQLite get error", error=str(e))
        
        return None
    
    def set(
        self,
        user_id: str,
        profile: Dict[str, Any],
        result: Dict[str, Any],
        ttl: Optional[int] = None,
        override: bool = False
    ) -> bool:
        """
        Cache result.
        
        Args:
            user_id: User identifier
            profile: Patient profile dict
            result: Calculation result dict
            ttl: Time to live in seconds (default from config)
            override: Whether this is an admin override
            
        Returns:
            True if cached successfully
        """
        profile_hash = self._hash_profile(profile)
        cache_key = self._generate_cache_key(user_id, profile_hash, override=override)
        
        if ttl is None:
            ttl = self.config.DEFAULT_TTL_SECONDS
        
        serialized = self._serialize(result)
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl, serialized)
                logger.info("Cached in Redis", user_id=user_id, profile_hash=profile_hash[:8], ttl=ttl)
                return True
            except Exception as e:
                logger.warning("Redis set error, trying SQLite", error=str(e))
        
        # Fallback to SQLite
        if self.sqlite_conn:
            try:
                expires_at = datetime.now() + timedelta(seconds=ttl)
                cursor = self.sqlite_conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO funding_cache 
                    (cache_key, cache_value, expires_at, user_id, profile_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (cache_key, serialized, expires_at.isoformat(), user_id, profile_hash))
                self.sqlite_conn.commit()
                logger.info("Cached in SQLite", user_id=user_id, profile_hash=profile_hash[:8], ttl=ttl)
                return True
            except Exception as e:
                logger.error("SQLite set error", error=str(e))
        
        return False
    
    def delete(
        self,
        user_id: str,
        profile: Dict[str, Any],
        override: bool = False
    ) -> bool:
        """
        Delete cached result.
        
        Args:
            user_id: User identifier
            profile: Patient profile dict
            override: Whether to delete override cache
            
        Returns:
            True if deleted successfully
        """
        profile_hash = self._hash_profile(profile)
        cache_key = self._generate_cache_key(user_id, profile_hash, override=override)
        
        deleted = False
        
        # Delete from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
                deleted = True
            except Exception as e:
                logger.warning("Redis delete error", error=str(e))
        
        # Delete from SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("DELETE FROM funding_cache WHERE cache_key = ?", (cache_key,))
                self.sqlite_conn.commit()
                deleted = True
            except Exception as e:
                logger.warning("SQLite delete error", error=str(e))
        
        if deleted:
            logger.info("Cache deleted", user_id=user_id, profile_hash=profile_hash[:8])
        
        return deleted
    
    def clear_user_cache(self, user_id: str) -> int:
        """
        Clear all cache entries for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of entries deleted
        """
        count = 0
        
        # Clear from Redis
        if self.redis_client:
            try:
                pattern = f"{self.config.CACHE_PREFIX}*:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    count += self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning("Redis clear error", error=str(e))
        
        # Clear from SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("DELETE FROM funding_cache WHERE user_id = ?", (user_id,))
                count += cursor.rowcount
                self.sqlite_conn.commit()
            except Exception as e:
                logger.warning("SQLite clear error", error=str(e))
        
        if count > 0:
            logger.info("User cache cleared", user_id=user_id, count=count)
        
        return count
    
    def _serialize(self, data: Dict[str, Any]) -> bytes:
        """Serialize data for caching."""
        try:
            # Try JSON first (human-readable)
            json_str = json.dumps(data, default=str)
            return json_str.encode('utf-8')
        except Exception:
            # Fallback to pickle
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize cached data."""
        try:
            # Try JSON first
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except Exception:
            # Fallback to pickle
            return pickle.loads(data)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        stats = {
            "redis_available": self.redis_client is not None,
            "sqlite_available": self.sqlite_conn is not None,
            "redis_keys": 0,
            "sqlite_keys": 0
        }
        
        # Redis stats
        if self.redis_client:
            try:
                pattern = f"{self.config.CACHE_PREFIX}*"
                keys = self.redis_client.keys(pattern)
                stats["redis_keys"] = len(keys) if keys else 0
            except Exception:
                pass
        
        # SQLite stats
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM funding_cache WHERE expires_at > datetime('now')")
                stats["sqlite_keys"] = cursor.fetchone()[0]
            except Exception:
                pass
        
        return stats
    
    def close(self):
        """Close cache connections."""
        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception:
                pass
        
        if self.sqlite_conn:
            try:
                self.sqlite_conn.close()
            except Exception:
                pass

