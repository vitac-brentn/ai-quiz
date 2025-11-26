"""Card data models."""

from typing import List
from pydantic import BaseModel, Field


class Card(BaseModel):
    """Represents a quiz card with an image and correct answer."""

    id: int
    image_filename: str
    correct_answer: str


class CardWithChoices(BaseModel):
    """Card with multiple choice answers for the quiz."""

    card_index: int = Field(..., description="Current card index (0-based)")
    total_cards: int = Field(..., description="Total number of cards in this game")
    image_url: str = Field(..., description="URL to the card image")
    choices: List[str] = Field(..., description="List of 5 answer choices (alphabetically sorted)")
