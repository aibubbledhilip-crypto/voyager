# Advanced Features Guide

This guide covers the advanced features added to the Intelligent RAG Data Analysis Tool:
- User Authentication & Authorization
- Multi-Tenancy Support
- Advanced Data Visualizations
- User Management & Admin Dashboard

---

## Table of Contents

1. [User Authentication](#user-authentication)
2. [Multi-Tenancy](#multi-tenancy)
3. [Advanced Visualizations](#advanced-visualizations)
4. [Admin Features](#admin-features)
5. [API Reference](#api-reference)

---

## User Authentication

The system now supports secure user authentication with JWT tokens and API keys.

### Registration

**Endpoint:** `POST /auth/register`

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_admin": false,
  "api_key": "sk_xxxxxxxxxxxxx"
}
```

### Login

**Endpoint:** `POST /auth/token`

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=secure_password123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using Authentication

There are two ways to authenticate API requests:

#### 1. JWT Token (Recommended for web apps)

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@data.csv"
```

#### 2. API Key (Recommended for scripts)

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "X-API-Key: sk_xxxxxxxxxxxxx" \
  -F "file=@data.csv"
```

### Default Admin Account

On first run, a default admin account is created:
- **Username:** `admin`
- **Password:** `admin123`
- **⚠️ IMPORTANT:** Change this password immediately!

---

## Multi-Tenancy

Multi-tenancy ensures data isolation between users. Each user gets their own workspace (tenant).

### How It Works

1. **Automatic Tenant Creation**: When a user registers, a default tenant is automatically created
2. **Data Isolation**: Each tenant has its own:
   - Storage directory (`data/tenants/{user_id}/`)
   - Vector store collections
   - File tracking
   - Query history

3. **Workspace Management**: Users can have multiple tenants (workspaces)

### Benefits

- **Data Privacy**: Users can only access their own data
- **Organization**: Separate workspaces for different projects
- **Scalability**: Easy to manage multiple users
- **Security**: Built-in access control

### Example: User-Specific Storage

```python
import requests

# Login
token_response = requests.post(
    "http://localhost:8000/auth/token",
    data={"username": "john_doe", "password": "password"}
)
token = token_response.json()["access_token"]

# Upload file (stored in user's tenant)
with open("sales_data.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f}
    )

# File is stored in: data/tenants/{user_id}/sales_data.csv
```

### Get User Tenants

**Endpoint:** `GET /auth/me/tenants`

```bash
curl -X GET "http://localhost:8000/auth/me/tenants" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Advanced Visualizations

The system now includes powerful visualization capabilities with automatic chart generation.

### Features

- **Summary Dashboards**: Comprehensive overview with multiple charts
- **Correlation Analysis**: Heatmaps showing relationships
- **Distribution Plots**: Histogram visualizations
- **Time Series**: Trend analysis over time
- **Missing Data**: Visualization of missing values
- **Categorical Analysis**: Bar charts for categorical data
- **Chart Export**: Export charts as PNG, JPG, PDF, SVG

### Create Summary Dashboard

**Endpoint:** `POST /visualize/dashboard/{file_id}`

```bash
curl -X POST "http://localhost:8000/visualize/dashboard/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response includes:**
```json
{
  "success": true,
  "file_name": "sales_data.csv",
  "visualizations": {
    "statistics": {
      "shape": {"rows": 1000, "columns": 6},
      "memory_usage": "0.05 MB",
      "missing_values": {...},
      "duplicates": 5
    },
    "column_types": {
      "chart": "...",  // Plotly JSON
      "data": {...}
    },
    "missing_values": {
      "chart": "...",
      "data": [...]
    },
    "distributions": {
      "chart": "..."
    },
    "correlation": {
      "chart": "...",
      "insights": [
        "Strong positive correlation (0.85) between Sales and Revenue"
      ]
    },
    "categorical": {
      "charts": {...}
    },
    "time_series": {
      "charts": {...}
    }
  },
  "summary": "Dataset contains 1,000 rows and 6 columns..."
}
```

### Trend Analysis

**Endpoint:** `POST /visualize/trend`

```bash
curl -X POST "http://localhost:8000/visualize/trend?file_id=1&x_column=Date&y_column=Sales" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Comparison Charts

**Endpoint:** `POST /visualize/comparison`

Compare data across multiple files:

```bash
curl -X POST "http://localhost:8000/visualize/comparison" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": [1, 2, 3],
    "x_field": "Month",
    "y_fields": ["Sales", "Revenue"],
    "chart_type": "bar"
  }'
```

### Export Charts

**Endpoint:** `POST /visualize/export`

```bash
curl -X POST "http://localhost:8000/visualize/export" \
  -H "Content-Type: application/json" \
  -d '{
    "chart_json": "...",
    "format": "png"
  }' \
  --output chart.png
```

### Get File Columns

Before creating visualizations, check available columns:

**Endpoint:** `GET /visualize/columns/{file_id}`

```bash
curl -X GET "http://localhost:8000/visualize/columns/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "columns": [
    {
      "name": "Date",
      "type": "object",
      "sample_values": ["2024-01-01", "2024-01-02", "2024-01-03"]
    },
    {
      "name": "Sales",
      "type": "int64",
      "sample_values": [1500, 2300, 1800]
    }
  ]
}
```

### Visualization Types

#### 1. Column Type Distribution
- Pie chart showing data types
- Helps understand dataset composition

#### 2. Missing Values
- Bar chart highlighting missing data
- Percentage-based visualization
- Identifies data quality issues

#### 3. Distributions
- Histograms for numeric columns
- Shows data spread and outliers
- Up to 6 columns displayed

#### 4. Correlation Matrix
- Heatmap with values
- Identifies strong relationships
- Auto-generated insights

#### 5. Categorical Analysis
- Top values bar charts
- Frequency distributions
- Up to 10 top values per column

#### 6. Time Series
- Line charts for temporal data
- Automatic date detection
- Moving averages

---

## Admin Features

Admin users have additional capabilities for user management.

### Admin Endpoints

All admin endpoints require admin role:

```bash
-H "Authorization: Bearer ADMIN_TOKEN"
```

### List All Users

**Endpoint:** `GET /auth/users`

```bash
curl -X GET "http://localhost:8000/auth/users?skip=0&limit=100" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Create User (Admin)

**Endpoint:** `POST /auth/users`

```bash
curl -X POST "http://localhost:8000/auth/users?is_admin=false" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "email": "newuser@example.com",
    "password": "password123",
    "full_name": "New User"
  }'
```

### Toggle User Active Status

**Endpoint:** `PUT /auth/users/{user_id}/toggle-active`

```bash
curl -X PUT "http://localhost:8000/auth/users/2/toggle-active" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Delete User

**Endpoint:** `DELETE /auth/users/{user_id}`

```bash
curl -X DELETE "http://localhost:8000/auth/users/2" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## API Reference

### User Management

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/auth/register` | POST | No | Register new user |
| `/auth/token` | POST | No | Login and get token |
| `/auth/me` | GET | Yes | Get current user info |
| `/auth/me` | PUT | Yes | Update current user |
| `/auth/me/regenerate-api-key` | POST | Yes | Generate new API key |
| `/auth/me/stats` | GET | Yes | Get user statistics |
| `/auth/me/tenants` | GET | Yes | List user tenants |
| `/auth/users` | GET | Admin | List all users |
| `/auth/users` | POST | Admin | Create user |
| `/auth/users/{id}` | DELETE | Admin | Delete user |
| `/auth/users/{id}/toggle-active` | PUT | Admin | Toggle user status |

### Visualization

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/visualize/dashboard/{file_id}` | POST | Optional | Create full dashboard |
| `/visualize/trend` | POST | Optional | Create trend chart |
| `/visualize/comparison` | POST | Optional | Compare multiple files |
| `/visualize/files` | GET | Optional | List available files |
| `/visualize/export` | POST | Optional | Export chart as image |
| `/visualize/columns/{file_id}` | GET | Optional | Get file columns |

### Data Upload & Query

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/upload` | POST | Optional | Upload single file |
| `/upload-multiple` | POST | Optional | Upload multiple files |
| `/query` | POST | Optional | Query data with RAG |
| `/insights` | POST | Optional | Get auto insights |
| `/overview` | GET | Optional | Get data overview |
| `/clear` | DELETE | Optional | Clear all data |

**Note:** "Optional" auth means the endpoint works both with and without authentication. Authenticated requests get multi-tenancy benefits.

---

## User Statistics

Get comprehensive statistics about your usage:

**Endpoint:** `GET /auth/me/stats`

```bash
curl -X GET "http://localhost:8000/auth/me/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_files": 25,
  "total_queries": 150,
  "storage_used": "125.50 MB"
}
```

---

## Python Client Examples

### Complete Workflow with Authentication

```python
import requests

BASE_URL = "http://localhost:8000"

class RAGClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.token = None

    def register(self, username, email, password, full_name=None):
        """Register a new user"""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.json()

    def login(self, username, password):
        """Login and store token"""
        response = requests.post(
            f"{self.base_url}/auth/token",
            data={"username": username, "password": password}
        )
        data = response.json()
        self.token = data["access_token"]
        return data

    def _headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}

    def upload_file(self, file_path):
        """Upload a file"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/upload",
                headers=self._headers(),
                files={"file": f}
            )
        return response.json()

    def query(self, question):
        """Query the data"""
        response = requests.post(
            f"{self.base_url}/query",
            headers=self._headers(),
            json={"question": question, "return_sources": True}
        )
        return response.json()

    def create_dashboard(self, file_id):
        """Create visualization dashboard"""
        response = requests.post(
            f"{self.base_url}/visualize/dashboard/{file_id}",
            headers=self._headers()
        )
        return response.json()

    def get_stats(self):
        """Get user statistics"""
        response = requests.get(
            f"{self.base_url}/auth/me/stats",
            headers=self._headers()
        )
        return response.json()

# Usage
client = RAGClient()

# Register
user = client.register("john_doe", "john@example.com", "password123", "John Doe")
print(f"Registered user: {user['username']}")
print(f"API Key: {user['api_key']}")

# Login
token_data = client.login("john_doe", "password123")
print("Logged in successfully!")

# Upload file
result = client.upload_file("sales_data.csv")
print(f"Uploaded: {result['file_name']}")

# Query
answer = client.query("What are the top trends in the data?")
print(f"Answer: {answer['answer']}")

# Create dashboard
dashboard = client.create_dashboard(1)
print(f"Dashboard created with {len(dashboard['visualizations'])} visualizations")

# Get stats
stats = client.get_stats()
print(f"Files: {stats['total_files']}, Queries: {stats['total_queries']}")
```

---

## Security Best Practices

1. **Change Default Admin Password**
   ```bash
   curl -X PUT "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"password": "new_secure_password"}'
   ```

2. **Store Tokens Securely**
   - Never commit tokens to version control
   - Use environment variables
   - Rotate API keys regularly

3. **Use HTTPS in Production**
   - Configure SSL/TLS certificates
   - Never send tokens over HTTP

4. **API Key Rotation**
   ```bash
   curl -X POST "http://localhost:8000/auth/me/regenerate-api-key" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

5. **Monitor User Activity**
   - Check query history
   - Review file uploads
   - Monitor storage usage

---

## Troubleshooting

### Authentication Errors

**Problem:** `401 Unauthorized`

**Solutions:**
- Verify token is valid and not expired
- Check Authorization header format
- Ensure API key is correct

### Permission Errors

**Problem:** `403 Forbidden`

**Solutions:**
- Verify user has required permissions
- Check if admin role is needed
- Confirm user is active

### Visualization Errors

**Problem:** Chart generation fails

**Solutions:**
- Verify file_id exists
- Check column names are correct
- Ensure file type is supported
- Confirm numeric columns for certain charts

---

## What's Next?

Explore these advanced capabilities:
1. Create dashboards for uploaded files
2. Export visualizations for reports
3. Set up multi-user environments
4. Track usage statistics
5. Build custom workflows with authentication

For more information, see:
- [README.md](README.md) - General overview
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference
- [GUI_GUIDE.md](GUI_GUIDE.md) - Web interface guide

---

**Built with**: FastAPI, SQLAlchemy, JWT, Plotly, and secure authentication best practices
