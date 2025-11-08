# API Documentation

Complete API reference for the Intelligent RAG Data Analysis Tool.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production use, consider adding API key authentication.

## Endpoints

### 1. Root Endpoint

Get basic information about the API.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "Intelligent RAG Data Analysis Tool",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### 2. Health Check

Check if the server is running and RAG engine is initialized.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "rag_engine_initialized": true
}
```

---

### 3. Upload Single File

Upload a single CSV or Excel file for analysis.

**Endpoint:** `POST /upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): The file to upload (.csv, .xlsx, .xls)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sales_data.csv"
```

**Success Response:**
```json
{
  "success": true,
  "file_name": "sales_data.csv",
  "chunks_created": 15,
  "insights": {
    "shape": {
      "rows": 1000,
      "columns": 6
    },
    "columns": ["Date", "Product", "Region", "Sales", "Quantity", "Customer_Segment"],
    "missing_values": {
      "Date": 0,
      "Product": 2,
      "Region": 0,
      "Sales": 1,
      "Quantity": 0,
      "Customer_Segment": 5
    },
    "data_types": {
      "Date": "object",
      "Product": "object",
      "Region": "object",
      "Sales": "int64",
      "Quantity": "int64",
      "Customer_Segment": "object"
    },
    "numeric_stats": {
      "Sales": {
        "mean": 450.5,
        "std": 200.3,
        "min": 100.0,
        "max": 999.0
      },
      "Quantity": {
        "mean": 25.2,
        "std": 14.1,
        "min": 1.0,
        "max": 50.0
      }
    },
    "categorical_unique_counts": {
      "Product": 3,
      "Region": 4,
      "Customer_Segment": 3
    }
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "file_name": "data.txt",
  "error": "Unsupported file type: .txt. Supported types: .csv, .xlsx, .xls"
}
```

---

### 4. Upload Multiple Files

Upload multiple CSV or Excel files at once (supports 50+ files).

**Endpoint:** `POST /upload-multiple`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `files` (required): Array of files to upload

**Example Request:**
```bash
curl -X POST "http://localhost:8000/upload-multiple" \
  -F "files=@sales_2023.csv" \
  -F "files=@sales_2024.csv" \
  -F "files=@customer_data.xlsx"
```

**Success Response:**
```json
[
  {
    "success": true,
    "file_name": "sales_2023.csv",
    "chunks_created": 12,
    "insights": { /* ... */ }
  },
  {
    "success": true,
    "file_name": "sales_2024.csv",
    "chunks_created": 8,
    "insights": { /* ... */ }
  },
  {
    "success": true,
    "file_name": "customer_data.xlsx",
    "chunks_created": 20,
    "insights": { /* ... */ }
  }
]
```

---

### 5. Query Data

Ask questions about the uploaded data in natural language.

**Endpoint:** `POST /query`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "question": "What are the top 5 products by sales?",
  "return_sources": true
}
```

**Parameters:**
- `question` (required): The question to ask about the data
- `return_sources` (optional): Whether to return source documents (default: true)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top 5 products by sales?",
    "return_sources": true
  }'
```

**Success Response:**
```json
{
  "success": true,
  "question": "What are the top 5 products by sales?",
  "answer": "Based on the sales data across all uploaded files, the top 5 products by total sales are:\n\n1. Product A: $1,234,567 (45% of total sales)\n2. Product B: $987,654 (35% of total sales)\n3. Product C: $543,210 (20% of total sales)\n4. Product D: $234,567 (8% of total sales)\n5. Product E: $123,456 (4% of total sales)\n\nProduct A clearly dominates with nearly half of all sales, followed by Product B and C which together account for another 55%.",
  "sources": [
    {
      "content": "Data from sales_2024.csv (rows 1 to 50):\nColumns: Date, Product, Region, Sales...",
      "metadata": {
        "file_name": "sales_2024.csv",
        "chunk_type": "data",
        "chunk_id": 2,
        "row_start": 0,
        "row_end": 50,
        "total_rows": 1000,
        "columns": ["Date", "Product", "Region", "Sales"]
      }
    }
  ]
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Question cannot be empty"
}
```

---

### 6. Get Data Overview

Get an overview of all uploaded datasets.

**Endpoint:** `GET /overview`

**Example Request:**
```bash
curl -X GET "http://localhost:8000/overview"
```

**Success Response:**
```json
{
  "total_files": 3,
  "total_chunks": 45,
  "files": [
    {
      "file_name": "sales_2023.csv",
      "total_rows": 1000,
      "columns": ["Date", "Product", "Region", "Sales", "Quantity"],
      "chunks": 15
    },
    {
      "file_name": "sales_2024.csv",
      "total_rows": 500,
      "columns": ["Date", "Product", "Region", "Sales", "Quantity"],
      "chunks": 10
    },
    {
      "file_name": "customer_data.xlsx",
      "total_rows": 2000,
      "columns": ["CustomerID", "Name", "Segment", "Revenue"],
      "chunks": 20
    }
  ]
}
```

---

### 7. Get Automatic Insights

Get AI-generated insights about the uploaded data.

**Endpoint:** `POST /insights`

**Query Parameters:**
- `focus` (optional): Specific aspect to focus on (e.g., "sales trends", "customer behavior")

**Example Requests:**
```bash
# General insights
curl -X POST "http://localhost:8000/insights"

# Focused insights
curl -X POST "http://localhost:8000/insights?focus=sales%20trends"
```

**Success Response:**
```json
{
  "success": true,
  "focus": "sales trends",
  "insights": "Based on the comprehensive analysis of all datasets:\n\n1. **Sales Trends**: Sales show a consistent upward trend throughout 2023-2024, with a 23% year-over-year growth. Peak sales occur in Q4 (October-December), likely due to holiday shopping.\n\n2. **Regional Performance**: The East region leads with 35% of total sales, followed by West (28%), North (22%), and South (15%). This suggests focusing expansion efforts on underperforming regions.\n\n3. **Product Mix**: Product A accounts for nearly half of all sales but has shown declining margins. Diversification into Products B and C could reduce dependency.\n\n4. **Customer Segments**: Enterprise customers provide 60% of revenue but represent only 15% of total customers, indicating strong enterprise focus with good SMB growth potential.\n\n5. **Actionable Recommendations**:\n   - Invest in South region marketing\n   - Develop premium versions of Products B and C\n   - Create SMB-specific offerings\n   - Address Product A margin decline",
  "based_on_files": [
    "sales_2023.csv",
    "sales_2024.csv",
    "customer_data.xlsx"
  ]
}
```

---

### 8. Clear All Data

Clear all uploaded data and reset the vector store.

**Endpoint:** `DELETE /clear`

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/clear"
```

**Success Response:**
```json
{
  "success": true,
  "message": "Vectorstore cleared"
}
```

---

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 500 | Internal Server Error |

## Rate Limiting

Currently, no rate limiting is implemented. For production, consider adding rate limiting based on your needs.

## Python Client Example

```python
import requests

class RAGAnalysisClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def health_check(self):
        return requests.get(f"{self.base_url}/health").json()

    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/upload",
                files={'file': f}
            )
        return response.json()

    def upload_files(self, file_paths):
        files = [('files', open(fp, 'rb')) for fp in file_paths]
        response = requests.post(
            f"{self.base_url}/upload-multiple",
            files=files
        )
        for _, f in files:
            f.close()
        return response.json()

    def query(self, question, return_sources=True):
        response = requests.post(
            f"{self.base_url}/query",
            json={
                "question": question,
                "return_sources": return_sources
            }
        )
        return response.json()

    def get_overview(self):
        return requests.get(f"{self.base_url}/overview").json()

    def get_insights(self, focus=None):
        params = {"focus": focus} if focus else {}
        response = requests.post(
            f"{self.base_url}/insights",
            params=params
        )
        return response.json()

    def clear_data(self):
        return requests.delete(f"{self.base_url}/clear").json()

# Usage
client = RAGAnalysisClient()
print(client.health_check())
client.upload_file("data.csv")
result = client.query("What are the main trends?")
print(result['answer'])
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to test all endpoints directly from your browser.
