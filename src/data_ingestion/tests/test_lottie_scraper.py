"""Tests for Lottie scraper."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import httpx
from data_ingestion.lottie_scraper import LottieScraper
from data_ingestion.exceptions import LottieScrapingError


@pytest.fixture
def lottie_scraper(tmp_path):
    """Create LottieScraper instance with temp cache dir."""
    return LottieScraper(cache_dir=tmp_path / "lottie")


@pytest.fixture
def sample_html():
    """Sample HTML with regional prices."""
    return """
    <html>
    <body>
        <table>
            <tr>
                <th>Region</th>
                <th>Residential</th>
                <th>Nursing</th>
            </tr>
            <tr>
                <td>London</td>
                <td>£950</td>
                <td>£1200</td>
            </tr>
            <tr>
                <td>South East</td>
                <td>£850</td>
                <td>£1100</td>
            </tr>
        </table>
    </body>
    </html>
    """


class TestLottieScraper:
    """Test LottieScraper class."""
    
    def test_init(self, tmp_path):
        """Test LottieScraper initialization."""
        scraper = LottieScraper(cache_dir=tmp_path / "lottie")
        assert scraper.cache_dir.exists()
    
    def test_fetch_page_success(self, lottie_scraper):
        """Test successful page fetch."""
        url = "https://example.com/test"
        html_content = "<html><body>Test</body></html>"
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.text = html_content
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = lottie_scraper.fetch_page(url)
            
            assert result == html_content
            cache_file = lottie_scraper.cache_dir / "test.html"
            assert cache_file.exists()
    
    def test_fetch_page_http_error(self, lottie_scraper):
        """Test page fetch with HTTP error."""
        url = "https://example.com/test"
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPError("HTTP 404")
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(LottieScrapingError):
                lottie_scraper.fetch_page(url)
    
    def test_extract_regional_prices(self, lottie_scraper, sample_html):
        """Test extracting regional prices from HTML."""
        result = lottie_scraper.extract_regional_prices(sample_html, "residential")
        
        assert "London" in result
        assert result["London"] == 950.0
        assert "South East" in result
        assert result["South East"] == 850.0
    
    def test_save_to_database(self, lottie_scraper):
        """Test saving Lottie data to database."""
        data = {
            "residential": {
                "London": 950.0,
                "South East": 850.0
            },
            "nursing": {
                "London": 1200.0,
                "South East": 1100.0
            }
        }
        
        with patch('data_ingestion.lottie_scraper.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn
            
            records = lottie_scraper.save_to_database(data)
            
            assert records == 4  # 2 regions * 2 care types
            assert mock_cursor.execute.called
            assert mock_conn.commit.called
    
    def test_load_lottie_data_full_flow(self, lottie_scraper):
        """Test full Lottie data loading flow."""
        html_content = """
        <html>
        <body>
            <table>
                <tr><td>London</td><td>£950</td></tr>
            </table>
        </body>
        </html>
        """
        
        with patch.object(lottie_scraper, 'fetch_page', return_value=html_content), \
             patch.object(lottie_scraper, 'save_to_database', return_value=3) as mock_save:
            
            records = lottie_scraper.load_lottie_data()
            
            assert records == 3
            assert mock_save.called

