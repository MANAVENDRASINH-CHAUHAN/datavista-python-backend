import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app.config.db import get_database, ping_database
from app.routes.ai_routes import router as ai_router
from app.routes.auth_routes import router as auth_router
from app.routes.dataset_routes import router as dataset_router

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(
    title="DataVista Python Backend",
    version="1.0.0",
    description="Production-style FastAPI backend for DataVista.",
)

frontend_origin = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dataset_router)
app.include_router(ai_router)


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0]
    message = first_error.get("msg", "Validation error")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": message,
            "data": None,
        },
    )


@app.on_event("startup")
def startup_event() -> None:
    uploads_dir = BASE_DIR / "app" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    get_database()


@app.get("/")
def root() -> dict:
    return {
        "success": True,
        "message": "DataVista Python backend is running",
        "data": {
            "service": "backend-python",
            "docs": "/docs",
        },
    }


@app.get("/api/health")
def health_check() -> dict:
    return {
        "success": True,
        "message": "Health check completed",
        "data": {
            "api": "running",
            "database": "connected" if ping_database() else "not connected",
        },
    }
