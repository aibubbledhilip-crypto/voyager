"""
Advanced analytics endpoints for cross-file data analysis
Handles queries that require aggregation across multiple files
"""
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import logging

from backend.database import get_db, User, UploadedFile
from backend.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/duplicates")
async def find_duplicates(
    column: str = QueryParam(..., description="Column name to check for duplicates (e.g., 'msisdn')"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find duplicate values across all uploaded files for a specific column
    Returns: list of duplicates with occurrence count and file names
    """
    try:
        # Get all uploaded files for this user (or all if no auth)
        query = db.query(UploadedFile).filter(UploadedFile.processing_status == 'completed')

        if current_user:
            query = query.filter(UploadedFile.user_id == current_user.id)

        files = query.all()

        if not files:
            return {
                "success": False,
                "error": "No files uploaded yet"
            }

        # Read all files and combine the specified column
        all_data = []

        for file_record in files:
            try:
                file_path = Path(file_record.file_path)

                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                # Read file based on type
                if file_record.file_type == 'csv':
                    df = pd.read_csv(file_path)
                elif file_record.file_type in ['xlsx', 'xls']:
                    df = pd.read_excel(file_path)
                else:
                    continue

                # Check if column exists
                if column not in df.columns:
                    logger.warning(f"Column '{column}' not found in {file_record.filename}")
                    continue

                # Add file info to each row
                df['_source_file'] = file_record.filename
                all_data.append(df[[column, '_source_file']])

            except Exception as e:
                logger.error(f"Error reading {file_record.filename}: {str(e)}")
                continue

        if not all_data:
            return {
                "success": False,
                "error": f"Column '{column}' not found in any files"
            }

        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)

        # Find duplicates
        duplicates = combined_df[combined_df.duplicated(column, keep=False)].copy()

        if len(duplicates) == 0:
            return {
                "success": True,
                "total_duplicates": 0,
                "message": f"No duplicate values found in column '{column}'",
                "duplicates": []
            }

        # Group by the column value and aggregate
        duplicate_groups = duplicates.groupby(column).agg({
            '_source_file': lambda x: list(x)
        }).reset_index()

        duplicate_groups['occurrence_count'] = duplicate_groups['_source_file'].apply(len)
        duplicate_groups = duplicate_groups.sort_values('occurrence_count', ascending=False)

        # Format results
        results = []
        for _, row in duplicate_groups.iterrows():
            value = row[column]
            files = row['_source_file']
            count = row['occurrence_count']

            # Count occurrences per file
            file_counts = {}
            for file in files:
                file_counts[file] = file_counts.get(file, 0) + 1

            results.append({
                column: str(value),
                'total_occurrences': int(count),
                'file_count': len(file_counts),
                'files': [
                    {'filename': fname, 'count': cnt}
                    for fname, cnt in file_counts.items()
                ]
            })

        return {
            "success": True,
            "column": column,
            "total_duplicates": len(results),
            "total_files_analyzed": len(files),
            "duplicates": results
        }

    except Exception as e:
        logger.error(f"Error finding duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/column-values")
async def get_unique_values(
    column: str = QueryParam(..., description="Column name"),
    limit: int = QueryParam(100, description="Max number of unique values to return"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get unique values and their counts for a specific column across all files
    """
    try:
        query = db.query(UploadedFile).filter(UploadedFile.processing_status == 'completed')

        if current_user:
            query = query.filter(UploadedFile.user_id == current_user.id)

        files = query.all()
        all_values = []

        for file_record in files:
            try:
                file_path = Path(file_record.file_path)

                if not file_path.exists():
                    continue

                if file_record.file_type == 'csv':
                    df = pd.read_csv(file_path)
                elif file_record.file_type in ['xlsx', 'xls']:
                    df = pd.read_excel(file_path)
                else:
                    continue

                if column in df.columns:
                    all_values.extend(df[column].dropna().tolist())

            except Exception as e:
                logger.error(f"Error reading {file_record.filename}: {str(e)}")
                continue

        if not all_values:
            return {
                "success": False,
                "error": f"Column '{column}' not found in any files"
            }

        # Count unique values
        value_counts = pd.Series(all_values).value_counts().head(limit)

        results = [
            {"value": str(val), "count": int(count)}
            for val, count in value_counts.items()
        ]

        return {
            "success": True,
            "column": column,
            "total_unique_values": len(value_counts),
            "values": results
        }

    except Exception as e:
        logger.error(f"Error getting unique values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregate")
async def aggregate_data(
    column: str = QueryParam(..., description="Column to aggregate"),
    operation: str = QueryParam("count", description="Operation: count, sum, mean, min, max"),
    group_by: Optional[str] = QueryParam(None, description="Column to group by"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform aggregation operations across all files
    """
    try:
        query = db.query(UploadedFile).filter(UploadedFile.processing_status == 'completed')

        if current_user:
            query = query.filter(UploadedFile.user_id == current_user.id)

        files = query.all()
        all_data = []

        for file_record in files:
            try:
                file_path = Path(file_record.file_path)

                if not file_path.exists():
                    continue

                if file_record.file_type == 'csv':
                    df = pd.read_csv(file_path)
                elif file_record.file_type in ['xlsx', 'xls']:
                    df = pd.read_excel(file_path)
                else:
                    continue

                if column in df.columns:
                    if group_by and group_by in df.columns:
                        all_data.append(df[[column, group_by]])
                    else:
                        all_data.append(df[[column]])

            except Exception as e:
                logger.error(f"Error reading {file_record.filename}: {str(e)}")
                continue

        if not all_data:
            return {
                "success": False,
                "error": f"Column '{column}' not found in any files"
            }

        combined_df = pd.concat(all_data, ignore_index=True)

        # Perform aggregation
        if group_by and group_by in combined_df.columns:
            if operation == 'count':
                result = combined_df.groupby(group_by)[column].count()
            elif operation == 'sum':
                result = combined_df.groupby(group_by)[column].sum()
            elif operation == 'mean':
                result = combined_df.groupby(group_by)[column].mean()
            elif operation == 'min':
                result = combined_df.groupby(group_by)[column].min()
            elif operation == 'max':
                result = combined_df.groupby(group_by)[column].max()
            else:
                raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")

            results = [
                {"group": str(idx), "value": float(val) if pd.notna(val) else None}
                for idx, val in result.items()
            ]
        else:
            if operation == 'count':
                value = int(combined_df[column].count())
            elif operation == 'sum':
                value = float(combined_df[column].sum())
            elif operation == 'mean':
                value = float(combined_df[column].mean())
            elif operation == 'min':
                value = float(combined_df[column].min()) if pd.api.types.is_numeric_dtype(combined_df[column]) else str(combined_df[column].min())
            elif operation == 'max':
                value = float(combined_df[column].max()) if pd.api.types.is_numeric_dtype(combined_df[column]) else str(combined_df[column].max())
            else:
                raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")

            results = [{"value": value}]

        return {
            "success": True,
            "column": column,
            "operation": operation,
            "group_by": group_by,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error performing aggregation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns")
async def list_all_columns(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all unique column names across all uploaded files
    """
    try:
        query = db.query(UploadedFile).filter(UploadedFile.processing_status == 'completed')

        if current_user:
            query = query.filter(UploadedFile.user_id == current_user.id)

        files = query.all()
        all_columns = {}

        for file_record in files:
            try:
                file_path = Path(file_record.file_path)

                if not file_path.exists():
                    continue

                if file_record.file_type == 'csv':
                    df = pd.read_csv(file_path, nrows=1)
                elif file_record.file_type in ['xlsx', 'xls']:
                    df = pd.read_excel(file_path, nrows=1)
                else:
                    continue

                for col in df.columns:
                    if col not in all_columns:
                        all_columns[col] = []
                    all_columns[col].append(file_record.filename)

            except Exception as e:
                logger.error(f"Error reading {file_record.filename}: {str(e)}")
                continue

        results = [
            {
                "column": col,
                "file_count": len(files),
                "files": files
            }
            for col, files in all_columns.items()
        ]

        return {
            "success": True,
            "total_columns": len(results),
            "columns": results
        }

    except Exception as e:
        logger.error(f"Error listing columns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
