"""Tests for postcode resolver."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx
from postcode_resolver.resolver import PostcodeResolver
from postcode_resolver.models import PostcodeInfo
from postcode_resolver.exceptions import InvalidPostcodeError, PostcodeNotFoundError, APIError


@pytest.fixture
def resolver():
    """Create PostcodeResolver instance."""
    return PostcodeResolver()


@pytest.fixture
def mock_api_response():
    """Mock postcodes.io API response."""
    return {
        "status": 200,
        "result": {
            "postcode": "B15 2HQ",
            "latitude": 52.475,
            "longitude": -1.920,
            "country": "England",
            "region": "West Midlands",
            "admin_district": "Birmingham",
            "admin_county": "West Midlands",
            "admin_ward": "Edgbaston",
            "parliamentary_constituency": "Birmingham Edgbaston"
        }
    }


class TestPostcodeResolver:
    """Test PostcodeResolver class."""
    
    def test_resolve_success(self, resolver, mock_api_response):
        """Test successful postcode resolution."""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch.object(resolver.cache, 'get', return_value=None):
                with patch.object(resolver.cache, 'set'):
                    result = resolver.resolve("B15 2HQ")
            
            assert isinstance(result, PostcodeInfo)
            assert result.postcode == "B15 2HQ"
            assert result.local_authority == "Birmingham"
            assert result.region == "West Midlands"
            assert result.lat == 52.475
            assert result.lon == -1.920
    
    def test_resolve_from_cache(self, resolver):
        """Test resolving from cache."""
        cached_result = PostcodeInfo(
            postcode="B15 2HQ",
            local_authority="Birmingham",
            region="West Midlands",
            lat=52.475,
            lon=-1.920
        )
        
        with patch.object(resolver.cache, 'get', return_value=cached_result):
            result = resolver.resolve("B15 2HQ", use_cache=True)
            
            assert result == cached_result
    
    def test_resolve_invalid_format(self, resolver):
        """Test resolving invalid postcode format."""
        with pytest.raises(InvalidPostcodeError):
            resolver.resolve("INVALID")
    
    def test_resolve_not_found(self, resolver):
        """Test resolving non-existent postcode."""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch.object(resolver.cache, 'get', return_value=None):
                with pytest.raises(PostcodeNotFoundError):
                    resolver.resolve("ZZ99 9ZZ")
    
    def test_resolve_api_error(self, resolver):
        """Test API error handling."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError("Connection error")
            
            with patch.object(resolver.cache, 'get', return_value=None):
                with pytest.raises(APIError):
                    resolver.resolve("B15 2HQ")

