"""Custom exceptions for postcode resolver module."""


class PostcodeResolverError(Exception):
    """Base exception for postcode resolver errors."""
    pass


class InvalidPostcodeError(PostcodeResolverError):
    """Invalid UK postcode format."""
    pass


class PostcodeNotFoundError(PostcodeResolverError):
    """Postcode not found in postcodes.io API."""
    pass


class APIError(PostcodeResolverError):
    """Error calling postcodes.io API."""
    pass


class CacheError(PostcodeResolverError):
    """Error with cache operations."""
    pass

