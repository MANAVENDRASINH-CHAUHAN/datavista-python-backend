from typing import Any

from pydantic import BaseModel, Field


class CleaningRequest(BaseModel):
    operations: list[Any] = Field(default_factory=list)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=128)
    confirmPassword: str = Field(..., min_length=6, max_length=128)
