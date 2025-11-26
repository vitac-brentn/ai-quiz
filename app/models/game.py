"""Game session data models."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class GameSession(BaseModel):
    """Represents the state of a game session."""

    cards: List[int] = Field(..., description="List of card IDs selected for this game")
    current_index: int = Field(default=0, description="Current card index (0-based)")
    score: int = Field(default=0, description="Number of correct answers")
    total_cards: int = Field(..., description="Total number of cards in this game")


class StartGameRequest(BaseModel):
    """Request to start a new game."""

    num_cards: int = Field(..., ge=5, description="Number of cards to play (minimum 5)")

    @field_validator("num_cards")
    @classmethod
    def validate_num_cards(cls, v: int) -> int:
        """Validate number of cards is at least 5."""
        if v < 5:
            raise ValueError("Number of cards must be at least 5")
        return v


class StartGameResponse(BaseModel):
    """Response after starting a new game."""

    message: str = "Game started"
    total_cards: int


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer for the current card."""

    answer: str = Field(..., min_length=1, description="The selected answer")


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""

    correct: bool = Field(..., description="Whether the answer was correct")
    correct_answer: str = Field(..., description="The correct answer for the card")
    is_complete: bool = Field(..., description="Whether the game is complete")


class GameResultsResponse(BaseModel):
    """Response containing final game results."""

    score: int = Field(..., description="Number of correct answers")
    total: int = Field(..., description="Total number of cards")
    percentage: float = Field(..., description="Percentage score (0-100)")
