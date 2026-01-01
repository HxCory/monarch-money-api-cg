#!/usr/bin/env python3
"""
Basic test script to verify imports and syntax without requiring authentication.
"""

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        import monarch_budgeting
        print("✓ monarch_budgeting package imports successfully")
    except Exception as e:
        print(f"✗ Failed to import monarch_budgeting: {e}")
        return False

    try:
        from monarch_budgeting import client
        print("✓ monarch_budgeting.client imports successfully")
    except Exception as e:
        print(f"✗ Failed to import client: {e}")
        return False

    try:
        from monarch_budgeting import analyzer
        print("✓ monarch_budgeting.analyzer imports successfully")
    except Exception as e:
        print(f"✗ Failed to import analyzer: {e}")
        return False

    try:
        from monarch_budgeting import main
        print("✓ monarch_budgeting.main imports successfully")
    except Exception as e:
        print(f"✗ Failed to import main: {e}")
        return False

    return True


def test_class_instantiation():
    """Test that classes can be instantiated without login."""
    print("\nTesting class instantiation...")

    try:
        from monarch_budgeting.client import MonarchClient
        client = MonarchClient()
        print("✓ MonarchClient instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate MonarchClient: {e}")
        return False

    try:
        from monarch_budgeting.analyzer import CreditCardAnalyzer
        # Create with empty data for testing
        analyzer = CreditCardAnalyzer(transactions=[], accounts=[])
        print("✓ CreditCardAnalyzer instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate CreditCardAnalyzer: {e}")
        return False

    return True


def test_analyzer_with_sample_data():
    """Test analyzer with sample data (no API calls)."""
    print("\nTesting analyzer with sample data...")

    try:
        from monarch_budgeting.analyzer import CreditCardAnalyzer

        # Sample credit card account
        sample_accounts = [{
            'id': 'test-123',
            'displayName': 'Test Credit Card',
            'currentBalance': -1500.00,
            'displayBalance': -1500.00,
            'isAsset': False,
            'type': {'name': 'credit', 'display': 'Credit Card'}
        }]

        # Sample transactions
        sample_transactions = [
            {
                'id': 'txn-1',
                'amount': -50.00,  # Purchase
                'date': '2025-01-01',
                'merchant': {'name': 'Amazon'},
                'account': {'id': 'test-123'}
            },
            {
                'id': 'txn-2',
                'amount': 200.00,  # Payment
                'date': '2025-01-02',
                'merchant': {'name': 'Payment'},
                'account': {'id': 'test-123'}
            }
        ]

        analyzer = CreditCardAnalyzer(
            transactions=sample_transactions,
            accounts=sample_accounts
        )

        # Test summary
        summary = analyzer.get_credit_card_summary()
        print(f"✓ Generated account summary: {len(summary)} accounts")

        # Test categorization
        categorized = analyzer.categorize_transactions()
        print(f"✓ Categorized transactions: {len(categorized['purchases'])} purchases, {len(categorized['payments'])} payments")

        # Test report generation
        report = analyzer.generate_report()
        print("✓ Generated text report successfully")

        return True
    except Exception as e:
        print(f"✗ Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Running Basic Tests (No Authentication Required)")
    print("=" * 60)
    print()

    results = []

    results.append(("Import Test", test_imports()))
    results.append(("Instantiation Test", test_class_instantiation()))
    results.append(("Analyzer Sample Data Test", test_analyzer_with_sample_data()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! Code is ready for authentication testing.")
    else:
        print("\n✗ Some tests failed. Please review errors above.")

    exit(0 if all_passed else 1)
