"""Game logic service for quiz game."""

from __future__ import annotations

import random
import logging
from typing import List, Tuple

from app.models.card import Card, CardWithChoices
from app.models.game import GameSession

logger = logging.getLogger(__name__)


class GameService:
    """Service for managing game logic."""

    def create_game_session(self, num_cards: int, all_cards: List[Card]) -> GameSession:
        """
        Create a new game session with randomly selected cards.

        Args:
            num_cards: Number of cards to include in the game
            all_cards: List of all available cards

        Returns:
            New GameSession instance

        Raises:
            ValueError: If num_cards is invalid
        """
        max_cards = len(all_cards) // 2
        if num_cards < 5:
            raise ValueError("Number of cards must be at least 5")
        if num_cards > max_cards:
            raise ValueError(f"Number of cards must not exceed {max_cards} (half of available cards)")

        # Randomly select cards for this game
        selected_cards = random.sample(all_cards, num_cards)
        card_ids = [card.id for card in selected_cards]

        logger.info(f"Created game session with {num_cards} cards")
        return GameSession(cards=card_ids, current_index=0, score=0, total_cards=num_cards)

    def get_current_card_with_choices(
        self, session: GameSession, all_cards: List[Card]
    ) -> CardWithChoices:
        """
        Get the current card with 5 answer choices (alphabetically sorted).

        Args:
            session: Current game session
            all_cards: List of all available cards

        Returns:
            CardWithChoices with current card and answer options

        Raises:
            ValueError: If current card not found or session invalid
        """
        if session.current_index >= session.total_cards:
            raise ValueError("Game is already complete")

        # Get the current card
        current_card_id = session.cards[session.current_index]
        current_card = next((card for card in all_cards if card.id == current_card_id), None)

        if current_card is None:
            raise ValueError(f"Card with ID {current_card_id} not found")

        # Generate 5 answer choices: correct answer + 4 random incorrect answers
        all_answers = [card.correct_answer for card in all_cards]
        incorrect_answers = [ans for ans in all_answers if ans != current_card.correct_answer]

        # Randomly select 4 incorrect answers
        num_incorrect = min(4, len(incorrect_answers))
        selected_incorrect = random.sample(incorrect_answers, num_incorrect)

        # Combine correct and incorrect answers, then sort alphabetically
        choices = [current_card.correct_answer] + selected_incorrect
        choices.sort()

        # Generate image URL (relative path for static files)
        image_url = f"/images/{current_card.image_filename}"

        logger.debug(f"Generated choices for card {current_card_id}: {choices}")

        return CardWithChoices(
            card_index=session.current_index,
            total_cards=session.total_cards,
            image_url=image_url,
            choices=choices,
        )

    def submit_answer(
        self, session: GameSession, answer: str, all_cards: List[Card]
    ) -> tuple[bool, str]:
        """
        Validate answer and update game session.

        Args:
            session: Current game session
            answer: Player's submitted answer
            all_cards: List of all available cards

        Returns:
            Tuple of (is_correct, correct_answer)

        Raises:
            ValueError: If session is invalid or game is complete
        """
        if session.current_index >= session.total_cards:
            raise ValueError("Game is already complete")

        # Get the current card
        current_card_id = session.cards[session.current_index]
        current_card = next((card for card in all_cards if card.id == current_card_id), None)

        if current_card is None:
            raise ValueError(f"Card with ID {current_card_id} not found")

        # Check if answer is correct
        is_correct = answer.strip() == current_card.correct_answer.strip()

        if is_correct:
            session.score += 1
            logger.info(f"Correct answer for card {current_card_id}")
        else:
            logger.info(f"Incorrect answer for card {current_card_id}")

        # Move to next card
        session.current_index += 1

        return is_correct, current_card.correct_answer

    def is_game_complete(self, session: GameSession) -> bool:
        """
        Check if all cards have been answered.

        Args:
            session: Current game session

        Returns:
            True if game is complete, False otherwise
        """
        return session.current_index >= session.total_cards

    def get_game_results(self, session: GameSession) -> tuple[int, int, float]:
        """
        Calculate final game results.

        Args:
            session: Completed game session

        Returns:
            Tuple of (score, total, percentage)

        Raises:
            ValueError: If game is not complete
        """
        if not self.is_game_complete(session):
            raise ValueError("Game is not complete yet")

        percentage = (session.score / session.total_cards) * 100 if session.total_cards > 0 else 0.0

        logger.info(
            f"Game results: {session.score}/{session.total_cards} ({percentage:.1f}%)"
        )

        return session.score, session.total_cards, percentage
