"""
Advanced visualization module for data insights
Creates interactive charts, exports, and visual analytics
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional
import io
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataVisualizer:
    """Advanced data visualization for insights"""

    def __init__(self):
        # Set seaborn style
        sns.set_theme(style="whitegrid")
        self.color_palette = px.colors.qualitative.Set2

    def create_summary_dashboard(self, df: pd.DataFrame, file_name: str) -> Dict[str, Any]:
        """
        Create a comprehensive dashboard with multiple visualizations
        """
        try:
            visualizations = {}

            # 1. Basic statistics
            visualizations['statistics'] = self._generate_statistics(df)

            # 2. Column type distribution
            visualizations['column_types'] = self._visualize_column_types(df)

            # 3. Missing values heatmap
            visualizations['missing_values'] = self._visualize_missing_values(df)

            # 4. Numeric distributions
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                visualizations['distributions'] = self._visualize_distributions(df, numeric_cols)

            # 5. Correlation matrix (if multiple numeric columns)
            if len(numeric_cols) > 1:
                visualizations['correlation'] = self._visualize_correlation(df, numeric_cols)

            # 6. Categorical analysis
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                visualizations['categorical'] = self._visualize_categorical(df, categorical_cols)

            # 7. Time series analysis (if date columns exist)
            date_cols = self._detect_date_columns(df)
            if date_cols:
                visualizations['time_series'] = self._visualize_time_series(df, date_cols)

            return {
                'success': True,
                'file_name': file_name,
                'visualizations': visualizations,
                'summary': self._generate_text_summary(df)
            }

        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive statistics"""
        return {
            'shape': {'rows': int(df.shape[0]), 'columns': int(df.shape[1])},
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB",
            'missing_values': df.isnull().sum().to_dict(),
            'duplicates': int(df.duplicated().sum()),
            'numeric_summary': df.describe().to_dict() if len(df.select_dtypes(include=['number']).columns) > 0 else {}
        }

    def _visualize_column_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Visualize column type distribution"""
        type_counts = df.dtypes.value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=[str(x) for x in type_counts.index],
            values=type_counts.values,
            hole=.3
        )])

        fig.update_layout(
            title="Column Type Distribution",
            showlegend=True
        )

        return {
            'chart': fig.to_json(),
            'data': type_counts.to_dict()
        }

    def _visualize_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Visualize missing values pattern"""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)

        # Only show columns with missing values
        missing_data = pd.DataFrame({
            'Column': missing[missing > 0].index,
            'Missing Count': missing[missing > 0].values,
            'Percentage': missing_pct[missing > 0].values
        })

        if len(missing_data) == 0:
            return {'chart': None, 'message': 'No missing values found!'}

        fig = px.bar(
            missing_data,
            x='Column',
            y='Percentage',
            title='Missing Values by Column',
            labels={'Percentage': 'Missing %'},
            color='Percentage',
            color_continuous_scale='Reds'
        )

        return {
            'chart': fig.to_json(),
            'data': missing_data.to_dict('records')
        }

    def _visualize_distributions(self, df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, Any]:
        """Visualize distributions of numeric columns"""
        # Limit to first 6 columns for readability
        cols_to_plot = list(numeric_cols[:6])

        # Create subplots
        rows = (len(cols_to_plot) + 2) // 3
        fig = make_subplots(
            rows=rows,
            cols=min(3, len(cols_to_plot)),
            subplot_titles=cols_to_plot
        )

        for idx, col in enumerate(cols_to_plot):
            row = idx // 3 + 1
            col_pos = idx % 3 + 1

            fig.add_trace(
                go.Histogram(x=df[col], name=col, showlegend=False),
                row=row,
                col=col_pos
            )

        fig.update_layout(
            title_text="Distribution of Numeric Columns",
            showlegend=False,
            height=300 * rows
        )

        return {'chart': fig.to_json()}

    def _visualize_correlation(self, df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, Any]:
        """Visualize correlation matrix"""
        corr_matrix = df[numeric_cols].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 10}
        ))

        fig.update_layout(
            title='Correlation Matrix',
            xaxis_title='Features',
            yaxis_title='Features',
            height=600
        )

        return {
            'chart': fig.to_json(),
            'insights': self._generate_correlation_insights(corr_matrix)
        }

    def _generate_correlation_insights(self, corr_matrix: pd.DataFrame) -> List[str]:
        """Generate insights from correlation matrix"""
        insights = []

        # Find strong correlations (> 0.7 or < -0.7)
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    direction = "positive" if corr_value > 0 else "negative"
                    insights.append(
                        f"Strong {direction} correlation ({corr_value:.2f}) between {col1} and {col2}"
                    )

        return insights[:5]  # Return top 5 insights

    def _visualize_categorical(self, df: pd.DataFrame, categorical_cols: List[str]) -> Dict[str, Any]:
        """Visualize categorical columns"""
        # Limit to first 4 columns
        cols_to_plot = list(categorical_cols[:4])

        charts = {}
        for col in cols_to_plot:
            value_counts = df[col].value_counts().head(10)

            fig = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f'Top Values in {col}',
                labels={'x': col, 'y': 'Count'}
            )

            charts[col] = fig.to_json()

        return {'charts': charts}

    def _detect_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect date/time columns"""
        date_cols = []

        for col in df.columns:
            # Check if already datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_cols.append(col)
            # Try to parse as date
            elif df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col].head(100), errors='raise')
                    date_cols.append(col)
                except:
                    pass

        return date_cols

    def _visualize_time_series(self, df: pd.DataFrame, date_cols: List[str]) -> Dict[str, Any]:
        """Visualize time series data"""
        charts = {}

        for date_col in date_cols[:2]:  # Limit to 2 date columns
            try:
                # Convert to datetime
                df_temp = df.copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col])
                df_temp = df_temp.sort_values(date_col)

                # Group by date and count
                time_series = df_temp.groupby(df_temp[date_col].dt.date).size()

                fig = px.line(
                    x=time_series.index,
                    y=time_series.values,
                    title=f'Time Series: {date_col}',
                    labels={'x': 'Date', 'y': 'Count'}
                )

                charts[date_col] = fig.to_json()
            except Exception as e:
                logger.warning(f"Could not create time series for {date_col}: {str(e)}")

        return {'charts': charts} if charts else None

    def _generate_text_summary(self, df: pd.DataFrame) -> str:
        """Generate text summary of the dataset"""
        summary_parts = [
            f"Dataset contains {df.shape[0]:,} rows and {df.shape[1]} columns.",
        ]

        # Missing values
        missing_total = df.isnull().sum().sum()
        if missing_total > 0:
            missing_pct = (missing_total / (df.shape[0] * df.shape[1]) * 100)
            summary_parts.append(f"Total missing values: {missing_total:,} ({missing_pct:.2f}%).")

        # Duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            summary_parts.append(f"Found {duplicates:,} duplicate rows.")

        # Column types
        numeric_count = len(df.select_dtypes(include=['number']).columns)
        categorical_count = len(df.select_dtypes(include=['object', 'category']).columns)
        summary_parts.append(f"Column types: {numeric_count} numeric, {categorical_count} categorical.")

        return " ".join(summary_parts)

    def create_trend_analysis(self, df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
        """Create trend analysis visualization"""
        try:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=f'Trend: {y_col} over {x_col}'
            )

            # Add trend line
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col].rolling(window=min(30, len(df)//10 or 1)).mean(),
                name='Moving Average',
                line=dict(dash='dash', color='red')
            ))

            return {
                'success': True,
                'chart': fig.to_json()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def export_chart_as_image(self, fig_json: str, format: str = 'png') -> bytes:
        """Export Plotly chart as image"""
        try:
            import plotly.io as pio
            fig = go.Figure(fig_json)
            img_bytes = pio.to_image(fig, format=format)
            return img_bytes
        except Exception as e:
            logger.error(f"Error exporting chart: {str(e)}")
            return None

    def create_comparison_chart(
        self,
        data: List[Dict[str, Any]],
        x_field: str,
        y_fields: List[str],
        chart_type: str = 'bar'
    ) -> Dict[str, Any]:
        """Create comparison chart for multiple metrics"""
        try:
            df = pd.DataFrame(data)

            if chart_type == 'bar':
                fig = px.bar(df, x=x_field, y=y_fields, barmode='group')
            elif chart_type == 'line':
                fig = px.line(df, x=x_field, y=y_fields)
            else:
                return {'success': False, 'error': f'Unknown chart type: {chart_type}'}

            fig.update_layout(
                title='Comparison Analysis',
                xaxis_title=x_field,
                yaxis_title='Values'
            )

            return {
                'success': True,
                'chart': fig.to_json()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
