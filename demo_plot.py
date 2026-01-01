#!/usr/bin/env python3
"""
Demo script to test cash flow plotting with dummy data.

This script demonstrates the cash flow analysis and visualization features
without requiring authentication to Monarch Money.
"""

from monarch_budgeting.analyzer import CreditCardAnalyzer
from monarch_budgeting.visualizer import BudgetVisualizer
from test_data import get_test_data


def main():
    """Run the cash flow demo."""
    print("=" * 70)
    print("Monarch Money - Cash Flow Analysis Demo")
    print("=" * 70)
    print()

    # Load test data
    print("Loading test data...")
    data = get_test_data()
    accounts = data['accounts']
    transactions = data['transactions']

    print(f"✓ Loaded {len(accounts)} accounts")
    print(f"✓ Loaded {len(transactions)} transactions")
    print()

    # Display account summary
    print("Account Summary:")
    print("-" * 70)
    for acc in accounts:
        acc_type = acc['type']['display']
        balance = acc['currentBalance']
        print(f"  {acc['displayName']:30} ({acc_type:15}) ${balance:>10,.2f}")
    print()

    # Initialize analyzer
    print("Initializing analyzer...")
    analyzer = CreditCardAnalyzer(transactions=transactions, accounts=accounts)
    print(f"✓ Found {len(analyzer.credit_card_accounts)} credit card accounts")
    print()

    # Calculate cash flow over time
    print("Calculating cash flow over time...")
    cash_flow = analyzer.calculate_cash_flow_over_time(frequency='ME')
    print(f"✓ Calculated cash flow for {len(cash_flow)} time periods")
    print()

    # Display cash flow data
    print("Cash Flow by Month:")
    print("-" * 70)
    print(f"{'Date':12} {'Income':>12} {'Total Exp':>12} {'CC Exp':>12} {'Cash Bal':>12}")
    print("-" * 70)
    for _, row in cash_flow.iterrows():
        date_str = row['date'].strftime('%Y-%m')
        print(f"{date_str:12} ${row['income']:>10,.2f} ${row['total_expenses']:>10,.2f} "
              f"${row['cc_expenses']:>10,.2f} ${row['cash_balance']:>10,.2f}")
    print()

    # Calculate summary statistics
    print("Summary Statistics:")
    print("-" * 70)
    summary = analyzer.calculate_monthly_summary()
    for key, value in summary.items():
        label = key.replace('_', ' ').title()
        print(f"  {label:35} ${value:>12,.2f}")
    print()

    # Create visualizer
    print("Creating visualization...")
    visualizer = BudgetVisualizer(figsize=(14, 7))

    # Generate summary table
    summary_table = visualizer.create_summary_table(cash_flow)
    print("\nSummary Table:")
    print("-" * 70)
    print(summary_table.to_string(index=False))
    print()

    # Create plot
    output_path = 'cash_flow_demo.png'
    print(f"Generating plot and saving to: {output_path}")
    visualizer.plot_cash_flow(
        cash_flow_df=cash_flow,
        title="Cash Flow Analysis - Demo Data (Last 6 Months)",
        save_path=output_path
    )

    print()
    print("=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)
    print()
    print("Key Insights:")
    print("-" * 70)
    print(f"• Average Monthly Income:      ${summary['avg_monthly_income']:>10,.2f}")
    print(f"• Average Monthly Expenses:    ${summary['avg_monthly_expenses']:>10,.2f}")
    print(f"• Average CC Expenses:         ${summary['avg_monthly_cc_expenses']:>10,.2f}")
    print(f"• Average Cash Balance:        ${summary['avg_cash_balance']:>10,.2f}")
    print(f"• Net Cash Flow (Total):       ${summary['net_cash_flow']:>10,.2f}")
    print()

    cc_pct = (summary['total_cc_expenses'] / summary['total_expenses'] * 100) if summary['total_expenses'] > 0 else 0
    print(f"• Credit cards account for {cc_pct:.1f}% of total expenses")
    print()

    print(f"View the plot at: {output_path}")
    print()


if __name__ == "__main__":
    main()
