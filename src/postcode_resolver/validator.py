"""UK postcode validation."""

import re
from typing import Optional
from .exceptions import InvalidPostcodeError


# UK postcode regex patterns
# Format: AA9A 9AA or A9A 9AA or A9 9AA or A99 9AA or AA9 9AA or AA99 9AA
UK_POSTCODE_PATTERN = re.compile(
    r'^([A-Z]{1,2}[0-9][A-Z0-9]?)\s*([0-9][A-Z]{2})$',
    re.IGNORECASE
)

# Special cases (Girobank, BFPO, etc.)
SPECIAL_POSTCODES = {
    'GIR', '0AA',  # Girobank
    'BF1', 'BF2', 'BF3', 'BF4', 'BF5', 'BF6', 'BF7', 'BF8', 'BF9',  # BFPO
    'BX1', 'BX2', 'BX3', 'BX4', 'BX5',  # PO Box
}


def normalize_postcode(postcode: str) -> str:
    """
    Normalize UK postcode format.
    
    Args:
        postcode: Raw postcode string
        
    Returns:
        Normalized postcode (uppercase, single space)
        
    Raises:
        InvalidPostcodeError: If postcode format is invalid
    """
    if not postcode:
        raise InvalidPostcodeError("Postcode cannot be empty")
    
    # Remove whitespace and convert to uppercase
    normalized = re.sub(r'\s+', '', postcode.upper())
    
    # Insert space before last 3 characters (outward + inward)
    if len(normalized) >= 5:
        normalized = normalized[:-3] + ' ' + normalized[-3:]
    
    return normalized


def validate_postcode(postcode: str) -> bool:
    """
    Validate UK postcode format.
    
    Args:
        postcode: Postcode string to validate
        
    Returns:
        True if valid format
        
    Raises:
        InvalidPostcodeError: If postcode format is invalid
    """
    if not postcode:
        raise InvalidPostcodeError("Postcode cannot be empty")
    
    # Normalize
    normalized = normalize_postcode(postcode)
    
    # Check against pattern
    match = UK_POSTCODE_PATTERN.match(normalized)
    if not match:
        raise InvalidPostcodeError(f"Invalid UK postcode format: {postcode}")
    
    # Extract outward and inward codes
    outward = match.group(1)
    inward = match.group(2)
    
    # Validate outward code (first part)
    # Cannot start with Q, V, X
    if outward[0] in 'QVX':
        raise InvalidPostcodeError(f"Postcode cannot start with Q, V, or X: {postcode}")
    
    # Second character cannot be I, J, or Z (except for some special cases)
    if len(outward) > 1 and outward[1] in 'IJZ' and outward not in SPECIAL_POSTCODES:
        # Allow some exceptions
        if outward[:2] not in ['AI', 'BJ', 'CZ']:
            raise InvalidPostcodeError(f"Invalid outward code format: {postcode}")
    
    # Validate inward code (second part)
    # First character cannot be C, I, K, M, O, V
    if inward[0] in 'CIKMOV':
        raise InvalidPostcodeError(f"Inward code cannot start with C, I, K, M, O, or V: {postcode}")
    
    return True


def is_valid_postcode(postcode: str) -> bool:
    """
    Check if postcode is valid format (without raising exception).
    
    Args:
        postcode: Postcode string to check
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        validate_postcode(postcode)
        return True
    except InvalidPostcodeError:
        return False

