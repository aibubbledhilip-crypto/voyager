# Quick Reference - Athena Testing Commands

## SSL Issue Fixed ✅ (Updated with Proper Fix)

The SSL certificate verification error has been resolved with a **proper code fix** that ensures the `.env` configuration is correctly read.

**Error seen:**
```
SSL validation failed for https://athena.us-east-1.amazonaws.com/
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

**Root Cause Identified:**
- The `athena_routes.py` was using `os.getenv()` directly, which doesn't read from `.env` files loaded by pydantic
- The settings object from `config.py` was not being used for SSL verification

**Solution Applied:**
1. ✅ Updated `backend/athena_routes.py` to use `settings.aws_verify_ssl` from config object
2. ✅ Added comprehensive logging for boto3 client creation
3. ✅ Enhanced error messages with specific troubleshooting steps
4. ✅ Improved health check endpoint with detailed configuration status
5. ✅ `.env` has `AWS_VERIFY_SSL=false` (for corporate environments)

---

## Important: Restart Required!

After changing `.env`, you **MUST restart** the application for changes to take effect:

```bash
# Stop the server (Ctrl+C in the terminal running the app)
# Then restart:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Authentication Endpoints

### ⚠️ IMPORTANT: Correct Endpoint

The login endpoint is:
- ✅ **CORRECT**: `POST /auth/token`
- ❌ **WRONG**: `POST /auth/login` (does not exist - returns 404)

Your logs show attempts to use `/auth/login` which doesn't exist in this application.

---

## Step-by-Step Testing Commands

### Step 1: Check Health (No Auth) - Now with Enhanced Diagnostics!

```bash
curl http://localhost:8000/athena/health
```

**Expected output (NEW - with detailed diagnostics):**
```json
{
  "boto3_available": true,
  "configured": true,
  "region": "us-east-1",
  "database": "default",
  "ssl_verify": false,
  "aws_credentials_configured": false,
  "s3_output_configured": false,
  "output_location": "s3://your-athena-output-bucket/",
  "workgroup": "primary",
  "status": "needs_configuration"
}
```

**Health Check Status Explained:**
- ✅ `boto3_available: true` - AWS SDK is installed
- ⚠️ `ssl_verify: false` - SSL verification disabled (good for corporate networks)
- ❌ `aws_credentials_configured: false` - Need to add AWS credentials to `.env`
- ❌ `s3_output_configured: false` - Need to add valid S3 bucket to `.env`
- ⚠️ `status: "needs_configuration"` - Configuration incomplete

**When fully configured, you'll see:**
```json
{
  "status": "ready",
  "aws_credentials_configured": true,
  "s3_output_configured": true,
  ...
}
```

---

### Step 2: Login and Get Token

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Expected output:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcwMDAwMDAwMH0.xxxxx",
  "token_type": "bearer"
}
```

**Save the token:**
```bash
# Copy the access_token value and use in next commands
export TOKEN="paste-your-token-here"
```

---

### Step 3: Test Database Listing (Requires Auth)

```bash
curl -X GET "http://localhost:8000/athena/databases" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected output:**
```json
{
  "databases": ["default", "sampledb", ...],
  "current_database": "default"
}
```

**If you get 401 Unauthorized:**
- Check that you're using the correct token
- Make sure the token hasn't expired (24 hour expiry)
- Verify the Authorization header format: `Bearer <token>`

---

### Step 4: List Tables in Database (Requires Auth)

```bash
curl -X GET "http://localhost:8000/athena/tables/default" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected output:**
```json
{
  "tables": ["table1", "table2", ...],
  "database": "default"
}
```

---

### Step 5: Run a Sample Query (Requires Auth)

```bash
curl -X POST "http://localhost:8000/athena/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM your_table_name LIMIT 10"
  }'
```

**Expected output:**
```json
{
  "success": true,
  "execution_id": "abc-123-def",
  "status": "SUCCEEDED",
  "columns": ["col1", "col2", "col3"],
  "rows": [
    ["value1", "value2", "value3"],
    ...
  ],
  "row_count": 10,
  "execution_time": 2.5,
  "data_scanned": "1.23 MB"
}
```

---

## Alternative: Using API Key Instead of JWT Token

### Get Your API Key

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

**Response includes:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "api_key": "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  ...
}
```

### Use API Key in Requests

```bash
export API_KEY="sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

curl -X GET "http://localhost:8000/athena/databases" \
  -H "X-API-Key: $API_KEY"
```

**Advantage:** API keys don't expire (unlike JWT tokens which expire after 24 hours)

---

## Common Issues & Solutions

### Issue: 401 Unauthorized

**Possible causes:**
1. No token provided
2. Wrong token format (must be: `Authorization: Bearer <token>`)
3. Token expired (24 hour expiry)
4. Using `/auth/login` instead of `/auth/token`

**Solution:**
```bash
# Get a fresh token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

### Issue: 404 Not Found on /auth/login

**Cause:** Wrong endpoint - this application uses `/auth/token` not `/auth/login`

**Solution:** Use the correct endpoint:
```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

### Issue: SSL Certificate Verification Failed

**Cause:** Corporate proxy or network with SSL inspection

**Solution:** Already fixed! `.env` now has `AWS_VERIFY_SSL=false`

**Remember to restart the application after this change!**

---

### Issue: 500 Internal Server Error on /athena/databases

**Possible causes:**
1. SSL verification issue (restart app after .env change)
2. Invalid AWS credentials
3. No AWS credentials configured
4. No internet connection to AWS

**Check:**
```bash
# 1. Verify .env has AWS_VERIFY_SSL=false
cat .env | grep AWS_VERIFY_SSL

# 2. Check health endpoint
curl http://localhost:8000/athena/health

# 3. Check application logs for specific error
```

---

## Testing Workflow

```bash
# 1. Restart application (IMPORTANT!)
# Ctrl+C to stop, then:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Test health
curl http://localhost:8000/athena/health

# 3. Login
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# 4. Save token
export TOKEN="<paste-token-here>"

# 5. Test databases
curl -X GET "http://localhost:8000/athena/databases" \
  -H "Authorization: Bearer $TOKEN"

# 6. Test tables
curl -X GET "http://localhost:8000/athena/tables/default" \
  -H "Authorization: Bearer $TOKEN"

# 7. Run query
curl -X POST "http://localhost:8000/athena/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM your_table LIMIT 5"}'
```

---

## All Available Auth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/token` | POST | Login (get JWT token) |
| `/auth/register` | POST | Create new user account |
| `/auth/me` | GET | Get current user profile (includes API key) |
| `/auth/me` | PUT | Update current user profile |
| `/auth/me/regenerate-api-key` | POST | Generate new API key |
| `/auth/users` | GET | List all users (admin only) |

**Note:** `/auth/login` does NOT exist in this application.

---

## Next Steps After SSL Fix

1. ✅ **Restart the application** (changes won't take effect until restart)
2. ✅ Test `/athena/health` endpoint
3. ✅ Login using `/auth/token` (NOT `/auth/login`)
4. ✅ Test `/athena/databases` with the token
5. ✅ If still getting errors, check application logs
6. ✅ Ensure AWS credentials are configured in `.env` (if you have real credentials)

---

## Need More Help?

- Check application logs for specific errors
- View all available endpoints: http://localhost:8000/docs
- Full setup guide: `ATHENA_SETUP.md`
