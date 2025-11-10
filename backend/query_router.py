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
            'type': 'duplicate' | 'aggregate' | 'unique' | 'rag',
            'column': extracted column name or None,
            'operation': for aggregate queries,
            'group_by': for grouped aggregations
        }
        """
        question_lower = question.lower()

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

        return "Analysis completed, but I'm not sure how to present the results."

    def _format_duplicate_response(self, result: Dict[str, Any], question: str) -> str:
        """Format duplicate detection results as natural language"""
        column = result.get('column', 'value')
        total_duplicates = result.get('total_duplicates', 0)
        duplicates = result.get('duplicates', [])

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

        return "\n".join(response_parts)

    def _format_unique_response(self, result: Dict[str, Any]) -> str:
        """Format unique values response"""
        column = result.get('column', 'value')
        total_unique = result.get('total_unique_values', 0)
        values = result.get('values', [])

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


# Global router instance
query_router = QueryRouter()
