# Development Plan

This document outlines the detailed development plan for the Quiz Game application.

## Phase 1: Project Setup and Infrastructure

### 1.0 Create Makefile

Create a `Makefile` in the project root for development automation (see Phase 3, Section 3.3 for complete Makefile content).

### 1.1 Initialize Project Structure
```
ai-quiz/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   ├── card.py             # Card data model
│   │   └── game.py             # Game state models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── game.py         # Game endpoints
│   │       └── health.py       # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── s3_service.py       # S3 integration
│   │   ├── game_service.py     # Game logic
│   │   └── cache_service.py    # Image caching
│   ├── static/
│   │   ├── index.html          # Frontend HTML
│   │   ├── css/
│   │   │   └── styles.css      # Tailwind CSS
│   │   └── js/
│   │       └── app.js          # Frontend JavaScript
│   └── cache/
│       └── images/             # Cached S3 images (created at runtime)
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_game_service.py
│   │   ├── test_s3_service.py
│   │   └── test_cache_service.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   └── test_session_management.py
│   └── conftest.py             # Pytest fixtures
├── requirements.txt            # Python dependencies (pinned versions)
├── requirements-dev.txt        # Development dependencies
├── Dockerfile
├── docker-compose.yml          # For local testing
├── .env.example                # Example environment variables
├── .dockerignore
├── .gitignore
├── pytest.ini
├── Makefile                    # Development automation tasks
├── README.md
├── CLAUDE.md
└── DEVELOPMENT.md
```

### 1.2 Create Requirements Files

**requirements.txt** (production):
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
boto3==1.35.0
pydantic==2.9.0
pydantic-settings==2.5.2
python-multipart==0.0.9
aiofiles==24.1.0
```

**requirements-dev.txt** (development):
```
-r requirements.txt
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
httpx==0.27.2
moto[s3]==5.0.14
black==24.8.0
flake8==7.1.1
mypy==1.11.2
```

### 1.3 Environment Configuration
Create `.env.example`:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=quiz-game-cards
S3_CARDS_JSON_KEY=cards.json
SESSION_SECRET_KEY=your-secret-key-min-32-chars
CACHE_DIR=/app/cache/images
ENVIRONMENT=development
```

## Phase 2: Backend Development

### 2.1 Configuration Module (app/config.py)
- Load environment variables using Pydantic Settings
- Validate required configuration
- Provide configuration access throughout application
- Support different environments (dev, test, prod)

### 2.2 Data Models (app/models/)

**card.py**:
- `Card` model: id, image_filename, correct_answer
- `CardWithChoices` model: extends Card with list of answer choices

**game.py**:
- `GameSession` model: session_id, cards, current_index, score, total_cards
- `StartGameRequest` model: num_cards (validated: 5 ≤ num_cards ≤ total/2)
- `SubmitAnswerRequest` model: answer
- `SubmitAnswerResponse` model: correct (bool), correct_answer (str)
- `GameResultResponse` model: score, total, percentage

### 2.3 S3 Service (app/services/s3_service.py)
- Initialize boto3 S3 client
- `fetch_cards_metadata()`: Download and parse cards.json from S3
- `download_image(bucket, key, local_path)`: Download single image
- `download_all_images(cards)`: Download all card images to cache directory
- Error handling for S3 operations
- **Unit tests**: Mock boto3 calls using moto

### 2.4 Cache Service (app/services/cache_service.py)
- `initialize_cache()`: Create cache directory if not exists
- `cache_exists(filename)`: Check if image is cached
- `get_cache_path(filename)`: Return path to cached image
- **Unit tests**: Test file system operations with temporary directories

### 2.5 Game Service (app/services/game_service.py)
- `create_game_session(num_cards, all_cards)`: Create new game with random card selection
- `get_current_card_with_choices(session, all_cards)`: Generate 5 answer choices (alphabetically sorted)
- `submit_answer(session, answer)`: Validate answer, update score, advance to next card
- `is_game_complete(session)`: Check if all cards answered
- `get_game_results(session)`: Calculate final score and percentage
- **Unit tests**: Test game logic, answer generation, scoring with known inputs

### 2.6 API Routes (app/api/routes/)

**health.py**:
- `GET /health`: Health check endpoint
- Returns: `{"status": "healthy", "cards_loaded": bool}`

**game.py**:
- `GET /api/cards/total`: Get total number of available cards
- `POST /api/game/start`: Start new game
  - Request body: `{num_cards: int}`
  - Validates: 5 ≤ num_cards ≤ total_cards/2
  - Creates session in signed cookie
  - Returns: `{message: "Game started", total_cards: int}`
- `GET /api/game/current`: Get current card and choices
  - Reads session from cookie
  - Returns: `{card_index: int, total_cards: int, image_url: str, choices: [str]}`
  - Returns 404 if no active game
- `POST /api/game/answer`: Submit answer for current card
  - Request body: `{answer: str}`
  - Updates session in cookie
  - Returns: `{correct: bool, correct_answer: str, is_complete: bool}`
- `GET /api/game/results`: Get final game results
  - Returns: `{score: int, total: int, percentage: float}`
  - Returns 400 if game not complete

### 2.7 Main Application (app/main.py)
- Initialize FastAPI app with metadata for Swagger docs
- Configure SessionMiddleware with secret key
- Implement startup event handler:
  - Initialize cache directory
  - Download cards.json from S3
  - Download all images to cache
  - Store cards list in app.state
- Mount StaticFiles:
  - `/static` → frontend assets
  - `/images` → cached card images
- Include API routers
- Configure CORS if needed
- Add exception handlers

## Phase 3: Testing Strategy

### 3.1 Unit Tests (tests/unit/)

**test_game_service.py**:
- Test game session creation
- Test answer choice generation (always 5, includes correct answer, alphabetically sorted)
- Test answer validation (correct/incorrect)
- Test score calculation
- Test edge cases (minimum cards, maximum cards)

**test_s3_service.py**:
- Mock S3 using moto
- Test cards.json download and parsing
- Test image download
- Test error handling (missing bucket, network errors)

**test_cache_service.py**:
- Test cache directory creation
- Test cache path generation
- Test file existence checks
- Use temporary directories for isolation

**Coverage target**: 90%+ for services layer

### 3.2 Integration Tests (tests/integration/)

**test_api_endpoints.py**:
- Test complete game flow:
  1. GET /api/cards/total
  2. POST /api/game/start
  3. GET /api/game/current (multiple times)
  4. POST /api/game/answer (for each card)
  5. GET /api/game/results
- Test session persistence across requests
- Test invalid inputs (num_cards out of range, invalid answers)
- Test error responses (404, 400, 422)

**test_session_management.py**:
- Test signed cookie creation and validation
- Test session isolation between different clients
- Test cookie tampering detection
- Test session expiration

**Setup**:
- Use `TestClient` from FastAPI
- Mock S3 operations
- Use in-memory card data for predictable tests

### 3.3 Makefile for Development Automation

Create a `Makefile` in the project root to streamline common development tasks:

```makefile
.PHONY: help install install-dev test test-unit test-integration coverage lint format typecheck quality clean run docker-build docker-run docker-test all

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
```

**Usage examples**:
```bash
# Install dependencies and run all checks
make install-dev
make all

# Development workflow
make format          # Format code
make quality         # Run all quality checks
make test            # Run tests
make coverage        # Run tests with coverage

# Quick test cycle
make test-unit       # Only run unit tests during development

# Docker testing
make docker-build
make docker-run
# In another terminal:
make docker-test
```

### 3.4 Testing Commands

**Using Makefile (recommended)**:
```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run all quality checks and tests
make all
```

**Using pytest directly**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_game_service.py -v

# Run with output
pytest -s
```

### 3.5 Pytest Configuration (pytest.ini)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --tb=short
```

## Phase 4: Frontend Development

### 4.1 HTML Structure (app/static/index.html)
- Single-page application structure
- Responsive meta tags for mobile
- Tailwind CSS CDN (or build process)
- Sections:
  - Start screen (card count selection)
  - Game screen (card image, answer choices)
  - Feedback screen (correct/incorrect)
  - Results screen (final score, new game button)

### 4.2 JavaScript Application (app/static/js/app.js)
- Fetch API for backend communication
- Handle cookies automatically (credentials: 'include')
- State management for current screen
- Event handlers:
  - Start game button
  - Answer selection
  - New game button
- Dynamic UI updates
- Mobile-friendly touch interactions

### 4.3 Tailwind CSS Styling (app/static/css/styles.css)
- Mobile-first responsive design
- Card display optimized for phone screens
- Button styling (large touch targets)
- Answer choice buttons (clear, accessible)
- Feedback animations (correct/incorrect)
- Loading states

### 4.4 Mobile Optimization
- Viewport configuration
- Touch-friendly button sizes (min 44x44px)
- Readable font sizes (min 16px to prevent zoom)
- Vertical layout for portrait orientation
- Test on actual mobile devices or emulators

## Phase 5: API Documentation

### 5.1 Swagger/OpenAPI Documentation
FastAPI automatically generates interactive API docs at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc alternative

### 5.2 Enhance API Documentation
In route definitions, add:
- Detailed docstrings
- Response model examples
- Error response documentation
- Request body examples
- Tags for grouping endpoints

Example:
```python
@router.post(
    "/game/start",
    response_model=StartGameResponse,
    tags=["game"],
    summary="Start a new game",
    description="Creates a new game session with specified number of cards",
    responses={
        200: {"description": "Game started successfully"},
        422: {"description": "Invalid number of cards"},
    }
)
async def start_game(request: StartGameRequest):
    """
    Start a new quiz game.

    - **num_cards**: Number of cards to play (5 to half of total available)
    """
    pass
```

### 5.3 API Documentation Export
- Generate OpenAPI spec: Available at `/openapi.json`
- Can be imported into Postman, Insomnia, etc.

## Phase 6: Docker Configuration

### 6.1 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create cache directory
RUN mkdir -p /app/cache/images

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 .dockerignore
```
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
htmlcov/
tests/
.env
*.md
venv/
env/
.venv/
```

### 6.3 docker-compose.yml (for local testing)
```yaml
version: '3.8'

services:
  quiz-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
      - S3_CARDS_JSON_KEY=${S3_CARDS_JSON_KEY}
      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
      - CACHE_DIR=/app/cache/images
      - ENVIRONMENT=development
    volumes:
      - ./app:/app/app  # For development hot-reload
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Phase 7: Developer Documentation

### 7.1 Local Development Setup

**Prerequisites**:
- Python 3.11+
- Docker and Docker Compose
- AWS credentials with S3 access

**Setup steps**:
```bash
# Clone repository
git clone <repository-url>
cd ai-quiz

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your AWS credentials and settings

# Run tests
pytest

# Run application locally (without Docker)
uvicorn app.main:app --reload

# Access application
# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 7.2 Docker Development

**Build and run with Docker Compose**:
```bash
# Build image
docker-compose build

# Run container
docker-compose up

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

**Build and run with Docker directly**:
```bash
# Build image
docker build -t quiz-game:latest .

# Run container
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  -e S3_BUCKET_NAME=quiz-game-cards \
  -e S3_CARDS_JSON_KEY=cards.json \
  -e SESSION_SECRET_KEY=your-secret-key \
  quiz-game:latest

# Access application at http://localhost:8000
```

### 7.3 Testing the Docker Container

**Health check**:
```bash
curl http://localhost:8000/health
```

**Test API endpoints**:
```bash
# Get total cards
curl http://localhost:8000/api/cards/total

# Start game (save cookies)
curl -X POST http://localhost:8000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"num_cards": 10}' \
  -c cookies.txt

# Get current card (use cookies)
curl http://localhost:8000/api/game/current \
  -b cookies.txt

# Submit answer (use cookies)
curl -X POST http://localhost:8000/api/game/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "Some Answer"}' \
  -b cookies.txt \
  -c cookies.txt

# Get results (use cookies)
curl http://localhost:8000/api/game/results \
  -b cookies.txt
```

### 7.4 Code Quality Tools

**Using Makefile (recommended)**:
```bash
# Format code
make format

# Check formatting without making changes
make format-check

# Run linter
make lint

# Run type checker
make typecheck

# Run all quality checks
make quality

# Run quality checks + tests with coverage
make all
```

**Using tools directly**:
```bash
# Formatting with Black
black app/ tests/

# Check formatting
black app/ tests/ --check

# Linting with Flake8
flake8 app/ tests/

# Type checking with mypy
mypy app/

# Run all quality checks
black app/ tests/ && flake8 app/ tests/ && mypy app/ && pytest
```

**Configure Flake8** (create `.flake8` file):
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .pytest_cache,
    venv,
    env,
    .venv
```

**Configure mypy** (create `mypy.ini` file):
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
exclude = tests/
```

### 7.5 S3 Bucket Setup

**Required S3 structure**:
```
s3://quiz-game-cards/
├── cards.json
├── card1.jpg
├── card2.jpg
└── ...
```

**cards.json format**:
```json
[
  {
    "id": 1,
    "image_filename": "card1.jpg",
    "correct_answer": "Answer One"
  },
  {
    "id": 2,
    "image_filename": "card2.jpg",
    "correct_answer": "Answer Two"
  }
]
```

**S3 Permissions**:
- IAM user/role needs `s3:GetObject` permission on bucket
- Images should be accessible by the application

### 7.6 Troubleshooting

**Application won't start**:
- Check AWS credentials are set correctly
- Verify S3 bucket name and region
- Check logs: `docker-compose logs -f`

**Images not loading**:
- Verify S3 bucket permissions
- Check cache directory exists: `docker exec <container> ls /app/cache/images`
- Check startup logs for S3 download errors

**Session issues**:
- Verify SESSION_SECRET_KEY is set (minimum 32 characters)
- Check browser is accepting cookies
- Test with curl using `-c` and `-b` flags

**Tests failing**:
- Ensure test dependencies installed: `pip install -r requirements-dev.txt`
- Check pytest is finding tests: `pytest --collect-only`
- Run tests with verbose output: `pytest -v`

## Phase 8: Deployment Preparation

### 8.1 Production Dockerfile Optimization
- Multi-stage build for smaller image size
- Non-root user for security
- Health check configuration

### 8.2 Security Considerations
- Rotate SESSION_SECRET_KEY regularly
- Use AWS IAM roles instead of access keys (when possible)
- Enable HTTPS in production
- Set secure cookie flags (secure=True, httponly=True, samesite='lax')
- Implement rate limiting for API endpoints

### 8.3 Monitoring and Logging
- Configure structured logging
- Add application metrics
- Health check endpoint for orchestration
- Log S3 operations and errors

## Development Timeline Estimate

- **Phase 1**: Project Setup - 1 day
- **Phase 2**: Backend Development - 3-4 days
- **Phase 3**: Testing Implementation - 2-3 days
- **Phase 4**: Frontend Development - 2-3 days
- **Phase 5**: API Documentation - 0.5 days (concurrent with Phase 2)
- **Phase 6**: Docker Configuration - 1 day
- **Phase 7**: Developer Documentation - 0.5 days
- **Phase 8**: Deployment Preparation - 1 day

**Total estimated time**: 10-14 days for a single developer

## Quick Start for Developers

```bash
# 1. Clone and setup
git clone <repository-url>
cd ai-quiz
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
make install-dev

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Run quality checks and tests
make all

# 5. Run application
make run
# Visit http://localhost:8000

# 6. Build and test Docker
make docker-build
make docker-run
# In another terminal: make docker-test
```

## Next Steps

1. Set up project structure and initialize Git repository
2. Create Makefile for development automation
3. Create virtual environment and install dependencies
4. Implement backend services starting with S3 integration
5. Write unit tests alongside service implementation (use `make test-unit`)
6. Implement API routes with proper documentation
7. Create frontend with mobile-first approach
8. Write integration tests for complete workflows (use `make test-integration`)
9. Build and test Docker container (use `make docker-build` and `make docker-test`)
10. Run all quality checks and coverage (use `make all`)
11. Prepare deployment configuration
12. Conduct final testing and code review
