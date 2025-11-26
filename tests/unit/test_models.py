"""Unit tests for data models."""

import pytest
from pydantic import ValidationError

from app.models.card import Card, CardWithChoices
from app.models.game import (
    GameSession,
    StartGameRequest,
    StartGameResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    GameResultsResponse,
)


# Card model tests
def test_card_creation() -> None:
    """Test creating a Card instance."""
    card = Card(id=1, image_filename="test.jpg", correct_answer="Test Answer")

    assert card.id == 1
    assert card.image_filename == "test.jpg"
    assert card.correct_answer == "Test Answer"


def test_card_from_dict() -> None:
    """Test creating Card from dictionary."""
    card_data = {"id": 5, "image_filename": "card5.jpg", "correct_answer": "Banana"}
    card = Card(**card_data)

    assert card.id == 5
    assert card.image_filename == "card5.jpg"
    assert card.correct_answer == "Banana"


def test_card_missing_fields() -> None:
    """Test Card raises error when fields are missing."""
    with pytest.raises(ValidationError):
        Card(id=1, image_filename="test.jpg")  # Missing correct_answer


# CardWithChoices model tests
def test_card_with_choices_creation() -> None:
    """Test creating CardWithChoices instance."""
    card = CardWithChoices(
        card_index=0,
        total_cards=10,
        image_url="/images/card1.jpg",
        choices=["Apple", "Banana", "Cherry", "Date", "Elderberry"],
    )

    assert card.card_index == 0
    assert card.total_cards == 10
    assert card.image_url == "/images/card1.jpg"
    assert len(card.choices) == 5


def test_card_with_choices_fields() -> None:
    """Test CardWithChoices field descriptions."""
    card = CardWithChoices(
        card_index=2,
        total_cards=5,
        image_url="/images/test.jpg",
        choices=["A", "B", "C", "D", "E"],
    )

    assert card.card_index == 2
    assert card.total_cards == 5


# GameSession model tests
def test_game_session_creation() -> None:
    """Test creating GameSession instance."""
    session = GameSession(cards=[1, 2, 3, 4, 5], total_cards=5)

    assert session.cards == [1, 2, 3, 4, 5]
    assert session.current_index == 0
    assert session.score == 0
    assert session.total_cards == 5


def test_game_session_with_progress() -> None:
    """Test GameSession with some progress."""
    session = GameSession(
        cards=[1, 2, 3], current_index=2, score=1, total_cards=3
    )

    assert session.current_index == 2
    assert session.score == 1


def test_game_session_model_dump() -> None:
    """Test GameSession can be converted to dict."""
    session = GameSession(cards=[1, 2, 3], total_cards=3)
    data = session.model_dump()

    assert isinstance(data, dict)
    assert data["cards"] == [1, 2, 3]
    assert data["total_cards"] == 3


# StartGameRequest model tests
def test_start_game_request_valid() -> None:
    """Test valid StartGameRequest."""
    request = StartGameRequest(num_cards=5)

    assert request.num_cards == 5


def test_start_game_request_minimum() -> None:
    """Test StartGameRequest with minimum cards."""
    request = StartGameRequest(num_cards=5)

    assert request.num_cards == 5


def test_start_game_request_too_few() -> None:
    """Test StartGameRequest rejects too few cards."""
    with pytest.raises(ValidationError):
        StartGameRequest(num_cards=3)


def test_start_game_request_zero() -> None:
    """Test StartGameRequest rejects zero cards."""
    with pytest.raises(ValidationError):
        StartGameRequest(num_cards=0)


def test_start_game_request_negative() -> None:
    """Test StartGameRequest rejects negative cards."""
    with pytest.raises(ValidationError):
        StartGameRequest(num_cards=-5)


# StartGameResponse model tests
def test_start_game_response() -> None:
    """Test StartGameResponse creation."""
    response = StartGameResponse(total_cards=10)

    assert response.message == "Game started"
    assert response.total_cards == 10


def test_start_game_response_custom_message() -> None:
    """Test StartGameResponse with custom message."""
    response = StartGameResponse(message="Custom message", total_cards=5)

    assert response.message == "Custom message"
    assert response.total_cards == 5


# SubmitAnswerRequest model tests
def test_submit_answer_request() -> None:
    """Test SubmitAnswerRequest creation."""
    request = SubmitAnswerRequest(answer="Apple")

    assert request.answer == "Apple"


def test_submit_answer_request_empty() -> None:
    """Test SubmitAnswerRequest rejects empty answer."""
    with pytest.raises(ValidationError):
        SubmitAnswerRequest(answer="")


def test_submit_answer_request_whitespace_only() -> None:
    """Test SubmitAnswerRequest with whitespace."""
    request = SubmitAnswerRequest(answer="  ")

    # Whitespace is allowed (will be stripped in service)
    assert request.answer == "  "


# SubmitAnswerResponse model tests
def test_submit_answer_response_correct() -> None:
    """Test SubmitAnswerResponse for correct answer."""
    response = SubmitAnswerResponse(
        correct=True, correct_answer="Apple", is_complete=False
    )

    assert response.correct is True
    assert response.correct_answer == "Apple"
    assert response.is_complete is False


def test_submit_answer_response_incorrect() -> None:
    """Test SubmitAnswerResponse for incorrect answer."""
    response = SubmitAnswerResponse(
        correct=False, correct_answer="Banana", is_complete=True
    )

    assert response.correct is False
    assert response.correct_answer == "Banana"
    assert response.is_complete is True


# GameResultsResponse model tests
def test_game_results_response() -> None:
    """Test GameResultsResponse creation."""
    response = GameResultsResponse(score=8, total=10, percentage=80.0)

    assert response.score == 8
    assert response.total == 10
    assert response.percentage == 80.0


def test_game_results_response_perfect() -> None:
    """Test GameResultsResponse with perfect score."""
    response = GameResultsResponse(score=10, total=10, percentage=100.0)

    assert response.score == 10
    assert response.total == 10
    assert response.percentage == 100.0


def test_game_results_response_zero() -> None:
    """Test GameResultsResponse with zero score."""
    response = GameResultsResponse(score=0, total=5, percentage=0.0)

    assert response.score == 0
    assert response.total == 5
    assert response.percentage == 0.0


def test_game_results_response_fractional_percentage() -> None:
    """Test GameResultsResponse with fractional percentage."""
    response = GameResultsResponse(score=3, total=7, percentage=42.857)

    assert response.score == 3
    assert response.total == 7
    assert pytest.approx(response.percentage, 0.001) == 42.857
