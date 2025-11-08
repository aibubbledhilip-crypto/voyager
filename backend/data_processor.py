"""
Data processing module for Excel and CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process Excel and CSV files for RAG"""

    def __init__(self):
        self.supported_extensions = {'.csv', '.xlsx', '.xls'}

    def is_supported_file(self, file_path: str) -> bool:
        """Check if file is a supported format"""
        return Path(file_path).suffix.lower() in self.supported_extensions

    def read_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Read Excel or CSV file into DataFrame"""
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file type: {file_ext}")
                return None

            logger.info(f"Successfully read {file_path}: {df.shape[0]} rows, {df.shape[1]} columns")
            return df

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None

    def generate_file_summary(self, df: pd.DataFrame, file_name: str) -> str:
        """Generate a comprehensive summary of the dataset"""
        summary_parts = [
            f"Dataset: {file_name}",
            f"Shape: {df.shape[0]} rows, {df.shape[1]} columns",
            f"\nColumns: {', '.join(df.columns.tolist())}",
            f"\nData Types:\n{df.dtypes.to_string()}",
        ]

        # Add basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"\n\nNumeric Column Statistics:\n{df[numeric_cols].describe().to_string()}")

        # Add info about missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            summary_parts.append(f"\n\nMissing Values:\n{missing[missing > 0].to_string()}")

        # Sample data
        summary_parts.append(f"\n\nFirst 5 Rows:\n{df.head().to_string()}")

        return "\n".join(summary_parts)

    def chunk_dataframe(self, df: pd.DataFrame, file_name: str, chunk_size: int = 50) -> List[Dict[str, Any]]:
        """
        Split DataFrame into chunks for embedding
        Each chunk contains a portion of rows with context
        """
        chunks = []
        total_rows = len(df)

        # Create metadata about the entire dataset
        file_metadata = {
            "file_name": file_name,
            "total_rows": total_rows,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict()
        }

        # Add full dataset summary as first chunk
        summary = self.generate_file_summary(df, file_name)
        chunks.append({
            "content": summary,
            "metadata": {
                **file_metadata,
                "chunk_type": "summary",
                "chunk_id": 0
            }
        })

        # Chunk the actual data
        for i in range(0, total_rows, chunk_size):
            chunk_df = df.iloc[i:i + chunk_size]

            # Convert chunk to detailed text representation
            chunk_text_parts = [
                f"Data from {file_name} (rows {i+1} to {min(i+chunk_size, total_rows)}):",
                f"Columns: {', '.join(df.columns.tolist())}",
                f"\n{chunk_df.to_string(index=False)}"
            ]

            # Add column-wise summary for this chunk
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(chunk_df[col]):
                    stats = chunk_df[col].describe()
                    chunk_text_parts.append(
                        f"\n{col} statistics in this chunk: "
                        f"mean={stats['mean']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f}"
                    )

            chunks.append({
                "content": "\n".join(chunk_text_parts),
                "metadata": {
                    **file_metadata,
                    "chunk_type": "data",
                    "chunk_id": len(chunks),
                    "row_start": i,
                    "row_end": min(i + chunk_size, total_rows)
                }
            })

        logger.info(f"Created {len(chunks)} chunks from {file_name}")
        return chunks

    def extract_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract key insights from the dataset"""
        insights = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": df.columns.tolist(),
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
        }

        # Numeric column insights
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            insights["numeric_stats"] = df[numeric_cols].describe().to_dict()

        # Categorical column insights
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            insights["categorical_unique_counts"] = {
                col: int(df[col].nunique()) for col in categorical_cols
            }

        return insights
