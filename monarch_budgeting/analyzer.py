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
