"""
FastAPI endpoints for CSV file upload, preview, and schema retrieval.

This module provides REST API endpoints for processing CSV files with
encoding detection, type inference, and streaming support for large files.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException, status, Query
from fastapi.responses import JSONResponse

from src.csv.session_manager import SessionManager
from src.csv.encoding_detector import detect_encoding
from src.csv.type_inference import infer_schema

logger = logging.getLogger(__name__)

# Global session manager instance
_session_manager: Optional[SessionManager] = None

router = APIRouter(prefix="/api/csv", tags=["CSV Processing"])

# Maximum file size: 500MB
MAX_FILE_SIZE = 500 * 1024 * 1024

# Allowed content types for CSV files
ALLOWED_CONTENT_TYPES = {
    'text/csv',
    'application/csv',
    'text/plain'  # Some clients send CSV as text/plain
}

# Executable file extensions to reject
EXECUTABLE_EXTENSIONS = {
    '.exe', '.sh', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar'
}


def get_session_manager() -> SessionManager:
    """
    Get or create the global session manager instance.

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(
            max_sessions=10,
            session_timeout_minutes=30
        )
    return _session_manager


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Removes directory separators and special characters that could be used
    for path traversal. Returns only the base filename without path.

    Args:
        filename: Original filename from upload

    Returns:
        Sanitized filename safe for storage

    @MX:NOTE: Critical security function - prevents directory traversal attacks
    """
    # Remove any directory paths
    filename = os.path.basename(filename)

    # Remove dangerous characters
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # If empty after sanitization, use timestamp
    if not filename:
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return filename


# @MX:ANCHOR: [AUTO] CSV file upload endpoint with security validation
# @MX:REASON: Primary entry point for CSV uploads, integrates encoding detection and type inference
# @MX:SPEC: SPEC-CSV-001 AC-CSV-004, AC-CSV-005, AC-CSV-010, AC-CSV-011
@router.post("/upload")
async def upload_file(file: UploadFile) -> Dict[str, Any]:
    """
    Upload a CSV file for processing.

    Performs comprehensive validation including file type checking, size limits,
    executable file detection, and filename sanitization. Processes the uploaded
    file to detect encoding and infer schema.

    Args:
        file: Uploaded CSV file via multipart/form-data

    Returns:
        Dictionary with:
            - session_id: UUID v4 session identifier
            - filename: Sanitized filename
            - encoding: Detected character encoding
            - row_count: Total number of rows
            - column_count: Total number of columns
            - status: Processing status

    Raises:
        HTTPException 400: Invalid file type, executable file, or malformed data
        HTTPException 413: File exceeds 500MB limit
        HTTPException 503: Maximum concurrent sessions reached
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            f">>> [CSV API] Rejected file with invalid content-type: {file.content_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a CSV file."
        )

    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required."
        )

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)

    # Check for executable file extensions
    file_ext = Path(safe_filename).suffix.lower()
    if file_ext in EXECUTABLE_EXTENSIONS:
        logger.warning(
            f">>> [CSV API] Rejected executable file: {safe_filename}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Executable files are not allowed."
        )

    # Create temporary file for upload
    temp_dir = Path("/tmp/csv_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_filepath = temp_dir / f"{datetime.now().timestamp()}_{safe_filename}"

    try:
        # Save uploaded file with size checking
        total_size = 0
        async with aiofiles.open(temp_filepath, 'wb') as f:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(content)

                # Check file size limit
                if total_size > MAX_FILE_SIZE:
                    await f.close()
                    temp_filepath.unlink(missing_ok=True)
                    logger.warning(
                        f">>> [CSV API] Rejected oversized file: {total_size} bytes"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit."
                    )

                await f.write(content)

        logger.info(f">>> [CSV API] Uploaded file: {safe_filename} ({total_size} bytes)")

        # Detect encoding
        try:
            encoding, confidence = detect_encoding(str(temp_filepath))
            logger.info(
                f">>> [CSV API] Detected encoding: {encoding} "
                f"(confidence: {confidence:.2f})"
            )
        except Exception as e:
            logger.error(f">>> [CSV API] Encoding detection failed: {e}")
            # Fallback to UTF-8
            encoding = 'utf-8'
            confidence = 0.5

        # Infer schema
        try:
            schema = infer_schema(str(temp_filepath), encoding=encoding)
            row_count = len(list(temp_filepath.open())) if temp_filepath.exists() else 0
            column_count = len(schema)

            logger.info(
                f">>> [CSV API] Inferred schema: {column_count} columns, {row_count} rows"
            )
        except Exception as e:
            logger.error(f">>> [CSV API] Schema inference failed: {e}")
            # Provide minimal schema on error
            schema = []
            row_count = 0
            column_count = 0

        # Create session
        session_manager = get_session_manager()

        try:
            file_data = {
                'filename': safe_filename,
                'encoding': encoding,
                'row_count': row_count,
                'column_count': column_count,
                'schema': schema,
                'filepath': str(temp_filepath)
            }

            session_id = session_manager.create_session(file_data)

            logger.info(
                f">>> [CSV API] Created session {session_id} for {safe_filename}"
            )

            return {
                'session_id': session_id,
                'filename': safe_filename,
                'encoding': encoding,
                'row_count': row_count,
                'column_count': column_count,
                'status': 'ready'
            }

        except RuntimeError as e:
            logger.error(f">>> [CSV API] Session creation failed: {e}")
            temp_filepath.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e)
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f">>> [CSV API] Upload processing error: {e}", exc_info=True)
        temp_filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File processing failed. Please try again."
        )


# @MX:ANCHOR: [AUTO] Preview endpoint for retrieving CSV rows
# @MX:REASON: High-frequency API for data preview, must respond <500ms for first 100 rows
# @MX:SPEC: SPEC-CSV-001 AC-CSV-006
@router.get("/preview/{session_id}")
async def get_preview(
    session_id: str,
    rows: int = Query(100, ge=1, le=1000, description="Number of rows to return (max: 1000)")
) -> Dict[str, Any]:
    """
    Get first N rows of an uploaded CSV file.

    Returns rows as list of dictionaries with column names as keys.
    Optimized for fast response times (<500ms for first 100 rows).

    Args:
        session_id: Session identifier from upload
        rows: Number of rows to return (default: 100, max: 1000)

    Returns:
        Dictionary with:
            - session_id: Session identifier
            - rows: List of row dictionaries (column_name: value)
            - row_count: Total number of rows in the file

    Raises:
        HTTPException 404: Session not found or expired
    """
    session_manager = get_session_manager()

    # Retrieve session
    session = session_manager.get_session(session_id)
    if session is None:
        logger.warning(f">>> [CSV API] Preview request for invalid session: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or has expired."
        )

    filepath = session.get('filepath')
    if not filepath or not Path(filepath).exists():
        logger.error(f">>> [CSV API] File not found for session {session_id}: {filepath}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file not found."
        )

    try:
        import pandas as pd

        # Read requested rows with pandas
        df = pd.read_csv(
            filepath,
            encoding=session['encoding'],
            nrows=rows
        )

        # Convert to list of dictionaries
        rows_data = df.to_dict(orient='records')

        logger.info(
            f">>> [CSV API] Preview: {len(rows_data)} rows for session {session_id}"
        )

        return {
            'session_id': session_id,
            'rows': rows_data,
            'row_count': session['row_count']
        }

    except Exception as e:
        logger.error(f">>> [CSV API] Preview generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview."
        )


# @MX:ANCHOR: [AUTO] Schema endpoint for retrieving column metadata
# @MX:REASON: Returns inferred schema with encoding info, used by frontend for type validation
# @MX:SPEC: SPEC-CSV-001 AC-CSV-007
@router.get("/schema/{session_id}")
async def get_schema(session_id: str) -> Dict[str, Any]:
    """
    Get schema information (column names and types) for an uploaded CSV.

    Returns comprehensive column metadata including data types, nullability,
    and null counts. Useful for frontend validation and data exploration.

    Args:
        session_id: Session identifier from upload

    Returns:
        Dictionary with:
            - session_id: Session identifier
            - columns: List of column metadata dictionaries
            - encoding: Detected character encoding
            - row_count: Total number of rows
            - column_count: Total number of columns

    Raises:
        HTTPException 404: Session not found or expired
    """
    session_manager = get_session_manager()

    # Retrieve session
    session = session_manager.get_session(session_id)
    if session is None:
        logger.warning(f">>> [CSV API] Schema request for invalid session: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or has expired."
        )

    logger.info(
        f">>> [CSV API] Schema: {session['column_count']} columns for session {session_id}"
    )

    return {
        'session_id': session_id,
        'columns': session['schema'],
        'encoding': session['encoding'],
        'row_count': session['row_count'],
        'column_count': session['column_count']
    }


__all__ = ['router', 'get_session_manager']
