"""Tests for batch postcode resolver."""

import pytest
from unittest.mock import Mock, patch
import httpx
from postcode_resolver.batch_resolver import BatchPostcodeResolver
from postcode_resolver.models import PostcodeInfo, BatchPostcodeResponse


@pytest.fixture
def batch_resolver():
    """Create BatchPostcodeResolver instance."""
    return BatchPostcodeResolver()


@pytest.fixture
def mock_batch_api_response():
    """Mock batch API response."""
    return {
        "status": 200,
        "result": [
            {
                "query": "B15 2HQ",
                "result": {
                    "postcode": "B15 2HQ",
                    "latitude": 52.475,
                    "longitude": -1.920,
                    "country": "England",
                    "region": "West Midlands",
                    "admin_district": "Birmingham"
                }
            },
            {
                "query": "SW1A 1AA",
                "result": {
                    "postcode": "SW1A 1AA",
                    "latitude": 51.499,
                    "longitude": -0.124,
                    "country": "England",
                    "region": "London",
                    "admin_district": "Westminster"
                }
            },
            {
                "query": "INVALID",
                "result": None
            }
        ]
    }


class TestBatchPostcodeResolver:
    """Test BatchPostcodeResolver class."""
    
    def test_resolve_batch_success(self, batch_resolver, mock_batch_api_response):
        """Test successful batch resolution."""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_batch_api_response
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response
            
            with patch.object(batch_resolver.cache, 'get', return_value=None):
                with patch.object(batch_resolver.cache, 'set'):
                    result = batch_resolver.resolve_batch(["B15 2HQ", "SW1A 1AA", "INVALID"])
            
            assert isinstance(result, BatchPostcodeResponse)
            assert result.total == 3
            assert result.found == 2
            assert result.not_found == 1
            assert len(result.results) == 3
            assert result.results[0] is not None
            assert result.results[1] is not None
            assert result.results[2] is None
    
    def test_resolve_batch_empty(self, batch_resolver):
        """Test batch resolution with empty list."""
        result = batch_resolver.resolve_batch([])
        assert result.total == 0
        assert result.found == 0
        assert result.not_found == 0
    
    def test_resolve_batch_large(self, batch_resolver):
        """Test batch resolution with large list (should split into batches)."""
        postcodes = [f"M{i} {i}AA" for i in range(1, 150)]  # 149 postcodes
        
        with patch.object(batch_resolver, '_resolve_via_api', return_value=[None] * 149):
            result = batch_resolver.resolve_batch(postcodes)
            
            assert result.total == 149

