"""S3 service for fetching cards and images from AWS S3."""

import json
import logging
from typing import List, Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.models.card import Card

logger = logging.getLogger(__name__)


class S3Service:
    """Service for interacting with AWS S3."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
    ) -> None:
        """Initialize S3 service with credentials."""
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

    def fetch_cards_metadata(self, cards_json_key: str) -> List[Card]:
        """
        Download and parse cards.json from S3.

        Args:
            cards_json_key: S3 key for the cards JSON file

        Returns:
            List of Card objects

        Raises:
            ClientError: If S3 operation fails
            json.JSONDecodeError: If JSON parsing fails
        """
        try:
            logger.info(f"Fetching cards metadata from s3://{self.bucket_name}/{cards_json_key}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=cards_json_key)
            content = response["Body"].read().decode("utf-8")
            cards_data = json.loads(content)

            cards = [Card(**card_dict) for card_dict in cards_data]
            logger.info(f"Successfully loaded {len(cards)} cards")
            return cards

        except ClientError as e:
            logger.error(f"Failed to fetch cards metadata: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cards JSON: {e}")
            raise

    def download_image(self, image_key: str, local_path: Path) -> None:
        """
        Download a single image from S3 to local path.

        Args:
            image_key: S3 key for the image file
            local_path: Local file path to save the image

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            logger.debug(f"Downloading {image_key} to {local_path}")
            self.s3_client.download_file(self.bucket_name, image_key, str(local_path))
        except ClientError as e:
            logger.error(f"Failed to download image {image_key}: {e}")
            raise

    def download_all_images(self, cards: List[Card], cache_dir: Path) -> None:
        """
        Download all card images to cache directory.

        Args:
            cards: List of Card objects
            cache_dir: Directory to save images

        Raises:
            ClientError: If any S3 operation fails
        """
        logger.info(f"Downloading {len(cards)} images to {cache_dir}")
        failed_downloads: List[str] = []

        for card in cards:
            local_path = cache_dir / card.image_filename
            try:
                self.download_image(card.image_filename, local_path)
            except ClientError as e:
                logger.error(f"Failed to download {card.image_filename}: {e}")
                failed_downloads.append(card.image_filename)

        if failed_downloads:
            error_msg = f"Failed to download {len(failed_downloads)} images: {failed_downloads}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info("All images downloaded successfully")
