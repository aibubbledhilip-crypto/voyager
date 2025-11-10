# Quick Start Guide

Get up and running with the Intelligent RAG Data Analysis Tool in 5 minutes!

Now with **beautiful web GUI** for easy interaction!

## Prerequisites

- Python 3.9+ installed
- An OpenAI API key (or Anthropic Claude API key)
- Some CSV or Excel files to analyze

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd voyager

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# Use any text editor, for example:
nano .env
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```

Or if using Claude:
```env
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
```

## Step 3: Start the Application

### Option A: With Web GUI (Recommended)

```bash
# Launches both API and beautiful Streamlit GUI
python run_gui.py
```

You should see:
```
🚀 Starting Intelligent RAG Data Analysis Tool - GUI Launcher
✅ All dependencies installed
🌐 Starting services...
📍 API will be available at: http://localhost:8000
📍 Web GUI will be available at: http://localhost:8501
```

Your browser will automatically open to the Streamlit interface!

### Option B: API Only + HTML GUI

```bash
# Starts only the API server
python run.py
```

Then access:
- **HTML GUI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Step 4: Use the Application

### With Web GUI (Easy!)

1. **The Streamlit interface opens automatically** at http://localhost:8501
2. Go to the **"Upload Data"** tab
3. **Drag and drop** your CSV/Excel files (or click "Choose Files")
4. Click **"Upload and Process"**
5. Switch to **"Ask Questions"** tab
6. Type a question or click a quick question button
7. **Get instant AI-powered answers!**

See [GUI_GUIDE.md](GUI_GUIDE.md) for complete GUI documentation.

### With Python (For developers)

Open a new terminal (keep the server running):

```bash
# Activate virtual environment again
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the example script (creates sample data and tests the API)
python example_usage.py
```

This will:
1. Create a sample sales dataset
2. Upload it to the system
3. Ask several questions
4. Show you the AI-generated answers

## Step 5: Upload Your Own Data

### Option A: Using the Web Interface

1. Open http://localhost:8000/docs in your browser
2. Find the `/upload` endpoint
3. Click "Try it out"
4. Choose your CSV/Excel file
5. Click "Execute"

### Option B: Using Python

```python
import requests

# Upload a file
with open('your_data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )
print(response.json())
```

### Option C: Using cURL

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_data.csv"
```

## Step 6: Ask Questions

### Via Web Interface

1. Go to http://localhost:8000/docs
2. Find the `/query` endpoint
3. Click "Try it out"
4. Enter your question:
   ```json
   {
     "question": "What are the main trends in the data?",
     "return_sources": true
   }
   ```
5. Click "Execute"

### Via Python

```python
import requests

response = requests.post(
    'http://localhost:8000/query',
    json={
        'question': 'What are the top 5 products by revenue?',
        'return_sources': True
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
```

### Via cURL

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me sales trends over time",
    "return_sources": true
  }'
```

## Common Questions

**Q: What file formats are supported?**
A: CSV (.csv), Excel (.xlsx, .xls)

**Q: How many files can I upload?**
A: 50+ files simultaneously. The system is designed to handle large numbers of files.

**Q: How do I upload multiple files at once?**
A: Use the `/upload-multiple` endpoint:

```python
files = [
    ('files', open('file1.csv', 'rb')),
    ('files', open('file2.xlsx', 'rb')),
    ('files', open('file3.csv', 'rb'))
]
response = requests.post('http://localhost:8000/upload-multiple', files=files)
```

**Q: Can I use local models instead of OpenAI?**
A: Yes! Set `EMBEDDING_PROVIDER=sentence-transformers` in .env for free local embeddings. For the LLM, you can use Anthropic Claude or set up a local LLM server.

**Q: How do I clear all uploaded data?**
A: Use the `/clear` endpoint:

```bash
curl -X DELETE "http://localhost:8000/clear"
```

**Q: Where is my data stored?**
A:
- Uploaded files: `./data/uploads/`
- Vector embeddings: `./data/vectorstore/`

**Q: How much does it cost?**
A: Costs depend on your LLM/embedding provider:
- OpenAI: ~$0.001 per query (GPT-4), ~$0.0001 per file embedded
- Claude: Similar pricing
- Local embeddings: Free (uses your CPU)

## Example Workflow

Here's a complete workflow analyzing sales data:

```python
import requests

base = "http://localhost:8000"

# 1. Upload files
files = [
    ('files', open('sales_2023.csv', 'rb')),
    ('files', open('sales_2024.csv', 'rb')),
    ('files', open('products.xlsx', 'rb'))
]
upload_result = requests.post(f"{base}/upload-multiple", files=files)
print(f"Uploaded {len(upload_result.json())} files")

# 2. Get overview
overview = requests.get(f"{base}/overview").json()
print(f"Total files: {overview['total_files']}, chunks: {overview['total_chunks']}")

# 3. Ask questions
questions = [
    "What was the total revenue in 2023 vs 2024?",
    "Which products are growing the fastest?",
    "What are the seasonal trends?",
    "Which customer segments should we focus on?",
    "Are there any concerning patterns in the data?"
]

for q in questions:
    response = requests.post(f"{base}/query", json={"question": q})
    print(f"\nQ: {q}")
    print(f"A: {response.json()['answer']}\n")

# 4. Get automatic insights
insights = requests.post(f"{base}/insights", params={"focus": "growth opportunities"})
print(f"Insights: {insights.json()['insights']}")
```

## Next Steps

- Read the [full README](README.md) for detailed information
- Check [API Documentation](API_DOCUMENTATION.md) for all endpoints
- Explore the interactive docs at http://localhost:8000/docs
- Customize the chunking strategy in `backend/data_processor.py`
- Adjust the RAG parameters in `backend/rag_engine.py`

## Troubleshooting

**Server won't start**
- Check if port 8000 is already in use
- Verify Python version: `python --version` (should be 3.9+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

**API key errors**
- Verify your API key is correct in .env
- Check you don't have spaces or quotes around the key
- Make sure .env file is in the project root

**Upload fails**
- Check file format (.csv, .xlsx, .xls only)
- Verify file is not corrupted
- Check file size (default limit: 100MB)

**Poor query results**
- Be more specific in your questions
- Upload more relevant data files
- Try GPT-4 instead of GPT-3.5 for better analysis

**Out of memory**
- Reduce chunk size in data_processor.py
- Process fewer files at once
- Use a machine with more RAM

## Getting Help

- Check the [README](README.md) for detailed documentation
- Review [API Documentation](API_DOCUMENTATION.md)
- Open an issue on GitHub
- Check server logs for error messages

Enjoy analyzing your data! 🚀
