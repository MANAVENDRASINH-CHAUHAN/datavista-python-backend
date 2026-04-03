from datetime import datetime, timezone

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.config.db import get_database
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.utils.security import create_access_token, hash_password, verify_password


def get_users_collection():
    database = get_database()
    users = database["users"]
    users.create_index("email", unique=True)
    return users


def format_user(user_document: dict) -> dict:
    return {
        "id": str(user_document["_id"]),
        "name": user_document["name"],
        "email": user_document["email"],
        "role": user_document.get("role", "user"),
        "created_at": user_document["created_at"],
    }


def register_user(payload: RegisterRequest) -> dict:
    users = get_users_collection()

    new_user = {
        "name": payload.name.strip(),
        "email": payload.email.lower(),
        "password": hash_password(payload.password),
        "role": payload.role,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = users.insert_one(new_user)
    except DuplicateKeyError:
        raise ValueError("An account with this email already exists")

    created_user = users.find_one({"_id": result.inserted_id})
    user_data = format_user(created_user)
    token = create_access_token(user_data["id"])

    return {
        "success": True,
        "message": "Registration successful",
        "data": {
            "token": token,
            "user": user_data,
        },
        "token": token,
        "user": user_data,
    }


def login_user(payload: LoginRequest) -> dict:
    users = get_users_collection()
    user_document = users.find_one({"email": payload.email.lower()})

    if not user_document:
        raise ValueError("Invalid email or password")

    if not verify_password(payload.password, user_document["password"]):
        raise ValueError("Invalid email or password")

    user_data = format_user(user_document)
    token = create_access_token(user_data["id"])

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "token": token,
            "user": user_data,
        },
        "token": token,
        "user": user_data,
    }


def get_user_by_id(user_id: str) -> dict | None:
    if not ObjectId.is_valid(user_id):
        return None

    users = get_users_collection()
    user_document = users.find_one({"_id": ObjectId(user_id)})

    if not user_document:
        return None

    return format_user(user_document)
