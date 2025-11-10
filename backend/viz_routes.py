"""
Visualization API routes for advanced charts and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
from pathlib import Path

from backend.database import get_db, User, UploadedFile
from backend.auth import get_current_user
from backend.visualizations import DataVisualizer

router = APIRouter(prefix="/visualize", tags=["visualizations"])
visualizer = DataVisualizer()


# Pydantic models
class VisualizationRequest(BaseModel):
    file_id: int
    chart_type: str  # 'summary', 'trend', 'comparison', etc.
    options: Optional[dict] = None


class ChartExportRequest(BaseModel):
    chart_json: str
    format: str = 'png'  # png, jpg, pdf, svg


# Routes
@router.post("/dashboard/{file_id}")
async def create_dashboard(
    file_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a comprehensive visualization dashboard for a file
    Works with or without authentication
    """
    # Get file info
    query = db.query(UploadedFile).filter(UploadedFile.id == file_id)

    # If authenticated, filter by user
    if current_user:
        query = query.filter(UploadedFile.user_id == current_user.id)

    file_record = query.first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Read the file
    try:
        file_path = Path(file_record.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Read based on file type
        if file_record.file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_record.file_type in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Create dashboard
        dashboard = visualizer.create_summary_dashboard(df, file_record.filename)

        return dashboard

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating dashboard: {str(e)}")


@router.post("/trend")
async def create_trend_chart(
    file_id: int,
    x_column: str,
    y_column: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a trend analysis chart"""
    # Get file
    query = db.query(UploadedFile).filter(UploadedFile.id == file_id)
    if current_user:
        query = query.filter(UploadedFile.user_id == current_user.id)

    file_record = query.first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path = Path(file_record.file_path)

        if file_record.file_type == 'csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        result = visualizer.create_trend_analysis(df, x_column, y_column)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparison")
async def create_comparison_chart(
    file_ids: List[int],
    x_field: str,
    y_fields: List[str],
    chart_type: str = 'bar',
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a comparison chart across multiple files"""
    # Get files
    query = db.query(UploadedFile).filter(UploadedFile.id.in_(file_ids))
    if current_user:
        query = query.filter(UploadedFile.user_id == current_user.id)

    files = query.all()

    if len(files) != len(file_ids):
        raise HTTPException(status_code=404, detail="Some files not found")

    try:
        # Combine data from all files
        all_data = []

        for file_record in files:
            file_path = Path(file_record.file_path)

            if file_record.file_type == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Add source file column
            df['_source_file'] = file_record.filename
            all_data.append(df)

        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)

        # Create comparison chart
        result = visualizer.create_comparison_chart(
            combined_df.to_dict('records'),
            x_field,
            y_fields,
            chart_type
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_visualization_files(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List available files for visualization"""
    query = db.query(UploadedFile).filter(UploadedFile.processing_status == 'completed')

    if current_user:
        query = query.filter(UploadedFile.user_id == current_user.id)

    files = query.offset(skip).limit(limit).all()

    return [
        {
            'id': f.id,
            'filename': f.filename,
            'rows': f.rows_count,
            'columns': f.columns_count,
            'upload_date': f.upload_date.isoformat() if f.upload_date else None
        }
        for f in files
    ]


@router.post("/export")
async def export_chart(
    request: ChartExportRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Export a chart as an image"""
    try:
        img_bytes = visualizer.export_chart_as_image(request.chart_json, request.format)

        if not img_bytes:
            raise HTTPException(status_code=500, detail="Failed to export chart")

        media_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'pdf': 'application/pdf',
            'svg': 'image/svg+xml'
        }

        media_type = media_type_map.get(request.format, 'application/octet-stream')

        return Response(
            content=img_bytes,
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="chart.{request.format}"'
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns/{file_id}")
async def get_file_columns(
    file_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get column names and types for a file"""
    query = db.query(UploadedFile).filter(UploadedFile.id == file_id)

    if current_user:
        query = query.filter(UploadedFile.user_id == current_user.id)

    file_record = query.first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path = Path(file_record.file_path)

        if file_record.file_type == 'csv':
            df = pd.read_csv(file_path, nrows=5)
        else:
            df = pd.read_excel(file_path, nrows=5)

        columns_info = [
            {
                'name': col,
                'type': str(df[col].dtype),
                'sample_values': df[col].head(3).tolist()
            }
            for col in df.columns
        ]

        return {
            'success': True,
            'columns': columns_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
