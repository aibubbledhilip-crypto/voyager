"""
NLP-based Intent Classification Model using SetFit
Replaces regex-based query routing with machine learning
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Try to import ML dependencies
try:
    from setfit import SetFitModel
    from sentence_transformers import SentenceTransformer
    SETFIT_AVAILABLE = True
except ImportError:
    SETFIT_AVAILABLE = False
    logger.warning("SetFit not available. Run: pip install setfit")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Run: pip install torch")


# Intent categories matching the existing router
INTENT_LABELS = [
    "search",              # Find specific values in data
    "duplicate",           # Find duplicate values
    "unique",              # List unique values
    "aggregate",           # Statistical operations (count, sum, mean, etc.)
    "column_comparison",   # Compare columns
    "metadata",            # System information (file count, etc.)
    "rag"                  # General/semantic questions requiring LLM
]

# Mapping for human-readable intent descriptions
INTENT_DESCRIPTIONS = {
    "search": "Search for specific value in files",
    "duplicate": "Find duplicate values in columns",
    "unique": "List unique/distinct values",
    "aggregate": "Statistical aggregations (count, sum, mean, min, max)",
    "column_comparison": "Compare duplicate rates across columns",
    "metadata": "System metadata (file count, list files)",
    "rag": "General semantic questions requiring LLM analysis"
}


class IntentClassifier:
    """
    Machine learning-based intent classifier using SetFit
    Falls back to regex patterns if model is unavailable
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the intent classifier

        Args:
            model_path: Path to saved model directory. If None, uses default.
        """
        self.model_path = model_path or "./data/models/intent_classifier"
        self.model = None
        self.fallback_enabled = True
        self.min_confidence_threshold = 0.6  # Use regex fallback if confidence < 60%

        # Initialize regex patterns as fallback
        self._init_fallback_patterns()

        # Try to load the model
        if SETFIT_AVAILABLE and TORCH_AVAILABLE:
            self._load_model()
        else:
            logger.warning("ML dependencies not available. Using regex fallback only.")

    def _init_fallback_patterns(self):
        """Initialize regex patterns for fallback (same as original QueryRouter)"""
        import re

        self.search_patterns = [
            r'\b(find|search\s+for|look\s+for|locate)\s+.*\s+(\w+)\s*[:\s]+\s*([^\s]+)',
            r'\b(which|what)\s+files?\s+(have|has|contain|contains)\s+.*\s+(\w+)\s*[:\s]+\s*([^\s]+)',
        ]

        self.column_comparison_patterns = [
            r'\b(which|what)\s+column.*(most|highest|largest|maximum).*duplicat',
            r'\bcompare.*duplicat.*column',
        ]

        self.duplicate_patterns = [
            r'\b(duplicate|repeated|repeat|occurring|appears?\s+multiple)\b',
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
        ]

        self.metadata_patterns = [
            r'\b(how\s+many|count)\s+(files|datasets)(?!\s+(?:have|has|contain))',
            r'\b(list|show|display)\s+(all\s+)?(files|datasets)(?!\s+(?:with|having|containing))',
        ]

    def _load_model(self):
        """Load the trained SetFit model if available"""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists() and (model_dir / "config.json").exists():
                logger.info(f"Loading intent classifier from {self.model_path}")
                self.model = SetFitModel.from_pretrained(self.model_path)
                logger.info("✅ Intent classifier model loaded successfully")
            else:
                logger.info("No trained model found. Will use regex fallback.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def predict(self, query: str) -> Dict[str, Any]:
        """
        Predict intent for a given query

        Args:
            query: User's natural language query

        Returns:
            {
                'intent': str,           # Predicted intent label
                'confidence': float,     # Confidence score (0-1)
                'method': str,           # 'ml' or 'regex'
                'all_scores': dict       # Scores for all intents (if ML)
            }
        """
        # Try ML model first
        if self.model is not None:
            try:
                prediction = self._predict_with_model(query)

                # If confidence is high enough, use ML prediction
                if prediction['confidence'] >= self.min_confidence_threshold:
                    prediction['method'] = 'ml'
                    return prediction
                else:
                    logger.info(f"Low ML confidence ({prediction['confidence']:.2f}), trying regex fallback")
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")

        # Fall back to regex patterns
        return self._predict_with_regex(query)

    def _predict_with_model(self, query: str) -> Dict[str, Any]:
        """Predict using the ML model"""
        # Get prediction and probabilities
        prediction = self.model.predict([query])[0]

        # Get probability scores for all classes
        try:
            probs = self.model.predict_proba([query])[0]
            all_scores = {label: float(prob) for label, prob in zip(INTENT_LABELS, probs)}
            confidence = float(max(probs))
        except:
            # Some models don't support predict_proba
            all_scores = {prediction: 1.0}
            confidence = 1.0

        return {
            'intent': prediction,
            'confidence': confidence,
            'all_scores': all_scores,
            'method': 'ml'
        }

    def _predict_with_regex(self, query: str) -> Dict[str, Any]:
        """Predict using regex patterns (fallback)"""
        import re
        query_lower = query.lower()

        # Check patterns in order (same as original router)

        # Search patterns
        for pattern in self.search_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'search',
                    'confidence': 0.9,
                    'method': 'regex'
                }

        # Metadata patterns
        for pattern in self.metadata_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'metadata',
                    'confidence': 0.9,
                    'method': 'regex'
                }

        # Column comparison patterns
        for pattern in self.column_comparison_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'column_comparison',
                    'confidence': 0.9,
                    'method': 'regex'
                }

        # Duplicate patterns
        for pattern in self.duplicate_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'duplicate',
                    'confidence': 0.85,
                    'method': 'regex'
                }

        # Unique patterns
        for pattern in self.unique_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'unique',
                    'confidence': 0.85,
                    'method': 'regex'
                }

        # Aggregation patterns
        for operation, pattern in self.aggregation_patterns.items():
            if re.search(pattern, query_lower):
                return {
                    'intent': 'aggregate',
                    'confidence': 0.85,
                    'method': 'regex',
                    'operation': operation
                }

        # Default to RAG
        return {
            'intent': 'rag',
            'confidence': 0.5,
            'method': 'regex'
        }

    def extract_parameters(self, query: str, intent: str) -> Dict[str, Any]:
        """
        Extract parameters based on detected intent

        Args:
            query: User's query
            intent: Detected intent

        Returns:
            Dictionary of extracted parameters
        """
        import re
        query_lower = query.lower()

        params = {}

        # Extract column name
        column_indicators = [
            r'\bmsisdn\b', r'\bimsi\b', r'\bimei\b',
            r'\baccount[_\s]?id\b', r'\border[_\s]?id\b',
            r'\bcustomer[_\s]?id\b', r'\bsegment\b',
            r'\bplan\b', r'\bstatus\b', r'\bcity\b',
            r'\bregion\b', r'\bproduct\b', r'\bcategory\b'
        ]

        for pattern in column_indicators:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                params['column'] = match.group(0).strip().replace(' ', '_').lower()
                break

        # Extract value for search queries
        if intent == 'search' and params.get('column'):
            value_pattern = rf'{re.escape(params["column"])}\s+([^\s,?.]+)'
            value_match = re.search(value_pattern, query_lower, re.IGNORECASE)
            if value_match:
                params['value'] = value_match.group(1).strip()

                # Check if analysis is needed
                analysis_indicators = [
                    r'\b(what|which).*(issue|error|problem|exception)',
                    r'\b(show|tell|give|get).*(issue|error|problem|exception)',
                ]
                params['needs_analysis'] = any(
                    re.search(ind, query_lower) for ind in analysis_indicators
                )

        # Extract operation for aggregations
        if intent == 'aggregate':
            for operation, pattern in self.aggregation_patterns.items():
                if re.search(pattern, query_lower):
                    params['operation'] = operation
                    break

            # Extract group by
            group_by_patterns = [
                r'\bby\s+(\w+)',
                r'\bper\s+(\w+)',
                r'\bfor\s+each\s+(\w+)',
                r'\bgroup(?:ed)?\s+by\s+(\w+)'
            ]
            for pattern in group_by_patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    params['group_by'] = match.group(1).lower()
                    break

        return params

    def is_available(self) -> bool:
        """Check if ML model is available"""
        return self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'model_available': self.model is not None,
            'model_path': self.model_path,
            'fallback_enabled': self.fallback_enabled,
            'min_confidence_threshold': self.min_confidence_threshold,
            'ml_dependencies': {
                'setfit': SETFIT_AVAILABLE,
                'torch': TORCH_AVAILABLE
            }
        }


# Global classifier instance
_classifier = None

def get_classifier() -> IntentClassifier:
    """Get or create the global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
