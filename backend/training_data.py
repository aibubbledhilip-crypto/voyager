"""
Training data generator for intent classification
Includes synthetic examples and query history export
"""
import json
import logging
from typing import List, Tuple, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


# Comprehensive training examples for each intent
TRAINING_EXAMPLES = {
    "search": [
        # Direct search queries
        "which files have msisdn 19392598468",
        "find msisdn 12345678901",
        "search for customer_id ABC123",
        "locate imei 123456789012345",
        "which files contain account_id 9876",
        "show me files with order_id ORD001",
        "check how many files has the msisdn 555666777",
        "what files have imsi 123456789012345",
        "look for segment premium",
        "find all files containing msisdn 1234567890",

        # Search with analysis
        "what are possible issues for msisdn 19392598468",
        "show me errors for customer_id XYZ789",
        "what problems does msisdn 999888777 have",
        "what issues are there for imei 111222333444555",
        "tell me about errors for account_id 12345",
        "get issues for order_id ORD999",
        "what's wrong with msisdn 123456789",
        "show problems with customer_id CUS001",
        "explain errors for imsi 987654321",
        "analyze issues for msisdn 555444333",

        # Variations
        "files containing the msisdn 12345",
        "where is msisdn 99999",
        "do we have data for customer_id TEST123",
        "is there any file with imei 999888777666",
        "check if msisdn 111222333 exists in files",
    ],

    "duplicate": [
        # Standard duplicate queries
        "find duplicate msisdns",
        "find duplicate customer_ids",
        "show me duplicate imeis",
        "list duplicate account_ids",
        "which msisdns appear multiple times",
        "find repeated imsis",
        "show duplicate segments",
        "find msisdn duplicates",
        "are there any duplicate order_ids",
        "check for duplicate values in msisdn",

        # Variations
        "find dupes in msisdn",
        "show repeated msisdns",
        "which msisdns occur more than once",
        "find same msisdn appearing multiple times",
        "list msisdns that repeat",
        "show me msisdns with multiple occurrences",
        "find all repeated customer_ids",
        "duplicate detection for imei",
        "check duplicate entries in account_id",
        "identify repeated imsi values",

        # Natural language variations
        "are there any msisdns that appear twice",
        "which customer ids are duplicated",
        "show me repeating imeis",
        "find msisdns that occur multiple times",
        "list all duplicate entries for segment",
    ],

    "unique": [
        # Standard unique queries
        "list unique segments",
        "show unique customer_ids",
        "what are the unique msisdns",
        "list all unique imeis",
        "show distinct segments",
        "list unique values in plan",
        "what are the different segments",
        "show all unique statuses",
        "list distinct customer_ids",
        "what unique regions do we have",

        # Variations
        "show me all unique msisdns",
        "list all different segments",
        "what are the distinct values in category",
        "show unique entries for product",
        "list all different plans",
        "what unique cities are in the data",
        "show distinct account_ids",
        "list unique order_ids",
        "what are all the different segments",
        "show me distinct msisdns",

        # Natural language variations
        "how many different segments exist",
        "what segments do we have",
        "show me all the different plans",
        "list every unique customer_id",
        "what are the available statuses",
    ],

    "aggregate": [
        # Count operations
        "count msisdns",
        "how many customer_ids are there",
        "total number of orders",
        "count unique segments",
        "how many records do we have",
        "count rows with status active",
        "number of msisdns by segment",
        "count customer_ids per region",
        "how many orders by status",
        "total msisdns in each file",

        # Sum operations
        "sum of revenue",
        "total revenue by segment",
        "add up all amounts",
        "sum price by category",
        "total sales per region",
        "cumulative revenue",
        "sum of all transactions",
        "total amount by customer_id",
        "sum revenue by plan",
        "add up all values in amount",

        # Average operations
        "average revenue",
        "mean price by segment",
        "avg amount per customer",
        "average revenue by region",
        "mean value of transactions",
        "average price per product",
        "avg revenue by plan",
        "mean amount by status",
        "average transaction value",
        "what's the average revenue per segment",

        # Min/Max operations
        "minimum price",
        "maximum revenue",
        "lowest amount by segment",
        "highest revenue by region",
        "min value in amount",
        "max price per category",
        "smallest transaction",
        "largest order value",
        "minimum revenue per plan",
        "maximum amount by customer",

        # Grouped aggregations
        "count msisdns by segment",
        "average revenue per region",
        "sum of sales by category",
        "total amount for each plan",
        "count orders grouped by status",
        "mean revenue per customer_id",
        "max price by product",
        "min amount per segment",
    ],

    "column_comparison": [
        # Standard comparison queries
        "which column has the most duplicates",
        "what column has most duplicate values",
        "compare duplicate rates across columns",
        "which column is most duplicated",
        "what column has highest duplication",
        "compare columns for duplicates",
        "which column has maximum duplicates",
        "what's the most duplicated column",
        "column with most repeated values",
        "compare duplication in all columns",

        # Variations
        "which column has most repeating values",
        "what column is highly duplicated",
        "compare all columns for duplicate count",
        "find the column with maximum duplication",
        "which column has highest duplicate rate",
        "show me column comparison for duplicates",
        "rank columns by duplicate count",
        "what's the most repeated column",
        "column duplicate analysis",
        "compare duplicate percentages across columns",

        # Natural language variations
        "tell me which column has most duplicates",
        "I want to compare duplicate rates in columns",
        "show me which columns have the most duplication",
        "compare columns to find most duplicated one",
        "which column should I focus on for duplicates",
    ],

    "metadata": [
        # File count queries
        "how many files",
        "how many files do we have",
        "count of files",
        "total files uploaded",
        "number of datasets",
        "how many files are there",
        "count files",
        "total number of files",
        "how many datasets do we have",
        "what's the file count",

        # List files queries
        "list all files",
        "show all files",
        "display all files",
        "what files do we have",
        "show me all datasets",
        "list uploaded files",
        "display all datasets",
        "what files are available",
        "show files uploaded",
        "list all my files",

        # Overview queries
        "overview of data",
        "data summary",
        "show me an overview",
        "what data do we have",
        "give me an overview of files",
        "system overview",
        "show dataset overview",
        "what's in the database",
        "overview of uploaded files",
        "summarize available data",

        # Variations
        "files uploaded",
        "files available",
        "what files exist",
        "show file list",
        "display files",
    ],

    "rag": [
        # Analytical questions
        "what trends do you see in the data",
        "summarize the customer segments",
        "what insights can you provide",
        "analyze the revenue patterns",
        "what are the key findings",
        "explain the data distribution",
        "what patterns exist in the data",
        "provide insights about customer behavior",
        "what correlations do you notice",
        "analyze sales trends",

        # Descriptive questions
        "describe the dataset",
        "what does this data tell us",
        "explain the customer demographics",
        "what is the data quality like",
        "describe the revenue distribution",
        "what can we learn from this data",
        "tell me about the customer base",
        "explain the market segments",
        "what does the data show about sales",
        "describe patterns in customer behavior",

        # Interpretive questions
        "why are revenues declining",
        "what caused the spike in orders",
        "how can we improve retention",
        "what drives customer churn",
        "why do certain segments perform better",
        "what factors affect revenue",
        "how does region impact sales",
        "what influences customer behavior",
        "why are there so many duplicates",
        "what's the relationship between price and sales",

        # Comparative questions
        "compare revenue across segments",
        "how do regions differ in performance",
        "what's the difference between plans",
        "compare customer behavior by segment",
        "how do products compare in sales",
        "what's better: plan A or plan B",
        "compare performance over time",
        "how do segments differ",
        "compare customer satisfaction by region",
        "what are the differences between categories",

        # Open-ended questions
        "tell me something interesting about the data",
        "what should I know about this dataset",
        "give me insights",
        "what's important here",
        "help me understand the data",
        "what stands out",
        "any recommendations",
        "what should I focus on",
        "guide me through the data",
        "what's noteworthy",
    ]
}


def get_training_data() -> List[Tuple[str, str]]:
    """
    Get training data as list of (text, label) tuples

    Returns:
        List of (query, intent) tuples
    """
    training_data = []

    for intent, examples in TRAINING_EXAMPLES.items():
        for example in examples:
            training_data.append((example, intent))

    logger.info(f"Generated {len(training_data)} training examples across {len(TRAINING_EXAMPLES)} intents")

    return training_data


def get_balanced_dataset(examples_per_intent: int = 25) -> List[Tuple[str, str]]:
    """
    Get a balanced dataset with equal examples per intent

    Args:
        examples_per_intent: Number of examples to include per intent

    Returns:
        Balanced list of (query, intent) tuples
    """
    balanced_data = []

    for intent, examples in TRAINING_EXAMPLES.items():
        # Take up to examples_per_intent, or all if fewer available
        selected = examples[:examples_per_intent]
        for example in selected:
            balanced_data.append((example, intent))

        logger.info(f"Intent '{intent}': {len(selected)} examples")

    logger.info(f"Balanced dataset: {len(balanced_data)} total examples")

    return balanced_data


def export_training_data(output_path: str = "./data/training_data.json"):
    """
    Export training data to JSON file

    Args:
        output_path: Path to save the training data
    """
    training_data = get_training_data()

    # Convert to list of dicts for JSON
    data_dicts = [
        {"text": text, "label": label}
        for text, label in training_data
    ]

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to file
    with open(output_path, 'w') as f:
        json.dump(data_dicts, f, indent=2)

    logger.info(f"✅ Exported {len(data_dicts)} training examples to {output_path}")

    return output_path


def export_query_history_training_data(db_session, output_path: str = "./data/query_history_data.json") -> int:
    """
    Export query history from database for training

    Args:
        db_session: SQLAlchemy database session
        output_path: Path to save the query history data

    Returns:
        Number of queries exported
    """
    from database import QueryHistory

    # Get all queries from history
    queries = db_session.query(QueryHistory.question).all()

    if not queries:
        logger.warning("No query history found in database")
        return 0

    # Extract just the questions
    query_texts = [q.question for q in queries]

    # Save to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(query_texts, f, indent=2)

    logger.info(f"✅ Exported {len(query_texts)} queries from history to {output_path}")

    return len(query_texts)


def get_intent_distribution() -> Dict[str, int]:
    """
    Get the distribution of intents in training data

    Returns:
        Dictionary mapping intent to count
    """
    distribution = {}

    for intent, examples in TRAINING_EXAMPLES.items():
        distribution[intent] = len(examples)

    return distribution


def print_training_data_stats():
    """Print statistics about the training data"""
    distribution = get_intent_distribution()

    print("\n" + "="*60)
    print("TRAINING DATA STATISTICS")
    print("="*60)

    total = sum(distribution.values())
    print(f"\nTotal Examples: {total}\n")

    print("Distribution by Intent:")
    print("-" * 60)

    # Sort by count descending
    sorted_intents = sorted(distribution.items(), key=lambda x: x[1], reverse=True)

    for intent, count in sorted_intents:
        percentage = (count / total) * 100
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = "█" * bar_length
        print(f"{intent:20s} | {count:3d} ({percentage:5.1f}%) {bar}")

    print("="*60 + "\n")


if __name__ == "__main__":
    # Test the training data
    print_training_data_stats()

    # Export to file
    export_training_data()

    print("\n✅ Training data ready!")
    print("   - Use get_training_data() to get all examples")
    print("   - Use get_balanced_dataset(N) to get N examples per intent")
    print("   - Training data exported to ./data/training_data.json")
