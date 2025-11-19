"""Tests for cache backends."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from postcode_resolver.cache import SQLiteCache, RedisCache, get_cache_backend
from postcode_resolver.models import PostcodeInfo
from postcode_resolver.config import config


@pytest.fixture
def sqlite_cache(tmp_path):
    """Create SQLiteCache instance with temp DB."""
    db_path = tmp_path / "test_cache.db"
    return SQLiteCache(db_path=db_path)


class TestSQLiteCache:
    """Test SQLiteCache backend."""
    
    def test_set_get(self, sqlite_cache):
        """Test setting and getting from cache."""
        postcode_info = PostcodeInfo(
            postcode="B15 2HQ",
            local_authority="Birmingham",
            region="West Midlands",
            lat=52.475,
            lon=-1.920
        )
        
        sqlite_cache.set("B15 2HQ", postcode_info, expiry_days=1)
        result = sqlite_cache.get("B15 2HQ")
        
        assert result is not None
        assert result.postcode == "B15 2HQ"
        assert result.local_authority == "Birmingham"
    
    def test_get_miss(self, sqlite_cache):
        """Test cache miss."""
        result = sqlite_cache.get("NONEXISTENT")
        assert result is None
    
    def test_delete(self, sqlite_cache):
        """Test cache deletion."""
        postcode_info = PostcodeInfo(
            postcode="B15 2HQ",
            local_authority="Birmingham",
            region="West Midlands",
            lat=52.475,
            lon=-1.920
        )
        
        sqlite_cache.set("B15 2HQ", postcode_info, expiry_days=1)
        sqlite_cache.delete("B15 2HQ")
        
        result = sqlite_cache.get("B15 2HQ")
        assert result is None
    
    def test_clear(self, sqlite_cache):
        """Test cache clearing."""
        postcode_info = PostcodeInfo(
            postcode="B15 2HQ",
            local_authority="Birmingham",
            region="West Midlands",
            lat=52.475,
            lon=-1.920
        )
        
        sqlite_cache.set("B15 2HQ", postcode_info, expiry_days=1)
        sqlite_cache.clear()
        
        result = sqlite_cache.get("B15 2HQ")
        assert result is None


class TestRedisCache:
    """Test RedisCache backend."""
    
    def test_redis_not_available(self):
        """Test fallback when Redis not available."""
        with patch('postcode_resolver.cache.redis') as mock_redis:
            mock_redis.Redis.side_effect = ImportError("No module named 'redis'")
            
            # Should fall back to SQLite
            cache = get_cache_backend()
            assert isinstance(cache, SQLiteCache)
    
    def test_redis_connection_error(self):
        """Test fallback when Redis connection fails."""
        with patch('postcode_resolver.cache.redis') as mock_redis:
            mock_redis_client = Mock()
            mock_redis_client.ping.side_effect = Exception("Connection failed")
            mock_redis.Redis.return_value = mock_redis_client
            
            # Should fall back to SQLite
            cache = get_cache_backend()
            assert isinstance(cache, SQLiteCache)

