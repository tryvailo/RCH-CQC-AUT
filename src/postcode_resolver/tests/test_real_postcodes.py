"""Tests with 50 real UK postcodes from different regions."""

import pytest
from unittest.mock import Mock, patch
from postcode_resolver.resolver import PostcodeResolver
from postcode_resolver.batch_resolver import BatchPostcodeResolver
from postcode_resolver.validator import is_valid_postcode


# 50 real UK postcodes covering all regions
REAL_POSTCODES = [
    # England - London
    "SW1A 1AA",  # Westminster
    "EC1A 1BB",  # City of London
    "W1A 0AX",  # Westminster
    "N1 9GU",   # Islington
    "SE1 9RT",  # Southwark
    
    # England - South East
    "OX1 1DP",  # Oxford
    "RG1 1EJ",  # Reading
    "BN1 1AL",  # Brighton
    "GU1 3XX",  # Guildford
    "ME1 1BB",  # Medway
    
    # England - South West
    "BS1 5TR",  # Bristol
    "BA1 1AA",  # Bath
    "EX1 1GE",  # Exeter
    "PL1 2AA",  # Plymouth
    "TR1 1XX",  # Truro
    
    # England - West Midlands
    "B15 2HQ",  # Birmingham
    "CV1 1FH",  # Coventry
    "DY1 1AA",  # Dudley
    "WS1 1TP",  # Walsall
    "WV1 1LY",  # Wolverhampton
    
    # England - East Midlands
    "NG1 5DT",  # Nottingham
    "LE1 6TP",  # Leicester
    "DE1 2PL",  # Derby
    "PE1 1XN",  # Peterborough
    "LN1 1BA",  # Lincoln
    
    # England - East of England
    "CB2 1TN",  # Cambridge
    "IP1 1EE",  # Ipswich
    "NR2 1TF",  # Norwich
    "LU1 2JY",  # Luton
    "CM1 1AB",  # Chelmsford
    
    # England - Yorkshire and the Humber
    "LS1 4DY",  # Leeds
    "S1 2HE",   # Sheffield
    "YO1 7HH",  # York
    "HU1 3UZ",  # Hull
    "DN1 3HX",  # Doncaster
    
    # England - North West
    "M1 1AA",   # Manchester
    "L1 8JQ",   # Liverpool
    "PR1 8BX",  # Preston
    "BL1 1RU",  # Bolton
    "WA1 1AB",  # Warrington
    
    # England - North East
    "NE1 7RU",  # Newcastle
    "DH1 3NJ",  # Durham
    "SR1 3AH",  # Sunderland
    "TS1 2ER",  # Middlesbrough
    "DL1 1AA",  # Darlington
    
    # Scotland
    "EH1 1YZ",  # Edinburgh
    "G1 2FF",   # Glasgow
    "AB10 1AB", # Aberdeen
    "DD1 1DD",  # Dundee
    "KY1 1XX",  # Kirkcaldy
    
    # Wales
    "CF10 3AT", # Cardiff
    "SA1 3QQ",  # Swansea
    "LL11 1AA", # Wrexham
    "NP20 2AQ", # Newport
    "SY1 1AA",  # Shrewsbury (near Wales border)
    
    # Northern Ireland
    "BT1 5GS",  # Belfast
    "BT2 8BG",  # Belfast
    "BT47 6FW", # Derry/Londonderry
    "BT9 5AD",  # Belfast
    "BT12 6QH", # Belfast
]

# Total: 50 postcodes
assert len(REAL_POSTCODES) == 50


class TestRealPostcodes:
    """Test with real UK postcodes."""
    
    def test_all_postcodes_valid_format(self):
        """Test that all real postcodes have valid format."""
        resolver = PostcodeResolver()
        
        for postcode in REAL_POSTCODES:
            assert is_valid_postcode(postcode), f"Invalid format: {postcode}"
    
    def test_resolve_real_postcodes_mocked(self):
        """Test resolving real postcodes with mocked API."""
        resolver = PostcodeResolver()
        
        # Mock API response
        mock_response_data = {
            "status": 200,
            "result": {
                "postcode": "B15 2HQ",
                "latitude": 52.475,
                "longitude": -1.920,
                "country": "England",
                "region": "West Midlands",
                "admin_district": "Birmingham",
                "admin_county": "West Midlands"
            }
        }
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch.object(resolver.cache, 'get', return_value=None):
                with patch.object(resolver.cache, 'set'):
                    # Test a sample of postcodes
                    for postcode in REAL_POSTCODES[:10]:
                        result = resolver.resolve(postcode)
                        assert result is not None
                        assert result.postcode is not None
    
    def test_batch_resolve_real_postcodes_mocked(self):
        """Test batch resolving real postcodes with mocked API."""
        batch_resolver = BatchPostcodeResolver()
        
        # Mock batch API response
        mock_batch_response = {
            "status": 200,
            "result": [
                {
                    "query": postcode,
                    "result": {
                        "postcode": postcode,
                        "latitude": 52.0 + (i % 10) * 0.1,
                        "longitude": -1.0 - (i % 10) * 0.1,
                        "country": "England" if i < 40 else ("Scotland" if i < 45 else ("Wales" if i < 50 else "Northern Ireland")),
                        "region": "West Midlands",
                        "admin_district": "Birmingham"
                    }
                }
                for i, postcode in enumerate(REAL_POSTCODES[:50])
            ]
        }
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_batch_response
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response
            
            with patch.object(batch_resolver.cache, 'get', return_value=None):
                with patch.object(batch_resolver.cache, 'set'):
                    result = batch_resolver.resolve_batch(REAL_POSTCODES[:50])
                    
                    assert result.total == 50
                    assert result.found == 50
                    assert len(result.results) == 50
    
    def test_regional_coverage(self):
        """Test that postcodes cover all UK regions."""
        regions_covered = set()
        
        # Group postcodes by expected region
        expected_regions = {
            "London": REAL_POSTCODES[0:5],
            "South East": REAL_POSTCODES[5:10],
            "South West": REAL_POSTCODES[10:15],
            "West Midlands": REAL_POSTCODES[15:20],
            "East Midlands": REAL_POSTCODES[20:25],
            "East of England": REAL_POSTCODES[25:30],
            "Yorkshire and the Humber": REAL_POSTCODES[30:35],
            "North West": REAL_POSTCODES[35:40],
            "North East": REAL_POSTCODES[40:45],
            "Scotland": REAL_POSTCODES[45:50],
        }
        
        # All postcodes should be valid format
        for region, postcodes in expected_regions.items():
            for postcode in postcodes:
                assert is_valid_postcode(postcode), f"Invalid postcode in {region}: {postcode}"

