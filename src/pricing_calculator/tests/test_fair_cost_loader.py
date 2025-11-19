"""Tests for fair_cost_loader.py."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from pricing_calculator.fair_cost_loader import (
    load_fair_cost_data,
    _download_file,
    _parse_msif_xls,
    _is_file_stale
)
from pricing_calculator.exceptions import FairCostDataError


def test_is_file_stale_not_exists():
    """Test file staleness check for non-existent file."""
    fake_path = Path("/nonexistent/file.xlsx")
    assert _is_file_stale(fake_path) is True


def test_is_file_stale_recent():
    """Test file staleness check for recent file."""
    import tempfile
    import time
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
        temp_path = Path(f.name)
    
    try:
        # File was just created, should not be stale
        assert _is_file_stale(temp_path, max_age_days=30) is False
    finally:
        temp_path.unlink()


@patch("pricing_calculator.fair_cost_loader.httpx.Client")
def test_download_file_success(mock_client_class):
    """Test successful file download."""
    mock_response = MagicMock()
    mock_response.content = b"fake xlsx content"
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    import tempfile
    temp_path = Path(tempfile.mktemp(suffix=".xlsx"))
    
    try:
        _download_file("http://example.com/file.xlsx", temp_path)
        assert temp_path.exists()
    finally:
        if temp_path.exists():
            temp_path.unlink()


@patch("pricing_calculator.fair_cost_loader.httpx.Client")
def test_download_file_error(mock_client_class):
    """Test file download error handling."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.side_effect = Exception("Network error")
    mock_client_class.return_value = mock_client
    
    import tempfile
    temp_path = Path(tempfile.mktemp(suffix=".xlsx"))
    
    with pytest.raises(FairCostDataError):
        _download_file("http://example.com/file.xlsx", temp_path)


@patch("pricing_calculator.fair_cost_loader.pd.ExcelFile")
@patch("pricing_calculator.fair_cost_loader.pd.read_excel")
def test_parse_msif_xls_success(mock_read_excel, mock_excel_file):
    """Test successful MSIF XLS parsing."""
    import pandas as pd
    
    # Mock Excel file
    mock_excel = MagicMock()
    mock_excel.sheet_names = ["Fees"]
    mock_excel_file.return_value = mock_excel
    
    # Mock DataFrame
    mock_df = pd.DataFrame({
        "Local Authority": ["Birmingham", "Westminster"],
        "Residential 65+ Median": [750.0, 950.0],
        "Nursing 65+ Median": [950.0, 1200.0],
        "Dementia Uplift": [50.0, 100.0]
    })
    mock_read_excel.return_value = mock_df
    
    import tempfile
    temp_path = Path(tempfile.mktemp(suffix=".xlsx"))
    temp_path.touch()
    
    try:
        result = _parse_msif_xls(temp_path)
        assert "Birmingham" in result
        assert "Westminster" in result
        assert result["Birmingham"]["residential"] == 750.0
    finally:
        if temp_path.exists():
            temp_path.unlink()


@patch("pricing_calculator.fair_cost_loader._is_file_stale")
@patch("pricing_calculator.fair_cost_loader._download_file")
@patch("pricing_calculator.fair_cost_loader._parse_msif_xls")
def test_load_fair_cost_data_cached(mock_parse, mock_download, mock_stale):
    """Test loading fair cost data from cache."""
    mock_stale.return_value = False  # File is not stale
    mock_parse.return_value = {"Birmingham": {"residential": 750.0}}
    
    import tempfile
    temp_path = Path(tempfile.mktemp(suffix=".xlsx"))
    temp_path.touch()
    
    try:
        result = load_fair_cost_data(xls_path=temp_path, force_download=False)
        assert "Birmingham" in result
        mock_download.assert_not_called()  # Should not download if cached
    finally:
        if temp_path.exists():
            temp_path.unlink()

