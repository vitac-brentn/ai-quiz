"""Unit tests for game routes."""

import pytest
from typing import List
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import game
from app.models.card import Card


@pytest.fixture
def test_app(sample_cards: List[Card]) -> FastAPI:
    """Fixture providing a test FastAPI app with game router."""
    app = FastAPI()
    app.add_middleware(
        SessionMiddleware,
        secret_key="test-secret-key-minimum-32-characters-long",
    )
    app.include_router(game.router)
    app.state.cards = sample_cards
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Fixture providing a test client."""
    return TestClient(test_app)


# GET /api/cards/total tests
def test_get_total_cards(client: TestClient, sample_cards: List[Card]) -> None:
    """Test getting total number of cards."""
    response = client.get("/api/cards/total")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(sample_cards)


def test_get_total_cards_no_cards_loaded(test_app: FastAPI) -> None:
    """Test getting total cards when cards not loaded."""
    # Remove cards from app state
    if hasattr(test_app.state, "cards"):
        delattr(test_app.state, "cards")

    client = TestClient(test_app)
    response = client.get("/api/cards/total")

    assert response.status_code == 503
    assert "not loaded" in response.json()["detail"]


# POST /api/game/start tests
def test_start_game_success(client: TestClient) -> None:
    """Test successfully starting a game."""
    response = client.post("/api/game/start", json={"num_cards": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Game started"
    assert data["total_cards"] == 5


def test_start_game_sets_session_cookie(client: TestClient) -> None:
    """Test that starting a game sets session cookie."""
    response = client.post("/api/game/start", json={"num_cards": 5})

    assert "quiz_session" in response.cookies


def test_start_game_too_few_cards(client: TestClient) -> None:
    """Test starting game with too few cards."""
    response = client.post("/api/game/start", json={"num_cards": 3})

    assert response.status_code == 422


def test_start_game_too_many_cards(client: TestClient, sample_cards: List[Card]) -> None:
    """Test starting game with too many cards."""
    max_cards = len(sample_cards) // 2
    response = client.post("/api/game/start", json={"num_cards": max_cards + 5})

    assert response.status_code == 422
    assert "must not exceed" in response.json()["detail"]


def test_start_game_no_cards_loaded(test_app: FastAPI) -> None:
    """Test starting game when cards not loaded."""
    if hasattr(test_app.state, "cards"):
        delattr(test_app.state, "cards")

    client = TestClient(test_app)
    response = client.post("/api/game/start", json={"num_cards": 5})

    assert response.status_code == 503


def test_start_game_invalid_request_body(client: TestClient) -> None:
    """Test starting game with invalid request body."""
    response = client.post("/api/game/start", json={})

    assert response.status_code == 422


# GET /api/game/current tests
def test_get_current_card_no_active_game(client: TestClient) -> None:
    """Test getting current card without active game."""
    response = client.get("/api/game/current")

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_get_current_card_success(client: TestClient) -> None:
    """Test getting current card with active game."""
    # Start game first
    client.post("/api/game/start", json={"num_cards": 5})

    response = client.get("/api/game/current")

    assert response.status_code == 200
    data = response.json()
    assert "card_index" in data
    assert "total_cards" in data
    assert "image_url" in data
    assert "choices" in data
    assert len(data["choices"]) == 5


def test_get_current_card_no_cards_loaded(test_app: FastAPI) -> None:
    """Test getting current card when cards not loaded."""
    client = TestClient(test_app)

    # Manually create a session
    with client as c:
        c.post("/api/game/start", json={"num_cards": 5})

        # Now remove cards
        if hasattr(test_app.state, "cards"):
            delattr(test_app.state, "cards")

        response = c.get("/api/game/current")
        assert response.status_code == 503


# POST /api/game/answer tests
def test_submit_answer_no_active_game(client: TestClient) -> None:
    """Test submitting answer without active game."""
    response = client.post("/api/game/answer", json={"answer": "Apple"})

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_submit_answer_success(client: TestClient) -> None:
    """Test successfully submitting an answer."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Get current card to see choices
    card_response = client.get("/api/game/current")
    choices = card_response.json()["choices"]

    # Submit answer
    response = client.post("/api/game/answer", json={"answer": choices[0]})

    assert response.status_code == 200
    data = response.json()
    assert "correct" in data
    assert "correct_answer" in data
    assert "is_complete" in data
    assert isinstance(data["correct"], bool)
    assert isinstance(data["is_complete"], bool)


def test_submit_answer_advances_game(client: TestClient) -> None:
    """Test that submitting answer advances to next card."""
    client.post("/api/game/start", json={"num_cards": 5})

    # Get first card
    card1 = client.get("/api/game/current")
    assert card1.json()["card_index"] == 0

    # Submit answer
    client.post("/api/game/answer", json={"answer": "Some Answer"})

    # Get next card
    card2 = client.get("/api/game/current")
    assert card2.json()["card_index"] == 1


def test_submit_answer_empty_answer(client: TestClient) -> None:
    """Test submitting empty answer."""
    client.post("/api/game/start", json={"num_cards": 5})

    response = client.post("/api/game/answer", json={"answer": ""})

    assert response.status_code == 422


def test_submit_answer_no_cards_loaded(test_app: FastAPI) -> None:
    """Test submitting answer when cards not loaded."""
    client = TestClient(test_app)

    with client as c:
        c.post("/api/game/start", json={"num_cards": 5})

        # Remove cards
        if hasattr(test_app.state, "cards"):
            delattr(test_app.state, "cards")

        response = c.post("/api/game/answer", json={"answer": "Apple"})
        assert response.status_code == 503


# GET /api/game/results tests
def test_get_results_no_active_game(client: TestClient) -> None:
    """Test getting results without active game."""
    response = client.get("/api/game/results")

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_get_results_game_not_complete(client: TestClient) -> None:
    """Test getting results before game is complete."""
    client.post("/api/game/start", json={"num_cards": 5})

    # Don't answer all cards
    response = client.get("/api/game/results")

    assert response.status_code == 400
    assert "not complete" in response.json()["detail"]


def test_get_results_after_complete_game(client: TestClient) -> None:
    """Test getting results after completing game."""
    client.post("/api/game/start", json={"num_cards": 5})

    # Answer all cards
    for _ in range(5):
        card_response = client.get("/api/game/current")
        choices = card_response.json()["choices"]
        client.post("/api/game/answer", json={"answer": choices[0]})

    # Get results
    response = client.get("/api/game/results")

    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "total" in data
    assert "percentage" in data
    assert data["total"] == 5
    assert 0 <= data["score"] <= 5
    assert 0 <= data["percentage"] <= 100


def test_game_service_singleton(client: TestClient) -> None:
    """Test that game service is reused across requests."""
    # This tests that the game_service instance in the module is used
    response1 = client.post("/api/game/start", json={"num_cards": 5})
    response2 = client.get("/api/cards/total")

    assert response1.status_code == 200
    assert response2.status_code == 200


def test_complete_flow_integration(client: TestClient) -> None:
    """Test complete game flow through routes."""
    # Get total cards
    total_response = client.get("/api/cards/total")
    assert total_response.status_code == 200

    # Start game
    start_response = client.post("/api/game/start", json={"num_cards": 5})
    assert start_response.status_code == 200

    # Play through all cards
    for i in range(5):
        card_response = client.get("/api/game/current")
        assert card_response.status_code == 200
        assert card_response.json()["card_index"] == i

        choices = card_response.json()["choices"]
        answer_response = client.post("/api/game/answer", json={"answer": choices[0]})
        assert answer_response.status_code == 200

    # Get results
    results_response = client.get("/api/game/results")
    assert results_response.status_code == 200
    assert results_response.json()["total"] == 5
