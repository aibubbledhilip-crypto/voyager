#!/usr/bin/env python
"""
Quick test script to verify search intent detection
"""
import sys
sys.path.insert(0, '/home/user/voyager')

from backend.query_router import query_router

# Test queries
test_queries = [
    "check how many files has the msisdn 19392598468",
    "which files have msisdn 12345",
    "find msisdn 99999",
    "how many files",  # This should be metadata, not search
    "list all files",  # This should be metadata, not search
    "search for customer_id ABC123",
    "files with imei 123456789",
]

print("Testing Search Intent Detection")
print("=" * 60)

for query in test_queries:
    intent = query_router.detect_intent(query)
    print(f"\nQuery: '{query}'")
    print(f"Intent Type: {intent['type']}")
    if intent['type'] == 'search':
        print(f"  Column: {intent.get('column')}")
        print(f"  Value: {intent.get('value')}")
    print(f"  Confidence: {intent.get('confidence')}")

print("\n" + "=" * 60)
print("Test Complete!")
