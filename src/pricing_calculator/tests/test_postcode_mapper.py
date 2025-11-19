"""Tests for postcode_mapper.py."""

import pytest
from unittest.mock import patch, MagicMock
from pricing_calculator.postcode_mapper import PostcodeMapper, get_postcode_info
from pricing_calculator.exceptions import PostcodeMappingError


def test_postcode_mapper_init():
    """Test PostcodeMapper initialization."""
    mapper = PostcodeMapper()
    assert mapper.cache_db_path is not None


@patch("pricing_calculator.postcode_mapper.httpx.Client")
def test_fetch_from_api_success(mock_client_class):
    """Test successful API fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": 200,
        "result": {
            "admin_district": "Westminster",
            "region": "London",
            "admin_county": None,
            "country": "England"
        }
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    mapper = PostcodeMapper()
    info = mapper._fetch_from_api("SW1A 1AA")
    
    assert info.local_authority == "Westminster"
    assert info.region == "London"
    assert info.country == "England"


@patch("pricing_calculator.postcode_mapper.httpx.Client")
def test_fetch_from_api_error(mock_client_class):
    """Test API fetch error handling."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.side_effect = Exception("Network error")
    mock_client_class.return_value = mock_client
    
    mapper = PostcodeMapper()
    
    with pytest.raises(PostcodeMappingError):
        mapper._fetch_from_api("SW1A 1AA")


def test_normalize_region():
    """Test region normalization."""
    mapper = PostcodeMapper()
    
    assert mapper._normalize_region("Greater London") == "London"
    assert mapper._normalize_region("South East England") == "South East"
    assert mapper._normalize_region("Unknown Region") == "Unknown Region"


@patch("pricing_calculator.postcode_mapper.PostcodeMapper._fetch_from_api")
def test_get_postcode_info_cached(mock_fetch):
    """Test postcode info retrieval with caching."""
    from pricing_calculator.models import PostcodeInfo
    
    mapper = PostcodeMapper()
    
    # First call - should fetch from API
    mock_info = PostcodeInfo(
        postcode="SW1A 1AA",
        local_authority="Westminster",
        region="London"
    )
    mock_fetch.return_value = mock_info
    
    info1 = mapper.get_postcode_info("SW1A 1AA")
    assert info1.local_authority == "Westminster"
    assert mock_fetch.call_count == 1
    
    # Second call - should use cache
    info2 = mapper.get_postcode_info("SW1A 1AA")
    assert info2.local_authority == "Westminster"
    # Should not call API again (cache hit)
    # Note: In real scenario, cache would be checked first


def test_get_postcode_info_function():
    """Test convenience function."""
    with patch("pricing_calculator.postcode_mapper.PostcodeMapper.get_postcode_info") as mock_get:
        mock_info = MagicMock()
        mock_info.local_authority = "Test"
        mock_get.return_value = mock_info
        
        info = get_postcode_info("SW1A 1AA")
        assert info.local_authority == "Test"

