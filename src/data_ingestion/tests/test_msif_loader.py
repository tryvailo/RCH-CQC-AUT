"""Tests for MSIF loader."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import httpx
from data_ingestion.msif_loader import MSIFLoader
from data_ingestion.exceptions import MSIFDownloadError, MSIFParseError


@pytest.fixture
def msif_loader(tmp_path):
    """Create MSIFLoader instance with temp cache dir."""
    return MSIFLoader(cache_dir=tmp_path / "msif")


@pytest.fixture
def sample_msif_xls(tmp_path):
    """Create sample MSIF XLS file."""
    file_path = tmp_path / "test_msif.xlsx"
    
    # Create sample data
    data = {
        'ONS Code': ['E06000001', 'E06000002', 'E06000003'],
        'Local Authority': ['Barnet', 'Camden', 'Westminster'],
        'Col1': [None, None, None],
        'Col2': [None, None, None],
        'Col3': [None, None, None],
        'Col4': [None, None, None],
        'Residential 65+ fee 2025-26': [1116.0, 1150.0, 1200.0],
        'Col7': [None, None, None],
        'Col8': [None, None, None],
        'Nursing 65+ fee 2025-26': [1500.0, 1550.0, 1600.0],
    }
    
    df = pd.DataFrame(data)
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Table A 2025-26', index=False)
    
    return file_path


class TestMSIFLoader:
    """Test MSIFLoader class."""
    
    def test_init(self, tmp_path):
        """Test MSIFLoader initialization."""
        loader = MSIFLoader(cache_dir=tmp_path / "msif")
        assert loader.cache_dir.exists()
    
    def test_download_msif_file_success(self, msif_loader, tmp_path):
        """Test successful MSIF file download."""
        url = "https://example.com/test.xlsx"
        content = b"fake xlsx content"
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.content = content
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            file_path = msif_loader.download_msif_file(url, 2025)
            
            assert file_path.exists()
            assert file_path.read_bytes() == content
    
    def test_download_msif_file_http_error(self, msif_loader):
        """Test MSIF download with HTTP error."""
        url = "https://example.com/test.xlsx"
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPError("HTTP 404")
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(MSIFDownloadError):
                msif_loader.download_msif_file(url, 2025)
    
    def test_parse_msif_xls_success(self, msif_loader, sample_msif_xls):
        """Test successful MSIF XLS parsing."""
        result = msif_loader.parse_msif_xls(sample_msif_xls, 2025)
        
        assert len(result) == 3
        assert "Barnet" in result
        assert result["Barnet"]["residential"] == 1116.0
        assert result["Barnet"]["nursing"] == 1500.0
        assert result["Barnet"]["residential_dementia"] == pytest.approx(1116.0 * 1.12)
        assert result["Barnet"]["nursing_dementia"] == pytest.approx(1500.0 * 1.12)
    
    def test_parse_msif_xls_missing_sheet(self, msif_loader, tmp_path):
        """Test parsing MSIF XLS with missing sheet."""
        file_path = tmp_path / "test.xlsx"
        
        # Create file with wrong sheet name
        df = pd.DataFrame({'A': [1, 2, 3]})
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Wrong Sheet', index=False)
        
        with pytest.raises(MSIFParseError):
            msif_loader.parse_msif_xls(file_path, 2025)
    
    def test_save_to_database(self, msif_loader):
        """Test saving MSIF data to database."""
        data = {
            "Barnet": {
                "residential": 1116.0,
                "nursing": 1500.0,
                "residential_dementia": 1249.92,
                "nursing_dementia": 1680.0,
                "respite": 1116.0
            }
        }
        
        with patch('data_ingestion.msif_loader.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn
            
            records = msif_loader.save_to_database(data, 2025)
            
            assert records == 1
            assert mock_cursor.execute.called
            assert mock_conn.commit.called
    
    def test_load_msif_data_full_flow(self, msif_loader, sample_msif_xls):
        """Test full MSIF data loading flow."""
        url = "https://example.com/test.xlsx"
        
        with patch.object(msif_loader, 'download_msif_file', return_value=sample_msif_xls), \
             patch.object(msif_loader, 'save_to_database', return_value=3) as mock_save:
            
            records = msif_loader.load_msif_data(2025)
            
            assert records == 3
            assert mock_save.called
    
    def test_load_msif_from_csv_success(self, msif_loader, tmp_path):
        """Test loading MSIF data from CSV file."""
        # Create sample CSV
        csv_path = tmp_path / "msif_2025_2026_processed.csv"
        csv_content = """local_authority,residential_65_median,nursing_65_median
Barnet,1151.0,1181.0
Birmingham,873.85,889.07
Westminster,1064.0,984.0"""
        csv_path.write_text(csv_content)
        
        result = msif_loader.load_msif_from_csv(csv_path=csv_path, year=2025)
        
        assert len(result) == 3
        assert "Barnet" in result
        assert result["Barnet"]["residential"] == 1151.0
        assert result["Barnet"]["nursing"] == 1181.0
        assert result["Barnet"]["residential_dementia"] == pytest.approx(1151.0 * 1.12)
        assert result["Barnet"]["nursing_dementia"] == pytest.approx(1181.0 * 1.12)
        assert result["Barnet"]["respite"] == 1151.0
    
    def test_load_msif_from_csv_missing_file(self, msif_loader):
        """Test loading MSIF from non-existent CSV file."""
        csv_path = Path("/nonexistent/path/msif.csv")
        
        with pytest.raises(MSIFParseError, match="CSV file not found"):
            msif_loader.load_msif_from_csv(csv_path=csv_path, year=2025)
    
    def test_load_msif_from_csv_missing_columns(self, msif_loader, tmp_path):
        """Test loading MSIF from CSV with missing columns."""
        csv_path = tmp_path / "bad_msif.csv"
        csv_content = """local_authority,other_column
Barnet,1151.0"""
        csv_path.write_text(csv_content)
        
        with pytest.raises(MSIFParseError, match="missing required columns"):
            msif_loader.load_msif_from_csv(csv_path=csv_path, year=2025)
    
    def test_load_msif_data_prefer_csv(self, msif_loader, tmp_path):
        """Test loading MSIF data with CSV preference."""
        csv_path = tmp_path / "msif_2025_2026_processed.csv"
        csv_content = """local_authority,residential_65_median,nursing_65_median
Barnet,1151.0,1181.0"""
        csv_path.write_text(csv_content)
        
        with patch.object(msif_loader, 'save_to_database', return_value=1) as mock_save:
            records = msif_loader.load_msif_data(
                year=2025,
                prefer_csv=True,
                csv_path=csv_path,
                fallback_to_csv=False
            )
            
            assert records == 1
            assert mock_save.called
    
    def test_load_msif_data_csv_fallback(self, msif_loader, tmp_path):
        """Test CSV fallback when Excel parsing fails."""
        csv_path = tmp_path / "msif_2025_2026_processed.csv"
        csv_content = """local_authority,residential_65_median,nursing_65_median
Barnet,1151.0,1181.0"""
        csv_path.write_text(csv_content)
        
        url = "https://example.com/test.xlsx"
        
        with patch.object(msif_loader, 'download_msif_file', side_effect=MSIFDownloadError("Download failed")), \
             patch.object(msif_loader, 'save_to_database', return_value=1) as mock_save:
            
            records = msif_loader.load_msif_data(
                year=2025,
                prefer_csv=False,
                csv_path=csv_path,
                fallback_to_csv=True
            )
            
            assert records == 1
            assert mock_save.called

