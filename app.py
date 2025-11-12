"""
Streamlit Web GUI for voyager - Intelligent RAG Data Analysis Tool

A beautiful, user-friendly interface for uploading data files and
getting AI-powered insights from your CSV and Excel files.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import time
from typing import List, Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="voyager - Data Analysis",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .upload-box {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9ff;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .ai-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .powered-by {
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        color: #666;
        font-size: 0.9rem;
    }
    .powered-by img {
        height: 32px;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files_info' not in st.session_state:
    st.session_state.uploaded_files_info = []
if 'data_overview' not in st.session_state:
    st.session_state.data_overview = None


def login(username: str, password: str) -> bool:
    """Login user and get access token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data['access_token']

            # Get user info
            user_response = requests.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            if user_response.status_code == 200:
                st.session_state.user_info = user_response.json()
                st.session_state.authenticated = True
                return True
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False


def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.chat_history = []
    st.session_state.uploaded_files_info = []
    st.session_state.data_overview = None


def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers"""
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}


def show_login_page():
    """Show login page"""
    st.markdown('<div class="main-header">🚀 voyager</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Intelligent Data Analysis Platform</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.subheader("🔐 Sign In")
        st.markdown("Please login to access the data analysis tool")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Sign In", type="primary", use_container_width=True):
                if username and password:
                    with st.spinner("Signing in..."):
                        if login(username, password):
                            st.success("✅ Login successful!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                else:
                    st.warning("Please enter username and password")

        with col_b:
            if st.button("Register", use_container_width=True):
                st.info("Please visit http://localhost:8000/static/register.html to create an account")

        st.markdown('</div>', unsafe_allow_html=True)

        # Default credentials info
        st.info("💡 **Default Admin:** username=`admin`, password=`admin123`")

        # Powered by Prodapt
        st.markdown("""
        <div class="powered-by">
            <div>Powered by</div>
            <img src="https://www.prodapt.com/wp-content/uploads/Logo-for-website.svg" alt="Prodapt">
        </div>
        """, unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def upload_files_to_api(uploaded_files: List) -> List[Dict[str, Any]]:
    """Upload files to the API"""
    files = [('files', (file.name, file.getvalue(), file.type)) for file in uploaded_files]
    try:
        response = requests.post(
            f"{API_BASE_URL}/upload-multiple",
            files=files,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Session expired. Please login again.")
            logout()
            st.rerun()
        else:
            st.error(f"Upload failed: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error uploading files: {str(e)}")
        return []


def get_data_overview() -> Dict[str, Any]:
    """Get overview of uploaded data"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/overview",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logout()
            st.rerun()
        return {}
    except Exception as e:
        st.error(f"Error getting overview: {str(e)}")
        return {}


def query_data(question: str, return_sources: bool = True) -> Dict[str, Any]:
    """Query the data"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"question": question, "return_sources": return_sources},
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logout()
            st.rerun()
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_insights(focus: str = None) -> Dict[str, Any]:
    """Get automatic insights"""
    try:
        params = {"focus": focus} if focus else {}
        response = requests.post(
            f"{API_BASE_URL}/insights",
            params=params,
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logout()
            st.rerun()
        return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def clear_all_data():
    """Clear all uploaded data"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/clear",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            st.session_state.chat_history = []
            st.session_state.uploaded_files_info = []
            st.session_state.data_overview = None
            return True
        return False
    except:
        return False


def main():
    """Main application"""

    # Check if user is authenticated
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Header
    st.markdown('<div class="main-header">🚀 voyager</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Intelligent RAG Data Analysis Module</div>',
        unsafe_allow_html=True
    )

    # Check API health
    if not check_api_health():
        st.error("⚠️ API server is not running! Please start it with: `python backend/main.py`")
        st.stop()

    # Sidebar
    with st.sidebar:
        # User info
        if st.session_state.user_info:
            st.success(f"👤 {st.session_state.user_info['username']}")
            if st.session_state.user_info.get('is_admin'):
                st.caption("🔑 Administrator")

        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

        st.divider()

        st.header("⚙️ Settings")

        # API Status
        st.success("✅ API Connected")

        st.divider()

        # Clear data button
        if st.button("🗑️ Clear All Data", use_container_width=True):
            with st.spinner("Clearing data..."):
                if clear_all_data():
                    st.success("Data cleared successfully!")
                    st.rerun()
                else:
                    st.error("Failed to clear data")

        st.divider()

        # About
        st.header("ℹ️ About")
        st.markdown("""
        This module uses **Retrieval Augmented Generation (RAG)** to analyze your data.

        **Features:**
        - Upload 50+ files at once
        - Natural language queries
        - AI-powered insights
        - Smart data chunking
        - Persistent storage
        """)

        st.divider()

        # Stats
        if st.session_state.data_overview:
            st.header("📈 Statistics")
            overview = st.session_state.data_overview
            st.metric("Files Uploaded", overview.get('total_files', 0))
            st.metric("Data Chunks", overview.get('total_chunks', 0))

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Data", "💬 Ask Questions", "🔍 Auto Insights", "📊 Data Overview"])

    # TAB 1: Upload Data
    with tab1:
        st.header("Upload Your Data Files")
        st.markdown("Upload CSV or Excel files (supports batch upload of 50+ files)")

        uploaded_files = st.file_uploader(
            "Choose files",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Upload one or more CSV/Excel files"
        )

        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} file(s) selected")

            # Show selected files
            with st.expander("View selected files"):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name} ({file.size / 1024:.2f} KB)")

            if st.button("🚀 Upload and Process", type="primary", use_container_width=True):
                with st.spinner("Uploading and processing files... This may take a moment."):
                    results = upload_files_to_api(uploaded_files)

                    if results:
                        st.session_state.uploaded_files_info.extend(results)

                        # Show results
                        success_count = sum(1 for r in results if r.get('success', False))

                        if success_count == len(results):
                            st.success(f"✅ Successfully uploaded and processed {success_count} file(s)!")
                        else:
                            st.warning(f"⚠️ Processed {success_count}/{len(results)} files successfully")

                        # Show details
                        with st.expander("View processing details"):
                            for result in results:
                                if result.get('success'):
                                    st.write(f"✅ **{result['file_name']}**")
                                    st.write(f"   - Chunks created: {result.get('chunks_created', 0)}")
                                    if 'insights' in result:
                                        insights = result['insights']
                                        shape = insights.get('shape', {})
                                        st.write(f"   - Rows: {shape.get('rows', 0)}, Columns: {shape.get('columns', 0)}")
                                else:
                                    st.write(f"❌ **{result['file_name']}**: {result.get('error', 'Unknown error')}")

                        # Refresh overview
                        st.session_state.data_overview = get_data_overview()
                        st.rerun()

        # Show previously uploaded files
        if st.session_state.uploaded_files_info:
            st.divider()
            st.subheader("Previously Uploaded Files")

            for result in st.session_state.uploaded_files_info[-10:]:  # Show last 10
                if result.get('success'):
                    with st.expander(f"📄 {result['file_name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Chunks", result.get('chunks_created', 0))
                        with col2:
                            insights = result.get('insights', {})
                            shape = insights.get('shape', {})
                            st.metric("Rows", shape.get('rows', 0))

    # TAB 2: Ask Questions
    with tab2:
        st.header("Ask Questions About Your Data")

        if not st.session_state.data_overview or st.session_state.data_overview.get('total_files', 0) == 0:
            st.warning("⚠️ Please upload some data files first!")
        else:
            st.markdown("Ask any question about your uploaded data in natural language")

            # Quick question buttons
            st.subheader("💡 Quick Questions")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📊 Show summary statistics", use_container_width=True):
                    st.session_state.quick_question = "Provide a comprehensive summary of the data including key statistics and metrics"

            with col2:
                if st.button("📈 Identify trends", use_container_width=True):
                    st.session_state.quick_question = "What are the main trends and patterns in the data?"

            with col3:
                if st.button("⚠️ Find anomalies", use_container_width=True):
                    st.session_state.quick_question = "Are there any anomalies or unusual patterns in the data?"

            # Question input
            question = st.text_area(
                "Your Question:",
                value=st.session_state.get('quick_question', ''),
                placeholder="e.g., What are the top 5 products by sales? What trends do you see over time?",
                height=100,
                key="question_input"
            )

            if 'quick_question' in st.session_state:
                del st.session_state.quick_question

            col1, col2 = st.columns([3, 1])
            with col1:
                ask_button = st.button("🔍 Get Answer", type="primary", use_container_width=True)
            with col2:
                show_sources = st.checkbox("Show sources", value=True)

            if ask_button and question:
                with st.spinner("Analyzing data and generating answer..."):
                    result = query_data(question, return_sources=show_sources)

                    if result.get('success'):
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'question': question,
                            'answer': result['answer'],
                            'sources': result.get('sources', []),
                            'timestamp': time.time()
                        })
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

            # Display chat history
            if st.session_state.chat_history:
                st.divider()
                st.subheader("💬 Conversation History")

                for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
                    with st.container():
                        # Question
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>🙋 You asked:</strong><br>
                            {chat['question']}
                        </div>
                        """, unsafe_allow_html=True)

                        # Answer
                        st.markdown(f"""
                        <div class="chat-message ai-message">
                            <strong>🤖 AI Answer:</strong><br>
                            {chat['answer']}
                        </div>
                        """, unsafe_allow_html=True)

                        # Sources
                        if show_sources and chat.get('sources'):
                            with st.expander(f"📚 View {len(chat['sources'])} source(s)"):
                                for j, source in enumerate(chat['sources'][:3], 1):
                                    metadata = source.get('metadata', {})
                                    st.write(f"**Source {j}:** {metadata.get('file_name', 'Unknown')}")
                                    st.write(f"Type: {metadata.get('chunk_type', 'N/A')}")
                                    if 'row_start' in metadata:
                                        st.write(f"Rows: {metadata['row_start']}-{metadata.get('row_end', 'N/A')}")

                        st.divider()

    # TAB 3: Auto Insights
    with tab3:
        st.header("🔍 Automatic Insights Generation")

        if not st.session_state.data_overview or st.session_state.data_overview.get('total_files', 0) == 0:
            st.warning("⚠️ Please upload some data files first!")
        else:
            st.markdown("Get AI-generated insights about your data automatically")

            focus_area = st.text_input(
                "Focus Area (optional):",
                placeholder="e.g., sales trends, customer behavior, revenue analysis",
                help="Specify a particular aspect to focus on, or leave empty for general insights"
            )

            if st.button("✨ Generate Insights", type="primary", use_container_width=True):
                with st.spinner("Analyzing data and generating insights... This may take a moment."):
                    result = get_insights(focus_area if focus_area else None)

                    if result.get('success'):
                        st.success("✅ Insights generated successfully!")

                        # Display insights
                        st.subheader(f"📊 Insights: {result.get('focus', 'General')}")
                        st.markdown(result.get('insights', ''))

                        # Show files used
                        if result.get('based_on_files'):
                            st.divider()
                            st.caption(f"Based on: {', '.join(result['based_on_files'])}")
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

            # Pre-defined insight categories
            st.divider()
            st.subheader("📋 Quick Insight Categories")

            categories = {
                "📈 Growth & Trends": "growth trends and patterns over time",
                "👥 Customer Analysis": "customer behavior and segments",
                "💰 Financial Performance": "financial metrics and performance",
                "🎯 Top Performers": "top performing items, categories, or segments",
                "⚠️ Risk & Anomalies": "risks, anomalies, and areas of concern"
            }

            cols = st.columns(2)
            for i, (label, focus) in enumerate(categories.items()):
                with cols[i % 2]:
                    if st.button(label, use_container_width=True, key=f"insight_{i}"):
                        with st.spinner(f"Generating insights for {label}..."):
                            result = get_insights(focus)
                            if result.get('success'):
                                with st.expander(f"💡 {label}", expanded=True):
                                    st.markdown(result.get('insights', ''))

    # TAB 4: Data Overview
    with tab4:
        st.header("📊 Data Overview")

        # Refresh overview
        if st.button("🔄 Refresh Overview"):
            st.session_state.data_overview = get_data_overview()
            st.rerun()

        overview = st.session_state.data_overview or get_data_overview()

        if not overview or overview.get('total_files', 0) == 0:
            st.info("ℹ️ No data uploaded yet. Upload some files to see the overview.")
        else:
            # Summary stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <h1>{overview.get('total_files', 0)}</h1>
                    <p>Files Uploaded</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <h1>{overview.get('total_chunks', 0)}</h1>
                    <p>Data Chunks</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                total_rows = sum(f.get('total_rows', 0) for f in overview.get('files', []))
                st.markdown(f"""
                <div class="stat-card">
                    <h1>{total_rows:,}</h1>
                    <p>Total Rows</p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # Files detail
            st.subheader("📁 Uploaded Files Details")

            files_data = []
            for file_info in overview.get('files', []):
                files_data.append({
                    'File Name': file_info.get('file_name', 'Unknown'),
                    'Total Rows': file_info.get('total_rows', 0),
                    'Columns': len(file_info.get('columns', [])),
                    'Chunks': file_info.get('chunks', 0)
                })

            if files_data:
                df_files = pd.DataFrame(files_data)
                st.dataframe(df_files, use_container_width=True)

                # Visualizations
                st.divider()
                st.subheader("📊 Data Visualizations")

                col1, col2 = st.columns(2)

                with col1:
                    # Rows per file chart
                    fig_rows = px.bar(
                        df_files,
                        x='File Name',
                        y='Total Rows',
                        title='Rows per File',
                        color='Total Rows',
                        color_continuous_scale='Viridis'
                    )
                    fig_rows.update_layout(showlegend=False)
                    st.plotly_chart(fig_rows, use_container_width=True)

                with col2:
                    # Chunks per file chart
                    fig_chunks = px.pie(
                        df_files,
                        values='Chunks',
                        names='File Name',
                        title='Chunks Distribution by File'
                    )
                    st.plotly_chart(fig_chunks, use_container_width=True)

                # Detailed file info
                st.divider()
                st.subheader("📋 Detailed File Information")

                for file_info in overview.get('files', []):
                    with st.expander(f"📄 {file_info.get('file_name', 'Unknown')}"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Total Rows", file_info.get('total_rows', 0))
                        with col2:
                            st.metric("Total Columns", len(file_info.get('columns', [])))
                        with col3:
                            st.metric("Data Chunks", file_info.get('chunks', 0))

                        if file_info.get('columns'):
                            st.write("**Columns:**")
                            st.write(", ".join(file_info['columns']))


if __name__ == "__main__":
    main()
