#!/usr/bin/env python3
"""
Debt Payoff Projection

Shows how quickly debt could be paid off based on expected monthly surplus
from budget forecast.

Supports three modes:
- Credit Cards (cc): CC debt only, payment = allocation % of surplus
- Loans (loan): Loan debt only, payment = base budget amount + allocation % of surplus
- Both (both): Combined CC + Loan payoff with various allocation splits

Usage:
    python debt_payoff.py                        # CC debt, current month
    python debt_payoff.py --type loan            # Loan debt, current month
    python debt_payoff.py --type both            # Combined CC + Loan
    python debt_payoff.py --type cc --month 2026-01
    python debt_payoff.py --use-local-budget     # Use custom_budget.json
"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
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
    load_custom_budget,
    load_month_budget,
    get_custom_budget_category_amount,
)


# Config file path
DEBT_CONFIG_PATH = Path("debt_config.json")


def load_debt_config() -> Dict[str, Any]:
    """Load debt configuration from JSON file."""
    if not DEBT_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"debt_config.json not found. Copy debt_config.example.json to debt_config.json "
            f"and update with your interest rates."
        )
    with open(DEBT_CONFIG_PATH, 'r') as f:
        return json.load(f)

# Account type names in Monarch API
ACCOUNT_TYPES = {
    'cc': 'credit',
    'loan': 'loan',
}

# Display names for debt types
DEBT_TYPE_NAMES = {
    'cc': 'Credit Card',
    'loan': 'Loan',
}


def project_payoff(
    total_debt: float,
    monthly_payment: float,
    annual_interest_rate: float,
    max_months: int = 240
) -> Dict[str, Any]:
    """
    Project debt payoff over time.

    Args:
        total_debt: Starting total debt (positive number)
        monthly_payment: Amount paid toward debt each month
        annual_interest_rate: Annual interest rate (e.g., 0.24 for 24%)
        max_months: Maximum months to project

    Returns:
        Dict with 'timeline' (list of (month, balance) tuples),
        'total_interest', 'total_paid', 'months', 'paid_off'
    """
    monthly_interest_rate = annual_interest_rate / 12
    balance = total_debt
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
    total_debt: float,
    monthly_surplus: float,
    base_payment: float,
    start_date: datetime,
    debt_type: str,
    annual_rate: float,
    payoff_percentages: List[float]
):
    """
    Generate a plot showing debt payoff projections at different allocation rates.

    Args:
        filepath: Output file path for the plot
        total_debt: Starting total debt
        monthly_surplus: Expected monthly surplus (leftover cash)
        base_payment: Base monthly payment (0 for CC, budgeted amount for loans)
        start_date: Starting month for projections
        debt_type: 'cc' or 'loan'
        annual_rate: Annual interest rate (e.g., 0.24 for 24%)
        payoff_percentages: List of allocation percentages to model
    """
    monthly_rate = annual_rate / 12
    type_name = DEBT_TYPE_NAMES[debt_type]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    # Colors for different percentages (cycle if more than 7)
    base_colors = ['#e74c3c', '#c0392b', '#e67e22', '#f39c12', '#27ae60', '#2980b9', '#8e44ad']
    colors = base_colors * ((len(payoff_percentages) // len(base_colors)) + 1)

    for i, pct in enumerate(payoff_percentages):
        additional_payment = monthly_surplus * pct
        total_payment = base_payment + additional_payment
        result = project_payoff(total_debt, total_payment, annual_rate)
        timeline = result['timeline']

        # Convert to dates and balances
        dates = [start_date + relativedelta(months=m) for m, _ in timeline]
        balances = [b for _, b in timeline]

        # Plot this scenario
        if base_payment > 0:
            label = f"{int(pct * 100)}% (+{format_currency(additional_payment)} = {format_currency(total_payment)}/mo)"
        else:
            label = f"{int(pct * 100)}% ({format_currency(total_payment)}/mo)"
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

    # Title
    if base_payment > 0:
        title = (f'{type_name} Debt Payoff Projections\n'
                 f'Starting Debt: {format_currency(total_debt)} | '
                 f'Base Payment: {format_currency(base_payment)}/mo | '
                 f'Surplus: {format_currency(monthly_surplus)}')
    else:
        title = (f'{type_name} Debt Payoff Projections\n'
                 f'Starting Debt: {format_currency(total_debt)} | '
                 f'Monthly Surplus: {format_currency(monthly_surplus)}')

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Remaining Balance', fontsize=12)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Format x-axis as dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    # Adjust interval based on payoff timeline
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45, ha='right')

    # Legend
    if base_payment > 0:
        ax.legend(title='Allocation % (+ Additional = Total Payment)',
                  loc='upper right', fontsize=8)
    else:
        ax.legend(title='Allocation % (Monthly Payment)',
                  loc='upper right', fontsize=9)

    # Add note about interest rate assumption
    ax.text(0.02, 0.02,
            f'* Assumes {annual_rate:.2%} APR ({monthly_rate:.2%}/month) interest on remaining balance',
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
    total_debt: float,
    monthly_surplus: float,
    base_payment: float,
    start_date: datetime,
    debt_type: str,
    annual_rate: float,
    payoff_percentages: List[float]
):
    """Display payoff projections in terminal."""
    monthly_rate = annual_rate / 12
    type_name = DEBT_TYPE_NAMES[debt_type]

    # Summary panel
    if base_payment > 0:
        summary = f"""
[bold]Starting {type_name} Debt:[/bold] {format_currency(total_debt)}
[bold]Base Monthly Payment:[/bold] {format_currency(base_payment)} (from budget)
[bold]Monthly Surplus:[/bold] {format_currency(monthly_surplus)}
[bold]Interest Rate:[/bold] {annual_rate:.2%} APR ({monthly_rate:.2%}/month)
"""
    else:
        summary = f"""
[bold]Starting {type_name} Debt:[/bold] {format_currency(total_debt)}
[bold]Monthly Surplus:[/bold] {format_currency(monthly_surplus)}
[bold]Interest Rate:[/bold] {annual_rate:.0%} APR ({monthly_rate:.2%}/month)
"""
    console.print(Panel(summary, title=f"{type_name} Debt Payoff Projections", border_style="blue"))

    # Projections table
    table = Table(title="Payoff Scenarios")
    table.add_column("Allocation", style="cyan", justify="right")
    if base_payment > 0:
        table.add_column("Additional", justify="right")
    table.add_column("Total Payment", justify="right")
    table.add_column("Months", justify="right")
    table.add_column("Payoff Date", justify="right")
    table.add_column("Total Interest", justify="right", style="red")

    for pct in payoff_percentages:
        additional_payment = monthly_surplus * pct
        total_payment = base_payment + additional_payment
        result = project_payoff(total_debt, total_payment, annual_rate)

        months = result['months']
        payoff_date = start_date + relativedelta(months=months)

        if result['paid_off']:
            if base_payment > 0:
                table.add_row(
                    f"{int(pct * 100)}%",
                    format_currency(additional_payment),
                    format_currency(total_payment),
                    str(months),
                    payoff_date.strftime("%b %Y"),
                    format_currency(result['total_interest'])
                )
            else:
                table.add_row(
                    f"{int(pct * 100)}%",
                    format_currency(total_payment),
                    str(months),
                    payoff_date.strftime("%b %Y"),
                    format_currency(result['total_interest'])
                )
        else:
            if base_payment > 0:
                table.add_row(
                    f"{int(pct * 100)}%",
                    format_currency(additional_payment),
                    format_currency(total_payment),
                    "240+",
                    "Not within 20 years",
                    "N/A",
                    style="dim"
                )
            else:
                table.add_row(
                    f"{int(pct * 100)}%",
                    format_currency(total_payment),
                    "120+",
                    "Not within 10 years",
                    "N/A",
                    style="dim"
                )

    console.print(table)


def display_combined_summary(
    console: Console,
    cc_debt: float,
    loan_debt: float,
    monthly_surplus: float,
    loan_base_payment: float,
    start_date: datetime,
    cc_rate: float,
    loan_rate: float,
):
    """Display combined CC + Loan payoff projections."""
    total_debt = cc_debt + loan_debt

    # Summary panel
    summary = f"""
[bold]Total Debt:[/bold] {format_currency(total_debt)}
  - Credit Card: {format_currency(cc_debt)} @ {cc_rate:.0%} APR
  - Loan: {format_currency(loan_debt)} @ {loan_rate:.2%} APR

[bold]Loan Base Payment:[/bold] {format_currency(loan_base_payment)}/month (from budget)
[bold]Monthly Surplus:[/bold] {format_currency(monthly_surplus)} (available for extra payments)
"""
    console.print(Panel(summary, title="Combined Debt Payoff Projections", border_style="blue"))

    # Define allocation scenarios
    # Format: (cc_pct, loan_pct, description)
    scenarios = [
        (0.10, 0.10, "Conservative"),
        (0.15, 0.15, "Moderate"),
        (0.20, 0.20, "Balanced"),
        (0.25, 0.25, "Aggressive"),
        (0.10, 0.15, "Loan Focus"),
        (0.15, 0.10, "CC Focus"),
    ]

    # Projections table
    table = Table(title="Combined Payoff Scenarios")
    table.add_column("Scenario", style="cyan")
    table.add_column("CC %", justify="right")
    table.add_column("Loan %", justify="right")
    table.add_column("CC Payment", justify="right")
    table.add_column("Loan Payment", justify="right")
    table.add_column("CC Payoff", justify="right")
    table.add_column("Loan Payoff", justify="right")
    table.add_column("Total Interest", justify="right", style="red")

    for cc_pct, loan_pct, desc in scenarios:
        total_pct = cc_pct + loan_pct
        if total_pct > 1.0:
            continue  # Skip invalid allocations

        cc_payment = monthly_surplus * cc_pct
        loan_additional = monthly_surplus * loan_pct
        loan_payment = loan_base_payment + loan_additional

        cc_result = project_payoff(cc_debt, cc_payment, cc_rate) if cc_debt > 0 and cc_payment > 0 else None
        loan_result = project_payoff(loan_debt, loan_payment, loan_rate) if loan_debt > 0 else None

        # Format CC payoff
        if cc_result and cc_result['paid_off']:
            cc_payoff_date = start_date + relativedelta(months=cc_result['months'])
            cc_payoff_str = cc_payoff_date.strftime("%b %Y")
            cc_interest = cc_result['total_interest']
        elif cc_debt <= 0:
            cc_payoff_str = "No debt"
            cc_interest = 0
        else:
            cc_payoff_str = "10+ yrs"
            cc_interest = 0

        # Format Loan payoff
        if loan_result and loan_result['paid_off']:
            loan_payoff_date = start_date + relativedelta(months=loan_result['months'])
            loan_payoff_str = loan_payoff_date.strftime("%b %Y")
            loan_interest = loan_result['total_interest']
        elif loan_debt <= 0:
            loan_payoff_str = "No debt"
            loan_interest = 0
        else:
            loan_payoff_str = "20+ yrs"
            loan_interest = 0

        total_interest = cc_interest + loan_interest

        table.add_row(
            desc,
            f"{int(cc_pct * 100)}%",
            f"{int(loan_pct * 100)}%",
            format_currency(cc_payment),
            format_currency(loan_payment),
            cc_payoff_str,
            loan_payoff_str,
            format_currency(total_interest) if total_interest > 0 else "N/A"
        )

    console.print(table)

    # Show allocation note
    console.print()
    console.print("[dim]* CC Payment = Surplus × CC%. Loan Payment = Base + (Surplus × Loan%)[/dim]")


def generate_combined_payoff_plot(
    filepath: str,
    cc_debt: float,
    loan_debt: float,
    monthly_surplus: float,
    loan_base_payment: float,
    start_date: datetime,
    cc_rate: float,
    loan_rate: float,
):
    """Generate a plot showing combined CC + Loan payoff projections."""
    # Define scenarios to plot
    scenarios = [
        (0.10, 0.10, "10%/10% Conservative", '#3498db'),
        (0.20, 0.20, "20%/20% Balanced", '#2ecc71'),
        (0.25, 0.25, "25%/25% Aggressive", '#9b59b6'),
        (0.15, 0.10, "15%/10% CC Focus", '#e74c3c'),
        (0.10, 0.15, "10%/15% Loan Focus", '#f39c12'),
    ]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    for cc_pct, loan_pct, label, color in scenarios:
        cc_payment = monthly_surplus * cc_pct
        loan_payment = loan_base_payment + (monthly_surplus * loan_pct)

        # CC projection
        if cc_debt > 0 and cc_payment > 0:
            cc_result = project_payoff(cc_debt, cc_payment, cc_rate)
            cc_dates = [start_date + relativedelta(months=m) for m, _ in cc_result['timeline']]
            cc_balances = [b for _, b in cc_result['timeline']]
            ax1.plot(cc_dates, cc_balances, marker='o', markersize=2, linewidth=2,
                     color=color, label=label, alpha=0.8)

        # Loan projection
        if loan_debt > 0:
            loan_result = project_payoff(loan_debt, loan_payment, loan_rate)
            loan_dates = [start_date + relativedelta(months=m) for m, _ in loan_result['timeline']]
            loan_balances = [b for _, b in loan_result['timeline']]
            ax2.plot(loan_dates, loan_balances, marker='o', markersize=2, linewidth=2,
                     color=color, label=label, alpha=0.8)

    # Format CC plot
    ax1.set_title(f'Credit Card Payoff\nStarting: {format_currency(cc_debt)} @ {cc_rate:.0%} APR',
                  fontsize=12, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=10)
    ax1.set_ylabel('Remaining Balance', fontsize=10)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # Format Loan plot
    ax2.set_title(f'Loan Payoff\nStarting: {format_currency(loan_debt)} @ {loan_rate:.2%} APR\nBase Payment: {format_currency(loan_base_payment)}/mo',
                  fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=10)
    ax2.set_ylabel('Remaining Balance', fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    # Overall title
    fig.suptitle(f'Combined Debt Payoff Projections\nMonthly Surplus: {format_currency(monthly_surplus)}',
                 fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)


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


def get_budget_category_amount(budget_data: Dict[str, Any], category_name: str) -> float:
    """
    Get the planned amount for a specific budget category.

    Args:
        budget_data: Raw budget data from client.get_budget_data()
        category_name: Name of the category to find (e.g., "Loan Repayment")

    Returns:
        Planned amount for the category, or 0 if not found
    """
    for cat_data in budget_data.get('monthlyAmountsByCategory', []):
        category = cat_data.get('category', {})
        if category.get('name', '').lower() == category_name.lower():
            amounts = cat_data.get('monthlyAmounts', [{}])[0]
            return amounts.get('plannedCashFlowAmount', 0)
    return 0


def parse_budget_totals(budget_data: Dict[str, Any]) -> Dict[str, float]:
    """Parse budget API response to extract income and expense totals."""
    result = {
        'total_income': 0,
        'total_expenses': 0,
    }

    totals = budget_data.get('totalsByMonth', [])
    if totals:
        result['total_income'] = totals[0].get('totalIncome', {}).get('plannedAmount', 0)
        result['total_expenses'] = totals[0].get('totalExpenses', {}).get('plannedAmount', 0)

    return result


async def run_combined_debt_payoff(month: str, use_local_budget: bool, console: Console):
    """Run combined CC + Loan debt payoff projection."""
    # Load config
    try:
        config = load_debt_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    interest_rates = config.get('interest_rates', {})
    loan_budget_category = config.get('loan_budget_category', 'Loan Repayment')
    cc_rate = interest_rates.get('cc', 0.21)
    loan_rate = interest_rates.get('loan', 0.1271)

    console.print()
    if use_local_budget:
        console.print("[bold]Combined Debt Payoff Projection[/bold] [dim](using local budget)[/dim]")
    else:
        console.print("[bold]Combined Debt Payoff Projection[/bold]")
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

    # Get all accounts
    console.print("[dim]Fetching accounts...[/dim]")
    accounts = await client.get_accounts()

    # Get CC debt
    cc_accounts = [
        acc for acc in accounts
        if acc.get('type', {}).get('name') == 'credit'
        and (acc.get('currentBalance', 0) or 0) < 0
        and acc.get('includeBalanceInNetWorth', False)
    ]
    cc_debt = sum(abs(acc.get('currentBalance', 0) or 0) for acc in cc_accounts)

    # Get Loan debt
    loan_accounts = [
        acc for acc in accounts
        if acc.get('type', {}).get('name') == 'loan'
        and (acc.get('currentBalance', 0) or 0) < 0
        and acc.get('includeBalanceInNetWorth', False)
    ]
    loan_debt = sum(abs(acc.get('currentBalance', 0) or 0) for acc in loan_accounts)

    total_debt = cc_debt + loan_debt

    console.print(f"[green]✓[/green] Found {len(cc_accounts)} credit cards with debt: {format_currency(cc_debt)}")
    console.print(f"[green]✓[/green] Found {len(loan_accounts)} loans with debt: {format_currency(loan_debt)}")
    console.print(f"[bold]Total Debt: {format_currency(total_debt)}[/bold]")
    console.print()

    # Get starting cash balance
    console.print("[dim]Fetching starting cash balance...[/dim]")
    starting_cash = await get_starting_cash(client, start_date)
    console.print(f"[green]✓[/green] Starting cash: {format_currency(starting_cash)}")

    # Get budget data
    if use_local_budget:
        custom_budget = load_month_budget(month_key)
        if custom_budget:
            console.print(f"[dim]Loading budget from budgets/{month_key}.json...[/dim]")
            expected_income = custom_budget.get('total_income', 0)
            expected_expenses = custom_budget.get('total_expenses', 0)
            loan_base_payment = get_custom_budget_category_amount(custom_budget, loan_budget_category)
        else:
            try:
                custom_budget = load_custom_budget()
                expected_income = custom_budget.get('total_income', 0)
                expected_expenses = custom_budget.get('total_expenses', 0)
                loan_base_payment = get_custom_budget_category_amount(custom_budget, loan_budget_category)
            except FileNotFoundError:
                console.print("[red]Error: No budget found![/red]")
                return
    else:
        console.print("[dim]Fetching budget data...[/dim]")
        budget_data = await client.get_budget_data(month_key)
        budget = parse_budget_totals(budget_data)
        expected_income = budget['total_income']
        expected_expenses = budget['total_expenses']
        loan_base_payment = get_budget_category_amount(budget_data, loan_budget_category)

    monthly_surplus = starting_cash + expected_income - expected_expenses

    console.print(f"[green]✓[/green] Expected income: {format_currency(expected_income)}")
    console.print(f"[green]✓[/green] Expected expenses: {format_currency(expected_expenses)}")
    console.print(f"[green]✓[/green] Loan base payment: {format_currency(loan_base_payment)}/month")
    console.print(f"[bold]Monthly Surplus: {format_currency(monthly_surplus)}[/bold]")
    console.print()

    if monthly_surplus <= 0:
        console.print("[red]Warning: No surplus available for additional debt payoff![/red]")
        return

    if total_debt <= 0:
        console.print("[green]No debt to pay off![/green]")
        return

    # Display summary
    display_combined_summary(
        console, cc_debt, loan_debt, monthly_surplus, loan_base_payment,
        start_date, cc_rate, loan_rate
    )

    # Generate plot
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    if use_local_budget:
        plot_filename = f"combined_payoff_custom_{month_key}.png"
    else:
        plot_filename = f"combined_payoff_{month_key}.png"
    plot_filepath = output_dir / plot_filename

    console.print()
    console.print("[dim]Generating combined payoff projection plot...[/dim]")
    generate_combined_payoff_plot(
        str(plot_filepath), cc_debt, loan_debt, monthly_surplus, loan_base_payment,
        start_date, cc_rate, loan_rate
    )
    console.print(f"[green]✓[/green] Plot saved to: {plot_filepath}")


async def run_debt_payoff(month: str = None, debt_type: str = 'cc', use_local_budget: bool = False):
    """Run the debt payoff projection analysis."""
    console = Console()

    # Handle 'both' type separately
    if debt_type == 'both':
        await run_combined_debt_payoff(month, use_local_budget, console)
        return

    type_name = DEBT_TYPE_NAMES[debt_type]
    account_type = ACCOUNT_TYPES[debt_type]

    # Load config
    try:
        config = load_debt_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    interest_rates = config.get('interest_rates', {})
    payoff_percentages = config.get('payoff_percentages', [0.25, 0.50, 0.75])
    loan_budget_category = config.get('loan_budget_category', 'Loan Repayment')
    annual_rate = interest_rates.get(debt_type, 0.10)

    console.print()
    if use_local_budget:
        console.print(f"[bold]{type_name} Debt Payoff Projection[/bold] [dim](using local budget)[/dim]")
    else:
        console.print(f"[bold]{type_name} Debt Payoff Projection[/bold]")
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

    # Get accounts and balances for the debt type
    console.print(f"[dim]Fetching {type_name.lower()} accounts...[/dim]")
    accounts = await client.get_accounts()
    debt_accounts = [acc for acc in accounts if acc.get('type', {}).get('name') == account_type]

    # Filter to accounts included in net worth with actual debt (negative balance)
    debt_accounts_with_balance = [
        acc for acc in debt_accounts
        if (acc.get('currentBalance', 0) or 0) < 0
        and acc.get('includeBalanceInNetWorth', False)
    ]

    total_debt = sum(
        abs(acc.get('currentBalance', 0) or 0)
        for acc in debt_accounts_with_balance
    )

    console.print(f"[green]✓[/green] Found {len(debt_accounts_with_balance)} {type_name.lower()} accounts with debt")
    for acc in debt_accounts_with_balance:
        balance = acc.get('currentBalance', 0) or 0
        console.print(f"[dim]  - {acc.get('displayName')}: {format_currency(abs(balance))}[/dim]")
    console.print(f"[bold]Total {type_name} Debt: {format_currency(total_debt)}[/bold]")
    console.print()

    # Get starting cash balance
    console.print("[dim]Fetching starting cash balance...[/dim]")
    starting_cash = await get_starting_cash(client, start_date)
    console.print(f"[green]✓[/green] Starting cash: {format_currency(starting_cash)}")

    # Get budget data - either from API or local file
    if use_local_budget:
        # Try month-specific budget first, then fall back to custom_budget.json
        custom_budget = load_month_budget(month_key)
        if custom_budget:
            console.print(f"[dim]Loading budget from budgets/{month_key}.json...[/dim]")
            expected_income = custom_budget.get('total_income', 0)
            expected_expenses = custom_budget.get('total_expenses', 0)
            console.print(f"[green]✓[/green] Loaded month budget")
        else:
            console.print("[dim]Loading custom budget from custom_budget.json...[/dim]")
            try:
                custom_budget = load_custom_budget()
                expected_income = custom_budget.get('total_income', 0)
                expected_expenses = custom_budget.get('total_expenses', 0)
                console.print(f"[green]✓[/green] Loaded custom budget")
            except FileNotFoundError:
                console.print("[red]Error: No budget found![/red]")
                console.print(f"[dim]Create budgets/{month_key}.json or custom_budget.json[/dim]")
                return
    else:
        console.print("[dim]Fetching budget data...[/dim]")
        budget_data = await client.get_budget_data(month_key)
        budget = parse_budget_totals(budget_data)
        expected_income = budget['total_income']
        expected_expenses = budget['total_expenses']

    monthly_surplus = starting_cash + expected_income - expected_expenses

    console.print(f"[green]✓[/green] Expected income: {format_currency(expected_income)}")
    console.print(f"[green]✓[/green] Expected expenses: {format_currency(expected_expenses)}")
    console.print(f"[bold]Monthly Surplus: {format_currency(monthly_surplus)}[/bold]")

    # For loans, get the base payment from budget
    base_payment = 0
    if debt_type == 'loan':
        if use_local_budget:
            base_payment = get_custom_budget_category_amount(custom_budget, loan_budget_category)
        else:
            base_payment = get_budget_category_amount(budget_data, loan_budget_category)
        console.print(f"[green]✓[/green] {loan_budget_category} budget: {format_currency(base_payment)}/month")

    console.print()

    if monthly_surplus <= 0:
        console.print("[red]Warning: No surplus available for additional debt payoff![/red]")
        if base_payment > 0:
            console.print(f"[dim]You can still pay the base amount of {format_currency(base_payment)}/month.[/dim]")
        else:
            console.print("[dim]Consider reducing expenses or increasing income.[/dim]")
        return

    if total_debt <= 0:
        console.print(f"[green]No {type_name.lower()} debt to pay off![/green]")
        return

    # Display summary
    display_summary(console, total_debt, monthly_surplus, base_payment, start_date, debt_type,
                    annual_rate, payoff_percentages)

    # Generate plot
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    if use_local_budget:
        plot_filename = f"{debt_type}_payoff_custom_{month_key}.png"
    else:
        plot_filename = f"{debt_type}_payoff_{month_key}.png"
    plot_filepath = output_dir / plot_filename

    console.print()
    console.print("[dim]Generating payoff projection plot...[/dim]")
    generate_payoff_plot(str(plot_filepath), total_debt, monthly_surplus, base_payment, start_date, debt_type,
                         annual_rate, payoff_percentages)
    console.print(f"[green]✓[/green] Plot saved to: {plot_filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Debt Payoff Projection - See how fast you can pay off debt"
    )
    parser.add_argument(
        "--type", "-t",
        choices=['cc', 'loan', 'both'],
        default='cc',
        help="Type of debt: 'cc' for credit cards, 'loan' for loans, 'both' for combined analysis"
    )
    parser.add_argument(
        "--month", "-m",
        help="Month for budget forecast in YYYY-MM format (default: current month)"
    )
    parser.add_argument(
        "--use-local-budget", "-l",
        action="store_true",
        help="Use custom_budget.json instead of fetching from Monarch Money"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_debt_payoff(month=args.month, debt_type=args.type, use_local_budget=args.use_local_budget))
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
