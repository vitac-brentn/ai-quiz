"""Integration tests for API endpoints."""

import pytest
from typing import List
from fastapi.testclient import TestClient

from app.main import app
from app.models.card import Card


@pytest.fixture
def client(sample_cards: List[Card]) -> TestClient:
    """Fixture providing a test client with mocked card data."""
    # Mock the cards in app state
    app.state.cards = sample_cards

    client = TestClient(app)
    return client


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cards_loaded"] is True


def test_health_check_no_cards() -> None:
    """Test health check when cards not loaded."""
    client = TestClient(app)
    # Don't set app.state.cards

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cards_loaded"] is False


def test_get_total_cards(client: TestClient, sample_cards: List[Card]) -> None:
    """Test getting total number of cards."""
    response = client.get("/api/cards/total")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(sample_cards)


def test_start_game(client: TestClient) -> None:
    """Test starting a new game."""
    response = client.post("/api/game/start", json={"num_cards": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Game started"
    assert data["total_cards"] == 5

    # Verify session cookie was set
    assert "quiz_session" in response.cookies


def test_start_game_invalid_num_cards_too_few(client: TestClient) -> None:
    """Test starting game with too few cards."""
    response = client.post("/api/game/start", json={"num_cards": 3})

    assert response.status_code == 422


def test_start_game_invalid_num_cards_too_many(
    client: TestClient, sample_cards: List[Card]
) -> None:
    """Test starting game with too many cards."""
    max_cards = len(sample_cards) // 2
    response = client.post("/api/game/start", json={"num_cards": max_cards + 1})

    assert response.status_code == 422


def test_get_current_card_no_game(client: TestClient) -> None:
    """Test getting current card without starting a game."""
    response = client.get("/api/game/current")

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_get_current_card(client: TestClient, sample_cards: List[Card]) -> None:
    """Test getting the current card."""
    # Start a game first
    start_response = client.post("/api/game/start", json={"num_cards": 5})
    assert start_response.status_code == 200

    # Get current card
    response = client.get("/api/game/current")

    assert response.status_code == 200
    data = response.json()
    assert data["card_index"] == 0
    assert data["total_cards"] == 5
    assert len(data["choices"]) == 5
    assert data["image_url"].startswith("/images/")

    # Verify choices are sorted alphabetically
    assert data["choices"] == sorted(data["choices"])


def test_submit_answer_no_game(client: TestClient) -> None:
    """Test submitting answer without starting a game."""
    response = client.post("/api/game/answer", json={"answer": "Apple"})

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_submit_answer_correct(client: TestClient, sample_cards: List[Card]) -> None:
    """Test submitting a correct answer."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Get current card to know the correct answer
    card_response = client.get("/api/game/current")
    card_data = card_response.json()

    # Get the correct answer from the choices (we need to find it from our sample data)
    # For testing, we'll submit one of the choices
    correct_answer = card_data["choices"][0]  # Submit first choice

    # Submit answer
    response = client.post("/api/game/answer", json={"answer": correct_answer})

    assert response.status_code == 200
    data = response.json()
    assert "correct" in data
    assert "correct_answer" in data
    assert "is_complete" in data
    assert data["is_complete"] is False  # Only answered 1 of 5


def test_submit_answer_incorrect(client: TestClient) -> None:
    """Test submitting an incorrect answer."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Submit wrong answer
    response = client.post("/api/game/answer", json={"answer": "Wrong Answer"})

    assert response.status_code == 200
    data = response.json()
    assert "correct" in data
    assert "correct_answer" in data
    assert data["is_complete"] is False


def test_complete_game_flow(client: TestClient, sample_cards: List[Card]) -> None:
    """Test complete game flow from start to finish."""
    # Start game with 5 cards
    start_response = client.post("/api/game/start", json={"num_cards": 5})
    assert start_response.status_code == 200

    # Answer all 5 cards
    for i in range(5):
        # Get current card
        card_response = client.get("/api/game/current")
        assert card_response.status_code == 200
        card_data = card_response.json()
        assert card_data["card_index"] == i

        # Submit answer (always submit first choice for simplicity)
        answer_response = client.post(
            "/api/game/answer", json={"answer": card_data["choices"][0]}
        )
        assert answer_response.status_code == 200

        answer_data = answer_response.json()
        if i < 4:
            assert answer_data["is_complete"] is False
        else:
            assert answer_data["is_complete"] is True

    # Get results
    results_response = client.get("/api/game/results")
    assert results_response.status_code == 200

    results_data = results_response.json()
    assert results_data["total"] == 5
    assert 0 <= results_data["score"] <= 5
    assert 0 <= results_data["percentage"] <= 100


def test_get_results_no_game(client: TestClient) -> None:
    """Test getting results without starting a game."""
    response = client.get("/api/game/results")

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_get_results_game_not_complete(client: TestClient) -> None:
    """Test getting results before game is complete."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Try to get results without finishing
    response = client.get("/api/game/results")

    assert response.status_code == 400
    assert "not complete" in response.json()["detail"]


def test_session_persistence(client: TestClient) -> None:
    """Test that session persists across requests."""
    # Start game
    start_response = client.post("/api/game/start", json={"num_cards": 5})
    cookies = start_response.cookies

    # Get current card (should use session from cookie)
    card_response = client.get("/api/game/current")
    assert card_response.status_code == 200

    # Submit answer
    answer_response = client.post(
        "/api/game/answer", json={"answer": "Some Answer"}
    )
    assert answer_response.status_code == 200

    # Get next card (should advance)
    next_card_response = client.get("/api/game/current")
    assert next_card_response.status_code == 200
    next_card_data = next_card_response.json()
    assert next_card_data["card_index"] == 1


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns API info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
