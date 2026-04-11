"""
Data API routes with RBAC authorization.

@MX:NOTE: Example routes demonstrating RBAC integration
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
import os
import uuid
import logging

from src.api.auth.decorators import require_permission
from src.api.auth.dependencies import get_current_user_with_role, authorize_endpoint
import csv
import io

logger = logging.getLogger(__name__)

# File upload configuration
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB maximum file size
MAX_FILE_SIZE_MB = MAX_FILE_SIZE / (1024 * 1024)  # For error messages

def _is_numeric(v: str) -> bool:
    try:
        float(v.strip())
        return True
    except ValueError:
        return False

def detect_kv(rows: list) -> bool:
    """
    Heuristic: k:v format if >50% of middle tokens (not first, not last)
    contain a colon across sampled rows.
    """
    sample = rows[:20]
    total = 0
    kv_count = 0

    for row in sample:
        if len(row) < 3: continue
        middle = row[1:-1]
        for item in middle:
            if item.strip():
                total += 1
                if ':' in item:
                    kv_count += 1

    return (kv_count / total) > 0.5 if total > 0 else False

router = APIRouter(prefix="/api/v1/data", tags=["Data"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the server for processing.

    Enforces maximum file size limit (500MB) to prevent DoS attacks.
    """
    import duckdb
    os.makedirs("uploads", exist_ok=True)

    # Check file size before reading content (prevents DoS via large files)
    # Use file.file which is a SpooledTemporaryFile that supports seeking
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position for normal reading

    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f">>> [FILE UPLOAD] Rejected file '{file.filename}': {file_size / (1024*1024):.1f}MB exceeds {MAX_FILE_SIZE_MB:.0f}MB limit"
        )
        raise HTTPException(
            status_code=413,  # Payload Too Large
            detail=f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB:.0f}MB). Please upload a smaller file or contact support for assistance."
        )

    logger.info(f">>> [FILE UPLOAD] Uploading '{file.filename}': {file_size / (1024*1024):.2f}MB")

    file_id = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join("uploads", file_id)

    # Read file content with size limit check
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        logger.error(
            f">>> [FILE UPLOAD] Size mismatch for '{file.filename}': reported {file_size} bytes, actual {len(content)} bytes"
        )
        raise HTTPException(
            status_code=413,
            detail=f"File content exceeds maximum allowed size ({MAX_FILE_SIZE_MB:.0f}MB)."
        )

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    logger.info(f">>> [FILE UPLOAD] Successfully saved to {file_path}")
        
    # Discover columns and row count after upload
    try:
        conn = duckdb.connect(database=':memory:')
        # Using DESCRIBE for columns and types
        desc_df = conn.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{file_path}')").df()
        columns = desc_df['column_name'].tolist()
        column_types = desc_df[['column_name', 'column_type']].to_dict(orient='records')
        row_count = conn.execute(f"SELECT COUNT(*) FROM read_csv_auto('{file_path}')").fetchone()[0]
        
        # Detect if it's KV format
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample_text = "".join([f.readline() for _ in range(25)])
            reader = csv.reader(io.StringIO(sample_text))
            sample_rows = [r for r in reader if r]
            is_kv = detect_kv(sample_rows)
            detected_format = "kv" if is_kv else "flat"
            
    except Exception as e:
        columns = []
        column_types = []
        row_count = 0
        detected_format = "flat"
        
    return {
        "file_id": file_id,
        "file_path": file_path, 
        "filename": file.filename,
        "available_columns": columns,
        "column_types": column_types,
        "total_rows": row_count,
        "detected_format": detected_format
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
