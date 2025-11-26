"""Base extraction service."""
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ExtractionServiceError(Exception):
    """Base exception for extraction services."""
    pass


class BaseExtractionService(ABC):
    """Abstract base class for extraction services."""

    def __init__(self, config: Dict[str, Any], timeout_seconds: int = 300):
        """Initialize service with configuration.

        Args:
            config: Configuration dictionary
            timeout_seconds: Maximum processing time
        """
        self.config = config
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def process(self, file_path: str) -> Dict[str, Any]:
        """Process file and extract data.

        Args:
            file_path: Path to file to process

        Returns:
            Dictionary with extracted data

        Raises:
            ExtractionServiceError: If processing fails
        """
        pass

    def _measure_time(self, func, *args, **kwargs) -> tuple[Any, int]:
        """Measure function execution time in milliseconds.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (result, time_ms)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = int((time.time() - start_time) * 1000)
        return result, elapsed_ms

    def _validate_file(self, file_path: str, max_size_mb: int = 50) -> bool:
        """Validate file before processing.

        Args:
            file_path: Path to file
            max_size_mb: Maximum file size in MB

        Returns:
            True if valid

        Raises:
            ExtractionServiceError: If validation fails
        """
        import os

        if not os.path.exists(file_path):
            raise ExtractionServiceError(f"File not found: {file_path}")

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ExtractionServiceError(
                f"File too large: {file_size_mb:.1f}MB (max {max_size_mb}MB)"
            )

        return True
