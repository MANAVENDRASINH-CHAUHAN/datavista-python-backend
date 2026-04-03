from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_user
from app.schemas.ai_schema import CleaningRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services.ai_service import (
    create_reset_token,
    generate_dataset_insights,
    get_cleaning_suggestions,
    reset_password_with_token,
    run_cleaning,
)

router = APIRouter(tags=["AI and Cleaning"])


@router.get("/api/ai/datasets/{dataset_id}/cleaner")
def cleaner_suggestions(dataset_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        result = get_cleaning_suggestions(dataset_id, current_user["id"])
        return {"success": True, "message": "Cleaning suggestions fetched successfully", "data": result, **result}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/api/ai/datasets/{dataset_id}/clean")
def clean_dataset(dataset_id: str, payload: CleaningRequest, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        result = run_cleaning(dataset_id, current_user["id"], payload.operations)
        return {"success": True, "message": "Cleaning completed successfully", "data": result, **result}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/api/ai/datasets/{dataset_id}/insights")
def dataset_insights(dataset_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        result = generate_dataset_insights(dataset_id, current_user["id"])
        return {"success": True, "message": "Insights generated successfully", "data": result, **result}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/api/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest) -> dict:
    try:
        result = create_reset_token(payload.email)
        return {"success": True, "message": "Reset link generated successfully", "data": result, **result}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/api/auth/reset-password/{token}")
def reset_password(token: str, payload: ResetPasswordRequest) -> dict:
    try:
        reset_password_with_token(token, payload.password, payload.confirmPassword)
        return {"success": True, "message": "Password reset successful", "data": None}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
