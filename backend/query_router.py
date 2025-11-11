"""
Intelligent query router that automatically detects query intent
and routes to appropriate endpoint (RAG vs Analytics)
"""
import re
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Smart query router that detects intent and routes to appropriate backend
    """

    def __init__(self):
        # Pattern definitions for different query types
        self.search_patterns = [
            r'\b(find|search\s+for|look\s+for|locate)\s+.*\s+(\w+)\s*[:\s]+\s*([^\s]+)',
            r'\b(which|what)\s+files?\s+(have|has|contain|contains)\s+.*\s+(\w+)\s*[:\s]+\s*([^\s]+)',
            r'\b(check|show|list).*\s+(files?|data).*\s+(has|have|contains?)\s+(?:the\s+)?(\w+)\s+([^\s]+)',
            r'\bfiles?\s+(?:with|having|containing)\s+(?:the\s+)?(\w+)\s+([^\s]+)',
        ]

        self.column_comparison_patterns = [
            r'\b(which|what)\s+column.*(most|highest|largest|maximum).*duplicat',
            r'\bcompare.*duplicat.*column',
            r'\b(which|what)\s+column.*(most|highly|mostly)\s+(repeat|duplicat)',
            r'\bcolumn.*comparison.*duplicat',
            r'\bmost\s+duplicat.*column',
            r'\bcolumn.*(has|have|with).*most.*duplicat'
        ]

        self.duplicate_patterns = [
            r'\b(duplicate|repeated|repeat|occurring|appears?\s+multiple)\b',
            r'\b(how\s+many\s+times|occurrence|count.*same)\b',
            r'\b(find.*same|list.*duplicate|show.*repeated)\b'
        ]

        self.aggregation_patterns = {
            'count': r'\b(count|how\s+many|number\s+of|total\s+number)\b',
            'sum': r'\b(sum|total|add\s+up|cumulative)\b',
            'mean': r'\b(average|mean|avg)\b',
            'min': r'\b(minimum|min|lowest|smallest)\b',
            'max': r'\b(maximum|max|highest|largest|biggest)\b'
        }

        self.unique_patterns = [
            r'\b(unique|distinct|different)\s+(values|entries)',
            r'\b(list\s+all|show\s+all)\s+(unique|distinct)',
            r'\b(what\s+are\s+the|which)\s+.*\s+(unique|distinct)'
        ]

        self.metadata_patterns = [
            r'\b(how\s+many|count)\s+(files|datasets)(?!\s+(?:have|has|contain|with))',  # Don't match if followed by have/has/contain
            r'\b(list|show|display)\s+(all\s+)?(files|datasets)(?!\s+(?:with|having|containing))',  # Don't match if followed by with/having
            r'\b(what\s+files|which\s+files)(?!\s+(?:have|has|contain))',  # Don't match if followed by have/has/contain
            r'\bfiles?\s+(do\s+we\s+have|uploaded|available)(?:\?|$)',  # Only at end of question
            r'\boverview\s+of\s+(data|files|datasets)'
        ]

        # Common column name patterns
        self.column_indicators = [
            r'\bmsisdn\b', r'\bimsi\b', r'\bimei\b',
            r'\baccount[_\s]?id\b', r'\border[_\s]?id\b',
            r'\bcustomer[_\s]?id\b', r'\bsegment\b',
            r'\bplan\b', r'\bstatus\b', r'\bcity\b',
            r'\bregion\b', r'\bproduct\b', r'\bcategory\b'
        ]

    def detect_intent(self, question: str) -> Dict[str, Any]:
        """
        Detect the intent of the query
        Returns: {
            'type': 'search' | 'column_comparison' | 'duplicate' | 'aggregate' | 'unique' | 'metadata' | 'rag',
            'column': extracted column name or None,
            'value': for search queries,
            'operation': for aggregate queries,
            'group_by': for grouped aggregations
        }
        """
        question_lower = question.lower()

        # Check for search queries FIRST (before metadata)
        search_result = self._detect_search(question_lower, question)
        if search_result:
            return search_result

        # Check for metadata queries (file count, list files, etc.)
        if self._matches_patterns(question_lower, self.metadata_patterns):
            return {
                'type': 'metadata',
                'confidence': 'high'
            }

        # Check for column comparison (before regular duplicate detection)
        if self._matches_patterns(question_lower, self.column_comparison_patterns):
            return {
                'type': 'column_comparison',
                'confidence': 'high'
            }

        # Check for duplicate detection
        if self._matches_patterns(question_lower, self.duplicate_patterns):
            column = self._extract_column(question_lower)
            return {
                'type': 'duplicate',
                'column': column or 'msisdn',  # default to msisdn
                'confidence': 'high'
            }

        # Check for unique values query
        if self._matches_patterns(question_lower, self.unique_patterns):
            column = self._extract_column(question_lower)
            return {
                'type': 'unique',
                'column': column or 'msisdn',
                'confidence': 'high'
            }

        # Check for aggregation
        for operation, pattern in self.aggregation_patterns.items():
            if re.search(pattern, question_lower):
                column = self._extract_column(question_lower)
                group_by = self._extract_group_by(question_lower)

                return {
                    'type': 'aggregate',
                    'operation': operation,
                    'column': column,
                    'group_by': group_by,
                    'confidence': 'high'
                }

        # Default to RAG for semantic queries
        return {
            'type': 'rag',
            'confidence': 'medium'
        }

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the patterns"""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def _detect_search(self, text_lower: str, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Detect if this is a search query for a specific value
        Returns: {type: 'search', column: str, value: str, confidence: 'high'} or None
        """
        # Pattern to capture: "check how many files has the msisdn 19392598468"
        # or "which files have msisdn 19392598468"
        # or "find msisdn 19392598468"

        # Try to find column name and value
        # Look for common pattern: [action] [column_name] [value]

        # First, check if any column indicator is present
        column_found = None
        for pattern in self.column_indicators:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                column_found = match.group(0).strip().replace(' ', '_').lower()
                break

        if not column_found:
            return None

        # Now try to extract the value after the column name
        # Pattern: column_name followed by a value (number or string)
        value_pattern = rf'{re.escape(column_found)}\s+([^\s,?.]+)'
        value_match = re.search(value_pattern, text_lower, re.IGNORECASE)

        if value_match:
            value = value_match.group(1).strip()

            # Check if this is actually a search query (has search indicators)
            search_indicators = [
                r'\b(which|what)\s+files?\s+(have|has|contain)',
                r'\b(check|show|find|search|list).*files?',
                r'\bfiles?\s+(with|having|containing)',
                r'\bhow\s+many\s+files?\s+(have|has|contain)',
                r'\b(what|which).{0,30}(issue|error|problem|exception)',  # Issues/problems/errors for a value (allow up to 30 chars between)
                r'\b(show|tell|give|get).*\b(issue|error|problem|data|information|detail)',  # Information about a value
            ]

            has_search_intent = any(re.search(ind, text_lower) for ind in search_indicators)

            if has_search_intent:
                logger.info(f"Detected search intent: column={column_found}, value={value}")
                return {
                    'type': 'search',
                    'column': column_found,
                    'value': value,
                    'confidence': 'high'
                }

        return None

    def _extract_column(self, text: str) -> Optional[str]:
        """
        Extract column name from query
        Uses common column name patterns
        """
        for pattern in self.column_indicators:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Clean up the matched column name
                column = match.group(0).strip().replace(' ', '_').lower()
                return column

        return None

    def _extract_group_by(self, text: str) -> Optional[str]:
        """Extract group by column from phrases like 'by segment', 'per region'"""
        group_by_patterns = [
            r'\bby\s+(\w+)',
            r'\bper\s+(\w+)',
            r'\bfor\s+each\s+(\w+)',
            r'\bgroup(?:ed)?\s+by\s+(\w+)'
        ]

        for pattern in group_by_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).lower()

        return None

    def format_analytics_response(
        self,
        query_type: str,
        analytics_result: Dict[str, Any],
        original_question: str
    ) -> str:
        """
        Format analytics results into natural language response
        """
        if not analytics_result.get('success'):
            return f"I couldn't complete the analysis: {analytics_result.get('error', 'Unknown error')}"

        if query_type == 'duplicate':
            return self._format_duplicate_response(analytics_result, original_question)
        elif query_type == 'unique':
            return self._format_unique_response(analytics_result)
        elif query_type == 'aggregate':
            return self._format_aggregate_response(analytics_result)
        elif query_type == 'metadata':
            return self._format_metadata_response(analytics_result)
        elif query_type == 'search':
            return self._format_search_response(analytics_result)
        elif query_type == 'column_comparison':
            return self._format_column_comparison_response(analytics_result)

        return "Analysis completed, but I'm not sure how to present the results."

    def _format_duplicate_response(self, result: Dict[str, Any], question: str) -> str:
        """Format duplicate detection results as natural language"""
        column = result.get('column', 'value')
        total_duplicates = result.get('total_duplicates', 0)
        duplicates = result.get('duplicates', [])
        csv_download = result.get('csv_download_url')

        if total_duplicates == 0:
            return f"✅ **No duplicate {column}s found** across all {result.get('total_files_analyzed', 0)} files. Each {column} is unique!"

        response_parts = [
            f"📊 **Duplicate {column.upper()}s Analysis**\n",
            f"Found **{total_duplicates} duplicate {column}(s)** across {result.get('total_files_analyzed', 0)} files.\n",
            "\n**Detailed List:**\n"
        ]

        for i, dup in enumerate(duplicates[:20], 1):  # Limit to top 20
            value = dup[column]
            total_count = dup['total_occurrences']
            file_count = dup['file_count']
            files = dup['files']

            response_parts.append(f"\n{i}. **{column.upper()}: `{value}`**")
            response_parts.append(f"   - Total occurrences: **{total_count}**")
            response_parts.append(f"   - Found in **{file_count} file(s)**:")

            for file_info in files:
                filename = file_info['filename']
                count = file_info['count']
                response_parts.append(f"     • `{filename}`: {count} time(s)")

        if total_duplicates > 20:
            response_parts.append(f"\n\n_Showing top 20 of {total_duplicates} duplicates_")

        # Add CSV export information
        if csv_download:
            response_parts.append(f"\n\n📥 **Complete Report Available**")
            response_parts.append(f"Download the full CSV report with all {total_duplicates} duplicates:")
            response_parts.append(f"🔗 `{csv_download}`")
            response_parts.append(f"\nAccess URL: `http://localhost:8000{csv_download}`")

        return "\n".join(response_parts)

    def _format_unique_response(self, result: Dict[str, Any]) -> str:
        """Format unique values response"""
        column = result.get('column', 'value')
        total_unique = result.get('total_unique_values', 0)
        values = result.get('values', [])
        csv_download = result.get('csv_download_url')

        response_parts = [
            f"📊 **Unique {column.upper()}s Analysis**\n",
            f"Found **{total_unique} unique value(s)** in the '{column}' column.\n",
            "\n**Top Values:**\n"
        ]

        for i, item in enumerate(values[:15], 1):
            value = item['value']
            count = item['count']
            response_parts.append(f"{i}. `{value}`: {count} occurrence(s)")

        if total_unique > 15:
            response_parts.append(f"\n_Showing top 15 of {total_unique} unique values_")

        # Add CSV export information
        if csv_download:
            response_parts.append(f"\n\n📥 **Complete Report Available**")
            response_parts.append(f"Download the full CSV report with all {total_unique} unique values:")
            response_parts.append(f"🔗 `{csv_download}`")
            response_parts.append(f"\nAccess URL: `http://localhost:8000{csv_download}`")

        return "\n".join(response_parts)

    def _format_aggregate_response(self, result: Dict[str, Any]) -> str:
        """Format aggregation response"""
        column = result.get('column', 'value')
        operation = result.get('operation', 'calculation')
        results = result.get('results', [])

        if result.get('group_by'):
            group_by = result['group_by']
            response_parts = [
                f"📊 **{operation.upper()} of {column} by {group_by}**\n"
            ]

            for item in results[:20]:
                group = item['group']
                value = item['value']
                if value is not None:
                    response_parts.append(f"• **{group}**: {value:,.2f}" if isinstance(value, float) else f"• **{group}**: {value}")
                else:
                    response_parts.append(f"• **{group}**: N/A")
        else:
            value = results[0]['value'] if results else None
            if value is not None:
                formatted_value = f"{value:,.2f}" if isinstance(value, float) else str(value)
                response_parts = [f"📊 **{operation.upper()} of {column}**: {formatted_value}"]
            else:
                response_parts = [f"📊 Unable to calculate {operation} of {column}"]

        return "\n".join(response_parts)

    def _format_metadata_response(self, result: Dict[str, Any]) -> str:
        """Format metadata/overview response"""
        total_files = result.get('total_files', 0)
        total_chunks = result.get('total_chunks', 0)
        files = result.get('files', [])

        if total_files == 0:
            return "📊 **No files have been uploaded yet.**\n\nPlease upload CSV or Excel files to get started with your data analysis."

        response_parts = [
            f"📊 **Data Overview**\n",
            f"**Total Files:** {total_files}",
            f"**Total Data Chunks:** {total_chunks}\n",
            "\n**Uploaded Files:**\n"
        ]

        for i, file_info in enumerate(files, 1):
            file_name = file_info.get('file_name', 'Unknown')
            total_rows = file_info.get('total_rows', 'N/A')
            chunks = file_info.get('chunks', 0)
            columns = file_info.get('columns', '')

            response_parts.append(f"\n{i}. **{file_name}**")
            response_parts.append(f"   - Rows: {total_rows}")
            response_parts.append(f"   - Chunks: {chunks}")
            if columns:
                # columns might be a string or list
                if isinstance(columns, str):
                    cols_display = columns
                else:
                    cols_display = ", ".join(columns) if len(columns) <= 5 else f"{', '.join(columns[:5])}, ..."
                response_parts.append(f"   - Columns: {cols_display}")

        return "\n".join(response_parts)

    def _format_search_response(self, result: Dict[str, Any]) -> str:
        """Format search results as natural language"""
        column = result.get('column', 'value')
        value = result.get('value', '')
        total_matches = result.get('total_matches', 0)
        files_containing = result.get('files_containing_value', 0)
        total_searched = result.get('total_files_searched', 0)
        results = result.get('results', [])
        csv_download = result.get('csv_download_url')

        if total_matches == 0:
            return f"🔍 **Search Results**\n\nValue **`{value}`** not found in column **{column}** across {total_searched} file(s).\n\nThe value does not exist in any of your uploaded files."

        response_parts = [
            f"🔍 **Search Results for {column.upper()}: `{value}`**\n",
            f"Found **{total_matches} match(es)** across **{files_containing} file(s)** (searched {total_searched} total files).\n",
            "\n**Files Containing This Value:**\n"
        ]

        for i, file_result in enumerate(results, 1):
            filename = file_result.get('filename', 'Unknown')
            match_count = file_result.get('match_count', 0)
            rows = file_result.get('rows', [])

            response_parts.append(f"\n{i}. **{filename}** ({match_count} occurrence(s))")

            # Show first few rows
            if rows:
                response_parts.append("   **Sample rows:**")
                for j, row in enumerate(rows[:3], 1):  # Limit to 3 rows per file
                    # Format row data nicely
                    row_str = ", ".join([f"{k}: {v}" for k, v in list(row.items())[:5]])  # First 5 columns
                    if len(row) > 5:
                        row_str += ", ..."
                    response_parts.append(f"   {j}. {row_str}")

                if match_count > 3:
                    response_parts.append(f"   _...and {match_count - 3} more row(s)_")

        # Add CSV export information
        if csv_download:
            response_parts.append(f"\n\n📥 **Complete Report Available**")
            response_parts.append(f"Download the full CSV report with all {total_matches} matching row(s):")
            response_parts.append(f"🔗 `{csv_download}`")
            response_parts.append(f"\nAccess URL: `http://localhost:8000{csv_download}`")

        return "\n".join(response_parts)

    def _format_column_comparison_response(self, result: Dict[str, Any]) -> str:
        """Format column comparison results as natural language"""
        total_columns = result.get('total_columns_analyzed', 0)
        total_files = result.get('total_files_analyzed', 0)
        columns = result.get('columns', [])
        most_duplicated = result.get('most_duplicated_column')
        csv_download = result.get('csv_download_url')

        if total_columns == 0:
            return "📊 **No columns found** in your uploaded files."

        response_parts = [
            f"📊 **Column Duplicate Comparison**\n",
            f"Analyzed **{total_columns} column(s)** across **{total_files} file(s)**.\n"
        ]

        if most_duplicated:
            response_parts.append(f"🏆 **Most Duplicated Column:** `{most_duplicated}`\n")

        response_parts.append("\n**Ranking by Duplicate Count:**\n")

        for i, col_stat in enumerate(columns[:10], 1):  # Show top 10
            column = col_stat['column']
            duplicate_count = col_stat['duplicate_values']
            duplicate_pct = col_stat['duplicate_percentage']
            files_with_col = col_stat['files_with_column']

            if i == 1:
                response_parts.append(f"\n{i}. 🥇 **{column}**")
            elif i == 2:
                response_parts.append(f"\n{i}. 🥈 **{column}**")
            elif i == 3:
                response_parts.append(f"\n{i}. 🥉 **{column}**")
            else:
                response_parts.append(f"\n{i}. **{column}**")

            response_parts.append(f"   - Duplicate values: **{duplicate_count}**")
            response_parts.append(f"   - Duplicate rate: **{duplicate_pct}%**")
            response_parts.append(f"   - Found in: {files_with_col} file(s)")

        if total_columns > 10:
            response_parts.append(f"\n\n_Showing top 10 of {total_columns} columns_")

        # Add CSV export information
        if csv_download:
            response_parts.append(f"\n\n📥 **Complete Report Available**")
            response_parts.append(f"Download the full CSV report with all {total_columns} columns:")
            response_parts.append(f"🔗 `{csv_download}`")
            response_parts.append(f"\nAccess URL: `http://localhost:8000{csv_download}`")

        return "\n".join(response_parts)


# Global router instance
query_router = QueryRouter()
