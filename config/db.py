import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()


@lru_cache
def get_settings() -> dict:
    mongo_uri = os.getenv("MONGO_URI")
    database_name = os.getenv("DATABASE_NAME", "datavista")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not set. Add it to backend-python/.env before starting the server.")

    return {
        "mongo_uri": mongo_uri,
        "database_name": database_name,
    }


@lru_cache
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings["mongo_uri"], serverSelectionTimeoutMS=5000)


def get_database() -> Database:
    settings = get_settings()
    client = get_mongo_client()
    return client[settings["database_name"]]


def ping_database() -> bool:
    try:
        get_mongo_client().admin.command("ping")
        return True
    except Exception:
        return False
