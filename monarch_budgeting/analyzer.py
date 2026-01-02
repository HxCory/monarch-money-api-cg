"""
Credit card debt and budgeting analysis.

This module provides analysis functionality for credit card debt payoff
and custom budgeting insights.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np


class CreditCardAnalyzer:
    """Analyzer for credit card debt and spending patterns."""

    def __init__(self, transactions: List[Dict[str, Any]], accounts: List[Dict[str, Any]]):
        """
        Initialize the analyzer with transactions and accounts.

        Args:
            transactions: List of transaction dictionaries
            accounts: List of account dictionaries
        """
        self.transactions = transactions
        self.accounts = accounts
        self.credit_card_accounts = [
            acc for acc in accounts
            if acc.get('type', {}).get('name') == 'credit'
        ]

    def get_credit_card_summary(self) -> pd.DataFrame:
        """
        Get a summary of all credit card accounts.

        Returns:
            DataFrame with credit card account information
        """
        summary_data = []

        for account in self.credit_card_accounts:
            summary_data.append({
                'account_id': account.get('id'),
                'account_name': account.get('displayName'),
                'current_balance': account.get('currentBalance', 0),
                'display_balance': account.get('displayBalance', 0),
                'is_asset': account.get('isAsset', False),
            })

        return pd.DataFrame(summary_data)

    def categorize_transactions(self) -> Dict[str, pd.DataFrame]:
        """
        Categorize credit card transactions as new purchases vs. payments.

        Returns:
            Dictionary with 'purchases' and 'payments' DataFrames
        """
        if not self.transactions:
            return {'purchases': pd.DataFrame(), 'payments': pd.DataFrame()}

        df = pd.DataFrame(self.transactions)

        # Extract account IDs from nested account data
        # Handle both dict and direct access patterns
        if 'account' in df.columns:
            df['account_id'] = df['account'].apply(
                lambda x: x.get('id') if isinstance(x, dict) else None
            )
        else:
            # If no account column, return empty DataFrames
            return {'purchases': pd.DataFrame(), 'payments': pd.DataFrame()}

        # Filter for credit card transactions
        cc_account_ids = [acc['id'] for acc in self.credit_card_accounts]
        cc_transactions = df[df['account_id'].isin(cc_account_ids)]

        # Positive amounts are payments, negative are purchases
        # (This may need adjustment based on actual Monarch data format)
        purchases = cc_transactions[cc_transactions['amount'] < 0].copy()
        payments = cc_transactions[cc_transactions['amount'] > 0].copy()

        return {
            'purchases': purchases,
            'payments': payments
        }

    def calculate_debt_payoff_progress(self, start_date: datetime,
                                      end_date: datetime) -> pd.DataFrame:
        """
        Calculate debt payoff progress over a time period.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            DataFrame with debt payoff progress by account
        """
        categorized = self.categorize_transactions()
        payments = categorized['payments']
        purchases = categorized['purchases']

        progress_data = []

        for account in self.credit_card_accounts:
            account_id = account['id']
            account_name = account['displayName']

            # Filter transactions for this account using the account_id column
            account_payments = payments[
                payments['account_id'] == account_id
            ] if 'account_id' in payments.columns else pd.DataFrame()

            account_purchases = purchases[
                purchases['account_id'] == account_id
            ] if 'account_id' in purchases.columns else pd.DataFrame()

            total_payments = account_payments['amount'].sum() if len(account_payments) > 0 else 0
            total_purchases = abs(account_purchases['amount'].sum()) if len(account_purchases) > 0 else 0
            net_payoff = total_payments - total_purchases

            progress_data.append({
                'account_id': account_id,
                'account_name': account_name,
                'total_payments': total_payments,
                'total_new_purchases': total_purchases,
                'net_debt_reduction': net_payoff,
                'current_balance': account.get('currentBalance', 0),
            })

        return pd.DataFrame(progress_data)

    def generate_report(self) -> str:
        """
        Generate a text report of credit card analysis.

        Returns:
            Formatted text report
        """
        summary = self.get_credit_card_summary()
        categorized = self.categorize_transactions()

        report = []
        report.append("=" * 60)
        report.append("CREDIT CARD DEBT ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        report.append("Account Summary:")
        report.append("-" * 60)
        for _, row in summary.iterrows():
            report.append(f"  {row['account_name']}: ${row['current_balance']:,.2f}")
        report.append("")

        total_balance = summary['current_balance'].sum()
        report.append(f"Total Credit Card Debt: ${total_balance:,.2f}")
        report.append("")

        report.append("Transaction Summary:")
        report.append("-" * 60)
        purchases_count = len(categorized['purchases'])
        payments_count = len(categorized['payments'])
        report.append(f"  New Purchases: {purchases_count} transactions")
        report.append(f"  Payments: {payments_count} transactions")
        report.append("")

        if purchases_count > 0:
            total_purchases = abs(categorized['purchases']['amount'].sum())
            report.append(f"  Total New Purchases: ${total_purchases:,.2f}")

        if payments_count > 0:
            total_payments = categorized['payments']['amount'].sum()
            report.append(f"  Total Payments: ${total_payments:,.2f}")

        report.append("=" * 60)

        return "\n".join(report)

    def calculate_cash_flow_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: str = 'ME'
    ) -> pd.DataFrame:
        """
        Calculate income, expenses, CC expenses, and cash balance over time.

        Args:
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            frequency: Pandas frequency string ('D'=daily, 'W'=weekly, 'ME'=month end)

        Returns:
            DataFrame with columns: date, income, total_expenses, cc_expenses, cash_balance
        """
        if not self.transactions:
            return pd.DataFrame(columns=['date', 'income', 'total_expenses', 'cc_expenses', 'cash_balance'])

        # Create DataFrame from transactions
        df = pd.DataFrame(self.transactions)

        # Parse dates
        df['date'] = pd.to_datetime(df['date'])

        # Filter by date range if provided
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]

        # Get credit card account IDs
        cc_account_ids = [acc['id'] for acc in self.credit_card_accounts]

        # Add account_id column
        if 'account' in df.columns:
            df['account_id'] = df['account'].apply(
                lambda x: x.get('id') if isinstance(x, dict) else None
            )
        else:
            df['account_id'] = None

        # Mark if transaction is from CC
        df['is_cc'] = df['account_id'].isin(cc_account_ids)

        # In Monarch Money:
        # - Positive amounts = income/payments/credits
        # - Negative amounts = expenses/purchases/debits

        # Calculate components
        df['income'] = df['amount'].apply(lambda x: x if x > 0 else 0)
        df['expense'] = df['amount'].apply(lambda x: -x if x < 0 else 0)
        df['cc_expense'] = df.apply(
            lambda row: -row['amount'] if row['amount'] < 0 and row['is_cc'] else 0,
            axis=1
        )

        # Group by time period
        grouped = df.groupby(pd.Grouper(key='date', freq=frequency)).agg({
            'income': 'sum',
            'expense': 'sum',
            'cc_expense': 'sum'
        }).reset_index()

        # Rename columns
        grouped.columns = ['date', 'income', 'total_expenses', 'cc_expenses']

        # Calculate cash balance = income - (total_expenses - cc_expenses)
        # This represents cash flow from non-CC expenses
        grouped['cash_balance'] = grouped['income'] - (grouped['total_expenses'] - grouped['cc_expenses'])

        # Remove rows where all values are zero
        grouped = grouped[(grouped['income'] != 0) |
                         (grouped['total_expenses'] != 0) |
                         (grouped['cc_expenses'] != 0)]

        return grouped

    def get_cc_account_ids(self) -> List[str]:
        """
        Get list of credit card account IDs.

        Returns:
            List of credit card account IDs
        """
        return [acc['id'] for acc in self.credit_card_accounts]

    def calculate_monthly_cc_activity(self) -> pd.DataFrame:
        """
        Calculate monthly credit card payments and purchases (all cards combined).

        Returns:
            DataFrame with columns: month, total_payments, total_purchases, net_change
        """
        categorized = self.categorize_transactions()
        payments = categorized['payments']
        purchases = categorized['purchases']

        if payments.empty and purchases.empty:
            return pd.DataFrame(columns=['month', 'total_payments', 'total_purchases', 'net_change'])

        # Process payments
        if not payments.empty:
            payments = payments.copy()
            payments['date'] = pd.to_datetime(payments['date'])
            payments['month'] = payments['date'].dt.to_period('M').dt.to_timestamp()
            monthly_payments = payments.groupby('month')['amount'].sum().reset_index()
            monthly_payments.columns = ['month', 'total_payments']
        else:
            monthly_payments = pd.DataFrame(columns=['month', 'total_payments'])

        # Process purchases
        if not purchases.empty:
            purchases = purchases.copy()
            purchases['date'] = pd.to_datetime(purchases['date'])
            purchases['month'] = purchases['date'].dt.to_period('M').dt.to_timestamp()
            monthly_purchases = purchases.groupby('month')['amount'].sum().abs().reset_index()
            monthly_purchases.columns = ['month', 'total_purchases']
        else:
            monthly_purchases = pd.DataFrame(columns=['month', 'total_purchases'])

        # Merge
        if not monthly_payments.empty and not monthly_purchases.empty:
            result = pd.merge(monthly_payments, monthly_purchases, on='month', how='outer')
        elif not monthly_payments.empty:
            result = monthly_payments
            result['total_purchases'] = 0
        elif not monthly_purchases.empty:
            result = monthly_purchases
            result['total_payments'] = 0
        else:
            return pd.DataFrame(columns=['month', 'total_payments', 'total_purchases', 'net_change'])

        result = result.fillna(0)
        result['net_change'] = result['total_payments'] - result['total_purchases']
        result = result.sort_values('month')

        return result

    def calculate_monthly_cc_by_account(self) -> pd.DataFrame:
        """
        Calculate monthly credit card activity broken down by account.

        Returns:
            DataFrame with columns: month, account_name, total_payments, total_purchases, net_change
        """
        categorized = self.categorize_transactions()
        payments = categorized['payments']
        purchases = categorized['purchases']

        if payments.empty and purchases.empty:
            return pd.DataFrame(columns=['month', 'account_name', 'total_payments', 'total_purchases', 'net_change'])

        # Create account ID to name mapping
        account_map = {acc['id']: acc['displayName'] for acc in self.credit_card_accounts}

        results = []

        for account_id, account_name in account_map.items():
            # Filter transactions for this account
            acc_payments = payments[payments['account_id'] == account_id] if not payments.empty and 'account_id' in payments.columns else pd.DataFrame()
            acc_purchases = purchases[purchases['account_id'] == account_id] if not purchases.empty and 'account_id' in purchases.columns else pd.DataFrame()

            # Monthly payments
            if not acc_payments.empty:
                acc_payments = acc_payments.copy()
                acc_payments['date'] = pd.to_datetime(acc_payments['date'])
                acc_payments['month'] = acc_payments['date'].dt.to_period('M').dt.to_timestamp()
                monthly_pay = acc_payments.groupby('month')['amount'].sum().reset_index()
                monthly_pay.columns = ['month', 'total_payments']
            else:
                monthly_pay = pd.DataFrame(columns=['month', 'total_payments'])

            # Monthly purchases
            if not acc_purchases.empty:
                acc_purchases = acc_purchases.copy()
                acc_purchases['date'] = pd.to_datetime(acc_purchases['date'])
                acc_purchases['month'] = acc_purchases['date'].dt.to_period('M').dt.to_timestamp()
                monthly_purch = acc_purchases.groupby('month')['amount'].sum().abs().reset_index()
                monthly_purch.columns = ['month', 'total_purchases']
            else:
                monthly_purch = pd.DataFrame(columns=['month', 'total_purchases'])

            # Merge for this account
            if not monthly_pay.empty and not monthly_purch.empty:
                merged = pd.merge(monthly_pay, monthly_purch, on='month', how='outer')
            elif not monthly_pay.empty:
                merged = monthly_pay
                merged['total_purchases'] = 0
            elif not monthly_purch.empty:
                merged = monthly_purch
                merged['total_payments'] = 0
            else:
                continue

            merged = merged.fillna(0)
            merged['account_name'] = account_name
            merged['net_change'] = merged['total_payments'] - merged['total_purchases']
            results.append(merged)

        if not results:
            return pd.DataFrame(columns=['month', 'account_name', 'total_payments', 'total_purchases', 'net_change'])

        result = pd.concat(results, ignore_index=True)
        result = result.sort_values(['month', 'account_name'])

        return result

    def calculate_monthly_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate summary statistics for the time period.

        Args:
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            Dictionary with summary statistics
        """
        cash_flow = self.calculate_cash_flow_over_time(start_date, end_date, frequency='ME')

        if cash_flow.empty:
            return {
                'total_income': 0,
                'total_expenses': 0,
                'total_cc_expenses': 0,
                'avg_monthly_income': 0,
                'avg_monthly_expenses': 0,
                'avg_monthly_cc_expenses': 0,
                'avg_cash_balance': 0,
                'net_cash_flow': 0
            }

        return {
            'total_income': cash_flow['income'].sum(),
            'total_expenses': cash_flow['total_expenses'].sum(),
            'total_cc_expenses': cash_flow['cc_expenses'].sum(),
            'avg_monthly_income': cash_flow['income'].mean(),
            'avg_monthly_expenses': cash_flow['total_expenses'].mean(),
            'avg_monthly_cc_expenses': cash_flow['cc_expenses'].mean(),
            'avg_cash_balance': cash_flow['cash_balance'].mean(),
            'net_cash_flow': cash_flow['income'].sum() - cash_flow['total_expenses'].sum()
        }


class CashBudgetAnalyzer:
    """
    Analyzer for cash-based budgeting that separates CC spending from cash flow.

    This provides a more accurate view of actual cash remaining by treating
    credit card spending separately from when cash actually leaves (CC payments).
    Uses actual cash account balances rather than income-based calculations.
    """

    # Categories to exclude from income/expense calculations
    EXCLUDED_CATEGORIES = {'Dividends & Capital Gains'}

    def __init__(self,
                 transactions: List[Dict[str, Any]],
                 accounts: List[Dict[str, Any]],
                 categories: Dict[str, Any]):
        """
        Initialize the cash budget analyzer.

        Args:
            transactions: List of transaction dictionaries
            accounts: List of account dictionaries
            categories: Dictionary of Category objects keyed by ID
        """
        self.transactions = transactions
        self.accounts = accounts
        self.categories = categories

        # Identify credit card accounts
        self.cc_account_ids = set(
            acc.get('id') for acc in accounts
            if acc.get('type', {}).get('name') == 'credit'
        )

        # Identify cash accounts (checking, savings, cash)
        self.cash_accounts = [
            acc for acc in accounts
            if acc.get('type', {}).get('name') in ('cash', 'checking', 'savings', 'depository')
        ]

        # Find the credit card payment category
        self.cc_payment_category_id = None
        for cat_id, cat in categories.items():
            if cat.is_cc_payment:
                self.cc_payment_category_id = cat_id
                break

    def get_cash_available(self) -> float:
        """Get total current balance from all cash accounts."""
        return sum(
            acc.get('currentBalance', 0) or 0
            for acc in self.cash_accounts
        )

    def _prepare_dataframe(self) -> pd.DataFrame:
        """Convert transactions to DataFrame with necessary computed columns."""
        if not self.transactions:
            return pd.DataFrame()

        df = pd.DataFrame(self.transactions)

        # Extract nested fields
        df['account_id'] = df['account'].apply(
            lambda x: x.get('id') if isinstance(x, dict) else None
        )
        df['category_id'] = df['category'].apply(
            lambda x: x.get('id') if isinstance(x, dict) else None
        )
        df['category_name'] = df['category'].apply(
            lambda x: x.get('name', 'Uncategorized') if isinstance(x, dict) else 'Uncategorized'
        )

        # Parse dates
        df['date'] = pd.to_datetime(df['date'])

        # Flag CC transactions
        df['is_cc_account'] = df['account_id'].isin(self.cc_account_ids)

        # Flag CC payment transactions
        df['is_cc_payment'] = df['category_id'] == self.cc_payment_category_id

        return df

    def _is_excluded_category(self, category_name: str) -> bool:
        """Check if a category should be excluded from calculations."""
        return category_name in self.EXCLUDED_CATEGORIES

    def calculate_top_level_metrics(self,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Calculate the top-level budget metrics.

        Returns dict with:
        - total_income: All positive amounts (excluding Dividends & Capital Gains)
        - total_expenses: All negative amounts (expenses, absolute value)
        - cc_expenses: Expenses on credit card accounts
        - cash_expenses: Expenses on non-CC accounts
        - cc_payments: Payments made to credit cards
        - true_cash_remaining: Income - Cash Expenses - CC Payments
        - total_new_cc_spending: Same as cc_expenses
        """
        df = self._prepare_dataframe()

        if df.empty:
            return {
                'total_income': 0,
                'total_expenses': 0,
                'cc_expenses': 0,
                'cash_expenses': 0,
                'cc_payments': 0,
                'true_cash_remaining': 0,
                'total_new_cc_spending': 0
            }

        # Filter by date range if provided
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]

        # Income: positive amounts (excluding CC payments and excluded categories)
        income_df = df[(df['amount'] > 0) & (~df['is_cc_payment'])]
        income_df = income_df[~income_df['category_name'].apply(self._is_excluded_category)]
        total_income = income_df['amount'].sum()

        # All expenses: negative amounts (excluding CC payment category)
        expense_df = df[(df['amount'] < 0) & (~df['is_cc_payment'])]
        total_expenses = abs(expense_df['amount'].sum())

        # CC expenses: negative amounts on CC accounts
        cc_expense_df = expense_df[expense_df['is_cc_account']]
        cc_expenses = abs(cc_expense_df['amount'].sum())

        # Cash expenses: negative amounts NOT on CC accounts
        cash_expenses = total_expenses - cc_expenses

        # CC Payments: transactions in the CC payment category
        # These show as negative from checking (paying) and positive on CC (receiving)
        # We want the outflow from non-CC accounts
        cc_payment_df = df[df['is_cc_payment'] & ~df['is_cc_account'] & (df['amount'] < 0)]
        cc_payments = abs(cc_payment_df['amount'].sum())

        # True Cash Remaining = Income - Cash Expenses - CC Payments
        true_cash_remaining = total_income - cash_expenses - cc_payments

        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'cc_expenses': cc_expenses,
            'cash_expenses': cash_expenses,
            'cc_payments': cc_payments,
            'true_cash_remaining': true_cash_remaining,
            'total_new_cc_spending': cc_expenses
        }

    def calculate_category_breakdown(self,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Calculate spending breakdown by category.

        Returns DataFrame with columns:
        - category_id, category_name, group_name, category_type
        - actual_amount: Total spending in category
        - cc_amount: Amount spent on credit cards
        - cash_amount: Amount spent with cash/debit
        """
        df = self._prepare_dataframe()

        if df.empty:
            return pd.DataFrame(columns=[
                'category_id', 'category_name', 'group_name', 'category_type',
                'actual_amount', 'cc_amount', 'cash_amount'
            ])

        # Filter by date range
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]

        # Exclude CC payment transfers from breakdown
        df = df[~df['is_cc_payment']]

        results = []

        for cat_id, group in df.groupby('category_id'):
            if cat_id is None:
                continue

            cat = self.categories.get(cat_id)
            if not cat:
                continue

            # Calculate amounts
            total = group['amount'].sum()
            cc_total = group[group['is_cc_account']]['amount'].sum()

            # For expenses (negative), we want absolute values
            if cat.is_expense:
                actual = abs(total)
                cc_amt = abs(cc_total)
            else:
                actual = total
                cc_amt = cc_total

            cash_amt = actual - cc_amt if cat.is_expense else 0

            results.append({
                'category_id': cat_id,
                'category_name': cat.name,
                'group_name': cat.group_name,
                'category_type': cat.category_type.value,
                'actual_amount': actual,
                'cc_amount': cc_amt if cat.is_expense else 0,
                'cash_amount': cash_amt
            })

        result_df = pd.DataFrame(results)

        # Sort by category type (income first) then by actual amount
        if not result_df.empty:
            type_order = {'income': 0, 'expense': 1, 'transfer': 2}
            result_df['type_order'] = result_df['category_type'].map(type_order)
            result_df = result_df.sort_values(
                ['type_order', 'actual_amount'],
                ascending=[True, False]
            )
            result_df = result_df.drop('type_order', axis=1)

        return result_df

    def get_income_breakdown(self,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get just the income categories breakdown (excluding Dividends & Capital Gains)."""
        breakdown = self.calculate_category_breakdown(start_date, end_date)
        income = breakdown[breakdown['category_type'] == 'income']
        # Exclude categories that shouldn't be shown
        return income[~income['category_name'].isin(self.EXCLUDED_CATEGORIES)]

    def get_expense_breakdown(self,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              include_cc_payments: bool = True) -> pd.DataFrame:
        """Get expense categories breakdown, optionally including CC payments."""
        breakdown = self.calculate_category_breakdown(start_date, end_date)
        expenses = breakdown[breakdown['category_type'] == 'expense']

        if include_cc_payments:
            # Calculate CC payments to add as a row
            df = self._prepare_dataframe()
            if not df.empty:
                if start_date:
                    df = df[df['date'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['date'] <= pd.to_datetime(end_date)]

                # CC Payments: outflows from non-CC accounts in CC payment category
                cc_payment_df = df[df['is_cc_payment'] & ~df['is_cc_account'] & (df['amount'] < 0)]
                cc_payments = abs(cc_payment_df['amount'].sum())

                if cc_payments > 0:
                    cc_payment_row = pd.DataFrame([{
                        'category_id': 'cc_payments',
                        'category_name': 'Credit Card Payments',
                        'group_name': 'Transfers',
                        'category_type': 'expense',
                        'actual_amount': cc_payments,
                        'cc_amount': 0,
                        'cash_amount': cc_payments
                    }])
                    expenses = pd.concat([expenses, cc_payment_row], ignore_index=True)

        return expenses
