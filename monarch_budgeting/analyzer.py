"""
Credit card debt and budgeting analysis.

This module provides analysis functionality for credit card debt payoff
and custom budgeting insights.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


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

        # Filter for credit card transactions
        cc_account_ids = [acc['id'] for acc in self.credit_card_accounts]
        cc_transactions = df[df.get('account', {}).get('id').isin(cc_account_ids)]

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

            # Filter transactions for this account
            account_payments = payments[
                payments.get('account', {}).get('id') == account_id
            ]
            account_purchases = purchases[
                purchases.get('account', {}).get('id') == account_id
            ]

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
