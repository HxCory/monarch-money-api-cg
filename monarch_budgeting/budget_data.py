"""
Data structures for budget and category data.

This module defines the data classes used for parsing and working with
Monarch Money budget and category information.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class CategoryType(Enum):
    """Type of category (income, expense, or transfer)."""
    INCOME = 'income'
    EXPENSE = 'expense'
    TRANSFER = 'transfer'


@dataclass
class Category:
    """Represents a transaction category from Monarch Money."""
    id: str
    name: str
    group_id: str
    group_name: str
    category_type: CategoryType
    system_category: Optional[str] = None  # e.g., 'groceries', 'paychecks'
    is_system_category: bool = True

    @property
    def is_income(self) -> bool:
        return self.category_type == CategoryType.INCOME

    @property
    def is_expense(self) -> bool:
        return self.category_type == CategoryType.EXPENSE

    @property
    def is_transfer(self) -> bool:
        return self.category_type == CategoryType.TRANSFER

    @property
    def is_cc_payment(self) -> bool:
        """Check if this category represents a credit card payment."""
        return self.system_category == 'credit_card_payment'


@dataclass
class CategoryBreakdown:
    """Breakdown of spending for a single category."""
    category_id: str
    category_name: str
    category_type: CategoryType
    group_name: str
    actual_amount: float  # Total actual spending (absolute value)
    cc_amount: float      # Amount spent on credit cards
    cash_amount: float    # Amount spent with cash/debit (actual - cc)

    @property
    def cc_percentage(self) -> float:
        """Percentage of spending that was on credit cards."""
        if self.actual_amount == 0:
            return 0.0
        return (self.cc_amount / self.actual_amount) * 100


@dataclass
class TopLevelMetrics:
    """Top-level budget metrics for display."""
    total_income: float
    total_expenses: float  # All expenses (CC + cash)
    cc_expenses: float     # Expenses charged to credit cards
    cash_expenses: float   # Expenses paid with cash/debit
    cc_payments: float     # Payments made TO credit cards
    true_cash_remaining: float  # Income - Cash Expenses - CC Payments
    total_new_cc_spending: float  # Same as cc_expenses

    @classmethod
    def calculate(cls,
                  total_income: float,
                  total_expenses: float,
                  cc_expenses: float,
                  cc_payments: float) -> 'TopLevelMetrics':
        """Calculate all metrics from base values."""
        cash_expenses = total_expenses - cc_expenses
        true_cash_remaining = total_income - cash_expenses - cc_payments

        return cls(
            total_income=total_income,
            total_expenses=total_expenses,
            cc_expenses=cc_expenses,
            cash_expenses=cash_expenses,
            cc_payments=cc_payments,
            true_cash_remaining=true_cash_remaining,
            total_new_cc_spending=cc_expenses
        )


def parse_categories(raw_categories: Dict[str, Any]) -> Dict[str, Category]:
    """
    Parse raw category API response into Category objects.

    Args:
        raw_categories: Raw response from get_transaction_categories()
                       Expected format: {'categories': [...]}

    Returns:
        Dictionary of Category objects keyed by category ID
    """
    categories = {}

    raw_list = raw_categories.get('categories', [])

    for raw in raw_list:
        cat_id = raw.get('id')
        if not cat_id:
            continue

        group = raw.get('group', {})
        type_str = group.get('type', 'expense').lower()

        try:
            cat_type = CategoryType(type_str)
        except ValueError:
            cat_type = CategoryType.EXPENSE

        category = Category(
            id=cat_id,
            name=raw.get('name', 'Unknown'),
            group_id=group.get('id', ''),
            group_name=group.get('name', 'Other'),
            category_type=cat_type,
            system_category=raw.get('systemCategory'),
            is_system_category=raw.get('isSystemCategory', False)
        )

        categories[cat_id] = category

    return categories


def get_category_by_name(categories: Dict[str, Category], name: str) -> Optional[Category]:
    """Find a category by name (case-insensitive)."""
    name_lower = name.lower()
    for cat in categories.values():
        if cat.name.lower() == name_lower:
            return cat
    return None


def get_categories_by_type(categories: Dict[str, Category],
                           cat_type: CategoryType) -> List[Category]:
    """Get all categories of a specific type."""
    return [c for c in categories.values() if c.category_type == cat_type]


def get_income_categories(categories: Dict[str, Category]) -> List[Category]:
    """Get all income categories."""
    return get_categories_by_type(categories, CategoryType.INCOME)


def get_expense_categories(categories: Dict[str, Category]) -> List[Category]:
    """Get all expense categories."""
    return get_categories_by_type(categories, CategoryType.EXPENSE)


def get_transfer_categories(categories: Dict[str, Category]) -> List[Category]:
    """Get all transfer categories (including CC payments)."""
    return get_categories_by_type(categories, CategoryType.TRANSFER)
