from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetResponse(BaseModel):
    _id: str
    datasetName: str
    category: str
    description: str
    fileName: str
    filePath: str
    rowCount: int
    columnCount: int
    columnNames: list[str]
    ownerId: str
    createdAt: datetime
    updatedAt: datetime


class RecordsQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    search: str = ""
    filterColumn: str = ""
    filterOperator: str = "contains"
    filterValue: str = ""
    sortBy: str = ""
    sortOrder: str = "asc"


class StatsResponse(BaseModel):
    rowCount: int
    columnCount: int
    missingValues: list[dict[str, Any]]
    duplicateRows: int
    numericSummary: dict[str, dict[str, Any]]
    columnTypes: list[dict[str, str]]
    numericColumns: list[str]
