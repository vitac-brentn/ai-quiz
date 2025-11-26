"""Unit tests for cache service."""

import pytest
from pathlib import Path

from app.services.cache_service import CacheService


def test_initialize_cache(temp_cache_dir: Path) -> None:
    """Test cache directory initialization."""
    cache_service = CacheService(str(temp_cache_dir / "new_cache"))
    cache_service.initialize_cache()

    assert cache_service.get_cache_dir().exists()
    assert cache_service.get_cache_dir().is_dir()


def test_initialize_cache_already_exists(temp_cache_dir: Path) -> None:
    """Test cache directory initialization when directory already exists."""
    cache_service = CacheService(str(temp_cache_dir))
    cache_service.initialize_cache()

    # Should not raise error even if directory exists
    assert cache_service.get_cache_dir().exists()


def test_cache_exists_file_present(temp_cache_dir: Path) -> None:
    """Test cache_exists returns True when file exists."""
    cache_service = CacheService(str(temp_cache_dir))

    # Create a test file
    test_file = temp_cache_dir / "test.jpg"
    test_file.write_text("test content")

    assert cache_service.cache_exists("test.jpg") is True


def test_cache_exists_file_not_present(temp_cache_dir: Path) -> None:
    """Test cache_exists returns False when file doesn't exist."""
    cache_service = CacheService(str(temp_cache_dir))

    assert cache_service.cache_exists("nonexistent.jpg") is False


def test_cache_exists_directory_not_file(temp_cache_dir: Path) -> None:
    """Test cache_exists returns False for directories."""
    cache_service = CacheService(str(temp_cache_dir))

    # Create a subdirectory
    subdir = temp_cache_dir / "subdir"
    subdir.mkdir()

    assert cache_service.cache_exists("subdir") is False


def test_get_cache_path(temp_cache_dir: Path) -> None:
    """Test get_cache_path returns correct path."""
    cache_service = CacheService(str(temp_cache_dir))

    path = cache_service.get_cache_path("test.jpg")

    assert path == temp_cache_dir / "test.jpg"
    assert isinstance(path, Path)


def test_get_cache_dir(temp_cache_dir: Path) -> None:
    """Test get_cache_dir returns correct directory."""
    cache_service = CacheService(str(temp_cache_dir))

    cache_dir = cache_service.get_cache_dir()

    assert cache_dir == temp_cache_dir
    assert isinstance(cache_dir, Path)


def test_initialize_cache_oserror(temp_cache_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test initialize_cache raises OSError when directory creation fails."""
    cache_service = CacheService(str(temp_cache_dir / "invalid"))

    # Mock Path.mkdir to raise OSError
    def mock_mkdir(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "mkdir", mock_mkdir)

    with pytest.raises(OSError, match="Permission denied"):
        cache_service.initialize_cache()
