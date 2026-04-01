"""
Data API routes with RBAC authorization.

@MX:NOTE: Example routes demonstrating RBAC integration
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
import os
import uuid

from src.api.auth.decorators import require_permission
from src.api.auth.dependencies import get_current_user_with_role, authorize_endpoint

router = APIRouter(prefix="/api/v1/data", tags=["Data"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the server for processing."""
    import duckdb
    os.makedirs("uploads", exist_ok=True)
    file_id = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join("uploads", file_id)
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)
        
    # Discover columns and row count after upload
    try:
        conn = duckdb.connect(database=':memory:')
        # Using DESCRIBE for columns and COUNT for rows
        columns = conn.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{file_path}')").df()['column_name'].tolist()
        row_count = conn.execute(f"SELECT COUNT(*) FROM read_csv_auto('{file_path}')").fetchone()[0]
    except Exception as e:
        columns = []
        row_count = 0
        
    return {
        "file_id": file_id, 
        "file_path": file_path, 
        "filename": file.filename,
        "available_columns": columns,
        "total_rows": row_count
    }


class DatasetResponse(BaseModel):
    """Dataset response model."""

    dataset_id: str
    data: Dict[str, Any]
    created_at: str


@router.get("/datasets/{dataset_id}")
@require_permission("data:read")
async def read_dataset(
    dataset_id: str,
    current_user: Dict = Depends(get_current_user_with_role),
):
    """
    Read dataset endpoint.

    Args:
        dataset_id: Dataset ID
        current_user: Current user with role

    Returns:
        Dataset data
    """
    # Mock dataset data
    dataset = {
        "dataset_id": dataset_id,
        "data": {"sample": "data"},
        "created_at": "2024-01-01",
    }

    return dataset


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a file from the server."""
    from fastapi.responses import FileResponse
    
    # Check downloads folder first (for exports/reports)
    file_path = os.path.join("downloads", filename)
    if not os.path.exists(file_path):
        # Fallback to uploads folder (for source data)
        file_path = os.path.join("uploads", filename)
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    media_type = 'application/octet-stream'
    if filename.endswith('.pdf'): media_type = 'application/pdf'
    elif filename.endswith('.md'): media_type = 'text/markdown'
    elif filename.endswith('.csv'): media_type = 'text/csv'
    
    # Return file as a download
    return FileResponse(
        path=file_path,
        filename=filename.split('_', 2)[-1] if '_' in filename else filename,
        media_type=media_type
    )

@router.post("/datasets")
@require_permission("data:write")
async def write_dataset(
    dataset: Dict[str, Any],
    current_user: Dict = Depends(get_current_user_with_role),
):
    """
    Write dataset endpoint.

    Args:
        dataset: Dataset data
        current_user: Current user with role

    Returns:
        Created dataset info
    """
    # Mock creation
    created_id = "dataset-123"
    created_at = "2024-01-01"

    return {"dataset_id": created_id, "created_at": created_at}
