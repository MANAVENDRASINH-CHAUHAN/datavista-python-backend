from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_csv_file(file_path: str | Path) -> pd.DataFrame:
    dataframe = pd.read_csv(file_path)
    dataframe = dataframe.where(pd.notnull(dataframe), None)
    return dataframe


def save_dataframe_to_csv(dataframe: pd.DataFrame, file_path: str | Path) -> None:
    dataframe.to_csv(file_path, index=False)


def dataframe_preview(dataframe: pd.DataFrame, limit: int = 5) -> list[dict]:
    return dataframe.head(limit).to_dict(orient="records")


def normalize_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def dataframe_to_records(dataframe: pd.DataFrame) -> list[dict]:
    records = dataframe.to_dict(orient="records")
    normalized_records = []
    for row in records:
        normalized_records.append({column: normalize_value(value) for column, value in row.items()})
    return normalized_records
