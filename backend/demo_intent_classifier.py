#!/usr/bin/env python3
"""
Demo script for the ML-based intent classifier
Shows how to use the classifier and QueryRouter
"""
import sys
from pathlib import Path

# Check if model exists
model_path = Path("./data/models/intent_classifier")
model_exists = (model_path / "config.json").exists()

print("\n" + "="*80)
print("VOYAGER ML INTENT CLASSIFIER - DEMO")
print("="*80 + "\n")

if not model_exists:
    print("⚠️  WARNING: No trained model found!")
    print(f"   Expected at: {model_path}")
    print("\n   To train the model, run:")
    print("   python train_intent_model.py --balanced\n")
    print("   This demo will use regex fallback.\n")
    print("="*80 + "\n")

# Import the components
try:
    from intent_classifier import IntentClassifier, INTENT_LABELS, INTENT_DESCRIPTIONS
    from query_router import QueryRouter
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the backend directory")
    sys.exit(1)


def demo_intent_classifier():
    """Demo the IntentClassifier directly"""

    print("🤖 IntentClassifier Demo\n")
    print("-" * 80)

    classifier = IntentClassifier()

    # Show model info
    info = classifier.get_model_info()
    print("Model Info:")
    print(f"  ML Available: {info['model_available']}")
    print(f"  Model Path: {info['model_path']}")
    print(f"  Fallback Enabled: {info['fallback_enabled']}")
    print(f"  Min Confidence: {info['min_confidence_threshold']}")
    print()

    # Test queries for each intent type
    test_cases = {
        "search": [
            "which files have msisdn 123456",
            "show me errors for customer_id ABC",
        ],
        "duplicate": [
            "find duplicate msisdns",
            "show repeated customer_ids",
        ],
        "unique": [
            "list unique segments",
            "what are the different plans",
        ],
        "aggregate": [
            "count msisdns by segment",
            "average revenue per region",
        ],
        "column_comparison": [
            "which column has most duplicates",
            "compare columns for duplication",
        ],
        "metadata": [
            "how many files do we have",
            "list all uploaded files",
        ],
        "rag": [
            "what trends do you see",
            "analyze customer behavior",
        ],
    }

    print("Testing queries across all intent types:\n")

    for intent, queries in test_cases.items():
        print(f"📊 {intent.upper()}: {INTENT_DESCRIPTIONS[intent]}")

        for query in queries:
            result = classifier.predict(query)
            predicted_intent = result['intent']
            confidence = result.get('confidence', 0.0)
            method = result.get('method', 'unknown')

            # Check if correct
            status = "✓" if predicted_intent == intent else "✗"

            print(f"  {status} \"{query}\"")
            print(f"     → {predicted_intent} (confidence: {confidence:.0%}, method: {method})")

        print()

    print("="*80 + "\n")


def demo_query_router():
    """Demo the QueryRouter with ML integration"""

    print("🎯 QueryRouter Demo\n")
    print("-" * 80)

    router = QueryRouter(use_ml=True)

    # Show model info
    info = router.get_model_info()
    print("Router Model Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()

    # Test queries with parameter extraction
    test_queries = [
        "which files have msisdn 123456789",
        "find duplicate customer_ids",
        "list unique segments",
        "average revenue by region",
        "count orders by status",
        "how many files do we have",
        "which column has most duplicates",
        "what trends do you see in the data",
        "show me errors for msisdn 999888777",
    ]

    print("Testing QueryRouter with parameter extraction:\n")

    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Query: \"{query}\"")

        result = router.detect_intent(query)

        print(f"   Intent: {result['type']}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Method: {result.get('method', 'N/A')}")

        # Show extracted parameters
        if result.get('column'):
            print(f"   Column: {result['column']}")
        if result.get('value'):
            print(f"   Value: {result['value']}")
        if result.get('operation'):
            print(f"   Operation: {result['operation']}")
        if result.get('group_by'):
            print(f"   Group By: {result['group_by']}")
        if result.get('needs_analysis') is not None:
            print(f"   Needs Analysis: {result['needs_analysis']}")

        print()

    print("="*80 + "\n")


def demo_variations():
    """Demo handling of query variations"""

    print("🔄 Query Variations Demo\n")
    print("-" * 80)

    classifier = IntentClassifier()

    # Test variations of the same intent
    variation_groups = [
        ("Search variations:", [
            "which files have msisdn 123",
            "find msisdn 123",
            "locate msisdn 123",
            "show files with msisdn 123",
            "files containing msisdn 123",
        ]),
        ("Duplicate variations:", [
            "find duplicate msisdns",
            "find dupes in msisdn",
            "show repeated msisdns",
            "which msisdns occur multiple times",
            "msisdns appearing twice",
        ]),
        ("Unique variations:", [
            "list unique segments",
            "show distinct segments",
            "what are the different segments",
            "all unique segments",
            "segments in the data",
        ]),
    ]

    for group_name, queries in variation_groups:
        print(f"📝 {group_name}")

        intents_found = {}
        for query in queries:
            result = classifier.predict(query)
            intent = result['intent']
            confidence = result.get('confidence', 0.0)
            method = result.get('method', 'unknown')

            intents_found[intent] = intents_found.get(intent, 0) + 1

            print(f"  \"{query}\"")
            print(f"     → {intent} ({confidence:.0%}, {method})")

        # Check consistency
        if len(intents_found) == 1:
            print(f"  ✅ All variations correctly identified as: {list(intents_found.keys())[0]}")
        else:
            print(f"  ⚠️  Multiple intents detected: {intents_found}")

        print()

    print("="*80 + "\n")


def demo_edge_cases():
    """Demo handling of edge cases"""

    print("⚠️  Edge Cases Demo\n")
    print("-" * 80)

    classifier = IntentClassifier()

    edge_cases = [
        ("Typo: 'dupes'", "find dupes in msisdn"),
        ("Typo: 'uniq'", "list uniq segments"),
        ("Very short", "msisdn 123"),
        ("Very vague", "show me everything"),
        ("Ambiguous", "how many files have msisdn 123"),  # metadata or search?
        ("Missing context", "compare columns"),
        ("Natural language", "i want to see files having customer_id ABC"),
        ("Informal", "gimme all unique segments plz"),
    ]

    print("Testing edge cases:\n")

    for description, query in edge_cases:
        result = classifier.predict(query)
        intent = result['intent']
        confidence = result.get('confidence', 0.0)
        method = result.get('method', 'unknown')

        print(f"{description}:")
        print(f"  Query: \"{query}\"")
        print(f"  → {intent} (confidence: {confidence:.0%}, method: {method})")
        print()

    print("="*80 + "\n")


def interactive_mode():
    """Interactive mode - test your own queries"""

    print("💬 Interactive Mode\n")
    print("-" * 80)
    print("Enter your queries to test the classifier (type 'quit' to exit)\n")

    classifier = IntentClassifier()
    router = QueryRouter(use_ml=True)

    while True:
        try:
            query = input("Query: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            # Get prediction
            result = router.detect_intent(query)

            print(f"  Intent: {result['type']}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            print(f"  Method: {result.get('method', 'N/A')}")

            # Show parameters
            params = {k: v for k, v in result.items()
                     if k not in ['type', 'confidence', 'method'] and v is not None}
            if params:
                print(f"  Parameters: {params}")

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"  ❌ Error: {e}\n")


def main():
    """Run all demos"""

    print("\n🎬 Running all demos...\n")

    # Run demos
    demo_intent_classifier()
    demo_query_router()
    demo_variations()
    demo_edge_cases()

    # Offer interactive mode
    print("\n" + "="*80)
    print("Want to try your own queries?")
    print("="*80 + "\n")

    response = input("Start interactive mode? (y/n): ").strip().lower()

    if response in ['y', 'yes']:
        interactive_mode()
    else:
        print("\n✅ Demo complete!\n")
        print("To test your own queries, run:")
        print("  python demo_intent_classifier.py\n")
        print("Then select 'y' for interactive mode.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!\n")
        sys.exit(0)
