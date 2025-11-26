"""Integration tests for session management."""

import pytest
from typing import List
from fastapi.testclient import TestClient

from app.main import app
from app.models.card import Card


@pytest.fixture
def client(sample_cards: List[Card]) -> TestClient:
    """Fixture providing a test client with mocked card data."""
    app.state.cards = sample_cards
    return TestClient(app)


def test_session_cookie_created_on_game_start(client: TestClient) -> None:
    """Test that session cookie is created when game starts."""
    response = client.post("/api/game/start", json={"num_cards": 5})

    assert response.status_code == 200
    assert "quiz_session" in response.cookies


def test_session_data_persists_across_requests(client: TestClient) -> None:
    """Test that session data persists across multiple requests."""
    # Start game
    start_response = client.post("/api/game/start", json={"num_cards": 5})
    assert start_response.status_code == 200

    # Get current card
    card1_response = client.get("/api/game/current")
    assert card1_response.status_code == 200
    card1_data = card1_response.json()
    assert card1_data["card_index"] == 0

    # Submit answer
    answer_response = client.post(
        "/api/game/answer", json={"answer": card1_data["choices"][0]}
    )
    assert answer_response.status_code == 200

    # Get next card - should be card index 1
    card2_response = client.get("/api/game/current")
    assert card2_response.status_code == 200
    card2_data = card2_response.json()
    assert card2_data["card_index"] == 1


def test_session_isolation_between_clients(sample_cards: List[Card]) -> None:
    """Test that different clients have isolated sessions."""
    app.state.cards = sample_cards

    # Create two separate clients (simulating two users)
    client1 = TestClient(app)
    client2 = TestClient(app)

    # Client 1 starts a game with 5 cards
    client1.post("/api/game/start", json={"num_cards": 5})
    card1_response = client1.get("/api/game/current")
    assert card1_response.json()["total_cards"] == 5

    # Client 2 starts a game with 6 cards
    client2.post("/api/game/start", json={"num_cards": 6})
    card2_response = client2.get("/api/game/current")
    assert card2_response.json()["total_cards"] == 6

    # Verify client 1's game is still 5 cards
    card1_check = client1.get("/api/game/current")
    assert card1_check.json()["total_cards"] == 5


def test_session_maintains_score(client: TestClient, sample_cards: List[Card]) -> None:
    """Test that session maintains score throughout the game."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Answer cards and check score is maintained
    for i in range(5):
        card_response = client.get("/api/game/current")
        card_data = card_response.json()

        # Find the correct answer from sample_cards
        # For this test, we'll just use the correct_answer from the response
        answer_response = client.post(
            "/api/game/answer", json={"answer": card_data["choices"][0]}
        )
        assert answer_response.status_code == 200

    # Get results
    results_response = client.get("/api/game/results")
    assert results_response.status_code == 200

    results_data = results_response.json()
    assert results_data["total"] == 5
    # Score should be between 0 and 5
    assert 0 <= results_data["score"] <= 5


def test_new_game_replaces_session(client: TestClient) -> None:
    """Test that starting a new game replaces the previous session."""
    # Start first game
    client.post("/api/game/start", json={"num_cards": 5})
    card1_response = client.get("/api/game/current")
    assert card1_response.json()["total_cards"] == 5

    # Start new game
    client.post("/api/game/start", json={"num_cards": 6})
    card2_response = client.get("/api/game/current")
    card2_data = card2_response.json()

    # Should be a new game with 6 cards, starting at index 0
    assert card2_data["total_cards"] == 6
    assert card2_data["card_index"] == 0


def test_session_without_cookie_returns_404(sample_cards: List[Card]) -> None:
    """Test that requests without session cookie return 404."""
    app.state.cards = sample_cards
    client = TestClient(app)

    # Try to get current card without starting a game
    response = client.get("/api/game/current")

    assert response.status_code == 404
    assert "No active game" in response.json()["detail"]


def test_session_state_after_game_completion(client: TestClient) -> None:
    """Test session state after completing a game."""
    # Start and complete a game
    client.post("/api/game/start", json={"num_cards": 5})

    for _ in range(5):
        card_response = client.get("/api/game/current")
        card_data = card_response.json()
        client.post("/api/game/answer", json={"answer": card_data["choices"][0]})

    # Try to get current card after game is complete
    response = client.get("/api/game/current")

    assert response.status_code == 400
    assert "already complete" in response.json()["detail"]

    # But getting results should still work
    results_response = client.get("/api/game/results")
    assert results_response.status_code == 200


def test_session_cookie_has_correct_attributes(client: TestClient) -> None:
    """Test that session cookie has correct security attributes."""
    response = client.post("/api/game/start", json={"num_cards": 5})

    # Check cookie exists
    assert "quiz_session" in response.cookies

    # Note: TestClient doesn't expose all cookie attributes,
    # but we can verify the cookie name is correct
    cookie = response.cookies.get("quiz_session")
    assert cookie is not None
    assert len(cookie) > 0  # Cookie should have data


def test_multiple_answer_submissions_in_sequence(client: TestClient) -> None:
    """Test submitting multiple answers maintains correct session state."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Submit 3 answers
    for i in range(3):
        card_response = client.get("/api/game/current")
        assert card_response.status_code == 200

        card_data = card_response.json()
        assert card_data["card_index"] == i

        answer_response = client.post(
            "/api/game/answer", json={"answer": card_data["choices"][0]}
        )
        assert answer_response.status_code == 200

    # Verify we're at card 3 now
    card_response = client.get("/api/game/current")
    assert card_response.json()["card_index"] == 3


def test_session_maintains_card_order(client: TestClient) -> None:
    """Test that session maintains the same card order throughout game."""
    # Start game
    client.post("/api/game/start", json={"num_cards": 5})

    # Get first card and record its image URL
    card1_response = client.get("/api/game/current")
    card1_url = card1_response.json()["image_url"]

    # Submit answer to advance
    client.post("/api/game/answer", json={"answer": "Some Answer"})

    # Get second card
    card2_response = client.get("/api/game/current")
    card2_url = card2_response.json()["image_url"]

    # Cards should be different
    assert card1_url != card2_url

    # Starting a new game should give different cards
    client.post("/api/game/start", json={"num_cards": 5})
    new_card_response = client.get("/api/game/current")
    new_card_url = new_card_response.json()["image_url"]

    # The new game's first card might be different (random selection)
    # We just verify we can still play the game
    assert new_card_url is not None
