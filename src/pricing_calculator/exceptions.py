"""Custom exceptions for pricing_calculator module."""


class PricingCalculatorError(Exception):
    """Base exception for pricing calculator errors."""
    pass


class FairCostDataError(PricingCalculatorError):
    """Error loading or parsing MSIF fair cost data."""
    pass


class LottieScrapingError(PricingCalculatorError):
    """Error scraping Lottie data."""
    pass


class PostcodeMappingError(PricingCalculatorError):
    """Error mapping postcode to local authority."""
    pass


class BandCalculationError(PricingCalculatorError):
    """Error calculating affordability band."""
    pass


class InvalidCareTypeError(PricingCalculatorError):
    """Invalid care type provided."""
    pass


class InvalidPostcodeError(PricingCalculatorError):
    """Invalid postcode format."""
    pass

