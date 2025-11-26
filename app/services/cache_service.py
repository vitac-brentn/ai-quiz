"""Cache service for managing local image cache."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing local file cache."""

    def __init__(self, cache_dir: str) -> None:
        """Initialize cache service with cache directory path."""
        self.cache_dir = Path(cache_dir)

    def initialize_cache(self) -> None:
        """
        Create cache directory if it doesn't exist.

        Raises:
            OSError: If directory creation fails
        """
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache directory initialized at {self.cache_dir}")
        except OSError as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise

    def cache_exists(self, filename: str) -> bool:
        """
        Check if a file exists in the cache.

        Args:
            filename: Name of the file to check

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.cache_dir / filename
        return file_path.exists() and file_path.is_file()

    def get_cache_path(self, filename: str) -> Path:
        """
        Get the full path for a cached file.

        Args:
            filename: Name of the file

        Returns:
            Path object for the cached file
        """
        return self.cache_dir / filename

    def get_cache_dir(self) -> Path:
        """
        Get the cache directory path.

        Returns:
            Path object for the cache directory
        """
        return self.cache_dir
