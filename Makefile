.PHONY: help install install-dev test test-unit test-integration coverage lint format format-check typecheck quality clean run docker-build docker-run docker-test all

help:
	@echo "Available targets:"
	@echo "  install          - Install production dependencies"
	@echo "  install-dev      - Install development dependencies"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  coverage         - Run tests with coverage report"
	@echo "  lint             - Run flake8 linter"
	@echo "  format           - Format code with black"
	@echo "  format-check     - Check code formatting without changes"
	@echo "  typecheck        - Run mypy type checking"
	@echo "  quality          - Run all code quality checks (format, lint, typecheck)"
	@echo "  all              - Run quality checks and all tests with coverage"
	@echo "  clean            - Remove cache and generated files"
	@echo "  run              - Run application locally"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-run       - Run Docker container"
	@echo "  docker-test      - Test Docker container health"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

coverage:
	pytest --cov=app --cov-report=html --cov-report=term --cov-report=xml --cov-fail-under=90

lint:
	flake8 app/ tests/ --count --statistics

format:
	black app/ tests/

format-check:
	black app/ tests/ --check

typecheck:
	mypy app/

quality: format lint typecheck
	@echo "All quality checks passed!"

all: quality coverage
	@echo "All checks and tests passed!"

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov/ .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t quiz-game:latest .

docker-run:
	docker-compose up

docker-test:
	@echo "Testing Docker container health..."
	@curl -f http://localhost:8000/health || (echo "Health check failed" && exit 1)
	@echo "Health check passed!"
