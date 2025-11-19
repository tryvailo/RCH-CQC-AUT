"""Tests for postcode validator."""

import pytest
from postcode_resolver.validator import (
    validate_postcode,
    normalize_postcode,
    is_valid_postcode
)
from postcode_resolver.exceptions import InvalidPostcodeError


class TestPostcodeValidator:
    """Test postcode validation."""
    
    def test_valid_postcodes(self):
        """Test valid UK postcode formats."""
        valid_postcodes = [
            "B15 2HQ",
            "SW1A 1AA",
            "M1 1AA",
            "EC1A 1BB",
            "W1A 0AX",
            "B33 8TH",
            "CR2 6XH",
            "DN55 1PT",
            "EH1 1YZ",
            "CF10 3AT",
            "BT1 5GS",
        ]
        
        for postcode in valid_postcodes:
            assert validate_postcode(postcode) is True
            assert is_valid_postcode(postcode) is True
    
    def test_invalid_postcodes(self):
        """Test invalid UK postcode formats."""
        invalid_postcodes = [
            "",
            "12345",
            "ABC",
            "B15",
            "B15 2",
            "B15 2H",
            "B15 2HQX",
            "QQ1 1AA",  # Starts with Q
            "VX1 1AA",  # Starts with V
            "XX1 1AA",  # Starts with X
            "B15 2CQ",  # Inward starts with C
            "B15 2IQ",  # Inward starts with I
        ]
        
        for postcode in invalid_postcodes:
            assert is_valid_postcode(postcode) is False
            with pytest.raises(InvalidPostcodeError):
                validate_postcode(postcode)
    
    def test_normalize_postcode(self):
        """Test postcode normalization."""
        test_cases = [
            ("b15 2hq", "B15 2HQ"),
            ("B152HQ", "B15 2HQ"),
            ("  B15  2HQ  ", "B15 2HQ"),
            ("sw1a1aa", "SW1A 1AA"),
        ]
        
        for input_postcode, expected in test_cases:
            result = normalize_postcode(input_postcode)
            assert result == expected
    
    def test_normalize_invalid(self):
        """Test normalization with invalid postcode."""
        with pytest.raises(InvalidPostcodeError):
            normalize_postcode("")

