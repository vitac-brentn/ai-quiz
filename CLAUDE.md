# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a quiz game application where players are shown card images and must select the correct answer from multiple choices. The game tracks progress and displays results at the end.

## Architecture

### Backend (Python 3 with FastAPI)
- Framework: FastAPI with uvicorn ASGI server
- Session Management: FastAPI's SessionMiddleware with signed cookies (no login required)
- Static File Serving: FastAPI's StaticFiles for frontend assets and cached images
- Runs inside a Docker container
- S3 Integration using boto3:
  - On startup: Download all card images from S3 to local cache directory
  - On startup: Fetch JSON file containing card metadata (image filename + correct answer)
  - Cache remains in memory/disk for duration of container runtime
- Serves API endpoints for:
  - Starting a new game (selecting number of cards: 5 to half of total available)
  - Getting the next card with 5 randomly selected answers (always includes correct answer, displayed alphabetically)
  - Submitting answers and receiving immediate feedback
  - Retrieving final score and game completion stats

### Frontend
- Browser-based, mobile-friendly interface
- Uses Tailwind CSS for styling
- Must work on phone-sized form factors
- Communicates with backend API

### Deployment
- Docker container hosting the entire application
- Listens on HTTP/HTTPS ports
- All dependencies (Python packages, Python version) must be version-pinned in configuration files

## Game Flow

1. Player selects number of cards (5 to half of total card set)
2. For each card:
   - Display card image
   - Show 5 answer choices (alphabetically sorted)
   - Accept player's selection
   - Show immediate feedback (correct/incorrect)
3. Display final score (e.g., "16 out of 20, 80%")
4. Offer option to start a new game

## Key Implementation Notes

### Session Management
- Use FastAPI's SessionMiddleware with signed cookies to track game state
- Cookies are cryptographically signed to prevent tampering
- No user authentication required
- Each browser session maintains independent game state
- Session data stored in cookie includes: current game cards, current card index, score, total cards

### Answer Selection Algorithm
- For each card, generate 5 answer choices:
  - Always include the correct answer
  - Randomly select 4 incorrect answers from the full card set
  - Sort all 5 answers alphabetically before display

### Card Selection
- Player chooses N cards where: 5 ≤ N ≤ (total_cards / 2)
- Randomly select N cards from the full set for each game

### S3 Image Caching Strategy
- On application startup, download all card images from S3 bucket to local directory
- Store in a cache directory (e.g., `/app/cache/images/`)
- Use FastAPI's StaticFiles to mount this directory and serve images directly
- Benefits: Faster response times, reduced S3 API calls, lower latency for players
- Card metadata JSON is also fetched on startup and kept in memory

## Technology Stack

### Python Backend
- **FastAPI** - Modern async web framework
- **uvicorn** - ASGI server for running FastAPI
- **boto3** - AWS SDK for S3 integration
- **Pydantic** - Data validation (included with FastAPI)
- **aiofiles** - (Optional) Async file operations for better performance during S3 downloads

### Dependency Management
- Use `requirements.txt` with pinned versions (`==` not `>=`)
- Lock Python version in Dockerfile

## Docker Container Requirements

- Container must be self-contained and ready to run
- Expose HTTP/HTTPS ports (typically 80/443 or 8000)
- All Python dependencies must be version-locked in requirements.txt
- Python version must be specified in Dockerfile
- Container should have sufficient disk space for cached S3 images
- Consider using startup event handlers to download S3 assets before serving requests

## Application Startup Flow

1. Initialize FastAPI application
2. Download card metadata JSON from S3
3. Parse JSON and download all card images to local cache directory
4. Mount StaticFiles for serving frontend assets (HTML, CSS, JS)
5. Mount StaticFiles for serving cached images
6. Start uvicorn server and begin accepting requests
