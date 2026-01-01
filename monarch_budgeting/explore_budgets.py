#!/usr/bin/env python3
"""
Explore Monarch Money budget and category API responses.

This script fetches raw budget and category data to understand the exact
structure returned by the API. Run this first to verify field names before
building the full feature.

Usage:
    python -m monarch_budgeting.explore_budgets
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from .client import MonarchClient


async def explore_budget_data():
    """Fetch and display budget and category data from Monarch Money."""
    print("=" * 60)
    print("Monarch Money Budget & Category Explorer")
    print("=" * 60)
    print()

    # Initialize client
    client = MonarchClient()

    # Login using env vars
    print("Logging in...")
    email = os.getenv('MONARCH_EMAIL')
    password = os.getenv('MONARCH_PASSWORD')
    await client.login(email=email, password=password, use_saved_session=True)
    print("✓ Login successful")
    print()

    # Calculate current month date range
    today = datetime.now()
    start_of_month = today.replace(day=1)
    # Get last day of month
    if today.month == 12:
        end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    start_date = start_of_month.strftime('%Y-%m-%d')
    end_date = end_of_month.strftime('%Y-%m-%d')

    print(f"Fetching data for: {start_date} to {end_date}")
    print()

    # Fetch budgets
    print("Fetching budgets...")
    try:
        budgets = await client.get_budgets(start_date=start_date, end_date=end_date)
        print(f"✓ Got budget data")
        print()
        print("=" * 60)
        print("BUDGET DATA STRUCTURE")
        print("=" * 60)
        print(json.dumps(budgets, indent=2, default=str))
    except Exception as e:
        print(f"✗ Error fetching budgets: {e}")
        budgets = None

    print()
    print()

    # Fetch categories
    print("Fetching transaction categories...")
    try:
        categories = await client.get_transaction_categories()
        print(f"✓ Got category data")
        print()
        print("=" * 60)
        print("CATEGORY DATA STRUCTURE")
        print("=" * 60)
        print(json.dumps(categories, indent=2, default=str))
    except Exception as e:
        print(f"✗ Error fetching categories: {e}")
        categories = None

    # Save to files for offline analysis
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    if budgets:
        budget_file = output_dir / "raw_budget_data.json"
        with open(budget_file, 'w') as f:
            json.dump(budgets, f, indent=2, default=str)
        print()
        print(f"✓ Budget data saved to: {budget_file}")

    if categories:
        category_file = output_dir / "raw_category_data.json"
        with open(category_file, 'w') as f:
            json.dump(categories, f, indent=2, default=str)
        print(f"✓ Category data saved to: {category_file}")

    # Also fetch a sample transaction to see category structure in transactions
    print()
    print("Fetching sample transactions to see category field...")
    try:
        transactions = await client.get_transactions(
            start_date=start_of_month,
            end_date=end_of_month,
            limit=5
        )
        print(f"✓ Got {len(transactions)} sample transactions")
        print()
        print("=" * 60)
        print("SAMPLE TRANSACTION STRUCTURE (first 2)")
        print("=" * 60)
        for i, txn in enumerate(transactions[:2]):
            print(f"\n--- Transaction {i+1} ---")
            print(json.dumps(txn, indent=2, default=str))
    except Exception as e:
        print(f"✗ Error fetching transactions: {e}")


if __name__ == "__main__":
    asyncio.run(explore_budget_data())
