#!/usr/bin/env python3
"""
Budget Forecast Report

Shows expected cash position at end of month based on:
- Starting cash balance (from accounts)
- Expected income (from budget)
- Expected expenses (from budget)

Usage:
    python budget_forecast.py                    # Current month
    python budget_forecast.py --month 2026-01    # Specific month
    python budget_forecast.py --month 2026-01 --pdf  # Generate PDF
"""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from monarch_budgeting.client import MonarchClient


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
        raise ValueError(f"Invalid month format: {month_str}. Use YYYY-MM (e.g., 2026-01)")


def parse_budget_data(budget_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse budget API response into a usable format."""
    result = {
        'total_income': 0,
        'total_expenses': 0,
        'income_categories': [],
        'expense_categories': []
    }

    # Get totals
    totals = budget_data.get('totalsByMonth', [])
    if totals:
        result['total_income'] = totals[0].get('totalIncome', {}).get('plannedAmount', 0)
        result['total_expenses'] = totals[0].get('totalExpenses', {}).get('plannedAmount', 0)

    # Get category breakdown
    for cat_data in budget_data.get('monthlyAmountsByCategory', []):
        category = cat_data.get('category', {})
        amounts = cat_data.get('monthlyAmounts', [{}])[0]
        planned = amounts.get('plannedCashFlowAmount', 0)

        if planned > 0:
            cat_type = category.get('group', {}).get('type', 'expense')
            entry = {
                'name': category.get('name', 'Unknown'),
                'group': category.get('group', {}).get('name', 'Other'),
                'planned': planned
            }

            if cat_type == 'income':
                result['income_categories'].append(entry)
            elif cat_type == 'expense':
                result['expense_categories'].append(entry)

    # Sort by amount
    result['income_categories'].sort(key=lambda x: x['planned'], reverse=True)
    result['expense_categories'].sort(key=lambda x: x['planned'], reverse=True)

    return result


def format_currency(amount: float) -> str:
    """Format a number as currency."""
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def generate_forecast_pdf(filepath: str, budget: Dict[str, Any],
                          starting_cash: float, month: str):
    """Generate a PDF report for the budget forecast."""
    plt.style.use('seaborn-v0_8-whitegrid')

    expected_income = budget['total_income']
    expected_expenses = budget['total_expenses']
    expected_end_cash = starting_cash + expected_income - expected_expenses

    with PdfPages(filepath) as pdf:
        # Page 1: Summary
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')

        fig.suptitle(f'Budget Forecast - {month}', fontsize=16, fontweight='bold', y=0.95)

        summary_text = f"""
EXPECTED CASH AT END OF MONTH: {format_currency(expected_end_cash)}

Starting Cash:       {format_currency(starting_cash)}
+ Expected Income:   {format_currency(expected_income)}
- Expected Expenses: {format_currency(expected_expenses)}
─────────────────────────────────────
= Expected End:      {format_currency(expected_end_cash)}
"""
        ax.text(0.5, 0.65, summary_text, transform=ax.transAxes,
                fontsize=14, verticalalignment='center', horizontalalignment='center',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

        # Page 2: Income breakdown
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_title('Expected Income', fontsize=14, fontweight='bold', pad=20)

        if budget['income_categories']:
            table_data = [[cat['name'], format_currency(cat['planned'])]
                         for cat in budget['income_categories']]
            table_data.append(['TOTAL', format_currency(expected_income)])

            table = ax.table(cellText=table_data,
                            colLabels=['Category', 'Budgeted'],
                            loc='center',
                            cellLoc='right')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)

            # Style header
            for i in range(2):
                table[(0, i)].set_facecolor('#4472C4')
                table[(0, i)].set_text_props(color='white', fontweight='bold')

            # Style total row
            last_row = len(table_data)
            for i in range(2):
                table[(last_row, i)].set_text_props(fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No income budgeted', ha='center', va='center', fontsize=12)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

        # Page 3: Expense breakdown
        fig = plt.figure(figsize=(8.5, 11))
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_title('Expected Expenses', fontsize=14, fontweight='bold', pad=20)

        if budget['expense_categories']:
            table_data = [[cat['name'], format_currency(cat['planned'])]
                         for cat in budget['expense_categories']]
            table_data.append(['TOTAL', format_currency(expected_expenses)])

            table = ax.table(cellText=table_data,
                            colLabels=['Category', 'Budgeted'],
                            loc='center',
                            cellLoc='right')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.4)

            # Style header
            for i in range(2):
                table[(0, i)].set_facecolor('#C44472')
                table[(0, i)].set_text_props(color='white', fontweight='bold')

            # Style total row
            last_row = len(table_data)
            for i in range(2):
                table[(last_row, i)].set_text_props(fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No expenses budgeted', ha='center', va='center', fontsize=12)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)


def display_forecast(console: Console, budget: Dict[str, Any],
                     starting_cash: float, month: str):
    """Display the budget forecast using rich tables."""
    expected_income = budget['total_income']
    expected_expenses = budget['total_expenses']
    expected_end_cash = starting_cash + expected_income - expected_expenses

    # Main summary panel
    summary = f"""
[bold]EXPECTED CASH AT END OF MONTH: {format_currency(expected_end_cash)}[/bold]

Starting Cash:      {format_currency(starting_cash)}
+ Expected Income:  {format_currency(expected_income)}
- Expected Expenses: {format_currency(expected_expenses)}
────────────────────────────────
= Expected End:     {format_currency(expected_end_cash)}
"""
    console.print(Panel(summary, title=f"Budget Forecast - {month}", border_style="green"))

    # Income table
    if budget['income_categories']:
        income_table = Table(title="Expected Income")
        income_table.add_column("Category", style="cyan")
        income_table.add_column("Budgeted", justify="right", style="green")

        for cat in budget['income_categories']:
            income_table.add_row(cat['name'], format_currency(cat['planned']))

        income_table.add_row("TOTAL", format_currency(expected_income), style="bold")
        console.print(income_table)

    # Expense table
    if budget['expense_categories']:
        expense_table = Table(title="Expected Expenses")
        expense_table.add_column("Category", style="cyan")
        expense_table.add_column("Budgeted", justify="right", style="red")

        for cat in budget['expense_categories']:
            expense_table.add_row(cat['name'], format_currency(cat['planned']))

        expense_table.add_row("TOTAL", format_currency(expected_expenses), style="bold")
        console.print(expense_table)


async def run_forecast(month: str = None, pdf: bool = False):
    """Run the budget forecast analysis."""
    console = Console()

    console.print()
    console.print("[bold]Budget Forecast[/bold]")
    console.print()

    # Parse month or use current month
    if month:
        start_date, end_date = parse_month(month)
    else:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
        if today.month == 12:
            end_date = datetime(today.year + 1, 1, 1)
        else:
            end_date = datetime(today.year, today.month + 1, 1)
        from datetime import timedelta
        end_date = end_date - timedelta(days=1)

    month_str = start_date.strftime("%B %Y")
    month_key = start_date.strftime("%Y-%m")
    console.print(f"[dim]Forecasting: {month_str}[/dim]")
    console.print()

    # Login
    console.print("[dim]Logging in to Monarch Money...[/dim]")
    client = MonarchClient()
    await client.login(use_saved_session=True)
    console.print("[green]✓[/green] Login successful")

    # Get starting cash balance (aggregate snapshot for start of month)
    console.print("[dim]Fetching starting cash balance...[/dim]")
    snapshots = await client.get_aggregate_snapshots(
        start_date=start_date,
        end_date=start_date,
        account_type='depository'
    )

    snapshot_list = snapshots.get('aggregateSnapshots', [])
    if snapshot_list:
        starting_cash = snapshot_list[0].get('balance', 0)
    else:
        # Try to get from previous day if no snapshot for start
        from datetime import timedelta
        prev_day = start_date - timedelta(days=1)
        snapshots = await client.get_aggregate_snapshots(
            start_date=prev_day,
            end_date=prev_day,
            account_type='depository'
        )
        snapshot_list = snapshots.get('aggregateSnapshots', [])
        starting_cash = snapshot_list[0].get('balance', 0) if snapshot_list else 0

    console.print(f"[green]✓[/green] Starting cash: {format_currency(starting_cash)}")

    # Get budget data
    console.print("[dim]Fetching budget data...[/dim]")
    budget_data = await client.get_budget_data(month_key)
    budget = parse_budget_data(budget_data)
    console.print(f"[green]✓[/green] Found {len(budget['income_categories'])} income, "
                  f"{len(budget['expense_categories'])} expense categories")
    console.print()

    # Display forecast
    display_forecast(console, budget, starting_cash, month_str)

    # Generate PDF if requested
    if pdf:
        from pathlib import Path
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        pdf_filename = f"budget_forecast_{month_key}.pdf"
        pdf_filepath = output_dir / pdf_filename

        console.print()
        console.print("[dim]Generating PDF report...[/dim]")
        generate_forecast_pdf(str(pdf_filepath), budget, starting_cash, month_str)
        console.print(f"[green]✓[/green] PDF saved to: {pdf_filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Budget Forecast - See expected cash position"
    )
    parser.add_argument(
        "--month", "-m",
        help="Month to forecast in YYYY-MM format (default: current month)"
    )
    parser.add_argument(
        "--pdf", "-p",
        action="store_true",
        help="Generate PDF report in output/ directory"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_forecast(month=args.month, pdf=args.pdf))
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
