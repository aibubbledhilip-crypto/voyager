"""
SQL Athena Query Runner API routes
Allows users to execute SQL queries against AWS Athena
"""
import logging
import re
import csv
import io
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
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

from backend.database import get_db, User, SystemSettings, get_system_setting, update_system_setting
from backend.auth import get_current_active_user


# Security configuration
MAX_QUERY_LENGTH = 10000  # Maximum characters in a query
MAX_RESULTS = 1000  # Maximum rows to return
QUERY_TIMEOUT_SECONDS = 120  # 2 minutes

# Rate limiting: track queries per user
query_rate_limiter = defaultdict(list)
MAX_QUERIES_PER_MINUTE = 10


# SQL Security Utilities
class SQLSecurityValidator:
    """Comprehensive SQL injection prevention and query validation"""

    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = [
        # Data Modification
        'DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE',
        # Schema Modification
        'ALTER', 'CREATE', 'RENAME',
        # Access Control
        'GRANT', 'REVOKE',
        # Database Operations
        'USE', 'EXEC', 'EXECUTE',
        # System Commands
        'SHUTDOWN', 'KILL',
        # Advanced Features that could be dangerous
        'LOAD', 'OUTFILE', 'DUMPFILE', 'INTO OUTFILE', 'INTO DUMPFILE',
        'LOAD_FILE', 'LOAD DATA',
    ]

    # SQL injection patterns to detect
    INJECTION_PATTERNS = [
        r';\s*DROP',  # ; DROP TABLE
        r';\s*DELETE',  # ; DELETE FROM
        r';\s*INSERT',  # ; INSERT INTO
        r';\s*UPDATE',  # ; UPDATE SET
        r'--',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r'@@',  # System variables
        r'UNION\s+SELECT',  # Union-based injection
        r'OR\s+1\s*=\s*1',  # Classic injection
        r'OR\s+\'1\'\s*=\s*\'1\'',
        r'AND\s+1\s*=\s*1',
        r'\bxp_\w+',  # Extended stored procedures (SQL Server)
        r'BENCHMARK\s*\(',  # MySQL benchmark (timing attacks)
        r'SLEEP\s*\(',  # Sleep functions (timing attacks)
        r'WAITFOR\s+DELAY',  # WAITFOR DELAY (SQL Server timing)
    ]

    @staticmethod
    def sanitize_identifier(identifier: str) -> str:
        """
        Sanitize database/table identifiers to prevent SQL injection
        Only allows alphanumeric characters, underscores, and hyphens
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")

        # Remove any whitespace
        identifier = identifier.strip()

        # Only allow safe characters: letters, numbers, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', identifier):
            raise ValueError(
                f"Invalid identifier '{identifier}'. Only alphanumeric characters, "
                "underscores, and hyphens are allowed."
            )

        # Prevent SQL keywords as identifiers
        if identifier.upper() in ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'TABLE', 'DATABASE']:
            raise ValueError(f"SQL keyword '{identifier}' cannot be used as identifier")

        return identifier

    @staticmethod
    def validate_query_safety(query: str) -> tuple[bool, Optional[str]]:
        """
        Validate that the query is safe to execute

        Returns:
            (is_safe, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"

        query = query.strip()
        query_upper = query.upper()

        # Check query length
        if len(query) > MAX_QUERY_LENGTH:
            return False, f"Query too long. Maximum {MAX_QUERY_LENGTH} characters allowed."

        # Check for dangerous keywords
        for keyword in SQLSecurityValidator.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                return False, f"Dangerous operation '{keyword}' not allowed. Only SELECT queries are permitted."

        # Check for SQL injection patterns
        for pattern in SQLSecurityValidator.INJECTION_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False, "Potentially malicious SQL pattern detected. Query blocked for security."

        # Ensure query starts with SELECT (allow whitespace and comments before)
        # Remove leading whitespace and comments
        cleaned_query = re.sub(r'^\s+', '', query_upper)
        if not cleaned_query.startswith('SELECT') and not cleaned_query.startswith('SHOW') and not cleaned_query.startswith('DESCRIBE'):
            return False, "Only SELECT, SHOW, and DESCRIBE queries are allowed"

        # Check for multiple statements (stacked queries)
        # Remove strings first to avoid false positives from semicolons in strings
        query_no_strings = re.sub(r"'[^']*'", '', query)
        query_no_strings = re.sub(r'"[^"]*"', '', query_no_strings)

        # Count semicolons (should be 0 or 1 at the end)
        semicolons = query_no_strings.count(';')
        if semicolons > 1:
            return False, "Multiple SQL statements not allowed"
        elif semicolons == 1 and not query_no_strings.rstrip().endswith(';'):
            return False, "Semicolon only allowed at end of query"

        return True, None

    @staticmethod
    def log_query_execution(user_id: int, username: str, query: str, success: bool, error: Optional[str] = None):
        """Log query execution for audit trail"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'username': username,
            'query_preview': query[:200] + ('...' if len(query) > 200 else ''),
            'success': success,
            'error': error
        }

        if success:
            logger.info(f"Query executed successfully by user {username} (ID: {user_id})")
        else:
            logger.warning(f"Query failed for user {username} (ID: {user_id}): {error}")

        # In production, you might want to store this in a database table
        logger.debug(f"Query audit log: {log_data}")


def check_rate_limit(user_id: int) -> bool:
    """
    Check if user has exceeded rate limit
    Returns True if within limits, False if exceeded
    """
    now = datetime.utcnow()
    minute_ago = now - timedelta(minutes=1)

    # Clean old entries
    query_rate_limiter[user_id] = [
        timestamp for timestamp in query_rate_limiter[user_id]
        if timestamp > minute_ago
    ]

    # Check limit
    if len(query_rate_limiter[user_id]) >= MAX_QUERIES_PER_MINUTE:
        return False

    # Add current request
    query_rate_limiter[user_id].append(now)
    return True


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    database: Optional[str] = None
    output_location: Optional[str] = None

    @validator('query')
    def validate_query(cls, v):
        """Validate query on input"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query too long. Maximum {MAX_QUERY_LENGTH} characters allowed")
        return v.strip()

    @validator('database')
    def validate_database(cls, v):
        """Validate database identifier"""
        if v:
            try:
                return SQLSecurityValidator.sanitize_identifier(v)
            except ValueError as e:
                raise ValueError(f"Invalid database name: {str(e)}")
        return v


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


def get_download_limit(db: Session) -> int:
    """Get the admin-configured download limit"""
    limit_str = get_system_setting(db, "athena_max_download_rows", "100000")
    try:
        return int(limit_str)
    except ValueError:
        return 100000  # Default fallback


def get_display_limit(db: Session) -> int:
    """Get the admin-configured display limit"""
    limit_str = get_system_setting(db, "athena_display_rows", "1000")
    try:
        return int(limit_str)
    except ValueError:
        return 1000  # Default fallback


def execute_athena_query_with_all_results(
    query: str,
    database: Optional[str] = None,
    output_location: Optional[str] = None,
    max_rows: int = 100000
) -> Dict[str, Any]:
    """
    Execute a query and fetch ALL results using pagination (for downloads)

    Args:
        query: SQL query to execute
        database: Database name
        output_location: S3 location for results
        max_rows: Maximum number of rows to fetch

    Returns:
        Dictionary with complete query results
    """
    config = get_athena_config()
    client = get_athena_client()

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
        logger.info(f"Started Athena query execution for download: {query_execution_id}")

        # Wait for query to complete
        max_attempts = 60
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

        if status == 'SUCCEEDED':
            # Fetch all results with pagination
            all_rows = []
            next_token = None
            columns = None
            total_fetched = 0

            while total_fetched < max_rows:
                # Calculate how many rows to fetch in this batch
                remaining = max_rows - total_fetched
                batch_size = min(1000, remaining)  # AWS Athena max is 1000 per request

                params = {
                    'QueryExecutionId': query_execution_id,
                    'MaxResults': batch_size
                }

                if next_token:
                    params['NextToken'] = next_token

                result = client.get_query_results(**params)

                # Extract column names from first batch
                if columns is None:
                    columns = [col['Label'] for col in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]

                # Extract rows (skip header row on first batch)
                rows = result['ResultSet']['Rows']
                start_idx = 1 if next_token is None else 0  # Skip header only on first batch

                for row in rows[start_idx:]:
                    row_data = [field.get('VarCharValue', '') for field in row['Data']]
                    all_rows.append(row_data)
                    total_fetched += 1

                    if total_fetched >= max_rows:
                        break

                # Check if there are more results
                next_token = result.get('NextToken')
                if not next_token:
                    break

            # Get statistics
            stats = query_status['QueryExecution'].get('Statistics', {})
            data_scanned = stats.get('DataScannedInBytes', 0)
            data_scanned_mb = data_scanned / (1024 * 1024)

            return {
                'success': True,
                'execution_id': query_execution_id,
                'status': status,
                'columns': columns,
                'rows': all_rows,
                'row_count': len(all_rows),
                'execution_time': round(execution_time, 2),
                'data_scanned': f"{data_scanned_mb:.2f} MB"
            }
        else:
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
            # Get query results (limit to MAX_RESULTS for security)
            result = client.get_query_results(
                QueryExecutionId=query_execution_id,
                MaxResults=MAX_RESULTS
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
    Execute a SQL query on Athena with comprehensive security checks

    Security Features:
    - SQL injection prevention
    - Rate limiting (max 10 queries/minute per user)
    - Only SELECT, SHOW, DESCRIBE queries allowed
    - Query length limits
    - Audit logging
    - Dangerous keyword blocking
    """
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AWS SDK (boto3) not installed. Please install: pip install boto3"
        )

    # Rate limiting check
    if not check_rate_limit(current_user.id):
        logger.warning(f"Rate limit exceeded for user {current_user.username} (ID: {current_user.id})")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {MAX_QUERIES_PER_MINUTE} queries per minute allowed."
        )

    query = query_request.query.strip()

    # Comprehensive security validation
    is_safe, error_message = SQLSecurityValidator.validate_query_safety(query)
    if not is_safe:
        # Log the blocked attempt
        SQLSecurityValidator.log_query_execution(
            user_id=current_user.id,
            username=current_user.username,
            query=query,
            success=False,
            error=f"Security validation failed: {error_message}"
        )
        raise HTTPException(status_code=403, detail=error_message)

    try:
        # Execute query
        result = execute_athena_query(
            query=query,
            database=query_request.database,
            output_location=query_request.output_location
        )

        # Log successful execution
        SQLSecurityValidator.log_query_execution(
            user_id=current_user.id,
            username=current_user.username,
            query=query,
            success=result.get('success', False),
            error=result.get('error')
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        # Log the error
        SQLSecurityValidator.log_query_execution(
            user_id=current_user.id,
            username=current_user.username,
            query=query,
            success=False,
            error=str(e)
        )
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
    """List tables in a specific database (SQL injection protected)"""
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="boto3 not installed"
        )

    try:
        # Sanitize database name to prevent SQL injection
        safe_database = SQLSecurityValidator.sanitize_identifier(database)

        # Use sanitized identifier in query
        result = execute_athena_query(f"SHOW TABLES IN {safe_database}", database=safe_database)

        if result['success']:
            # Extract table names from rows
            tables = [row[0] for row in result['rows']]

            return TableInfo(
                tables=tables,
                database=safe_database
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list tables'))

    except ValueError as e:
        # Sanitization failed
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/download")
async def download_query_results(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Execute query and download results as CSV (up to admin-configured limit)

    Returns a CSV file with all results up to the maximum download limit.
    Default is 100,000 rows, configurable by admin.
    """
    if not BOTO3_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="AWS SDK (boto3) not installed"
        )

    # Rate limiting check
    if not check_rate_limit(current_user.id):
        logger.warning(f"Rate limit exceeded for user {current_user.username} (ID: {current_user.id})")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {MAX_QUERIES_PER_MINUTE} queries per minute allowed."
        )

    query = query_request.query.strip()

    # Security validation
    is_safe, error_message = SQLSecurityValidator.validate_query_safety(query)
    if not is_safe:
        SQLSecurityValidator.log_query_execution(
            user_id=current_user.id,
            username=current_user.username,
            query=query,
            success=False,
            error=f"Security validation failed: {error_message}"
        )
        raise HTTPException(status_code=403, detail=error_message)

    # Get admin-configured download limit
    max_download_rows = get_download_limit(db)

    try:
        # Execute query with full results
        result = execute_athena_query_with_all_results(
            query=query,
            database=query_request.database,
            output_location=query_request.output_location,
            max_rows=max_download_rows
        )

        # Log execution
        SQLSecurityValidator.log_query_execution(
            user_id=current_user.id,
            username=current_user.username,
            query=query,
            success=result.get('success', False),
            error=result.get('error')
        )

        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Query failed'))

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(result['columns'])

        # Write data rows
        for row in result['rows']:
            writer.writerow(row)

        # Create streaming response
        output.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"athena_results_{timestamp}.csv"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'X-Row-Count': str(result['row_count']),
                'X-Execution-Time': str(result['execution_time']),
                'X-Data-Scanned': result['data_scanned']
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        SQLSecurityValidator.log_query_execution(
            user_id=current_user.id,
            username=current_user.username,
            query=query,
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/settings")
async def get_admin_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Athena settings (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    max_download = get_download_limit(db)
    display_limit = get_display_limit(db)

    return {
        "athena_max_download_rows": max_download,
        "athena_display_rows": display_limit,
        "description": {
            "athena_max_download_rows": "Maximum rows that can be downloaded from Athena queries",
            "athena_display_rows": "Maximum rows to display in UI"
        }
    }


@router.put("/admin/settings/download-limit")
async def update_download_limit(
    limit: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update maximum download row limit (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate limit
    if limit < 1000:
        raise HTTPException(status_code=400, detail="Minimum limit is 1,000 rows")
    if limit > 1000000:
        raise HTTPException(status_code=400, detail="Maximum limit is 1,000,000 rows")

    update_system_setting(db, "athena_max_download_rows", str(limit), current_user.id)

    logger.info(f"Admin {current_user.username} updated download limit to {limit}")

    return {
        "success": True,
        "message": f"Download limit updated to {limit:,} rows",
        "athena_max_download_rows": limit
    }


@router.put("/admin/settings/display-limit")
async def update_display_limit(
    limit: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update maximum display row limit (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate limit
    if limit < 10:
        raise HTTPException(status_code=400, detail="Minimum limit is 10 rows")
    if limit > 10000:
        raise HTTPException(status_code=400, detail="Maximum limit is 10,000 rows")

    update_system_setting(db, "athena_display_rows", str(limit), current_user.id)

    logger.info(f"Admin {current_user.username} updated display limit to {limit}")

    return {
        "success": True,
        "message": f"Display limit updated to {limit:,} rows",
        "athena_display_rows": limit
    }


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
