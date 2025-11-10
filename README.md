# Intelligent RAG Data Analysis Tool

An AI-powered data analysis tool that uses Retrieval Augmented Generation (RAG) to analyze Excel and CSV files. Upload multiple datasets and ask questions in natural language to get insights, trends, and detailed analysis.

## Features

### Core Features
- **🎨 Beautiful Web GUI**: Two intuitive interfaces (Streamlit + HTML/JS)
- **📤 Multi-File Support**: Upload and analyze 50+ Excel/CSV files simultaneously
- **🤖 RAG-Powered Analysis**: Uses LangChain and vector embeddings for intelligent data retrieval
- **💬 Natural Language Queries**: Ask questions about your data in plain English
- **✨ Automatic Insights**: Generate comprehensive insights automatically
- **🔧 Flexible LLM Support**: Works with OpenAI GPT or Anthropic Claude
- **📊 Local or Cloud Embeddings**: Choose between OpenAI embeddings or local Sentence Transformers
- **🚀 RESTful API**: Easy-to-use FastAPI endpoints
- **💾 Persistent Storage**: ChromaDB vector store persists your data

### Advanced Features (NEW! ✨)
- **🔐 User Authentication**: Secure JWT token & API key authentication
- **👥 Multi-Tenancy**: Data isolation per user/organization
- **📈 Advanced Visualizations**: Interactive dashboards with Plotly
  - Correlation matrices with insights
  - Distribution plots and histograms
  - Time series analysis
  - Missing data visualizations
  - Chart export (PNG, PDF, SVG)
- **🛡️ User Management**: Admin dashboard for user control
- **📊 Usage Statistics**: Track files, queries, and storage per user
- **🎯 Role-Based Access**: Admin and user roles

### Intelligent Analytics (NEW! 🚀)
- **🧠 Smart Query Routing**: Automatically detects query intent and routes to appropriate backend
  - RAG for semantic questions ("What trends do you see?")
  - Analytics for exact data queries ("Find duplicates")
  - Metadata for system queries ("How many files?")
- **🔍 Cross-File Analytics**: Direct data analysis across all uploaded files
  - Find duplicates with occurrence counts and file tracking
  - Get unique values with frequency analysis
  - Perform aggregations (count, sum, mean, min, max)
  - Group by any column for segmented analysis
- **📥 Complete CSV Export**: Download full analytics reports
  - Automatic CSV generation for every analytics query
  - Complete data (not limited to preview)
  - Excel-compatible format for further analysis
  - Timestamped exports for audit trails

👉 **See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for complete guide**

## Architecture

```
┌─────────────┐
│  CSV/Excel  │
│   Files     │
└──────┬──────┘
       │
       v
┌─────────────────┐
│ Data Processor  │  ← Pandas-based chunking & summarization
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         v                  v
┌─────────────────┐  ┌──────────────┐
│   Embeddings    │  │   Database   │  ← SQLAlchemy (File tracking)
│ (RAG Storage)   │  │   (SQLite)   │
└────────┬────────┘  └──────┬───────┘
         │                  │
         v                  │
┌─────────────────┐         │
│    ChromaDB     │         │
│  Vector Store   │         │
└────────┬────────┘         │
         │                  │
         v                  v
     User Query ──────> Query Router  ← Smart Intent Detection
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         v                  v                  v
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │   RAG    │      │Analytics │      │ Metadata │
   │ (Semantic)│      │ (Exact)  │      │(Overview)│
   └────┬─────┘      └────┬─────┘      └────┬─────┘
        │                 │                   │
        v                 v                   │
   ┌──────────┐      ┌──────────┐           │
   │   LLM    │      │  Pandas  │           │
   │(GPT/     │      │Direct SQL│           │
   │ Claude)  │      └────┬─────┘           │
   └────┬─────┘           │                  │
        │                 v                  │
        │          ┌──────────┐              │
        │          │CSV Export│              │
        │          └────┬─────┘              │
        │               │                    │
        └───────────────┴────────────────────┘
                        │
                        v
                 User Response
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voyager
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_key_here

   LLM_PROVIDER=openai  # or anthropic
   LLM_MODEL=gpt-4-turbo-preview  # or claude-3-sonnet-20240229
   ```

## Usage

### Option 1: Web GUI (Recommended)

Start the beautiful Streamlit interface:

```bash
# Launches both API and Streamlit GUI
python run_gui.py
```

Then open your browser to:
- **Streamlit GUI**: http://localhost:8501
- **API**: http://localhost:8000

Or use the HTML interface:

```bash
# Start API only
python run.py
```

Then open: **http://localhost:8000** (HTML GUI)

See [GUI_GUIDE.md](GUI_GUIDE.md) for complete GUI documentation.

### Option 2: API Only

```bash
# From the project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

### API Endpoints

#### Core Endpoints

##### 1. Upload Single File

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_data.csv"
```

##### 2. Upload Multiple Files

```bash
curl -X POST "http://localhost:8000/upload-multiple" \
  -F "files=@file1.csv" \
  -F "files=@file2.xlsx" \
  -F "files=@file3.csv"
```

##### 3. Intelligent Query (Automatic Routing)

The `/query` endpoint now automatically detects query intent and routes to the appropriate backend:

```bash
# Semantic question → RAG
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What trends do you see in the sales data?"}'

# Duplicate detection → Analytics
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Find duplicate msisdns across all files"}'

# File count → Metadata
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many files do we have?"}'
```

##### 4. Get Data Overview

```bash
curl -X GET "http://localhost:8000/overview"
```

##### 5. Get Automatic Insights

```bash
curl -X POST "http://localhost:8000/insights?focus=sales%20trends"
```

##### 6. Clear All Data

```bash
curl -X DELETE "http://localhost:8000/clear"
```

#### Analytics Endpoints (Direct Access)

##### 7. Find Duplicates

```bash
curl -X GET "http://localhost:8000/analytics/duplicates?column=msisdn"
```

Response includes:
- List of all duplicate values
- Occurrence counts per file
- Total files analyzed
- **CSV download link** for complete report

##### 8. Get Unique Values

```bash
curl -X GET "http://localhost:8000/analytics/column-values?column=segment&limit=100"
```

Response includes:
- Unique values with frequency counts
- **CSV download link** for complete list

##### 9. Aggregate Data

```bash
curl -X GET "http://localhost:8000/analytics/aggregate?column=revenue&operation=sum&group_by=region"
```

Operations: `count`, `sum`, `mean`, `min`, `max`

##### 10. Download CSV Export

```bash
curl -O "http://localhost:8000/download/duplicates_msisdn_20251110_043022_a1b2c3d4.csv"
```

CSV files are automatically generated for analytics queries and stored in `data/exports/`

### Example Python Client

```python
import requests

# Upload files
with open('sales_data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )
    print(response.json())

# Intelligent query (automatic routing)
response = requests.post(
    'http://localhost:8000/query',
    json={
        'question': 'Find duplicate customer IDs across all files',
        'return_sources': True
    }
)
result = response.json()
print(f"Answer: {result['answer']}")

# If CSV export is available, download it
if 'sources' in result and result['sources']:
    metadata = result['sources'][0].get('metadata', {})
    if 'csv_download_url' in metadata:
        csv_url = f"http://localhost:8000{metadata['csv_download_url']}"
        csv_response = requests.get(csv_url)
        with open('duplicates_report.csv', 'wb') as f:
            f.write(csv_response.content)
        print("CSV report downloaded!")

# Direct analytics query
response = requests.get(
    'http://localhost:8000/analytics/duplicates',
    params={'column': 'msisdn'}
)
analytics = response.json()
print(f"Found {analytics['total_duplicates']} duplicates")
print(f"Download CSV: {analytics['csv_download_url']}")

# Get automatic insights
response = requests.post(
    'http://localhost:8000/insights',
    params={'focus': 'customer behavior'}
)
print(response.json())
```

## How It Works

### Data Processing Pipeline

1. **File Upload**: CSV/Excel files are uploaded via the API
2. **Dual Storage**: Each file is:
   - Tracked in SQLite database (metadata, file paths, status)
   - Processed for RAG (chunking, embeddings, vector storage)
3. **Data Chunking** (for RAG): Each file is:
   - Read into a pandas DataFrame
   - Analyzed for structure (columns, types, statistics)
   - Split into manageable chunks (default: 50 rows per chunk)
   - Summary metadata is generated
4. **Embedding Generation**: Each chunk is converted to vector embeddings
5. **Vector Storage**: Embeddings are stored in ChromaDB with metadata
6. **Intelligent Query Processing**: User questions go through:
   - **Intent Detection**: Query router analyzes the question
     - Metadata queries: "How many files?" → Database overview
     - Duplicate detection: "Find duplicates" → Analytics engine
     - Unique values: "List unique segments" → Analytics engine
     - Aggregations: "Average revenue by region" → Analytics engine
     - Semantic questions: "What trends..." → RAG engine
   - **Routing**: Query is sent to appropriate backend
   - **Processing**:
     - RAG: Retrieves top 20 chunks, sends to LLM with context
     - Analytics: Directly queries database + reads files with Pandas
     - Metadata: Queries vector store for file information
   - **CSV Export**: Analytics queries automatically generate CSV reports
7. **Response**: Formatted answer with optional CSV download link

### Chunking Strategy

The tool uses an intelligent chunking strategy:

- **Summary Chunk**: First chunk contains overall dataset summary
- **Data Chunks**: Subsequent chunks contain actual data rows with:
  - Row ranges
  - All columns
  - Statistical summaries for numeric columns
  - Metadata about source file

This ensures both high-level understanding and detailed data access.

## Configuration Options

### LLM Providers

**OpenAI** (Recommended for best quality)
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for faster/cheaper
OPENAI_API_KEY=your_key
```

**Anthropic Claude**
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=your_key
```

### Embedding Options

**OpenAI Embeddings** (Best quality, requires API key)
```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

**Local Embeddings** (Free, runs locally)
```env
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Example Use Cases

### 1. Data Quality & Duplicate Detection
Upload multiple data files and ask:
- **"Find duplicate MSISDNs across all files"** → Analytics engine finds all duplicates
- **"Are there any repeated customer IDs?"** → Gets complete duplicate report
- **"Show me unique segments"** → Lists all unique values with counts
- **"How many files have we uploaded?"** → Metadata overview
- **Download complete CSV** with all 610 duplicates (not just top 20)

### 2. Sales Analysis
Upload multiple sales CSV files and ask:
- "What were the top performing products last quarter?" → RAG analysis
- "Count sales by region" → Analytics aggregation
- "Show me sales trends over time" → RAG with time series insights
- "Which customers have the highest lifetime value?" → RAG analysis

### 3. Financial Data
Upload financial spreadsheets and query:
- "What are the main expense categories?" → RAG semantic analysis
- "Sum revenue by department" → Analytics aggregation
- "Find duplicate transaction IDs" → Analytics duplicate detection
- "Identify unusual transactions or outliers" → RAG analysis

### 4. Customer Analytics
Upload customer data and ask:
- "Find duplicate email addresses" → Analytics with CSV export
- "List unique customer segments" → Analytics unique values
- "What are the common characteristics of our best customers?" → RAG analysis
- "Average customer lifetime value by segment" → Analytics aggregation

### 5. Telecom Data Analysis
Upload subscriber/usage data and query:
- "Find duplicate MSISDNs across all files" → Analytics (complete CSV)
- "List unique IMEIs" → Analytics unique values
- "Count subscribers by segment" → Analytics aggregation
- "What trends do you see in usage patterns?" → RAG semantic analysis
- "Average revenue by region" → Analytics with grouping

## Performance Considerations

- **File Size**: Tested with files up to 100MB each
- **Number of Files**: Supports 50+ files simultaneously
- **Query Speed**: Typically 2-5 seconds depending on LLM provider
- **Memory**: ~2GB RAM for moderate datasets (10-20 files)
- **Storage**: Vector store grows ~10-20% of original data size

## Troubleshooting

### Common Issues

**API Key Errors**
```
Error: OpenAI API key not provided
```
Solution: Ensure `.env` file has valid API key

**File Upload Fails**
```
Error: Unsupported file type
```
Solution: Only .csv, .xlsx, .xls files are supported

**Poor Query Results**
- Try being more specific in your questions
- Ensure uploaded files contain relevant data
- Consider using GPT-4 instead of GPT-3.5 for better analysis

## Development

### Project Structure

```
voyager/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── data_processor.py    # Data processing & chunking
│   ├── rag_engine.py        # RAG implementation
│   ├── query_router.py      # 🆕 Intelligent query routing
│   ├── analytics_routes.py  # 🆕 Analytics endpoints
│   ├── database.py          # Database models & connection
│   ├── auth.py              # Authentication logic
│   ├── auth_routes.py       # User management API
│   ├── viz_routes.py        # Visualization endpoints
│   └── visualizations.py    # Chart generation
├── static/                  # HTML/CSS/JS web interface
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   ├── uploads/             # Uploaded files
│   ├── vectorstore/         # ChromaDB storage
│   ├── exports/             # 🆕 Generated CSV reports
│   ├── app.db               # SQLite database
│   └── tenants/             # Multi-tenant file storage
├── app.py                   # Streamlit GUI application
├── run_gui.py               # GUI launcher script
├── run.py                   # API launcher script
├── example_usage.py         # Python usage examples
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── ADVANCED_FEATURES.md     # Advanced features guide
├── GUI_GUIDE.md             # Complete GUI documentation
├── QUICKSTART.md            # Quick start guide
└── API_DOCUMENTATION.md     # API reference
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Documentation

- **[README.md](README.md)** - This file, comprehensive overview
- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - ⭐ Authentication, Multi-Tenancy & Visualizations
- **[GUI_GUIDE.md](GUI_GUIDE.md)** - Complete guide to using the web interfaces
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Full API reference

## Roadmap

- [x] Web UI for easier interaction (Streamlit + HTML)
- [x] Advanced visualization of insights
- [x] User authentication & multi-tenancy
- [x] Intelligent query routing with intent detection
- [x] Cross-file analytics (duplicates, unique values, aggregations)
- [x] CSV export for complete analytics reports
- [x] File persistence for all users (authenticated & unauthenticated)
- [ ] Support for more file formats (JSON, Parquet)
- [ ] Multi-language support
- [ ] Scheduled automatic insights
- [ ] Export insights to PDF/Word
- [ ] Collaborative workspaces
- [ ] ML-based intent classification (vs regex patterns)
- [ ] Real-time data streaming support
- [ ] Advanced aggregations (median, percentile, variance)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for any purpose.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with**: FastAPI, LangChain, ChromaDB, Pandas, and OpenAI/Anthropic APIs
