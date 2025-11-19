"""Custom exceptions for funding calculator module."""


class FundingCalculatorError(Exception):
    """Base exception for funding calculator errors."""
    pass


class InvalidPatientProfileError(FundingCalculatorError):
    """Invalid patient profile data."""
    pass


class CalculationError(FundingCalculatorError):
    """Error during funding calculation."""
    pass

