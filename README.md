# Intelligent RAG Data Analysis Tool

An AI-powered data analysis tool that uses Retrieval Augmented Generation (RAG) to analyze Excel and CSV files. Upload multiple datasets and ask questions in natural language to get insights, trends, and detailed analysis.

## Features

- **Multi-File Support**: Upload and analyze 50+ Excel/CSV files simultaneously
- **RAG-Powered Analysis**: Uses LangChain and vector embeddings for intelligent data retrieval
- **Natural Language Queries**: Ask questions about your data in plain English
- **Automatic Insights**: Generate comprehensive insights automatically
- **Flexible LLM Support**: Works with OpenAI GPT or Anthropic Claude
- **Local or Cloud Embeddings**: Choose between OpenAI embeddings or local Sentence Transformers
- **RESTful API**: Easy-to-use FastAPI endpoints
- **Persistent Storage**: ChromaDB vector store persists your data

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
         v
┌─────────────────┐
│   Embeddings    │  ← OpenAI or Local (Sentence Transformers)
└────────┬────────┘
         │
         v
┌─────────────────┐
│    ChromaDB     │  ← Vector storage & retrieval
│  Vector Store   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│   RAG Engine    │  ← LangChain QA Chain
└────────┬────────┘
         │
         v
┌─────────────────┐
│  LLM (GPT/Claude)│ ← Answer generation
└────────┬────────┘
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

### Starting the Server

```bash
# From the project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

### API Endpoints

#### 1. Upload Single File

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_data.csv"
```

#### 2. Upload Multiple Files

```bash
curl -X POST "http://localhost:8000/upload-multiple" \
  -F "files=@file1.csv" \
  -F "files=@file2.xlsx" \
  -F "files=@file3.csv"
```

#### 3. Query Data

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top 5 trends in the sales data?",
    "return_sources": true
  }'
```

#### 4. Get Data Overview

```bash
curl -X GET "http://localhost:8000/overview"
```

#### 5. Get Automatic Insights

```bash
curl -X POST "http://localhost:8000/insights?focus=sales%20trends"
```

#### 6. Clear All Data

```bash
curl -X DELETE "http://localhost:8000/clear"
```

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

# Query the data
response = requests.post(
    'http://localhost:8000/query',
    json={
        'question': 'What is the average sales by region?',
        'return_sources': True
    }
)
result = response.json()
print(f"Answer: {result['answer']}")

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
2. **Data Chunking**: Each file is:
   - Read into a pandas DataFrame
   - Analyzed for structure (columns, types, statistics)
   - Split into manageable chunks (default: 50 rows per chunk)
   - Summary metadata is generated
3. **Embedding Generation**: Each chunk is converted to vector embeddings
4. **Vector Storage**: Embeddings are stored in ChromaDB with metadata
5. **Query Processing**: User questions are:
   - Embedded using the same model
   - Used to retrieve relevant data chunks (top 10 most similar)
   - Sent to LLM with context for answer generation
6. **Response**: AI-generated answer with source references

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

### 1. Sales Analysis
Upload multiple sales CSV files and ask:
- "What were the top performing products last quarter?"
- "Show me sales trends by region over time"
- "Which customers have the highest lifetime value?"

### 2. Financial Data
Upload financial spreadsheets and query:
- "What are the main expense categories?"
- "Compare revenue growth year over year"
- "Identify unusual transactions or outliers"

### 3. Customer Analytics
Upload customer data and ask:
- "What are the common characteristics of our best customers?"
- "Segment customers by behavior patterns"
- "Predict which customers are at risk of churning"

### 4. Inventory Management
Upload inventory Excel files and query:
- "Which products are running low on stock?"
- "What's the average inventory turnover rate?"
- "Identify slow-moving items"

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
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   ├── data_processor.py # Data processing & chunking
│   └── rag_engine.py     # RAG implementation
├── data/
│   ├── uploads/          # Uploaded files
│   └── vectorstore/      # ChromaDB storage
├── .env                  # Environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Roadmap

- [ ] Web UI for easier interaction
- [ ] Support for more file formats (JSON, Parquet)
- [ ] Advanced visualization of insights
- [ ] Multi-language support
- [ ] Scheduled automatic insights
- [ ] Export insights to PDF/Word
- [ ] User authentication & multi-tenancy

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for any purpose.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with**: FastAPI, LangChain, ChromaDB, Pandas, and OpenAI/Anthropic APIs
