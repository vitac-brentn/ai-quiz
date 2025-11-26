"""Pytest fixtures for quiz game tests."""

import pytest
from typing import List, Generator
from pathlib import Path
import tempfile
import shutil

from app.models.card import Card


@pytest.fixture
def sample_cards() -> List[Card]:
    """Fixture providing sample cards for testing."""
    return [
        Card(id=1, image_filename="card1.jpg", correct_answer="Apple"),
        Card(id=2, image_filename="card2.jpg", correct_answer="Banana"),
        Card(id=3, image_filename="card3.jpg", correct_answer="Cherry"),
        Card(id=4, image_filename="card4.jpg", correct_answer="Date"),
        Card(id=5, image_filename="card5.jpg", correct_answer="Elderberry"),
        Card(id=6, image_filename="card6.jpg", correct_answer="Fig"),
        Card(id=7, image_filename="card7.jpg", correct_answer="Grape"),
        Card(id=8, image_filename="card8.jpg", correct_answer="Honeydew"),
        Card(id=9, image_filename="card9.jpg", correct_answer="Kiwi"),
        Card(id=10, image_filename="card10.jpg", correct_answer="Lemon"),
    ]


@pytest.fixture
def temp_cache_dir() -> Generator[Path, None, None]:
    """Fixture providing a temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture to set mock environment variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_access_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret_key")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("S3_CARDS_JSON_KEY", "cards.json")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-key-minimum-32-characters-long")
    monkeypatch.setenv("CACHE_DIR", "/tmp/test-cache")
    monkeypatch.setenv("ENVIRONMENT", "test")
