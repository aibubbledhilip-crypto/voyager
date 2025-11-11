"""
Test and evaluate the intent classifier
"""
import sys
from pathlib import Path

try:
    from intent_classifier import IntentClassifier, INTENT_LABELS
    from training_data import get_training_data, TRAINING_EXAMPLES
    from query_router import QueryRouter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the backend directory")
    sys.exit(1)


def test_classifier_predictions():
    """Test the classifier with various queries"""

    test_cases = [
        # Search queries
        ("which files have msisdn 123456", "search"),
        ("find customer_id ABC123", "search"),
        ("what issues does msisdn 999 have", "search"),
        ("show me errors for account_id 12345", "search"),

        # Duplicate queries
        ("find duplicate msisdns", "duplicate"),
        ("show repeated customer_ids", "duplicate"),
        ("which values appear multiple times", "duplicate"),

        # Unique queries
        ("list unique segments", "unique"),
        ("show distinct plans", "unique"),
        ("what are the different regions", "unique"),

        # Aggregation queries
        ("count msisdns", "aggregate"),
        ("average revenue by segment", "aggregate"),
        ("sum of sales", "aggregate"),
        ("maximum price per category", "aggregate"),

        # Column comparison
        ("which column has most duplicates", "column_comparison"),
        ("compare columns for duplicate rates", "column_comparison"),

        # Metadata
        ("how many files", "metadata"),
        ("list all files", "metadata"),
        ("show me an overview", "metadata"),

        # RAG queries
        ("what trends do you see", "rag"),
        ("analyze the data patterns", "rag"),
        ("explain the customer behavior", "rag"),
        ("why are revenues declining", "rag"),
    ]

    print("\n" + "="*80)
    print("INTENT CLASSIFIER TEST")
    print("="*80 + "\n")

    # Test with IntentClassifier
    classifier = IntentClassifier()

    if classifier.is_available():
        print("✅ ML Model is available\n")
    else:
        print("⚠️  ML Model not available, using regex fallback\n")

    correct = 0
    total = len(test_cases)

    print(f"Testing {total} queries...\n")
    print("-" * 80)

    for query, expected_intent in test_cases:
        prediction = classifier.predict(query)
        predicted_intent = prediction['intent']
        confidence = prediction.get('confidence', 0.0)
        method = prediction.get('method', 'unknown')

        is_correct = predicted_intent == expected_intent
        if is_correct:
            correct += 1
            status = "✓"
        else:
            status = "✗"

        print(f"{status} Query: {query}")
        print(f"  Expected: {expected_intent}")
        print(f"  Predicted: {predicted_intent} (confidence: {confidence:.2f}, method: {method})")
        print()

    accuracy = (correct / total) * 100
    print("-" * 80)
    print(f"\nAccuracy: {correct}/{total} = {accuracy:.1f}%")
    print("="*80 + "\n")

    return accuracy


def test_query_router():
    """Test the QueryRouter with ML classifier"""

    print("\n" + "="*80)
    print("QUERY ROUTER TEST")
    print("="*80 + "\n")

    router = QueryRouter(use_ml=True)

    # Get model info
    model_info = router.get_model_info()
    print("Model Info:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    print()

    test_queries = [
        "which files have msisdn 123456",
        "find duplicate customer_ids",
        "list unique segments",
        "average revenue by segment",
        "how many files do we have",
        "which column has most duplicates",
        "what trends do you see in the data",
    ]

    print("-" * 80)
    print("Testing queries with QueryRouter:\n")

    for query in test_queries:
        result = router.detect_intent(query)
        print(f"Query: {query}")
        print(f"  Intent: {result.get('type')}")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")
        print(f"  Method: {result.get('method', 'N/A')}")
        if result.get('column'):
            print(f"  Column: {result.get('column')}")
        if result.get('value'):
            print(f"  Value: {result.get('value')}")
        if result.get('operation'):
            print(f"  Operation: {result.get('operation')}")
        print()

    print("="*80 + "\n")


def test_parameter_extraction():
    """Test parameter extraction from queries"""

    print("\n" + "="*80)
    print("PARAMETER EXTRACTION TEST")
    print("="*80 + "\n")

    classifier = IntentClassifier()

    test_cases = [
        ("which files have msisdn 123456", "search", {'column': 'msisdn', 'value': '123456'}),
        ("find duplicate customer_ids", "duplicate", {'column': 'customer_id'}),
        ("list unique segments", "unique", {'column': 'segment'}),
        ("average revenue by segment", "aggregate", {'operation': 'mean', 'column': 'revenue'}),
        ("count msisdns by region", "aggregate", {'operation': 'count', 'column': 'msisdn', 'group_by': 'region'}),
    ]

    print("Testing parameter extraction:\n")
    print("-" * 80)

    for query, intent, expected_params in test_cases:
        extracted = classifier.extract_parameters(query, intent)

        print(f"Query: {query}")
        print(f"Intent: {intent}")
        print(f"Expected: {expected_params}")
        print(f"Extracted: {extracted}")

        # Check if all expected params are present
        all_correct = all(
            extracted.get(k) == v
            for k, v in expected_params.items()
        )

        if all_correct:
            print("  ✓ Correct")
        else:
            print("  ✗ Incorrect")
        print()

    print("="*80 + "\n")


def test_edge_cases():
    """Test edge cases and ambiguous queries"""

    print("\n" + "="*80)
    print("EDGE CASES TEST")
    print("="*80 + "\n")

    classifier = IntentClassifier()

    edge_cases = [
        "how many files have msisdn 123",  # Could be metadata or search
        "find dupes in msisdn",  # Typo: dupes
        "list uniq segments",  # Typo: uniq
        "avg revenue",  # Missing group by
        "compare columns",  # Missing context
        "what",  # Too short
        "show me everything",  # Too vague
        "msisdn 123456",  # Just column and value
    ]

    print("Testing edge cases:\n")
    print("-" * 80)

    for query in edge_cases:
        prediction = classifier.predict(query)
        print(f"Query: '{query}'")
        print(f"  Intent: {prediction['intent']} (confidence: {prediction.get('confidence', 0.0):.2f})")
        print()

    print("="*80 + "\n")


def compare_ml_vs_regex():
    """Compare ML vs regex performance"""

    print("\n" + "="*80)
    print("ML vs REGEX COMPARISON")
    print("="*80 + "\n")

    # Test with variations that regex might miss
    test_queries = [
        "find dupes in msisdn",  # Typo
        "show repeated customer ids",  # Without underscore
        "which columns have lots of duplicates",  # Natural language
        "what are all the segments",  # Implicit "unique"
        "how many unique segments exist",  # Explicit "unique"
        "files with msisdn 123",  # Short form
        "i want to see files having customer_id ABC",  # Long form
    ]

    classifier = IntentClassifier()

    print("Comparing ML vs Regex on variations:\n")
    print("-" * 80)

    for query in test_queries:
        prediction = classifier.predict(query)

        print(f"Query: {query}")
        print(f"  Intent: {prediction['intent']}")
        print(f"  Confidence: {prediction.get('confidence', 0.0):.2f}")
        print(f"  Method: {prediction.get('method', 'unknown')}")
        print()

    print("="*80 + "\n")


def main():
    """Run all tests"""

    print("\n" + "╔"+"═"*78+"╗")
    print("║" + " "*25 + "VOYAGER INTENT CLASSIFIER" + " "*28 + "║")
    print("║" + " "*30 + "TEST SUITE" + " "*37 + "║")
    print("╚"+"═"*78+"╝")

    # Check if model exists
    model_path = Path("./data/models/intent_classifier")
    if not (model_path / "config.json").exists():
        print("\n⚠️  WARNING: No trained model found!")
        print(f"   Expected at: {model_path}")
        print("\n   To train the model, run:")
        print("   python train_intent_model.py\n")
        print("   Tests will use regex fallback.\n")

    # Run tests
    try:
        accuracy = test_classifier_predictions()
        test_query_router()
        test_parameter_extraction()
        test_edge_cases()
        compare_ml_vs_regex()

        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)

        if accuracy >= 90:
            print(f"\n🎉 Excellent accuracy: {accuracy:.1f}%")
        elif accuracy >= 80:
            print(f"\n✅ Good accuracy: {accuracy:.1f}%")
        elif accuracy >= 70:
            print(f"\n⚠️  Acceptable accuracy: {accuracy:.1f}% (consider retraining)")
        else:
            print(f"\n❌ Low accuracy: {accuracy:.1f}% (retraining recommended)")

        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
