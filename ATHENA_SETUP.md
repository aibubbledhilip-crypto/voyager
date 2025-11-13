# AWS Athena Setup and Configuration Guide

## Issues Fixed ✅

### 1. **Bcrypt Warning** - FIXED
- **Issue**: `bcrypt 4.1.1` was incompatible with `passlib 1.7.4`
- **Fix**: Downgraded to `bcrypt 4.0.1` for compatibility
- **Status**: ✅ No more warnings on startup

### 2. **.env File Missing** - FIXED
- **Issue**: No `.env` file existed, so AWS credentials were empty
- **Fix**: Created `.env` file from template
- **Action Required**: You must add your actual AWS credentials (see below)

### 3. **401 Unauthorized Errors** - EXPLAINED
- **Not a bug**: Athena endpoints require authentication
- **Solution**: See "How to Authenticate" section below

### 4. **404 for /athena** - EXPLAINED
- **Not a bug**: No endpoint exists at `/athena` root
- **Valid endpoints**: `/athena/query`, `/athena/databases`, `/athena/health`, etc.

---

## Step 1: Configure AWS Credentials

Edit the `.env` file and replace the placeholder values:

```bash
# Required AWS Configuration
AWS_ACCESS_KEY_ID=AKIA...your-actual-key...
AWS_SECRET_ACCESS_KEY=your-actual-secret-key
AWS_REGION=us-east-1  # or your region

# Required S3 bucket for Athena query results
ATHENA_OUTPUT_LOCATION=s3://your-athena-results-bucket/query-results/
ATHENA_WORKGROUP=primary  # or your workgroup name

# SSL Configuration (set to false if behind corporate proxy)
AWS_VERIFY_SSL=true
```

### How to Get AWS Credentials:

1. **AWS Console** → **IAM** → **Users** → **Your User** → **Security Credentials**
2. Click "Create access key"
3. Choose "Application running outside AWS"
4. Copy the Access Key ID and Secret Access Key

### Required IAM Permissions:

Your AWS user needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution",
        "athena:GetWorkGroup",
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions",
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

### S3 Bucket for Query Results:

1. Create an S3 bucket (e.g., `my-company-athena-results`)
2. Set `ATHENA_OUTPUT_LOCATION=s3://my-company-athena-results/`

---

## Step 2: Restart the Application

After updating `.env`, restart your application:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Step 3: Authentication

All Athena endpoints require authentication. You have two options:

### Option A: JWT Token (Recommended)

1. **Login to get a token**:

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

2. **Use the token in subsequent requests**:

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/athena/databases" \
  -H "Authorization: Bearer $TOKEN"
```

### Option B: API Key

1. **Get your API key**:

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

Response includes:
```json
{
  "api_key": "sk_abc123...",
  ...
}
```

2. **Use API key in requests**:

```bash
curl -X GET "http://localhost:8000/athena/databases" \
  -H "X-API-Key: sk_abc123..."
```

---

## Step 4: Test Athena Connectivity

### Test 1: Health Check (No Auth Required)

```bash
curl http://localhost:8000/athena/health
```

Expected response:
```json
{
  "boto3_available": true,
  "configured": true,
  "region": "us-east-1",
  "database": "default"
}
```

### Test 2: List Databases (Auth Required)

```bash
curl -X GET "http://localhost:8000/athena/databases" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "databases": ["default", "my_database", "analytics"],
  "current_database": "default"
}
```

### Test 3: List Tables (Auth Required)

```bash
curl -X GET "http://localhost:8000/athena/tables/default" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "tables": ["table1", "table2", "customers"],
  "database": "default"
}
```

### Test 4: Run a Query (Auth Required)

```bash
curl -X POST "http://localhost:8000/athena/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM my_table LIMIT 10"
  }'
```

Expected response:
```json
{
  "success": true,
  "execution_id": "abc-123-def",
  "status": "SUCCEEDED",
  "columns": ["id", "name", "email"],
  "rows": [
    ["1", "John Doe", "john@example.com"],
    ["2", "Jane Smith", "jane@example.com"]
  ],
  "row_count": 10,
  "execution_time": 2.34,
  "data_scanned": "1.23 MB"
}
```

### Test 5: Download Query Results as CSV (Auth Required)

```bash
curl -X POST "http://localhost:8000/athena/query/download" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM my_table LIMIT 1000"
  }' \
  --output results.csv
```

---

## Available Athena Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/athena/health` | GET | ❌ No | Check if Athena is configured |
| `/athena/config` | GET | ✅ Yes | Get current Athena configuration |
| `/athena/databases` | GET | ✅ Yes | List all databases |
| `/athena/tables/{database}` | GET | ✅ Yes | List tables in a database |
| `/athena/query` | POST | ✅ Yes | Execute a SQL query (max 1000 rows) |
| `/athena/query/download` | POST | ✅ Yes | Execute query and download as CSV (max 100K rows) |
| `/athena/admin/settings` | GET | ✅ Admin | Get admin settings (admin only) |
| `/athena/admin/settings/download-limit` | PUT | ✅ Admin | Update download limit (admin only) |
| `/athena/admin/settings/display-limit` | PUT | ✅ Admin | Update display limit (admin only) |

---

## Security Features

### 1. SQL Injection Prevention
- Only `SELECT`, `SHOW`, `DESCRIBE` queries allowed
- Dangerous keywords blocked: `DROP`, `DELETE`, `INSERT`, `UPDATE`, etc.
- Pattern matching for injection attempts
- Identifier sanitization (database/table names)

### 2. Rate Limiting
- Maximum 10 queries per minute per user
- Prevents abuse and cost overruns

### 3. Query Limits
- Display queries: Max 1,000 rows
- Download queries: Max 100,000 rows (configurable by admin)
- Query length: Max 10,000 characters
- Timeout: 2 minutes

### 4. Audit Logging
- All query executions logged
- User tracking
- Success/failure tracking

---

## Common Issues and Solutions

### Issue: "boto3 not installed"
**Solution**:
```bash
pip install boto3==1.34.0
```

### Issue: "Invalid AWS credentials"
**Solution**:
- Check your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`
- Verify credentials work with AWS CLI: `aws sts get-caller-identity`

### Issue: "Access Denied" or "Forbidden"
**Solution**:
- Check IAM permissions (see "Required IAM Permissions" above)
- Verify S3 bucket permissions for Athena output location

### Issue: "Table not found"
**Solution**:
- Use `/athena/databases` to list available databases
- Use `/athena/tables/{database}` to list available tables
- Verify you're using the correct database in your query

### Issue: "SSL verification failed"
**Solution** (Corporate proxies only):
```bash
# In .env file:
AWS_VERIFY_SSL=false
```
⚠️ **WARNING**: Only disable SSL in trusted corporate networks!

### Issue: "Rate limit exceeded"
**Solution**:
- Wait 1 minute before retrying
- Reduce query frequency
- Contact admin to adjust rate limits if needed

---

## Default Admin Credentials

**Username**: `admin`
**Password**: `admin123`

⚠️ **IMPORTANT**: Change the admin password immediately in production!

```bash
# Login
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Change password
curl -X PUT "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "new_secure_password_here"
  }'
```

---

## Next Steps

1. ✅ Update `.env` with your AWS credentials
2. ✅ Restart the application
3. ✅ Login to get authentication token
4. ✅ Test `/athena/health` endpoint
5. ✅ Test `/athena/databases` endpoint
6. ✅ Run your first query!
7. ✅ Change admin password

---

## Support

For issues, check:
- Application logs for error messages
- AWS CloudWatch Logs for Athena query errors
- AWS Athena console for query history
- Network connectivity to AWS services

## Documentation

- FastAPI Swagger UI: http://localhost:8000/docs
- ReDoc UI: http://localhost:8000/redoc
