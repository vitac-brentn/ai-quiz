"""Unit tests for health check route."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import health
from app.models.card import Card


@pytest.fixture
def test_app() -> FastAPI:
    """Fixture providing a test FastAPI app with health router."""
    app = FastAPI()
    app.include_router(health.router)
    return app


def test_health_check_with_cards_loaded(test_app: FastAPI) -> None:
    """Test health check when cards are loaded."""
    # Set up app state with cards
    test_app.state.cards = [
        Card(id=1, image_filename="card1.jpg", correct_answer="Apple"),
        Card(id=2, image_filename="card2.jpg", correct_answer="Banana"),
    ]

    client = TestClient(test_app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cards_loaded"] is True


def test_health_check_without_cards(test_app: FastAPI) -> None:
    """Test health check when cards are not loaded."""
    # Don't set app.state.cards
    client = TestClient(test_app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cards_loaded"] is False


def test_health_check_with_empty_cards_list(test_app: FastAPI) -> None:
    """Test health check when cards list is empty."""
    test_app.state.cards = []

    client = TestClient(test_app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["cards_loaded"] is False


def test_health_check_response_structure(test_app: FastAPI) -> None:
    """Test health check response has correct structure."""
    test_app.state.cards = [Card(id=1, image_filename="card.jpg", correct_answer="Test")]

    client = TestClient(test_app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "cards_loaded" in data
    assert isinstance(data["status"], str)
    assert isinstance(data["cards_loaded"], bool)


def test_health_check_always_returns_healthy(test_app: FastAPI) -> None:
    """Test health check always returns 'healthy' status."""
    client = TestClient(test_app)

    # Test without cards
    response1 = client.get("/health")
    assert response1.json()["status"] == "healthy"

    # Test with cards
    test_app.state.cards = [Card(id=1, image_filename="card.jpg", correct_answer="Test")]
    response2 = client.get("/health")
    assert response2.json()["status"] == "healthy"
