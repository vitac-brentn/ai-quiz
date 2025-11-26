"""Unit tests for game service."""

import pytest
from typing import List

from app.services.game_service import GameService
from app.models.card import Card
from app.models.game import GameSession


@pytest.fixture
def game_service() -> GameService:
    """Fixture providing a GameService instance."""
    return GameService()


def test_create_game_session(game_service: GameService, sample_cards: List[Card]) -> None:
    """Test creating a new game session."""
    session = game_service.create_game_session(5, sample_cards)

    assert session.total_cards == 5
    assert len(session.cards) == 5
    assert session.current_index == 0
    assert session.score == 0
    assert all(card_id in [card.id for card in sample_cards] for card_id in session.cards)


def test_create_game_session_minimum_cards(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test creating game with minimum 5 cards."""
    session = game_service.create_game_session(5, sample_cards)
    assert session.total_cards == 5


def test_create_game_session_maximum_cards(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test creating game with maximum allowed cards (half of total)."""
    max_cards = len(sample_cards) // 2
    session = game_service.create_game_session(max_cards, sample_cards)
    assert session.total_cards == max_cards


def test_create_game_session_too_few_cards(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when requesting too few cards."""
    with pytest.raises(ValueError, match="at least 5"):
        game_service.create_game_session(3, sample_cards)


def test_create_game_session_too_many_cards(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when requesting too many cards."""
    max_cards = len(sample_cards) // 2
    with pytest.raises(ValueError, match="must not exceed"):
        game_service.create_game_session(max_cards + 1, sample_cards)


def test_get_current_card_with_choices(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test getting current card with answer choices."""
    session = game_service.create_game_session(5, sample_cards)
    card_with_choices = game_service.get_current_card_with_choices(session, sample_cards)

    assert card_with_choices.card_index == 0
    assert card_with_choices.total_cards == 5
    assert len(card_with_choices.choices) == 5
    assert card_with_choices.image_url.startswith("/images/")

    # Find the correct answer for the current card
    current_card = next(card for card in sample_cards if card.id == session.cards[0])
    assert current_card.correct_answer in card_with_choices.choices


def test_choices_are_sorted_alphabetically(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test that answer choices are sorted alphabetically."""
    session = game_service.create_game_session(5, sample_cards)
    card_with_choices = game_service.get_current_card_with_choices(session, sample_cards)

    sorted_choices = sorted(card_with_choices.choices)
    assert card_with_choices.choices == sorted_choices


def test_choices_include_correct_answer(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test that choices always include the correct answer."""
    session = game_service.create_game_session(5, sample_cards)

    for _ in range(session.total_cards):
        current_card = next(card for card in sample_cards if card.id == session.cards[session.current_index])
        card_with_choices = game_service.get_current_card_with_choices(session, sample_cards)

        assert current_card.correct_answer in card_with_choices.choices
        session.current_index += 1


def test_get_current_card_game_complete(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when trying to get card after game is complete."""
    session = game_service.create_game_session(5, sample_cards)
    session.current_index = 5  # Set to end of game

    with pytest.raises(ValueError, match="already complete"):
        game_service.get_current_card_with_choices(session, sample_cards)


def test_submit_answer_correct(game_service: GameService, sample_cards: List[Card]) -> None:
    """Test submitting a correct answer."""
    session = game_service.create_game_session(5, sample_cards)
    current_card = next(card for card in sample_cards if card.id == session.cards[0])

    is_correct, correct_answer = game_service.submit_answer(
        session, current_card.correct_answer, sample_cards
    )

    assert is_correct is True
    assert correct_answer == current_card.correct_answer
    assert session.score == 1
    assert session.current_index == 1


def test_submit_answer_incorrect(game_service: GameService, sample_cards: List[Card]) -> None:
    """Test submitting an incorrect answer."""
    session = game_service.create_game_session(5, sample_cards)
    current_card = next(card for card in sample_cards if card.id == session.cards[0])

    is_correct, correct_answer = game_service.submit_answer(
        session, "Wrong Answer", sample_cards
    )

    assert is_correct is False
    assert correct_answer == current_card.correct_answer
    assert session.score == 0
    assert session.current_index == 1


def test_submit_answer_whitespace_handling(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test that whitespace in answers is handled correctly."""
    session = game_service.create_game_session(5, sample_cards)
    current_card = next(card for card in sample_cards if card.id == session.cards[0])

    # Answer with extra whitespace should be considered correct
    is_correct, _ = game_service.submit_answer(
        session, f"  {current_card.correct_answer}  ", sample_cards
    )

    assert is_correct is True


def test_submit_answer_game_complete(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when submitting answer after game is complete."""
    session = game_service.create_game_session(5, sample_cards)
    session.current_index = 5  # Set to end of game

    with pytest.raises(ValueError, match="already complete"):
        game_service.submit_answer(session, "Answer", sample_cards)


def test_is_game_complete(game_service: GameService, sample_cards: List[Card]) -> None:
    """Test game completion detection."""
    session = game_service.create_game_session(5, sample_cards)

    assert game_service.is_game_complete(session) is False

    # Answer all cards
    for _ in range(5):
        game_service.submit_answer(session, "Any Answer", sample_cards)

    assert game_service.is_game_complete(session) is True


def test_get_game_results(game_service: GameService, sample_cards: List[Card]) -> None:
    """Test getting game results."""
    session = game_service.create_game_session(5, sample_cards)

    # Answer 3 correctly, 2 incorrectly
    for i in range(5):
        current_card = next(card for card in sample_cards if card.id == session.cards[i])
        if i < 3:
            game_service.submit_answer(session, current_card.correct_answer, sample_cards)
        else:
            game_service.submit_answer(session, "Wrong Answer", sample_cards)

    score, total, percentage = game_service.get_game_results(session)

    assert score == 3
    assert total == 5
    assert percentage == 60.0


def test_get_game_results_perfect_score(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test game results with perfect score."""
    session = game_service.create_game_session(5, sample_cards)

    # Answer all correctly
    for i in range(5):
        current_card = next(card for card in sample_cards if card.id == session.cards[i])
        game_service.submit_answer(session, current_card.correct_answer, sample_cards)

    score, total, percentage = game_service.get_game_results(session)

    assert score == 5
    assert total == 5
    assert percentage == 100.0


def test_get_game_results_zero_score(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test game results with zero score."""
    session = game_service.create_game_session(5, sample_cards)

    # Answer all incorrectly
    for _ in range(5):
        game_service.submit_answer(session, "Wrong Answer", sample_cards)

    score, total, percentage = game_service.get_game_results(session)

    assert score == 0
    assert total == 5
    assert percentage == 0.0


def test_get_game_results_game_not_complete(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when getting results before game is complete."""
    session = game_service.create_game_session(5, sample_cards)

    with pytest.raises(ValueError, match="not complete"):
        game_service.get_game_results(session)


def test_get_current_card_card_not_found(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when card ID in session doesn't exist in cards list."""
    session = game_service.create_game_session(5, sample_cards)
    # Modify session to have an invalid card ID
    session.cards[0] = 99999  # Non-existent ID

    with pytest.raises(ValueError, match="not found"):
        game_service.get_current_card_with_choices(session, sample_cards)


def test_submit_answer_card_not_found(
    game_service: GameService, sample_cards: List[Card]
) -> None:
    """Test error when card ID in session doesn't exist when submitting answer."""
    session = game_service.create_game_session(5, sample_cards)
    # Modify session to have an invalid card ID
    session.cards[0] = 99999  # Non-existent ID

    with pytest.raises(ValueError, match="not found"):
        game_service.submit_answer(session, "Some Answer", sample_cards)
