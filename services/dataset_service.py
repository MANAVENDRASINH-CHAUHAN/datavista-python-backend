from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from fastapi import UploadFile

from app.config.db import get_database
from app.utils.csv_utils import dataframe_to_records, read_csv_file, save_dataframe_to_csv
from app.utils.stats_utils import build_basic_stats, build_chart_data

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "app" / "uploads"


def get_datasets_collection():
    return get_database()["datasets"]


def format_dataset(document: dict) -> dict:
    return {
        "_id": str(document["_id"]),
        "datasetName": document["datasetName"],
        "category": document.get("category", "General"),
        "description": document.get("description", ""),
        "fileName": document["fileName"],
        "filePath": document["filePath"],
        "rowCount": int(document.get("rowCount", 0)),
        "columnCount": int(document.get("columnCount", 0)),
        "columnNames": document.get("columnNames", []),
        "ownerId": document["ownerId"],
        "createdAt": document["createdAt"],
        "updatedAt": document["updatedAt"],
    }


def ensure_dataset_owner(dataset_id: str, owner_id: str) -> dict:
    if not ObjectId.is_valid(dataset_id):
        raise ValueError("Invalid dataset id")

    dataset = get_datasets_collection().find_one({"_id": ObjectId(dataset_id), "ownerId": owner_id})
    if not dataset:
        raise ValueError("Dataset not found")
    return dataset


async def create_dataset(owner_id: str, dataset_name: str, category: str, description: str, dataset_file: UploadFile) -> dict:
    if not dataset_file.filename or not dataset_file.filename.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid4().hex}_{dataset_file.filename}"
    file_path = UPLOADS_DIR / unique_name

    content = await dataset_file.read()
    file_path.write_bytes(content)

    dataframe = read_csv_file(file_path)
    stats = build_basic_stats(dataframe)
    now = datetime.now(timezone.utc)

    dataset_document = {
        "datasetName": dataset_name.strip(),
        "category": category.strip() or "General",
        "description": description.strip(),
        "fileName": dataset_file.filename,
        "filePath": str(file_path),
        "ownerId": owner_id,
        "rowCount": stats["rowCount"],
        "columnCount": stats["columnCount"],
        "columnNames": list(dataframe.columns),
        "createdAt": now,
        "updatedAt": now,
    }

    result = get_datasets_collection().insert_one(dataset_document)
    created = get_datasets_collection().find_one({"_id": result.inserted_id})

    return format_dataset(created)


def list_user_datasets(owner_id: str) -> list[dict]:
    datasets = get_datasets_collection().find({"ownerId": owner_id}).sort("createdAt", -1)
    return [format_dataset(dataset) for dataset in datasets]


def get_dataset_by_id(dataset_id: str, owner_id: str) -> dict:
    dataset = ensure_dataset_owner(dataset_id, owner_id)
    return format_dataset(dataset)


def delete_dataset(dataset_id: str, owner_id: str) -> None:
    dataset = ensure_dataset_owner(dataset_id, owner_id)
    file_path = dataset.get("filePath")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    get_datasets_collection().delete_one({"_id": dataset["_id"]})


def read_dataset_dataframe(dataset_id: str, owner_id: str):
    dataset = ensure_dataset_owner(dataset_id, owner_id)
    dataframe = read_csv_file(dataset["filePath"])
    return dataset, dataframe


def get_dataset_records(dataset_id: str, owner_id: str, params: dict) -> dict:
    dataset, dataframe = read_dataset_dataframe(dataset_id, owner_id)

    search = (params.get("search") or "").strip().lower()
    filter_column = (params.get("filterColumn") or "").strip()
    filter_operator = (params.get("filterOperator") or "contains").strip()
    filter_value = (params.get("filterValue") or "").strip()
    sort_by = (params.get("sortBy") or "").strip()
    sort_order = (params.get("sortOrder") or "asc").strip().lower()
    page = max(int(params.get("page", 1)), 1)
    limit = min(max(int(params.get("limit", 10)), 1), 100)

    filtered_df = dataframe.copy()

    if search:
        mask = filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(search, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]

    if filter_column and filter_column in filtered_df.columns:
        series = filtered_df[filter_column]
        if filter_operator == "contains":
            filtered_df = filtered_df[series.astype(str).str.contains(filter_value, case=False, na=False)]
        elif filter_operator == "equals":
            filtered_df = filtered_df[series.astype(str).str.lower() == filter_value.lower()]
        elif filter_operator in {"gt", "gte", "lt", "lte"}:
            numeric_series = series.astype(float)
            filter_number = float(filter_value)
            if filter_operator == "gt":
                filtered_df = filtered_df[numeric_series > filter_number]
            elif filter_operator == "gte":
                filtered_df = filtered_df[numeric_series >= filter_number]
            elif filter_operator == "lt":
                filtered_df = filtered_df[numeric_series < filter_number]
            elif filter_operator == "lte":
                filtered_df = filtered_df[numeric_series <= filter_number]
        elif filter_operator == "isEmpty":
            filtered_df = filtered_df[series.isna() | (series.astype(str).str.strip() == "")]
        elif filter_operator == "isNotEmpty":
            filtered_df = filtered_df[~series.isna() & (series.astype(str).str.strip() != "")]

    if sort_by and sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=sort_order != "desc", na_position="last")

    total_rows = int(len(filtered_df))
    total_pages = max((total_rows + limit - 1) // limit, 1)
    start_index = (page - 1) * limit
    page_df = filtered_df.iloc[start_index : start_index + limit]

    return {
        "dataset": format_dataset(dataset),
        "rows": dataframe_to_records(page_df),
        "pagination": {
            "page": page,
            "limit": limit,
            "totalRows": total_rows,
            "totalPages": total_pages,
        },
    }


def get_dataset_stats(dataset_id: str, owner_id: str, x_axis: str = "", y_axis: str = "") -> dict:
    _, dataframe = read_dataset_dataframe(dataset_id, owner_id)
    stats = build_basic_stats(dataframe)
    chart_data = build_chart_data(dataframe, x_axis=x_axis, y_axis=y_axis)
    return {
        "stats": stats,
        "chartData": chart_data,
    }


def get_dataset_summary(owner_id: str) -> dict:
    datasets = list_user_datasets(owner_id)
    total_records = sum(int(dataset.get("rowCount", 0)) for dataset in datasets)
    recent_uploads = len(datasets[:3])

    return {
        "totalDatasets": len(datasets),
        "totalRecords": total_records,
        "recentUploads": recent_uploads,
        "reportsGenerated": len(datasets),
    }


def save_cleaned_dataset(dataset_id: str, owner_id: str, dataframe) -> dict:
    dataset = ensure_dataset_owner(dataset_id, owner_id)
    save_dataframe_to_csv(dataframe, dataset["filePath"])

    stats = build_basic_stats(dataframe)
    update_data = {
        "rowCount": stats["rowCount"],
        "columnCount": stats["columnCount"],
        "columnNames": list(dataframe.columns),
        "updatedAt": datetime.now(timezone.utc),
    }
    get_datasets_collection().update_one({"_id": dataset["_id"]}, {"$set": update_data})
    updated = get_datasets_collection().find_one({"_id": dataset["_id"]})
    return format_dataset(updated)
