from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

import pandas as pd

from app.config.db import get_database
from app.services.auth_service import get_users_collection
from app.services.dataset_service import read_dataset_dataframe, save_cleaned_dataset
from app.utils.cleaning_utils import apply_cleaning_operations, detect_cleaning_issues
from app.utils.stats_utils import build_basic_stats
from app.utils.security import hash_password


def get_cleaning_suggestions(dataset_id: str, owner_id: str) -> dict:
    dataset, dataframe = read_dataset_dataframe(dataset_id, owner_id)
    cleaning = detect_cleaning_issues(dataframe)
    return {
        "dataset": {
            "_id": str(dataset["_id"]),
            "datasetName": dataset["datasetName"],
            "columnNames": list(dataframe.columns),
        },
        "cleaning": cleaning,
    }


def run_cleaning(dataset_id: str, owner_id: str, operations: list) -> dict:
    _, dataframe = read_dataset_dataframe(dataset_id, owner_id)
    cleaned_df, cleaning_summary = apply_cleaning_operations(dataframe, operations)
    dataset = save_cleaned_dataset(dataset_id, owner_id, cleaned_df)
    return {
        "dataset": dataset,
        "cleaningSummary": cleaning_summary,
        "previewRows": cleaned_df.head(5).to_dict(orient="records"),
    }


def generate_dataset_insights(dataset_id: str, owner_id: str) -> dict:
    dataset, dataframe = read_dataset_dataframe(dataset_id, owner_id)
    stats = build_basic_stats(dataframe)
    insights: list[str] = []

    insights.append(
        f"{dataset['datasetName']} contains {stats['rowCount']} rows and {stats['columnCount']} columns."
    )

    missing_total = sum(item["missingCount"] for item in stats["missingValues"])
    if missing_total:
        insights.append(f"The dataset has {missing_total} missing values across all columns.")
    else:
        insights.append("No missing values were detected, so the dataset is structurally complete.")

    if stats["duplicateRows"]:
        insights.append(f"There are {stats['duplicateRows']} duplicate rows that may affect analysis.")

    numeric_summary = stats["numericSummary"]
    if numeric_summary:
        first_numeric = next(iter(numeric_summary))
        summary = numeric_summary[first_numeric]
        insights.append(
            f"The numeric column {first_numeric} has an average value of {summary['mean']} and a maximum of {summary['max']}."
        )

    object_columns = list(dataframe.select_dtypes(include="object").columns)
    if object_columns:
        top_column = object_columns[0]
        top_values = dataframe[top_column].astype(str).value_counts().head(3).index.tolist()
        insights.append(
            f"Column {top_column} is categorical and common values include {', '.join(top_values)}."
        )

    return {
        "dataset": {
            "_id": str(dataset["_id"]),
            "datasetName": dataset["datasetName"],
        },
        "insights": insights,
        "stats": stats,
    }


def create_reset_token(email: str) -> dict:
    users = get_users_collection()
    user = users.find_one({"email": email.lower()})
    if not user:
        raise ValueError("No account found with this email")

    reset_token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    users.update_one(
        {"_id": user["_id"]},
        {"$set": {"resetToken": reset_token, "resetTokenExpiresAt": expires_at}},
    )

    return {
        "resetToken": reset_token,
        "resetUrl": f"http://localhost:5173/reset-password/{reset_token}",
    }


def reset_password_with_token(token: str, password: str, confirm_password: str) -> None:
    if password != confirm_password:
        raise ValueError("Passwords do not match")

    users = get_users_collection()
    user = users.find_one({"resetToken": token})
    if not user:
        raise ValueError("Invalid reset token")

    expires_at = user.get("resetTokenExpiresAt")
    if not expires_at or expires_at < datetime.utcnow():
        raise ValueError("Reset token has expired")

    users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": hash_password(password)},
            "$unset": {"resetToken": "", "resetTokenExpiresAt": ""},
        },
    )
