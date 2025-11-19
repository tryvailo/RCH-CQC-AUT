"""Custom exceptions for pricing core module."""


class PricingCoreError(Exception):
    """Base exception for pricing core errors."""
    pass


class DataNotFoundError(PricingCoreError):
    """Required pricing data not found."""
    pass


class InvalidInputError(PricingCoreError):
    """Invalid input parameters."""
    pass


class CalculationError(PricingCoreError):
    """Error during price calculation."""
    pass

