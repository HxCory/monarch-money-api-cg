#!/usr/bin/env python3
"""
Debt Payoff Projection

Shows how quickly credit card debt could be paid off based on
expected monthly surplus from budget forecast.

Generates projections for different allocation percentages:
25%, 50%, 60%, 65%, 70%, 75% of leftover money going to CC debt.

Usage:
    python debt_payoff.py                    # Current month forecast
    python debt_payoff.py --month 2026-01    # Specific month forecast
"""

import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dateutil.relativedelta import relativedelta

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from monarch_budgeting.client import MonarchClient
from monarch_budgeting.utils import (
    format_currency,
    parse_month,
    get_current_month_range,
    parse_budget_totals,
)


# Payoff allocation percentages to model
PAYOFF_PERCENTAGES = [0.25, 0.35, 0.50, 0.60, 0.65, 0.70, 0.75]

# Assumed annual interest rate for credit cards
ANNUAL_INTEREST_RATE = 0.24
MONTHLY_INTEREST_RATE = ANNUAL_INTEREST_RATE / 12


def project_payoff(
    total_cc_debt: float,
    monthly_payment: float,
    monthly_interest_rate: float = MONTHLY_INTEREST_RATE,
    max_months: int = 120
) -> Dict[str, Any]:
    """
    Project debt payoff over time.

    Args:
        total_cc_debt: Starting total CC debt (positive number)
        monthly_payment: Amount paid toward debt each month
        monthly_interest_rate: Monthly interest rate (default 2% = 24% APR / 12)
        max_months: Maximum months to project

    Returns:
        Dict with 'timeline' (list of (month, balance) tuples),
        'total_interest', 'total_paid', 'months'
    """
    balance = total_cc_debt
    timeline = [(0, balance)]
    total_interest = 0
    total_paid = 0

    for month in range(1, max_months + 1):
        # Add interest
        interest_this_month = balance * monthly_interest_rate
        balance += interest_this_month
        total_interest += interest_this_month

        # Subtract payment (or remaining balance if less)
        payment = min(monthly_payment, balance)
        balance -= payment
        total_paid += payment

        timeline.append((month, balance))

        if balance <= 0:
            break

    return {
        'timeline': timeline,
        'total_interest': total_interest,
        'total_paid': total_paid,
        'months': len(timeline) - 1,
        'paid_off': balance <= 0
    }


def generate_payoff_plot(
    filepath: str,
    total_cc_debt: float,
    monthly_surplus: float,
    start_date: datetime
):
    """
    Generate a plot showing debt payoff projections at different allocation rates.

    Args:
        filepath: Output file path for the plot
        total_cc_debt: Starting total CC debt
        monthly_surplus: Expected monthly surplus (leftover cash)
        start_date: Starting month for projections
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    # Colors for different percentages
    colors = ['#e74c3c', '#c0392b', '#e67e22', '#f39c12', '#27ae60', '#2980b9', '#8e44ad']

    for i, pct in enumerate(PAYOFF_PERCENTAGES):
        monthly_payment = monthly_surplus * pct
        result = project_payoff(total_cc_debt, monthly_payment)
        timeline = result['timeline']

        # Convert to dates and balances
        dates = [start_date + relativedelta(months=m) for m, _ in timeline]
        balances = [b for _, b in timeline]

        # Plot this scenario
        label = f"{int(pct * 100)}% ({format_currency(monthly_payment)}/mo)"
        ax.plot(dates, balances, marker='o', markersize=3, linewidth=2,
                color=colors[i], label=label, alpha=0.8)

        # Mark payoff point
        if result['paid_off']:
            ax.annotate(f"{result['months']} mo",
                       xy=(dates[-1], 0),
                       xytext=(5, 10),
                       textcoords='offset points',
                       fontsize=8,
                       color=colors[i])

    # Formatting
    ax.set_title(f'Credit Card Debt Payoff Projections\n'
                 f'Starting Debt: {format_currency(total_cc_debt)} | '
                 f'Monthly Surplus: {format_currency(monthly_surplus)}',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Remaining Balance', fontsize=12)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Format x-axis as dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45, ha='right')

    # Legend
    ax.legend(title='Allocation % (Monthly Payment)', loc='upper right', fontsize=9)

    # Add note about interest rate assumption
    ax.text(0.02, 0.02,
            f'* Assumes {ANNUAL_INTEREST_RATE:.0%} APR ({MONTHLY_INTEREST_RATE:.2%}/month) interest on remaining balance',
            transform=ax.transAxes,
            fontsize=9,
            style='italic',
            color='gray')

    # Grid
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)


def display_summary(
    console: Console,
    total_cc_debt: float,
    monthly_surplus: float,
    start_date: datetime
):
    """Display payoff projections in terminal."""
    # Summary panel
    summary = f"""
[bold]Starting CC Debt:[/bold] {format_currency(total_cc_debt)}
[bold]Monthly Surplus:[/bold] {format_currency(monthly_surplus)}
[bold]Interest Rate:[/bold] {ANNUAL_INTEREST_RATE:.0%} APR ({MONTHLY_INTEREST_RATE:.2%}/month)
"""
    console.print(Panel(summary, title="Debt Payoff Projections", border_style="blue"))

    # Projections table
    table = Table(title="Payoff Scenarios")
    table.add_column("Allocation", style="cyan", justify="right")
    table.add_column("Monthly Payment", justify="right")
    table.add_column("Months to Payoff", justify="right")
    table.add_column("Payoff Date", justify="right")
    table.add_column("Total Interest Paid", justify="right", style="red")

    for pct in PAYOFF_PERCENTAGES:
        monthly_payment = monthly_surplus * pct
        result = project_payoff(total_cc_debt, monthly_payment)

        months = result['months']
        payoff_date = start_date + relativedelta(months=months)

        if result['paid_off']:
            table.add_row(
                f"{int(pct * 100)}%",
                format_currency(monthly_payment),
                str(months),
                payoff_date.strftime("%b %Y"),
                format_currency(result['total_interest'])
            )
        else:
            table.add_row(
                f"{int(pct * 100)}%",
                format_currency(monthly_payment),
                "120+",
                "Not within 10 years",
                "N/A",
                style="dim"
            )

    console.print(table)


async def get_starting_cash(client: MonarchClient, start_date: datetime) -> float:
    """Get starting cash balance from account snapshots."""
    snapshots = await client.get_aggregate_snapshots(
        start_date=start_date,
        end_date=start_date,
        account_type='depository'
    )

    snapshot_list = snapshots.get('aggregateSnapshots', [])
    if snapshot_list:
        return snapshot_list[0].get('balance', 0)

    # Try previous day if no snapshot for start
    prev_day = start_date - timedelta(days=1)
    snapshots = await client.get_aggregate_snapshots(
        start_date=prev_day,
        end_date=prev_day,
        account_type='depository'
    )
    snapshot_list = snapshots.get('aggregateSnapshots', [])
    return snapshot_list[0].get('balance', 0) if snapshot_list else 0


async def run_debt_payoff(month: str = None):
    """Run the debt payoff projection analysis."""
    console = Console()

    console.print()
    console.print("[bold]Debt Payoff Projection[/bold]")
    console.print()

    # Parse month or use current month
    if month:
        start_date, end_date = parse_month(month)
    else:
        start_date, end_date = get_current_month_range()

    month_str = start_date.strftime("%B %Y")
    month_key = start_date.strftime("%Y-%m")
    console.print(f"[dim]Based on forecast for: {month_str}[/dim]")
    console.print()

    # Login
    console.print("[dim]Logging in to Monarch Money...[/dim]")
    client = MonarchClient()
    await client.login(use_saved_session=True)
    console.print("[green]✓[/green] Login successful")

    # Get credit card accounts and balances
    console.print("[dim]Fetching credit card accounts...[/dim]")
    accounts = await client.get_accounts()
    cc_accounts = [acc for acc in accounts if acc.get('type', {}).get('name') == 'credit']

    total_cc_debt = sum(
        abs(acc.get('currentBalance', 0) or 0)
        for acc in cc_accounts
    )

    console.print(f"[green]✓[/green] Found {len(cc_accounts)} credit cards")
    for acc in cc_accounts:
        balance = acc.get('currentBalance', 0) or 0
        console.print(f"[dim]  - {acc.get('displayName')}: {format_currency(abs(balance))}[/dim]")
    console.print(f"[bold]Total CC Debt: {format_currency(total_cc_debt)}[/bold]")
    console.print()

    # Get starting cash balance
    console.print("[dim]Fetching starting cash balance...[/dim]")
    starting_cash = await get_starting_cash(client, start_date)
    console.print(f"[green]✓[/green] Starting cash: {format_currency(starting_cash)}")

    # Get budget data
    console.print("[dim]Fetching budget data...[/dim]")
    budget_data = await client.get_budget_data(month_key)
    budget = parse_budget_totals(budget_data)

    expected_income = budget['total_income']
    expected_expenses = budget['total_expenses']
    monthly_surplus = starting_cash + expected_income - expected_expenses

    console.print(f"[green]✓[/green] Expected income: {format_currency(expected_income)}")
    console.print(f"[green]✓[/green] Expected expenses: {format_currency(expected_expenses)}")
    console.print(f"[bold]Monthly Surplus: {format_currency(monthly_surplus)}[/bold]")
    console.print()

    if monthly_surplus <= 0:
        console.print("[red]Warning: No surplus available for debt payoff![/red]")
        console.print("[dim]Consider reducing expenses or increasing income.[/dim]")
        return

    if total_cc_debt <= 0:
        console.print("[green]No credit card debt to pay off![/green]")
        return

    # Display summary
    display_summary(console, total_cc_debt, monthly_surplus, start_date)

    # Generate plot
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    plot_filename = f"debt_payoff_{month_key}.png"
    plot_filepath = output_dir / plot_filename

    console.print()
    console.print("[dim]Generating payoff projection plot...[/dim]")
    generate_payoff_plot(str(plot_filepath), total_cc_debt, monthly_surplus, start_date)
    console.print(f"[green]✓[/green] Plot saved to: {plot_filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Debt Payoff Projection - See how fast you can pay off CC debt"
    )
    parser.add_argument(
        "--month", "-m",
        help="Month for budget forecast in YYYY-MM format (default: current month)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_debt_payoff(month=args.month))
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
