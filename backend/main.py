"""
FastAPI application for Intelligent RAG Data Analysis Tool
"""
import logging
import shutil
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import settings
from backend.rag_engine import RAGEngine
from backend.database import init_db, get_db, User, UploadedFile as DBUploadedFile
from backend.auth import get_current_user, init_admin_user
from backend.auth_routes import router as auth_router
from backend.viz_routes import router as viz_router
from backend.analytics_routes import router as analytics_router
from backend.query_router import query_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RAG engine instance
rag_engine: Optional[RAGEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global rag_engine

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Create admin user
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        init_admin_user(db)
    finally:
        db.close()

    # Initialize RAG engine
    logger.info("Initializing RAG Engine...")
    try:
        rag_engine = RAGEngine()
        logger.info("RAG Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Engine: {str(e)}")
        raise

    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Intelligent RAG Data Analysis Tool",
    description="AI-powered data analysis tool for Excel and CSV files using RAG with authentication and advanced visualizations",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(viz_router)
app.include_router(analytics_router)


# Pydantic models
class QueryRequest(BaseModel):
    question: str
    return_sources: bool = True


class QueryResponse(BaseModel):
    success: bool
    question: str
    answer: str
    sources: Optional[List[dict]] = None
    error: Optional[str] = None


class FileUploadResponse(BaseModel):
    success: bool
    file_name: str
    chunks_created: Optional[int] = None
    insights: Optional[dict] = None
    error: Optional[str] = None


class DataOverviewResponse(BaseModel):
    total_files: int
    total_chunks: int
    files: List[dict]


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - serves the web GUI"""
    static_index = Path(__file__).parent.parent / "static" / "index.html"
    if static_index.exists():
        return FileResponse(static_index)
    return {
        "message": "Intelligent RAG Data Analysis Tool",
        "version": "1.0.0",
        "docs": "/docs",
        "gui": "Install GUI dependencies and restart to access the web interface"
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "Intelligent RAG Data Analysis Tool - API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_engine_initialized": rag_engine is not None
    }


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download exported CSV files from analytics
    """
    try:
        # Sanitize filename to prevent directory traversal
        safe_filename = Path(filename).name
        file_path = Path("./data/exports") / safe_filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Verify it's in the exports directory (security check)
        if not file_path.resolve().is_relative_to(Path("./data/exports").resolve()):
            raise HTTPException(status_code=403, detail="Access denied")

        return FileResponse(
            path=str(file_path),
            filename=safe_filename,
            media_type="text/csv"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a single Excel or CSV file for analysis
    Works with or without authentication (multi-tenancy aware)
    """
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")

        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in {'.csv', '.xlsx', '.xls'}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported types: .csv, .xlsx, .xls"
            )

        # Determine storage path (user-specific if authenticated)
        if current_user:
            from backend.auth import get_user_tenant
            tenant = get_user_tenant(db, current_user)
            tenant_path = Path(tenant.storage_path)
            tenant_path.mkdir(parents=True, exist_ok=True)
            upload_path = tenant_path / file.filename
        else:
            upload_path = Path(settings.upload_dir) / file.filename

        # Save uploaded file
        file_size = 0
        with upload_path.open("wb") as buffer:
            content = file.file.read()
            file_size = len(content)
            buffer.write(content)

        logger.info(f"Saved uploaded file: {file.filename}")

        # Process the file
        result = rag_engine.add_file(str(upload_path))

        # Track in database (always, for both authenticated and unauthenticated users)
        if result["success"]:
            insights = result.get("insights", {})

            # Get tenant info if authenticated
            tenant_id = None
            user_id = None
            if current_user:
                from backend.auth import get_user_tenant
                tenant = get_user_tenant(db, current_user)
                tenant_id = tenant.id
                user_id = current_user.id

            db_file = DBUploadedFile(
                filename=file.filename,
                original_filename=file.filename,
                file_path=str(upload_path),
                file_size=file_size,
                file_type=file_ext.replace('.', ''),
                user_id=user_id,
                tenant_id=tenant_id,
                rows_count=insights.get('shape', {}).get('rows'),
                columns_count=insights.get('shape', {}).get('columns'),
                chunks_created=result.get('chunks_created'),
                processing_status='completed'
            )
            db.add(db_file)
            db.commit()
            logger.info(f"Tracked file in database: {file.filename}")

        if result["success"]:
            return FileUploadResponse(**result)
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple Excel or CSV files for analysis
    Supports batch upload of 50+ files
    Works with or without authentication (multi-tenancy aware)
    """
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")

        # Determine storage path
        if current_user:
            from backend.auth import get_user_tenant
            tenant = get_user_tenant(db, current_user)
            tenant_path = Path(tenant.storage_path)
            tenant_path.mkdir(parents=True, exist_ok=True)
            storage_dir = tenant_path
        else:
            storage_dir = Path(settings.upload_dir)

        results = []
        saved_files = []
        file_metadata = []  # Track file info for database

        # Save all uploaded files
        for file in files:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in {'.csv', '.xlsx', '.xls'}:
                results.append(FileUploadResponse(
                    success=False,
                    file_name=file.filename,
                    error=f"Unsupported file type: {file_ext}"
                ))
                continue

            upload_path = storage_dir / file.filename  # Use storage_dir instead of hardcoded path
            file_size = 0
            with upload_path.open("wb") as buffer:
                content = file.file.read()
                file_size = len(content)
                buffer.write(content)

            saved_files.append(str(upload_path))
            file_metadata.append({
                'filename': file.filename,
                'path': str(upload_path),
                'size': file_size,
                'type': file_ext.replace('.', '')
            })
            logger.info(f"Saved uploaded file: {file.filename}")

        # Process all saved files
        processing_results = rag_engine.add_multiple_files(saved_files)

        # Get tenant info if authenticated (for database tracking)
        tenant_id = None
        user_id = None
        if current_user:
            from backend.auth import get_user_tenant
            tenant = get_user_tenant(db, current_user)
            tenant_id = tenant.id
            user_id = current_user.id

        # Track all files in database and prepare results
        for i, result in enumerate(processing_results):
            results.append(FileUploadResponse(**result))

            # Track in database if processing was successful
            if result["success"] and i < len(file_metadata):
                metadata = file_metadata[i]
                insights = result.get("insights", {})

                db_file = DBUploadedFile(
                    filename=metadata['filename'],
                    original_filename=metadata['filename'],
                    file_path=metadata['path'],
                    file_size=metadata['size'],
                    file_type=metadata['type'],
                    user_id=user_id,
                    tenant_id=tenant_id,
                    rows_count=insights.get('shape', {}).get('rows'),
                    columns_count=insights.get('shape', {}).get('columns'),
                    chunks_created=result.get('chunks_created'),
                    processing_status='completed'
                )
                db.add(db_file)

        # Commit all database records at once
        db.commit()
        logger.info(f"Processed and tracked {len(files)} files in database")
        return results

    except Exception as e:
        logger.error(f"Error uploading multiple files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_data(
    request: QueryRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Intelligent query endpoint that automatically routes to RAG or Analytics
    based on query intent detection
    """
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")

        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        question = request.question.strip()

        # Detect query intent
        intent = query_router.detect_intent(question)
        logger.info(f"Query intent detected: {intent['type']} (confidence: {intent.get('confidence', 'unknown')})")

        # Route based on intent
        if intent['type'] == 'duplicate':
            # Call analytics duplicates endpoint internally
            from backend.analytics_routes import find_duplicates

            column = intent.get('column', 'msisdn')
            analytics_result = await find_duplicates(
                column=column,
                current_user=current_user,
                db=db
            )

            # Format as natural language
            answer = query_router.format_analytics_response(
                'duplicate',
                analytics_result,
                question
            )

            return QueryResponse(
                success=True,
                question=question,
                answer=answer,
                sources=[{
                    "content": f"Analytics: Duplicate detection on column '{column}'",
                    "metadata": {
                        "query_type": "analytics",
                        "intent": "duplicate_detection",
                        "column": column
                    }
                }] if request.return_sources else None
            )

        elif intent['type'] == 'unique':
            # Call analytics unique values endpoint
            from backend.analytics_routes import get_unique_values

            column = intent.get('column', 'msisdn')
            analytics_result = await get_unique_values(
                column=column,
                limit=100,
                current_user=current_user,
                db=db
            )

            answer = query_router.format_analytics_response(
                'unique',
                analytics_result,
                question
            )

            return QueryResponse(
                success=True,
                question=question,
                answer=answer,
                sources=[{
                    "content": f"Analytics: Unique values for column '{column}'",
                    "metadata": {
                        "query_type": "analytics",
                        "intent": "unique_values",
                        "column": column
                    }
                }] if request.return_sources else None
            )

        elif intent['type'] == 'aggregate':
            # Call analytics aggregate endpoint
            from backend.analytics_routes import aggregate_data

            column = intent.get('column')
            operation = intent.get('operation', 'count')
            group_by = intent.get('group_by')

            if not column:
                # Fall back to RAG if we can't determine column
                result = rag_engine.query(question, request.return_sources)
                if result["success"]:
                    return QueryResponse(**result)
                else:
                    raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

            analytics_result = await aggregate_data(
                column=column,
                operation=operation,
                group_by=group_by,
                current_user=current_user,
                db=db
            )

            answer = query_router.format_analytics_response(
                'aggregate',
                analytics_result,
                question
            )

            return QueryResponse(
                success=True,
                question=question,
                answer=answer,
                sources=[{
                    "content": f"Analytics: {operation} of {column}" + (f" by {group_by}" if group_by else ""),
                    "metadata": {
                        "query_type": "analytics",
                        "intent": "aggregation",
                        "operation": operation,
                        "column": column,
                        "group_by": group_by
                    }
                }] if request.return_sources else None
            )

        elif intent['type'] == 'metadata':
            # Get overview data
            logger.info("Retrieving metadata overview")
            overview = rag_engine.get_data_overview()

            answer = query_router.format_analytics_response(
                'metadata',
                overview,
                question
            )

            return QueryResponse(
                success=True,
                question=question,
                answer=answer,
                sources=[{
                    "content": f"Metadata: Data overview with {overview.get('total_files', 0)} files",
                    "metadata": {
                        "query_type": "metadata",
                        "intent": "overview",
                        "total_files": overview.get('total_files', 0),
                        "total_chunks": overview.get('total_chunks', 0)
                    }
                }] if request.return_sources else None
            )

        elif intent['type'] == 'search':
            # Call analytics search endpoint
            from backend.analytics_routes import search_value

            column = intent.get('column', 'msisdn')
            value = intent.get('value', '')

            logger.info(f"Searching for {column}={value} across all files")

            analytics_result = await search_value(
                column=column,
                value=value,
                current_user=current_user,
                db=db
            )

            answer = query_router.format_analytics_response(
                'search',
                analytics_result,
                question
            )

            return QueryResponse(
                success=True,
                question=question,
                answer=answer,
                sources=[{
                    "content": f"Analytics: Search for {column}={value}",
                    "metadata": {
                        "query_type": "analytics",
                        "intent": "search",
                        "column": column,
                        "value": value,
                        "total_matches": analytics_result.get('total_matches', 0)
                    }
                }] if request.return_sources else None
            )

        elif intent['type'] == 'column_comparison':
            # Call analytics column comparison endpoint
            from backend.analytics_routes import compare_duplicates_across_columns

            logger.info("Comparing duplicates across all columns")

            analytics_result = await compare_duplicates_across_columns(
                current_user=current_user,
                db=db
            )

            answer = query_router.format_analytics_response(
                'column_comparison',
                analytics_result,
                question
            )

            return QueryResponse(
                success=True,
                question=question,
                answer=answer,
                sources=[{
                    "content": f"Analytics: Column duplicate comparison across {analytics_result.get('total_columns_analyzed', 0)} columns",
                    "metadata": {
                        "query_type": "analytics",
                        "intent": "column_comparison",
                        "most_duplicated_column": analytics_result.get('most_duplicated_column'),
                        "total_columns": analytics_result.get('total_columns_analyzed', 0)
                    }
                }] if request.return_sources else None
            )

        else:
            # Use RAG for semantic queries
            logger.info("Using RAG for semantic query")
            result = rag_engine.query(question, request.return_sources)

            if result["success"]:
                return QueryResponse(**result)
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/overview", response_model=DataOverviewResponse)
async def get_data_overview():
    """
    Get an overview of all uploaded datasets
    """
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")

        overview = rag_engine.get_data_overview()

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        return DataOverviewResponse(**overview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insights")
async def get_automatic_insights(
    focus: Optional[str] = Query(None, description="Specific aspect to focus on (e.g., 'sales trends', 'customer behavior')")
):
    """
    Get automatic insights from all uploaded data
    """
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")

        # Generate insight questions based on focus
        if focus:
            question = f"Provide detailed insights about {focus} based on all the datasets."
        else:
            question = (
                "Provide a comprehensive analysis of all the datasets including: "
                "1. Key trends and patterns, "
                "2. Important statistics and metrics, "
                "3. Relationships between different data points, "
                "4. Any anomalies or notable observations, "
                "5. Actionable recommendations based on the data."
            )

        result = rag_engine.query(question, return_sources=True)

        if result["success"]:
            return {
                "success": True,
                "focus": focus or "general",
                "insights": result["answer"],
                "based_on_files": [
                    source["metadata"].get("file_name")
                    for source in result.get("sources", [])
                    if "metadata" in source and "file_name" in source["metadata"]
                ]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear")
async def clear_data():
    """
    Clear all uploaded data and reset the vectorstore
    """
    try:
        if not rag_engine:
            raise HTTPException(status_code=500, detail="RAG engine not initialized")

        result = rag_engine.clear_vectorstore()

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
