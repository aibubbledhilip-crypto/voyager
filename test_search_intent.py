#!/usr/bin/env python
"""
Quick test script to verify intent detection
"""
import sys
sys.path.insert(0, '/home/user/voyager')

from backend.query_router import query_router

# Test queries
test_queries = [
    # Search queries
    ("check how many files has the msisdn 19392598468", "search"),
    ("which files have msisdn 12345", "search"),
    ("files with imei 123456789", "search"),

    # Metadata queries
    ("how many files", "metadata"),
    ("list all files", "metadata"),

    # Column comparison queries
    ("which column has the most duplicates", "column_comparison"),
    ("what column is mostly repeated", "column_comparison"),
    ("compare duplicates across all columns", "column_comparison"),
    ("what are column names we have in the files and which column is mostly repeated", "column_comparison"),

    # Duplicate queries
    ("find duplicate msisdns", "duplicate"),
]

print("Testing Intent Detection")
print("=" * 80)

passed = 0
failed = 0

for query, expected_type in test_queries:
    intent = query_router.detect_intent(query)
    actual_type = intent['type']
    status = "✓" if actual_type == expected_type else "✗"

    if actual_type == expected_type:
        passed += 1
    else:
        failed += 1

    print(f"\n{status} Query: '{query}'")
    print(f"  Expected: {expected_type}")
    print(f"  Detected: {actual_type}")
    if intent.get('column'):
        print(f"  Column: {intent.get('column')}")
    if intent.get('value'):
        print(f"  Value: {intent.get('value')}")

print("\n" + "=" * 80)
print(f"Test Complete! Passed: {passed}/{len(test_queries)}, Failed: {failed}/{len(test_queries)}")
