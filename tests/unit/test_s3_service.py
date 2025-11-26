"""Unit tests for S3 service."""

import json
import pytest
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import boto3
from moto import mock_aws
from botocore.exceptions import ClientError

from app.services.s3_service import S3Service
from app.models.card import Card


@pytest.fixture
def s3_setup():
    """Fixture to set up mock S3 resources."""
    with mock_aws():
        # Create mock S3 client and bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        # Upload test cards JSON
        cards_data = [
            {"id": 1, "image_filename": "card1.jpg", "correct_answer": "Apple"},
            {"id": 2, "image_filename": "card2.jpg", "correct_answer": "Banana"},
            {"id": 3, "image_filename": "card3.jpg", "correct_answer": "Cherry"},
        ]
        s3_client.put_object(
            Bucket=bucket_name,
            Key="cards.json",
            Body=json.dumps(cards_data).encode("utf-8"),
        )

        # Upload test images
        for card in cards_data:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=card["image_filename"],
                Body=b"fake image data",
            )

        yield {
            "bucket_name": bucket_name,
            "cards_data": cards_data,
        }


def test_fetch_cards_metadata(s3_setup: dict) -> None:
    """Test fetching cards metadata from S3."""
    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    cards = s3_service.fetch_cards_metadata("cards.json")

    assert len(cards) == 3
    assert all(isinstance(card, Card) for card in cards)
    assert cards[0].id == 1
    assert cards[0].image_filename == "card1.jpg"
    assert cards[0].correct_answer == "Apple"


def test_fetch_cards_metadata_missing_file(s3_setup: dict) -> None:
    """Test error when cards.json doesn't exist."""
    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    with pytest.raises(ClientError):
        s3_service.fetch_cards_metadata("nonexistent.json")


def test_fetch_cards_metadata_invalid_json(s3_setup: dict) -> None:
    """Test error when JSON is invalid."""
    # Upload invalid JSON
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.put_object(
        Bucket=s3_setup["bucket_name"],
        Key="invalid.json",
        Body=b"not valid json{",
    )

    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    with pytest.raises(json.JSONDecodeError):
        s3_service.fetch_cards_metadata("invalid.json")


def test_download_image(s3_setup: dict, temp_cache_dir: Path) -> None:
    """Test downloading a single image from S3."""
    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    local_path = temp_cache_dir / "card1.jpg"
    s3_service.download_image("card1.jpg", local_path)

    assert local_path.exists()
    assert local_path.read_bytes() == b"fake image data"


def test_download_image_missing_file(s3_setup: dict, temp_cache_dir: Path) -> None:
    """Test error when downloading non-existent image."""
    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    local_path = temp_cache_dir / "nonexistent.jpg"

    with pytest.raises(ClientError):
        s3_service.download_image("nonexistent.jpg", local_path)


def test_download_all_images(s3_setup: dict, temp_cache_dir: Path) -> None:
    """Test downloading all card images."""
    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    cards = s3_service.fetch_cards_metadata("cards.json")
    s3_service.download_all_images(cards, temp_cache_dir)

    # Verify all images were downloaded
    for card in cards:
        image_path = temp_cache_dir / card.image_filename
        assert image_path.exists()
        assert image_path.read_bytes() == b"fake image data"


def test_download_all_images_partial_failure(
    s3_setup: dict, temp_cache_dir: Path
) -> None:
    """Test error when some images fail to download."""
    s3_service = S3Service(
        bucket_name=s3_setup["bucket_name"],
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )

    # Create cards with one non-existent image
    cards = [
        Card(id=1, image_filename="card1.jpg", correct_answer="Apple"),
        Card(id=99, image_filename="missing.jpg", correct_answer="Missing"),
    ]

    with pytest.raises(RuntimeError, match="Failed to download"):
        s3_service.download_all_images(cards, temp_cache_dir)


def test_s3_service_initialization() -> None:
    """Test S3Service initialization with credentials."""
    s3_service = S3Service(
        bucket_name="test-bucket",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-west-2",
    )

    assert s3_service.bucket_name == "test-bucket"
    assert s3_service.s3_client is not None
