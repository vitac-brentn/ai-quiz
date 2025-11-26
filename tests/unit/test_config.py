"""Unit tests for configuration module."""

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_settings_with_valid_env_vars(mock_env_vars: None) -> None:
    """Test Settings with valid environment variables."""
    settings = Settings()

    assert settings.aws_access_key_id == "test_access_key"
    assert settings.aws_secret_access_key == "test_secret_key"
    assert settings.aws_region == "us-east-1"
    assert settings.s3_bucket_name == "test-bucket"
    assert settings.s3_cards_json_key == "cards.json"
    assert settings.session_secret_key == "test-secret-key-minimum-32-characters-long"
    assert settings.cache_dir == "/tmp/test-cache"
    assert settings.environment == "test"


def test_settings_default_values(mock_env_vars: None) -> None:
    """Test Settings uses default values when not provided."""
    settings = Settings()

    # These should use defaults
    assert settings.aws_region == "us-east-1"
    assert settings.s3_cards_json_key == "cards.json"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_settings_custom_host_port(mock_env_vars: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Settings with custom host and port."""
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")

    settings = Settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000


def test_settings_missing_required_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Settings raises error when required field is missing."""
    # Only set some required fields, leave others missing
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_key")
    # Don't set AWS_SECRET_ACCESS_KEY

    with pytest.raises(ValidationError):
        Settings()


def test_get_settings(mock_env_vars: None) -> None:
    """Test get_settings returns Settings instance."""
    settings = get_settings()

    assert isinstance(settings, Settings)
    assert settings.aws_access_key_id == "test_access_key"


def test_settings_with_production_environment(mock_env_vars: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Settings with production environment."""
    monkeypatch.setenv("ENVIRONMENT", "production")

    settings = Settings()

    assert settings.environment == "production"


def test_settings_with_custom_cache_dir(mock_env_vars: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Settings with custom cache directory."""
    monkeypatch.setenv("CACHE_DIR", "/custom/cache/path")

    settings = Settings()

    assert settings.cache_dir == "/custom/cache/path"


def test_settings_with_different_aws_region(mock_env_vars: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Settings with different AWS region."""
    monkeypatch.setenv("AWS_REGION", "eu-west-1")

    settings = Settings()

    assert settings.aws_region == "eu-west-1"


def test_settings_with_custom_s3_key(mock_env_vars: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Settings with custom S3 cards JSON key."""
    monkeypatch.setenv("S3_CARDS_JSON_KEY", "data/quiz-cards.json")

    settings = Settings()

    assert settings.s3_cards_json_key == "data/quiz-cards.json"
