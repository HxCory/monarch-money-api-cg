"""
Shared utilities for Monarch Money budgeting tools.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# Default path for custom budget file
DEFAULT_CUSTOM_BUDGET_PATH = Path("custom_budget.json")


def format_currency(amount: float, show_sign: bool = False) -> str:
    """
    Format a number as currency.

    Args:
        amount: The amount to format
        show_sign: If True, show + for positive amounts

    Returns:
        Formatted currency string (e.g., "$1,234.56" or "-$500.00")
    """
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    elif show_sign and amount > 0:
        return f"+${amount:,.2f}"
    return f"${amount:,.2f}"


def parse_month(month_str: str) -> Tuple[datetime, datetime]:
    """
    Parse month string (YYYY-MM) into start and end dates.

    Args:
        month_str: Month in YYYY-MM format (e.g., "2026-01")

    Returns:
        Tuple of (start_date, end_date) for the month

    Raises:
        ValueError: If month_str is not in valid format
    """
    try:
        year, month = map(int, month_str.split('-'))
        start = datetime(year, month, 1)

        # Get last day of month
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        end = end - timedelta(days=1)

        return start, end
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid month format: {month_str}. Use YYYY-MM (e.g., 2026-01)")


def get_current_month_range() -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the current month.

    Returns:
        Tuple of (start_date, end_date) for current month
    """
    today = datetime.now()
    start_date = datetime(today.year, today.month, 1)

    if today.month == 12:
        end_date = datetime(today.year + 1, 1, 1)
    else:
        end_date = datetime(today.year, today.month + 1, 1)

    end_date = end_date - timedelta(days=1)
    return start_date, end_date


def get_previous_month_range() -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the previous month.

    Returns:
        Tuple of (start_date, end_date) for previous month
    """
    today = datetime.now()

    if today.month == 1:
        start_date = datetime(today.year - 1, 12, 1)
        end_date = datetime(today.year - 1, 12, 31)
    else:
        start_date = datetime(today.year, today.month - 1, 1)
        end_date = datetime(today.year, today.month, 1) - timedelta(days=1)

    return start_date, end_date


def parse_budget_totals(budget_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Parse budget API response to extract income and expense totals.

    Args:
        budget_data: Raw budget data from client.get_budget_data()

    Returns:
        Dict with 'total_income' and 'total_expenses' keys
    """
    result = {
        'total_income': 0,
        'total_expenses': 0,
    }

    totals = budget_data.get('totalsByMonth', [])
    if totals:
        result['total_income'] = totals[0].get('totalIncome', {}).get('plannedAmount', 0)
        result['total_expenses'] = totals[0].get('totalExpenses', {}).get('plannedAmount', 0)

    return result


def load_custom_budget(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load custom budget from a JSON file.

    Args:
        filepath: Path to the JSON file. Defaults to custom_budget.json in current directory.

    Returns:
        Dict with budget data including:
        - total_income: Total expected income
        - total_expenses: Total expected expenses
        - income_categories: List of income category dicts with 'name', 'group', 'amount'
        - expense_categories: List of expense category dicts with 'name', 'group', 'amount'

    Raises:
        FileNotFoundError: If the budget file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if filepath is None:
        filepath = DEFAULT_CUSTOM_BUDGET_PATH

    with open(filepath, 'r') as f:
        return json.load(f)


def get_custom_budget_category_amount(budget: Dict[str, Any], category_name: str) -> float:
    """
    Get the amount for a specific category from custom budget data.

    Args:
        budget: Custom budget data loaded from JSON
        category_name: Name of the category to find (e.g., "Loan Repayment")

    Returns:
        Amount for the category, or 0 if not found
    """
    # Check expense categories
    for cat in budget.get('expense_categories', []):
        if cat.get('name', '').lower() == category_name.lower():
            return cat.get('amount', 0)

    # Check income categories
    for cat in budget.get('income_categories', []):
        if cat.get('name', '').lower() == category_name.lower():
            return cat.get('amount', 0)

    return 0
