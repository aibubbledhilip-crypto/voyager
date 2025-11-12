"""
SQL Athena Query Runner API routes
Allows users to execute SQL queries against AWS Athena
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/athena", tags=["athena"])

# Try to import boto3 for Athena
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available. Install with: pip install boto3")

from backend.database import get_db, User
from backend.auth import get_current_active_user


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    database: Optional[str] = None
    output_location: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    execution_id: Optional[str] = None
    status: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    data_scanned: Optional[str] = None


class AthenaConfig(BaseModel):
    database: str
    output_location: str
    region: str
    workgroup: Optional[str] = None


class DatabaseInfo(BaseModel):
    databases: List[str]
    current_database: Optional[str] = None


class TableInfo(BaseModel):
    tables: List[str]
    database: str


# Athena configuration from environment variables
def get_athena_config() -> Dict[str, str]:
    """Get Athena configuration from environment variables"""
    return {
        "database": os.getenv("ATHENA_DATABASE", "default"),
        "output_location": os.getenv("ATHENA_OUTPUT_LOCATION", "s3://aws-athena-query-results/"),
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "workgroup": os.getenv("ATHENA_WORKGROUP", "primary")
    }


def get_athena_client():
    """Get boto3 Athena client"""
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="boto3 not installed. Please install: pip install boto3"
        )

    config = get_athena_config()
    return boto3.client('athena', region_name=config['region'])


def execute_athena_query(
    query: str,
    database: Optional[str] = None,
    output_location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a query on AWS Athena

    Args:
        query: SQL query to execute
        database: Database name (optional, uses default from config)
        output_location: S3 location for results (optional, uses default from config)

    Returns:
        Dictionary with query results
    """
    config = get_athena_config()
    client = get_athena_client()

    # Use provided values or defaults
    db = database or config['database']
    output = output_location or config['output_location']
    workgroup = config.get('workgroup', 'primary')

    try:
        # Start query execution
        start_time = time.time()

        response = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': db},
            ResultConfiguration={'OutputLocation': output},
            WorkGroup=workgroup
        )

        query_execution_id = response['QueryExecutionId']
        logger.info(f"Started Athena query execution: {query_execution_id}")

        # Wait for query to complete
        max_attempts = 60  # 60 attempts * 2 seconds = 2 minutes timeout
        attempt = 0

        while attempt < max_attempts:
            query_status = client.get_query_execution(
                QueryExecutionId=query_execution_id
            )

            status = query_status['QueryExecution']['Status']['State']

            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break

            time.sleep(2)
            attempt += 1

        execution_time = time.time() - start_time

        # Check final status
        if status == 'SUCCEEDED':
            # Get query results
            result = client.get_query_results(
                QueryExecutionId=query_execution_id,
                MaxResults=1000  # Limit to 1000 rows
            )

            # Extract column names
            columns = [col['Label'] for col in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]

            # Extract rows (skip header row)
            rows = []
            for row in result['ResultSet']['Rows'][1:]:  # Skip first row (headers)
                row_data = [field.get('VarCharValue', '') for field in row['Data']]
                rows.append(row_data)

            # Get statistics
            stats = query_status['QueryExecution'].get('Statistics', {})
            data_scanned = stats.get('DataScannedInBytes', 0)
            data_scanned_mb = data_scanned / (1024 * 1024)

            return {
                'success': True,
                'execution_id': query_execution_id,
                'status': status,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time': round(execution_time, 2),
                'data_scanned': f"{data_scanned_mb:.2f} MB"
            }
        else:
            # Query failed or was cancelled
            error_message = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')

            return {
                'success': False,
                'execution_id': query_execution_id,
                'status': status,
                'error': error_message,
                'execution_time': round(execution_time, 2)
            }

    except Exception as e:
        logger.error(f"Athena query error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/query", response_model=QueryResponse)
async def run_query(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Execute a SQL query on Athena

    Requires authentication. Returns query results including columns and rows.
    """
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AWS SDK (boto3) not installed. Please install: pip install boto3"
        )

    # Validate query (basic security check)
    query = query_request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Check for dangerous operations (basic protection)
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE DATABASE', 'DROP DATABASE']
    query_upper = query.upper()

    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(
                status_code=403,
                detail=f"Dangerous operation '{keyword}' not allowed. Only SELECT queries are permitted."
            )

    try:
        result = execute_athena_query(
            query=query,
            database=query_request.database,
            output_location=query_request.output_location
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=AthenaConfig)
async def get_config(
    current_user: User = Depends(get_current_active_user)
):
    """Get current Athena configuration"""
    config = get_athena_config()
    return AthenaConfig(**config)


@router.get("/databases", response_model=DatabaseInfo)
async def list_databases(
    current_user: User = Depends(get_current_active_user)
):
    """List available databases in Athena"""
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="boto3 not installed"
        )

    try:
        client = get_athena_client()
        config = get_athena_config()

        # Query to list databases
        result = execute_athena_query("SHOW DATABASES")

        if result['success']:
            # Extract database names from rows
            databases = [row[0] for row in result['rows']]

            return DatabaseInfo(
                databases=databases,
                current_database=config['database']
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list databases'))

    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{database}", response_model=TableInfo)
async def list_tables(
    database: str,
    current_user: User = Depends(get_current_active_user)
):
    """List tables in a specific database"""
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="boto3 not installed"
        )

    try:
        result = execute_athena_query(f"SHOW TABLES IN {database}", database=database)

        if result['success']:
            # Extract table names from rows
            tables = [row[0] for row in result['rows']]

            return TableInfo(
                tables=tables,
                database=database
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list tables'))

    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check if Athena service is properly configured"""
    config = get_athena_config()

    return {
        "boto3_available": BOTO3_AVAILABLE,
        "configured": bool(config.get('database') and config.get('output_location')),
        "region": config.get('region'),
        "database": config.get('database')
    }
