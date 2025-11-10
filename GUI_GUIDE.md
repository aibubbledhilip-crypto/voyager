# GUI User Guide

The Intelligent RAG Data Analysis Tool provides **two beautiful web interfaces** for easy interaction with your data.

## Option 1: Streamlit Web App (Recommended)

A feature-rich, interactive web application built with Streamlit.

### Starting Streamlit GUI

```bash
# Quick start - launches both API and GUI
python run_gui.py
```

The application will open in your browser automatically at **http://localhost:8501**

### Features

- **📤 Upload Data Tab**
  - Drag-and-drop file upload
  - Batch upload support (50+ files)
  - Real-time upload progress
  - File processing details
  - Visual feedback

- **💬 Ask Questions Tab**
  - Natural language query interface
  - Quick question buttons
  - Chat-style conversation history
  - Source document references
  - Keyboard shortcuts (Ctrl+Enter to submit)

- **🔍 Auto Insights Tab**
  - Automatic insight generation
  - Focused insight categories
  - Pre-defined analysis templates
  - Comprehensive data analysis

- **📊 Data Overview Tab**
  - Interactive statistics cards
  - File details and metadata
  - Visual charts with Plotly
  - Column information
  - Real-time data refresh

- **⚙️ Sidebar**
  - API status indicator
  - Clear data function
  - Live statistics
  - About information

### Screenshots & Usage

#### 1. Uploading Files

1. Click the "📤 Upload Data" tab
2. Drag and drop your CSV/Excel files, or click "Choose Files"
3. Review selected files
4. Click "🚀 Upload and Process"
5. Wait for processing (shows progress)
6. View results and insights

#### 2. Asking Questions

1. Go to "💬 Ask Questions" tab
2. Either:
   - Type your question in the text area
   - Click a quick question button
3. Check/uncheck "Show sources" if needed
4. Click "🔍 Get Answer" or press Ctrl+Enter
5. View the AI-generated answer with sources
6. Scroll down to see conversation history

#### 3. Getting Insights

1. Navigate to "🔍 Auto Insights" tab
2. Either:
   - Leave focus area empty for general insights
   - Enter a specific focus (e.g., "sales trends")
   - Click a category button
3. Click "✨ Generate Insights"
4. Read comprehensive AI analysis

#### 4. Viewing Overview

1. Click "📊 Data Overview" tab
2. See summary statistics in cards
3. View uploaded files list
4. Check charts showing data distribution
5. Click "🔄 Refresh Overview" to update

### Keyboard Shortcuts

- `Ctrl + Enter` - Submit question (in Ask Questions tab)
- `Ctrl + R` - Refresh page
- `Esc` - Close dialogs/modals

---

## Option 2: HTML/CSS/JS Web Interface

A lightweight, standalone web interface that works in any modern browser.

### Starting HTML GUI

```bash
# Start only the API server
python run.py
```

Then open your browser to **http://localhost:8000**

### Features

- **Clean, Modern Design**
  - Gradient background
  - Smooth animations
  - Responsive layout
  - Mobile-friendly

- **Interactive Tabs**
  - Upload Data
  - Ask Questions
  - Auto Insights
  - Data Overview

- **Real-time Updates**
  - Live API status indicator
  - Instant feedback
  - Progress indicators

- **Drag & Drop**
  - Intuitive file upload
  - Visual file selection
  - Batch processing

### Usage

#### Uploading Files

1. Go to the "Upload Data" tab (default)
2. Drag files onto the upload box, or click "Choose Files"
3. See selected files listed
4. Click "Upload and Process"
5. View results with success/error indicators

#### Querying Data

1. Switch to "Ask Questions" tab
2. Click a quick question button or type your own
3. Toggle "Show sources" checkbox
4. Click "Get Answer"
5. See question and answer in chat-style format
6. View source documents if enabled

#### Auto Insights

1. Click "Auto Insights" tab
2. Optionally enter a focus area
3. Or click a category button:
   - Growth & Trends
   - Customer Analysis
   - Financial Performance
   - Top Performers
   - Risk & Anomalies
4. View comprehensive insights

#### Data Overview

1. Navigate to "Data Overview" tab
2. See summary cards (files, chunks, rows)
3. View detailed file information
4. Check file metadata and columns
5. Click "Refresh Overview" to update

### Sidebar Features

The right sidebar provides:
- API connection status
- Clear all data button
- About information
- Live statistics

---

## Comparison: Streamlit vs HTML

| Feature | Streamlit | HTML/JS |
|---------|-----------|---------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Visual Appeal** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Features** | More interactive | Standard |
| **Performance** | Good | Excellent |
| **Setup** | Run script | Just open URL |
| **Customization** | Python code | HTML/CSS/JS |
| **Best For** | Data scientists | Quick access |

**Recommendation**: Use **Streamlit** for the best experience. Use the **HTML interface** for lightweight access or when Streamlit isn't available.

---

## Common Tasks

### Task 1: Analyze Sales Data

1. **Upload Files**
   - Navigate to Upload tab
   - Upload: sales_2023.csv, sales_2024.csv, products.xlsx
   - Wait for processing

2. **Get Overview**
   - Go to Data Overview
   - Check total rows and columns
   - Verify all files uploaded

3. **Ask Questions**
   - "What were the total sales in 2023 vs 2024?"
   - "Which products had the highest growth?"
   - "What are the seasonal trends?"

4. **Generate Insights**
   - Go to Auto Insights
   - Focus: "sales performance and trends"
   - Review comprehensive analysis

### Task 2: Customer Analysis

1. **Upload** customer data files
2. **Quick Question**: "Show summary statistics"
3. **Custom Query**: "Segment customers by behavior"
4. **Auto Insights**: Click "Customer Analysis" category
5. **Review** patterns and recommendations

### Task 3: Find Anomalies

1. Upload relevant datasets
2. Click "Find anomalies" quick button
3. Or ask: "Are there any unusual patterns or outliers?"
4. Review AI analysis of anomalies
5. Ask follow-up questions for details

---

## Troubleshooting GUI Issues

### Streamlit Won't Start

**Problem**: `streamlit: command not found`

**Solution**:
```bash
pip install streamlit plotly
python run_gui.py
```

### HTML Interface Shows "API Offline"

**Problem**: Cannot connect to API

**Solution**:
1. Make sure API is running: `python run.py`
2. Check if port 8000 is available
3. Verify .env file has valid API keys
4. Check browser console for errors

### Uploads Fail

**Problem**: Files won't upload

**Solutions**:
- Check file format (.csv, .xlsx, .xls only)
- Verify file size (< 100MB by default)
- Ensure API server is running
- Check browser console for errors
- Try uploading fewer files at once

### Slow Performance

**Problem**: GUI is slow or unresponsive

**Solutions**:
- Reduce number of files uploaded
- Use smaller datasets
- Clear old data: click "Clear All Data"
- Restart both API and GUI
- Check system resources (RAM, CPU)

### Can't See Uploaded Files

**Problem**: Overview shows 0 files after upload

**Solutions**:
- Click "Refresh Overview" button
- Check upload results for errors
- Verify API logs for issues
- Try uploading again

---

## Advanced Features

### Streamlit-Specific

**Session State**: Your conversation history persists during the session

**File Caching**: Recently uploaded files are remembered

**Auto-Refresh**: Overview updates automatically after uploads

**Expandable Sections**: Click to expand/collapse details

### HTML-Specific

**Keyboard Navigation**: Tab through interface elements

**Drag & Drop**: Works with multiple files

**Responsive Design**: Works on tablets and phones

**No Installation**: Just open the URL

---

## Tips & Best Practices

### For Best Results

1. **Upload Order**: Upload related files together for better context

2. **File Naming**: Use descriptive names (e.g., `sales_2024_Q1.csv`)

3. **Question Clarity**: Be specific in your questions
   - ❌ "Show me data"
   - ✅ "What are the top 5 products by revenue in Q4 2024?"

4. **Use Quick Buttons**: Start with quick questions to understand your data

5. **Review Sources**: Check source documents to verify answers

6. **Generate Insights First**: Get overview before asking specific questions

7. **Clear Old Data**: Remove irrelevant data before new analysis

### Performance Tips

- Upload files in batches of 10-20 for large datasets
- Use focused questions instead of very broad queries
- Clear chat history periodically (refresh page)
- Close other browser tabs to free memory

### Security Notes

- All data processing happens locally
- API keys are never exposed to frontend
- Uploaded files stored in `data/uploads/`
- Clear data regularly if analyzing sensitive information

---

## Customization

### Streamlit Theme

Edit `.streamlit/config.toml` (create if doesn't exist):

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f9fafb"
textColor = "#1f2937"
font = "sans serif"
```

### HTML Styles

Edit `static/styles.css` to customize:
- Colors (`:root` CSS variables)
- Fonts
- Layout
- Animations

### API Configuration

Edit `.env` to change:
- Port numbers
- File size limits
- Model selection
- Embedding provider

---

## Getting Help

### Resources

- **README.md** - Full project documentation
- **API_DOCUMENTATION.md** - API endpoint reference
- **QUICKSTART.md** - Quick setup guide
- **/docs** - Interactive API docs (http://localhost:8000/docs)

### Support

If you encounter issues:
1. Check this guide first
2. Review error messages
3. Check API logs
4. Consult documentation
5. Open GitHub issue with details

---

## Next Steps

Now that you know how to use the GUI:

1. **Upload your data** and explore the features
2. **Try different types of questions** to see what works best
3. **Generate insights** to discover patterns
4. **Experiment with focus areas** for targeted analysis
5. **Share findings** by copying answers or screenshots

Enjoy analyzing your data with AI! 📊🚀
