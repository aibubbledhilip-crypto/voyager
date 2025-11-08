"""
Example usage script for the Intelligent RAG Data Analysis Tool

This script demonstrates how to interact with the API programmatically.
Make sure the server is running (python run.py) before running this script.
"""
import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_health():
    """Check if the server is healthy"""
    print_section("Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200


def upload_single_file(file_path):
    """Upload a single file"""
    print_section(f"Uploading Single File: {file_path}")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        print("💡 Create a sample CSV file to test with!")
        return None

    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={'file': f}
        )

    result = response.json()
    print(json.dumps(result, indent=2))
    return result


def upload_multiple_files(file_paths):
    """Upload multiple files"""
    print_section(f"Uploading {len(file_paths)} Files")

    files = []
    for file_path in file_paths:
        if Path(file_path).exists():
            files.append(('files', open(file_path, 'rb')))
        else:
            print(f"⚠️  Skipping missing file: {file_path}")

    if not files:
        print("❌ No valid files to upload")
        return None

    response = requests.post(
        f"{BASE_URL}/upload-multiple",
        files=files
    )

    # Close file handles
    for _, f in files:
        f.close()

    result = response.json()
    print(json.dumps(result, indent=2))
    return result


def query_data(question, return_sources=True):
    """Query the uploaded data"""
    print_section(f"Query: {question}")

    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "question": question,
            "return_sources": return_sources
        }
    )

    result = response.json()

    if result.get("success"):
        print(f"📊 Answer:\n{result['answer']}\n")

        if return_sources and "sources" in result:
            print(f"📚 Based on {len(result['sources'])} sources:")
            for i, source in enumerate(result['sources'][:3], 1):
                metadata = source.get('metadata', {})
                print(f"\n  Source {i}:")
                print(f"  - File: {metadata.get('file_name', 'Unknown')}")
                print(f"  - Type: {metadata.get('chunk_type', 'Unknown')}")
    else:
        print(f"❌ Error: {result.get('error')}")

    return result


def get_overview():
    """Get data overview"""
    print_section("Data Overview")

    response = requests.get(f"{BASE_URL}/overview")
    result = response.json()

    print(f"📁 Total Files: {result.get('total_files', 0)}")
    print(f"📦 Total Chunks: {result.get('total_chunks', 0)}\n")

    for file_info in result.get('files', []):
        print(f"  - {file_info.get('file_name')}")
        print(f"    Rows: {file_info.get('total_rows')}, "
              f"Columns: {len(file_info.get('columns', []))}, "
              f"Chunks: {file_info.get('chunks')}")

    return result


def get_insights(focus=None):
    """Get automatic insights"""
    focus_text = f" on {focus}" if focus else ""
    print_section(f"Automatic Insights{focus_text}")

    params = {"focus": focus} if focus else {}
    response = requests.post(f"{BASE_URL}/insights", params=params)

    result = response.json()

    if result.get("success"):
        print(f"🔍 Insights:\n{result.get('insights')}\n")
        print(f"📊 Based on files: {', '.join(result.get('based_on_files', []))}")
    else:
        print(f"❌ Error: {result.get('error')}")

    return result


def clear_data():
    """Clear all data"""
    print_section("Clearing All Data")

    response = requests.delete(f"{BASE_URL}/clear")
    result = response.json()

    if result.get("success"):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Error: {result.get('error')}")

    return result


def create_sample_csv():
    """Create a sample CSV file for testing"""
    import pandas as pd
    import numpy as np

    print_section("Creating Sample Data")

    # Sample sales data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    data = {
        'Date': dates,
        'Product': np.random.choice(['Product A', 'Product B', 'Product C'], 100),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], 100),
        'Sales': np.random.randint(100, 1000, 100),
        'Quantity': np.random.randint(1, 50, 100),
        'Customer_Segment': np.random.choice(['Enterprise', 'SMB', 'Individual'], 100)
    }

    df = pd.DataFrame(data)

    # Save to CSV
    sample_file = "sample_sales_data.csv"
    df.to_csv(sample_file, index=False)
    print(f"✅ Created sample file: {sample_file}")
    print(f"📊 Shape: {df.shape[0]} rows, {df.shape[1]} columns")

    return sample_file


def main():
    """Main example workflow"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Intelligent RAG Data Analysis Tool - Example Usage     ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Check if server is running
    try:
        if not check_health():
            print("\n❌ Server is not healthy. Please start it with: python run.py")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Please start it with: python run.py")
        return

    # Create sample data
    sample_file = create_sample_csv()

    # Upload the sample file
    upload_single_file(sample_file)

    # Get overview
    get_overview()

    # Example queries
    questions = [
        "What is the total sales amount?",
        "Which product has the highest average sales?",
        "What are the sales trends by region?",
        "Which customer segment generates the most revenue?"
    ]

    for question in questions:
        query_data(question, return_sources=True)

    # Get automatic insights
    get_insights(focus="sales performance")

    # Uncomment to clear data after testing
    # clear_data()

    print("\n✅ Example completed!")
    print("💡 Try uploading your own CSV/Excel files and asking custom questions!")


if __name__ == "__main__":
    main()
