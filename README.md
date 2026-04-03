# DataVista Python Backend

This folder contains the new FastAPI backend for DataVista. The React frontend can continue using the existing `/api/...` route shape while the backend is rebuilt in Python phase by phase.

## Phase 1 Scope

- Set up a production-style FastAPI entrypoint
- Add MongoDB connection management
- Add environment-based configuration
- Prepare the folder layout for upcoming auth, dataset, cleaning, and AI modules

## Run Locally

1. Create and activate a virtual environment
2. Install dependencies from `requirements.txt`
3. Copy `.env` values and update MongoDB credentials
4. Start the API with Uvicorn on port `5000`

## Available Endpoints

- `GET /`
- `GET /api/health`
- `GET /docs`
