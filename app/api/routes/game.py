"""Game API endpoints."""

from __future__ import annotations

import logging
from typing import Dict
from fastapi import APIRouter, Request, HTTPException, status

from app.models.game import (
    StartGameRequest,
    StartGameResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    GameResultsResponse,
    GameSession,
)
from app.models.card import CardWithChoices
from app.services.game_service import GameService

router = APIRouter(prefix="/api", tags=["game"])
logger = logging.getLogger(__name__)

game_service = GameService()


@router.get("/cards/total")
def get_total_cards(request: Request) -> Dict[str, int]:
    """
    Get the total number of available cards.

    Returns:
        Dictionary with total card count
    """
    if not hasattr(request.app.state, "cards"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cards not loaded yet",
        )

    total = len(request.app.state.cards)
    return {"total": total}


@router.post("/game/start", response_model=StartGameResponse)
def start_game(
    game_request: StartGameRequest,
    request: Request,
) -> StartGameResponse:
    """
    Start a new quiz game.

    Creates a new game session with the specified number of cards.
    The session is stored in a signed cookie.

    Args:
        game_request: Request containing number of cards to play
        request: FastAPI request object

    Returns:
        Response confirming game started with total cards

    Raises:
        HTTPException: If cards not loaded or num_cards is invalid
    """
    if not hasattr(request.app.state, "cards"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cards not loaded yet",
        )

    all_cards = request.app.state.cards
    max_cards = len(all_cards) // 2

    if game_request.num_cards > max_cards:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Number of cards must not exceed {max_cards} (half of total available)",
        )

    try:
        session = game_service.create_game_session(game_request.num_cards, all_cards)
        # Store session in request.session (managed by SessionMiddleware)
        request.session["game"] = session.model_dump()

        logger.info(f"Started new game with {game_request.num_cards} cards")
        return StartGameResponse(total_cards=game_request.num_cards)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get("/game/current", response_model=CardWithChoices)
def get_current_card(request: Request) -> CardWithChoices:
    """
    Get the current card with answer choices.

    Returns the current card image URL and 5 alphabetically sorted answer choices.

    Args:
        request: FastAPI request object

    Returns:
        Current card with choices

    Raises:
        HTTPException: If no active game or cards not loaded
    """
    if "game" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active game. Please start a new game.",
        )

    if not hasattr(request.app.state, "cards"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cards not loaded yet",
        )

    session_data = request.session["game"]
    session = GameSession(**session_data)
    all_cards = request.app.state.cards

    try:
        card_with_choices = game_service.get_current_card_with_choices(session, all_cards)
        return card_with_choices

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/game/answer", response_model=SubmitAnswerResponse)
def submit_answer(
    answer_request: SubmitAnswerRequest,
    request: Request,
) -> SubmitAnswerResponse:
    """
    Submit an answer for the current card.

    Validates the answer, updates the score, and advances to the next card.

    Args:
        answer_request: Request containing the submitted answer
        request: FastAPI request object

    Returns:
        Response indicating if answer was correct and game completion status

    Raises:
        HTTPException: If no active game or cards not loaded
    """
    if "game" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active game. Please start a new game.",
        )

    if not hasattr(request.app.state, "cards"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cards not loaded yet",
        )

    session_data = request.session["game"]
    session = GameSession(**session_data)
    all_cards = request.app.state.cards

    try:
        is_correct, correct_answer = game_service.submit_answer(
            session, answer_request.answer, all_cards
        )

        # Update session in cookie
        request.session["game"] = session.model_dump()

        is_complete = game_service.is_game_complete(session)

        logger.info(
            f"Answer submitted: correct={is_correct}, complete={is_complete}, "
            f"score={session.score}/{session.total_cards}"
        )

        return SubmitAnswerResponse(
            correct=is_correct,
            correct_answer=correct_answer,
            is_complete=is_complete,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/game/results", response_model=GameResultsResponse)
def get_game_results(request: Request) -> GameResultsResponse:
    """
    Get final game results.

    Returns the score, total cards, and percentage.

    Args:
        request: FastAPI request object

    Returns:
        Game results with score and percentage

    Raises:
        HTTPException: If no active game or game not complete
    """
    if "game" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active game. Please start a new game.",
        )

    session_data = request.session["game"]
    session = GameSession(**session_data)

    try:
        score, total, percentage = game_service.get_game_results(session)

        return GameResultsResponse(
            score=score,
            total=total,
            percentage=round(percentage, 1),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
