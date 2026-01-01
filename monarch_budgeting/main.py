"""
Main entry point for Monarch Money budgeting analysis.

This script provides a command-line interface for running credit card
debt analysis and generating reports.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from .client import MonarchClient
from .analyzer import CreditCardAnalyzer


async def main():
    """Main execution function."""
    print("Monarch Money - Custom Budgeting Analysis")
    print("=" * 60)
    print()

    # Initialize client
    client = MonarchClient()

    # Login
    print("Logging in to Monarch Money...")
    email = os.getenv('MONARCH_EMAIL')
    password = os.getenv('MONARCH_PASSWORD')

    try:
        await client.login(email=email, password=password, use_saved_session=True)
        print("✓ Login successful")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return

    print()

    # Fetch data
    print("Fetching account data...")
    accounts = await client.get_accounts()
    print(f"✓ Found {len(accounts)} accounts")

    credit_cards = await client.get_credit_card_accounts()
    print(f"✓ Found {len(credit_cards)} credit card accounts")
    print()

    # Get transactions for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"Fetching transactions from {start_date.date()} to {end_date.date()}...")
    transactions = await client.get_transactions(
        start_date=start_date,
        end_date=end_date,
        limit=1000
    )
    print(f"✓ Found {len(transactions)} transactions")
    print()

    # Analyze
    print("Analyzing credit card data...")
    analyzer = CreditCardAnalyzer(transactions=transactions, accounts=accounts)

    # Generate and display report
    report = analyzer.generate_report()
    print(report)
    print()

    # Get debt payoff progress
    progress = analyzer.calculate_debt_payoff_progress(start_date, end_date)
    if not progress.empty:
        print("Debt Payoff Progress (Last 30 Days):")
        print("-" * 60)
        for _, row in progress.iterrows():
            print(f"\n{row['account_name']}:")
            print(f"  Payments Made:      ${row['total_payments']:,.2f}")
            print(f"  New Purchases:      ${row['total_new_purchases']:,.2f}")
            print(f"  Net Debt Reduction: ${row['net_debt_reduction']:,.2f}")
            print(f"  Current Balance:    ${row['current_balance']:,.2f}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
