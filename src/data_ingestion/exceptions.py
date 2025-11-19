"""Custom exceptions for data ingestion module."""


class DataIngestionError(Exception):
    """Base exception for data ingestion errors."""
    pass


class MSIFDownloadError(DataIngestionError):
    """Error downloading MSIF files."""
    pass


class MSIFParseError(DataIngestionError):
    """Error parsing MSIF XLS files."""
    pass


class LottieScrapingError(DataIngestionError):
    """Error scraping Lottie website."""
    pass


class DatabaseError(DataIngestionError):
    """Error with database operations."""
    pass


class TelegramAlertError(DataIngestionError):
    """Error sending Telegram alerts."""
    pass

