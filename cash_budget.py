#!/usr/bin/env python3
"""
Cash-Based Budget View

Shows your true cash remaining by separating credit card spending from
actual cash outflows. When you pay for groceries with a credit card,
cash only leaves when you pay the CC bill, not when you make the purchase.

Usage:
    python cash_budget.py                    # Current month
    python cash_budget.py --month 2025-12    # Specific month
    python cash_budget.py --month 2025-12 --save  # Save output to file
    python cash_budget.py --month 2025-12 --pdf   # Generate PDF report
"""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from monarch_budgeting.client import MonarchClient
from monarch_budgeting.analyzer import CashBudgetAnalyzer
from monarch_budgeting.budget_data import parse_categories
from monarch_budgeting.budget_display import BudgetDisplay
from monarch_budgeting.budget_pdf import BudgetPDFReport


def parse_month(month_str: str) -> tuple[datetime, datetime]:
    """Parse month string (YYYY-MM) into start and end dates."""
    try:
        year, month = map(int, month_str.split('-'))
        start = datetime(year, month, 1)

        # Get last day of month
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        from datetime import timedelta
        end = end - timedelta(days=1)

        return start, end
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid month format: {month_str}. Use YYYY-MM (e.g., 2025-12)")


async def fetch_categories(client: MonarchClient) -> dict:
    """Fetch and parse categories from API."""
    raw_categories = await client.get_transaction_categories()
    return parse_categories(raw_categories)


def parse_cash_balances(snapshots: dict, start_date: datetime, end_date: datetime) -> dict:
    """
    Parse cash balance snapshots to get month start and end balances.

    Args:
        snapshots: API response from get_aggregate_snapshots
        start_date: First day of month
        end_date: Last day of month

    Returns:
        Dict with 'start_balance', 'end_balance', 'start_date', 'end_date'
    """
    # Extract the aggregateSnapshots list
    snapshot_list = snapshots.get('aggregateSnapshots', [])

    if not snapshot_list:
        return {
            'start_balance': None,
            'end_balance': None,
            'start_date': start_date,
            'end_date': end_date
        }

    # Sort by date
    sorted_snapshots = sorted(snapshot_list, key=lambda x: x.get('date', ''))

    # Get first and last balance
    start_balance = sorted_snapshots[0].get('balance') if sorted_snapshots else None
    end_balance = sorted_snapshots[-1].get('balance') if sorted_snapshots else None

    # Get actual dates from snapshots
    actual_start = sorted_snapshots[0].get('date') if sorted_snapshots else None
    actual_end = sorted_snapshots[-1].get('date') if sorted_snapshots else None

    return {
        'start_balance': start_balance,
        'end_balance': end_balance,
        'start_date': actual_start or start_date.strftime('%Y-%m-%d'),
        'end_date': actual_end or end_date.strftime('%Y-%m-%d')
    }


async def run_cash_budget(month: str = None, save: bool = False, pdf: bool = False):
    """Run the cash budget analysis."""
    display = BudgetDisplay()
    console = display.console

    console.print()
    console.print("[bold]Cash-Based Budget Analysis[/bold]")
    console.print()

    # Parse month or use previous month (current month likely incomplete)
    if month:
        start_date, end_date = parse_month(month)
    else:
        # Default to previous month
        today = datetime.now()
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
            end_date = datetime(today.year - 1, 12, 31)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
            if today.month == 2:
                end_date = datetime(today.year, today.month, 1)
            else:
                end_date = datetime(today.year, today.month, 1)
            from datetime import timedelta
            end_date = end_date - timedelta(days=1)

    month_str = start_date.strftime("%B %Y")
    console.print(f"[dim]Analyzing: {month_str}[/dim]")
    console.print()

    # Login
    console.print("[dim]Logging in to Monarch Money...[/dim]")
    client = MonarchClient()
    await client.login(use_saved_session=True)
    console.print("[green]✓[/green] Login successful")

    # Fetch accounts
    console.print("[dim]Fetching accounts...[/dim]")
    accounts = await client.get_accounts()
    console.print(f"[green]✓[/green] Found {len(accounts)} accounts")

    # Show cash accounts for debugging
    cash_account_types = ('cash', 'checking', 'savings', 'depository')
    cash_accounts = [acc for acc in accounts if acc.get('type', {}).get('name') in cash_account_types]
    console.print(f"[dim]Cash accounts ({len(cash_accounts)}):[/dim]")
    for acc in cash_accounts:
        acc_type = acc.get('type', {}).get('name', 'unknown')
        balance = acc.get('currentBalance', 0)
        console.print(f"[dim]  - {acc.get('displayName')}: ${balance:,.2f} ({acc_type})[/dim]")

    # Fetch categories
    console.print("[dim]Fetching categories...[/dim]")
    categories = await fetch_categories(client)
    console.print(f"[green]✓[/green] Found {len(categories)} categories")

    # Fetch transactions
    console.print(f"[dim]Fetching transactions for {month_str}...[/dim]")
    transactions = await client.get_transactions(
        start_date=start_date,
        end_date=end_date,
        limit=2000
    )
    console.print(f"[green]✓[/green] Found {len(transactions)} transactions")
    console.print()

    # Fetch cash balance snapshots for the month
    console.print(f"[dim]Fetching cash balance snapshots...[/dim]")
    snapshots = await client.get_aggregate_snapshots(
        start_date=start_date,
        end_date=end_date,
        account_type='depository'  # Cash/checking/savings accounts
    )
    cash_balances = parse_cash_balances(snapshots, start_date, end_date)
    console.print(f"[green]✓[/green] Got balance snapshots")
    console.print()

    # Analyze
    analyzer = CashBudgetAnalyzer(transactions, accounts, categories)
    metrics = analyzer.calculate_top_level_metrics()
    income = analyzer.get_income_breakdown()
    expenses = analyzer.get_expense_breakdown()

    # Display
    display.display_full_budget(metrics, income, expenses, cash_balances, month=month_str)

    # Save text file if requested
    if save:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        filename = f"cash_budget_{start_date.strftime('%Y%m')}.txt"
        filepath = output_dir / filename

        # Export to file using rich's export
        with open(filepath, 'w') as f:
            from rich.console import Console
            file_console = Console(file=f, force_terminal=True, width=100)
            file_display = BudgetDisplay()
            file_display.console = file_console
            file_display.display_full_budget(metrics, income, expenses, cash_balances, month=month_str)

        console.print(f"[green]✓[/green] Saved to: {filepath}")

    # Generate PDF if requested
    if pdf:
        console.print()
        console.print("[dim]Fetching account histories for chart...[/dim]")

        # Fetch history for each cash account
        account_histories = {}
        for acc in cash_accounts:
            acc_id = acc.get('id')
            acc_name = acc.get('displayName', f'Account {acc_id}')
            try:
                history = await client.get_account_history(acc_id)
                account_histories[acc_name] = history
            except Exception as e:
                console.print(f"[yellow]Warning: Could not fetch history for {acc_name}: {e}[/yellow]")

        console.print(f"[green]✓[/green] Fetched history for {len(account_histories)} accounts")

        # Generate PDF
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        pdf_filename = f"cash_budget_{start_date.strftime('%Y%m')}.pdf"
        pdf_filepath = output_dir / pdf_filename

        console.print("[dim]Generating PDF report...[/dim]")
        pdf_report = BudgetPDFReport()
        pdf_report.generate_report(
            filepath=str(pdf_filepath),
            metrics=metrics,
            income_df=income,
            expense_df=expenses,
            cash_balances=cash_balances,
            account_histories=account_histories,
            start_date=start_date,
            end_date=end_date,
            month=month_str
        )
        console.print(f"[green]✓[/green] PDF saved to: {pdf_filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Cash-Based Budget View - See your true cash remaining"
    )
    parser.add_argument(
        "--month", "-m",
        help="Month to analyze in YYYY-MM format (default: previous month)"
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save output to file in output/ directory"
    )
    parser.add_argument(
        "--pdf", "-p",
        action="store_true",
        help="Generate PDF report with charts in output/ directory"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_cash_budget(month=args.month, save=args.save, pdf=args.pdf))
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
