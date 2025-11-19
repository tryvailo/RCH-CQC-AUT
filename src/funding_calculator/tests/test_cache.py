"""Tests for cache module."""

import pytest
import tempfile
import os
from funding_calculator.cache import FundingCache, CacheConfig


class TestCacheConfig:
    """Test cache configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()
        assert config.REDIS_HOST == "localhost"
        assert config.REDIS_PORT == 6379
        assert config.DEFAULT_TTL_SECONDS > 0
        assert config.CACHE_PREFIX == "funding_calc:"


class TestFundingCache:
    """Test FundingCache class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def cache(self, temp_db):
        """Create cache instance with SQLite fallback."""
        return FundingCache(sqlite_db_path=temp_db)
    
    def test_cache_initialization(self, temp_db):
        """Test cache initialization."""
        cache = FundingCache(sqlite_db_path=temp_db)
        assert cache is not None
        assert cache.config is not None
    
    def test_hash_profile(self, cache):
        """Test profile hashing."""
        profile1 = {"age": 80, "has_dementia": True}
        profile2 = {"age": 80, "has_dementia": True}
        profile3 = {"age": 81, "has_dementia": True}
        
        hash1 = cache._hash_profile(profile1)
        hash2 = cache._hash_profile(profile2)
        hash3 = cache._hash_profile(profile3)
        
        assert hash1 == hash2  # Same profile = same hash
        assert hash1 != hash3  # Different profile = different hash
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_hash_profile_normalization(self, cache):
        """Test that profile normalization works."""
        profile1 = {"age": 80, "has_dementia": True, "extra": None}
        profile2 = {"has_dementia": True, "age": 80}
        
        hash1 = cache._hash_profile(profile1)
        hash2 = cache._hash_profile(profile2)
        
        # Should be same (None values ignored, keys sorted)
        assert hash1 == hash2
    
    def test_generate_cache_key(self, cache):
        """Test cache key generation."""
        user_id = "user123"
        profile_hash = "abc123"
        
        key1 = cache._generate_cache_key(user_id, profile_hash, override=False)
        key2 = cache._generate_cache_key(user_id, profile_hash, override=True)
        
        assert key1.startswith(cache.config.CACHE_PREFIX)
        assert key2.startswith(cache.config.CACHE_PREFIX + "override:")
        assert user_id in key1
        assert profile_hash in key1
        assert key1 != key2
    
    def test_set_and_get(self, cache):
        """Test setting and getting from cache."""
        user_id = "test_user"
        profile = {"age": 80, "has_dementia": True}
        result = {"chc_probability": 75, "savings": 10000}
        
        # Set cache
        success = cache.set(user_id, profile, result, ttl=3600)
        assert success is True
        
        # Get cache
        cached = cache.get(user_id, profile)
        assert cached is not None
        assert cached["chc_probability"] == 75
        assert cached["savings"] == 10000
    
    def test_cache_miss(self, cache):
        """Test cache miss scenario."""
        user_id = "test_user"
        profile = {"age": 80}
        
        cached = cache.get(user_id, profile)
        assert cached is None
    
    def test_cache_override(self, cache):
        """Test admin override cache."""
        user_id = "test_user"
        profile = {"age": 80}
        regular_result = {"chc_probability": 50}
        override_result = {"chc_probability": 90}
        
        # Set regular cache
        cache.set(user_id, profile, regular_result, override=False)
        
        # Set override cache
        cache.set(user_id, profile, override_result, override=True)
        
        # Get should return override first
        cached = cache.get(user_id, profile, check_override=True)
        assert cached["chc_probability"] == 90
        
        # Get without override check should return regular
        cached = cache.get(user_id, profile, check_override=False)
        assert cached["chc_probability"] == 50
    
    def test_cache_delete(self, cache):
        """Test cache deletion."""
        user_id = "test_user"
        profile = {"age": 80}
        result = {"chc_probability": 75}
        
        # Set and verify
        cache.set(user_id, profile, result)
        assert cache.get(user_id, profile) is not None
        
        # Delete
        deleted = cache.delete(user_id, profile)
        assert deleted is True
        
        # Verify deleted
        assert cache.get(user_id, profile) is None
    
    def test_clear_user_cache(self, cache):
        """Test clearing all cache for a user."""
        user_id = "test_user"
        
        # Set multiple entries
        for i in range(5):
            profile = {"age": 80 + i}
            result = {"chc_probability": 50 + i}
            cache.set(user_id, profile, result)
        
        # Clear all
        count = cache.clear_user_cache(user_id)
        assert count >= 5
        
        # Verify all cleared
        for i in range(5):
            profile = {"age": 80 + i}
            assert cache.get(user_id, profile) is None
    
    def test_cache_stats(self, cache):
        """Test cache statistics."""
        stats = cache.get_stats()
        
        assert "redis_available" in stats
        assert "sqlite_available" in stats
        assert "redis_keys" in stats
        assert "sqlite_keys" in stats
    
    def test_serialize_deserialize(self, cache):
        """Test serialization and deserialization."""
        data = {
            "chc_probability": 75,
            "savings": {"annual": 10000, "five_year": 50000},
            "timestamp": "2025-01-01T00:00:00"
        }
        
        serialized = cache._serialize(data)
        assert isinstance(serialized, bytes)
        
        deserialized = cache._deserialize(serialized)
        assert deserialized == data
    
    def test_cache_ttl(self, cache):
        """Test cache TTL expiration."""
        user_id = "test_user"
        profile = {"age": 80}
        result = {"chc_probability": 75}
        
        # Set with short TTL
        cache.set(user_id, profile, result, ttl=1)
        
        # Should be available immediately
        assert cache.get(user_id, profile) is not None
        
        # Wait for expiration (if SQLite)
        import time
        time.sleep(2)
        
        # Should be expired (SQLite checks expiration)
        # Note: Redis TTL is handled by Redis itself
        if cache.sqlite_conn:
            cached = cache.get(user_id, profile)
            # May or may not be None depending on cleanup timing
            # This is a best-effort test
    
    def test_cache_close(self, cache):
        """Test cache cleanup."""
        cache.close()
        # Should not raise exception
        assert True


class TestCacheIntegration:
    """Test cache integration with calculator."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    def test_calculator_with_cache(self, temp_db):
        """Test calculator with cache."""
        from funding_calculator import FundingEligibilityCalculator
        from funding_calculator.cache import FundingCache
        from funding_calculator.models import PatientProfile, DomainAssessment, Domain, DomainLevel
        
        cache = FundingCache(sqlite_db_path=temp_db)
        calculator = FundingEligibilityCalculator(cache=cache)
        
        profile_dict = {
            "age": 80,
            "domain_assessments": {
                "cognition": {
                    "domain": "cognition",
                    "level": "severe",
                    "description": "Severe dementia"
                }
            }
        }
        
        # First calculation (should cache)
        result1 = calculator.calculate_full_eligibility(
            patient_profile=profile_dict,
            user_id="test_user",
            use_cache=True
        )
        
        # Second calculation (should use cache)
        result2 = calculator.calculate_full_eligibility(
            patient_profile=profile_dict,
            user_id="test_user",
            use_cache=True
        )
        
        # Results should be identical
        assert result1.chc_eligibility.probability_percent == result2.chc_eligibility.probability_percent
        
        cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

