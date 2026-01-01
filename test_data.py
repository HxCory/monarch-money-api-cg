"""
Test data simulating Monarch Money API responses.

This module provides realistic dummy data for testing without requiring authentication.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_dummy_accounts() -> List[Dict[str, Any]]:
    """
    Generate dummy account data simulating Monarch Money API response.

    Returns:
        List of account dictionaries
    """
    return [
        {
            'id': 'checking-001',
            'displayName': 'Chase Checking',
            'currentBalance': 3500.00,
            'displayBalance': 3500.00,
            'isAsset': True,
            'type': {'name': 'checking', 'display': 'Checking'},
            'subtype': {'name': 'checking', 'display': 'Checking'}
        },
        {
            'id': 'savings-001',
            'displayName': 'Ally Savings',
            'currentBalance': 15000.00,
            'displayBalance': 15000.00,
            'isAsset': True,
            'type': {'name': 'savings', 'display': 'Savings'},
            'subtype': {'name': 'savings', 'display': 'Savings'}
        },
        {
            'id': 'cc-001',
            'displayName': 'Chase Sapphire',
            'currentBalance': -1245.67,
            'displayBalance': -1245.67,
            'isAsset': False,
            'type': {'name': 'credit', 'display': 'Credit Card'},
            'subtype': {'name': 'credit_card', 'display': 'Credit Card'}
        },
        {
            'id': 'cc-002',
            'displayName': 'Capital One Quicksilver',
            'currentBalance': -850.32,
            'displayBalance': -850.32,
            'isAsset': False,
            'type': {'name': 'credit', 'display': 'Credit Card'},
            'subtype': {'name': 'credit_card', 'display': 'Credit Card'}
        },
        {
            'id': 'cc-003',
            'displayName': 'Discover It',
            'currentBalance': 0.00,
            'displayBalance': 0.00,
            'isAsset': False,
            'type': {'name': 'credit', 'display': 'Credit Card'},
            'subtype': {'name': 'credit_card', 'display': 'Credit Card'}
        }
    ]


def generate_dummy_transactions(num_months: int = 6) -> List[Dict[str, Any]]:
    """
    Generate dummy transaction data simulating Monarch Money API response.

    Args:
        num_months: Number of months of data to generate

    Returns:
        List of transaction dictionaries
    """
    transactions = []
    current_date = datetime.now()

    # Account IDs
    checking_id = 'checking-001'
    cc1_id = 'cc-001'
    cc2_id = 'cc-002'

    # Generate transactions for each month
    for month_offset in range(num_months):
        # Calculate month start date
        month_date = current_date - timedelta(days=30 * month_offset)
        month_str = month_date.strftime('%Y-%m')

        # Monthly income (paycheck)
        transactions.append({
            'id': f'txn-income-{month_offset}-1',
            'amount': 5000.00,  # Positive = income
            'date': f'{month_str}-01',
            'merchant': {'name': 'Employer Direct Deposit'},
            'category': {'id': 'cat-income', 'name': 'Income'},
            'account': {'id': checking_id, 'displayName': 'Chase Checking'},
            'pending': False,
            'notes': 'Monthly salary'
        })

        # Rent (from checking - non-CC expense)
        transactions.append({
            'id': f'txn-rent-{month_offset}',
            'amount': -1500.00,  # Negative = expense
            'date': f'{month_str}-05',
            'merchant': {'name': 'Landlord LLC'},
            'category': {'id': 'cat-housing', 'name': 'Rent'},
            'account': {'id': checking_id, 'displayName': 'Chase Checking'},
            'pending': False,
            'notes': 'Monthly rent'
        })

        # Utilities (from checking - non-CC expense)
        transactions.append({
            'id': f'txn-utilities-{month_offset}',
            'amount': -120.00,
            'date': f'{month_str}-08',
            'merchant': {'name': 'Electric Company'},
            'category': {'id': 'cat-utilities', 'name': 'Utilities'},
            'account': {'id': checking_id, 'displayName': 'Chase Checking'},
            'pending': False,
            'notes': 'Electric bill'
        })

        # Groceries (from CC - CC expense)
        transactions.append({
            'id': f'txn-groceries-{month_offset}-1',
            'amount': -300.00,
            'date': f'{month_str}-10',
            'merchant': {'name': 'Whole Foods'},
            'category': {'id': 'cat-groceries', 'name': 'Groceries'},
            'account': {'id': cc1_id, 'displayName': 'Chase Sapphire'},
            'pending': False,
            'notes': 'Weekly groceries'
        })

        # Groceries (from CC - CC expense)
        transactions.append({
            'id': f'txn-groceries-{month_offset}-2',
            'amount': -250.00,
            'date': f'{month_str}-20',
            'merchant': {'name': 'Trader Joes'},
            'category': {'id': 'cat-groceries', 'name': 'Groceries'},
            'account': {'id': cc1_id, 'displayName': 'Chase Sapphire'},
            'pending': False,
            'notes': 'Weekly groceries'
        })

        # Dining (from CC - CC expense)
        transactions.append({
            'id': f'txn-dining-{month_offset}-1',
            'amount': -75.00,
            'date': f'{month_str}-12',
            'merchant': {'name': 'Restaurant ABC'},
            'category': {'id': 'cat-dining', 'name': 'Dining'},
            'account': {'id': cc2_id, 'displayName': 'Capital One Quicksilver'},
            'pending': False,
            'notes': 'Dinner'
        })

        # Shopping (from CC - CC expense)
        transactions.append({
            'id': f'txn-shopping-{month_offset}',
            'amount': -150.00,
            'date': f'{month_str}-15',
            'merchant': {'name': 'Amazon'},
            'category': {'id': 'cat-shopping', 'name': 'Shopping'},
            'account': {'id': cc1_id, 'displayName': 'Chase Sapphire'},
            'pending': False,
            'notes': 'Online shopping'
        })

        # Gas (from checking - non-CC expense)
        transactions.append({
            'id': f'txn-gas-{month_offset}',
            'amount': -60.00,
            'date': f'{month_str}-18',
            'merchant': {'name': 'Shell Gas Station'},
            'category': {'id': 'cat-auto', 'name': 'Auto & Transport'},
            'account': {'id': checking_id, 'displayName': 'Chase Checking'},
            'pending': False,
            'notes': 'Gas'
        })

        # Credit Card Payment (from checking to CC - positive on checking)
        transactions.append({
            'id': f'txn-cc-payment-{month_offset}',
            'amount': -800.00,
            'date': f'{month_str}-25',
            'merchant': {'name': 'Credit Card Payment'},
            'category': {'id': 'cat-transfer', 'name': 'Transfer'},
            'account': {'id': checking_id, 'displayName': 'Chase Checking'},
            'pending': False,
            'notes': 'CC payment'
        })

        # Additional income (bonus, occasional)
        if month_offset == 0:  # Current month
            transactions.append({
                'id': f'txn-bonus-{month_offset}',
                'amount': 1000.00,
                'date': f'{month_str}-15',
                'merchant': {'name': 'Employer Bonus'},
                'category': {'id': 'cat-income', 'name': 'Income'},
                'account': {'id': checking_id, 'displayName': 'Chase Checking'},
                'pending': False,
                'notes': 'Performance bonus'
            })

    return transactions


def get_test_data() -> Dict[str, Any]:
    """
    Get complete test dataset for analysis.

    Returns:
        Dictionary with 'accounts' and 'transactions' keys
    """
    return {
        'accounts': generate_dummy_accounts(),
        'transactions': generate_dummy_transactions(num_months=6)
    }


if __name__ == '__main__':
    """Print sample data for inspection."""
    data = get_test_data()

    print("Sample Accounts:")
    print("=" * 60)
    for acc in data['accounts']:
        print(f"  {acc['displayName']:30} ${acc['currentBalance']:>10,.2f}")

    print("\n\nSample Transactions (first 10):")
    print("=" * 60)
    for txn in data['transactions'][:10]:
        print(f"  {txn['date']:12} {txn['merchant']['name']:30} ${txn['amount']:>10,.2f}")

    print(f"\n\nTotal accounts: {len(data['accounts'])}")
    print(f"Total transactions: {len(data['transactions'])}")
