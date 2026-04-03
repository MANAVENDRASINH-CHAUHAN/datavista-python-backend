from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.middleware.auth_middleware import get_current_user
from app.services.dataset_service import (
    create_dataset,
    delete_dataset,
    get_dataset_by_id,
    get_dataset_records,
    get_dataset_stats,
    get_dataset_summary,
    list_user_datasets,
)

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.get("/summary")
def dataset_summary(current_user: dict = Depends(get_current_user)) -> dict:
    summary = get_dataset_summary(current_user["id"])
    return {"success": True, "message": "Dataset summary fetched successfully", "data": {"summary": summary}, "summary": summary}


@router.post("")
async def upload_dataset(
    datasetName: str = Form(...),
    category: str = Form("General"),
    description: str = Form(""),
    datasetFile: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        dataset = await create_dataset(current_user["id"], datasetName, category, description, datasetFile)
        return {"success": True, "message": "Dataset uploaded successfully", "data": {"dataset": dataset}, "dataset": dataset}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/mine")
def my_datasets(current_user: dict = Depends(get_current_user)) -> dict:
    datasets = list_user_datasets(current_user["id"])
    return {"success": True, "message": "Datasets fetched successfully", "data": {"datasets": datasets}, "datasets": datasets}


@router.get("/{dataset_id}")
def dataset_details(dataset_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        dataset = get_dataset_by_id(dataset_id, current_user["id"])
        return {"success": True, "message": "Dataset fetched successfully", "data": {"dataset": dataset}, "dataset": dataset}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.delete("/{dataset_id}")
def remove_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        delete_dataset(dataset_id, current_user["id"])
        return {"success": True, "message": "Dataset deleted successfully", "data": None}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{dataset_id}/download")
def download_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    try:
        dataset = get_dataset_by_id(dataset_id, current_user["id"])
        return FileResponse(
            path=dataset["filePath"],
            filename=Path(dataset["fileName"]).name,
            media_type="text/csv",
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{dataset_id}/records")
def dataset_records(
    dataset_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    search: str = "",
    filterColumn: str = "",
    filterOperator: str = "contains",
    filterValue: str = "",
    sortBy: str = "",
    sortOrder: str = "asc",
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        result = get_dataset_records(
            dataset_id,
            current_user["id"],
            {
                "page": page,
                "limit": limit,
                "search": search,
                "filterColumn": filterColumn,
                "filterOperator": filterOperator,
                "filterValue": filterValue,
                "sortBy": sortBy,
                "sortOrder": sortOrder,
            },
        )
        return {
            "success": True,
            "message": "Dataset records fetched successfully",
            "data": result,
            "rows": result["rows"],
            "pagination": result["pagination"],
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to process records: {error}") from error


@router.get("/{dataset_id}/stats")
def dataset_stats(
    dataset_id: str,
    xAxis: str = "",
    yAxis: str = "",
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        result = get_dataset_stats(dataset_id, current_user["id"], x_axis=xAxis, y_axis=yAxis)
        return {
            "success": True,
            "message": "Dataset stats fetched successfully",
            "data": result,
            "stats": result["stats"],
            "chartData": result["chartData"],
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
