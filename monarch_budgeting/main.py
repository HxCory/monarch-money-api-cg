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
from .visualizer import BudgetVisualizer, create_output_dir


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

    # Get transactions for the last 6 months (for time series analysis)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    print(f"Fetching transactions from {start_date.date()} to {end_date.date()}...")
    transactions = await client.get_transactions(
        start_date=start_date,
        end_date=end_date,
        limit=5000
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

    # Generate visualizations
    print("Generating visualizations...")
    output_dir = create_output_dir()
    print(f"Output directory: {output_dir}")
    print()

    visualizer = BudgetVisualizer()

    # Get monthly aggregated data
    monthly_activity = analyzer.calculate_monthly_cc_activity()
    monthly_by_card = analyzer.calculate_monthly_cc_by_account()

    # 1. Monthly payments vs purchases (all cards combined)
    visualizer.plot_monthly_cc_activity(
        monthly_activity,
        title="Monthly Credit Card Payments vs Purchases",
        save_path=str(output_dir / "01_monthly_payments_vs_purchases.png")
    )

    # 2. Monthly purchases by card
    visualizer.plot_monthly_by_card(
        monthly_by_card,
        value_col='total_purchases',
        title="Monthly Purchases by Credit Card",
        save_path=str(output_dir / "02_monthly_purchases_by_card.png")
    )

    # 3. Cumulative net debt change
    visualizer.plot_cumulative_net_debt(
        monthly_activity,
        title="Cumulative Net Credit Card Debt Change",
        save_path=str(output_dir / "03_cumulative_net_debt.png")
    )

    print()
    print(f"Analysis complete! Figures saved to: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
