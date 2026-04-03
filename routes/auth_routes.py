from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_user
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register")
def register(payload: RegisterRequest) -> dict:
    try:
        return register_user(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    try:
        return login_user(payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    return {
        "success": True,
        "message": "Current user fetched successfully",
        "data": {
            "user": current_user,
        },
        "user": current_user,
    }
