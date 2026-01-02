"""
PDF report generator for cash-based budget view.

Generates a PDF report with budget tables and cash balance charts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates as mdates


class BudgetPDFReport:
    """Generate PDF reports for budget analysis."""

    def __init__(self):
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8-whitegrid')

    def _format_currency(self, amount: float) -> str:
        """Format a number as currency."""
        if amount < 0:
            return f"-${abs(amount):,.2f}"
        return f"${amount:,.2f}"

    def _create_summary_page(self, fig, metrics: Dict[str, float], month: str):
        """Create a summary metrics page."""
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title
        fig.suptitle(f'Cash Budget Summary - {month}', fontsize=16, fontweight='bold', y=0.95)

        # Summary text
        true_cash = metrics['true_cash_remaining']
        cash_color = 'green' if true_cash >= 0 else 'red'

        summary_text = f"""
TRUE CASH REMAINING: {self._format_currency(true_cash)}
(Income - Cash Expenses - CC Payments)

New CC Spending: {self._format_currency(metrics['total_new_cc_spending'])}

────────────────────────────────────

Income:              {self._format_currency(metrics['total_income'])}
Total Expenses:      {self._format_currency(metrics['total_expenses'])}
  CC Expenses:       {self._format_currency(metrics['cc_expenses'])}
  Cash Expenses:     {self._format_currency(metrics['cash_expenses'])}
CC Payments:         {self._format_currency(metrics['cc_payments'])}
"""

        ax.text(0.5, 0.6, summary_text, transform=ax.transAxes,
                fontsize=12, verticalalignment='center', horizontalalignment='center',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))

    def _create_table_page(self, fig, df: pd.DataFrame, title: str, columns: List[str],
                           show_total: bool = True):
        """Create a page with a table."""
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        if df.empty:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=12)
            return

        # Prepare table data
        table_data = []
        for _, row in df.iterrows():
            row_data = []
            for col in columns:
                val = row.get(col, '')
                if isinstance(val, (int, float)) and col != 'category_name':
                    row_data.append(self._format_currency(val))
                else:
                    row_data.append(str(val))
            table_data.append(row_data)

        # Add total row if requested
        if show_total and not df.empty:
            total_row = []
            for col in columns:
                if col == 'category_name':
                    total_row.append('TOTAL')
                elif col in df.columns and df[col].dtype in ['float64', 'int64', 'float', 'int']:
                    total_row.append(self._format_currency(df[col].sum()))
                else:
                    total_row.append('')
            table_data.append(total_row)

        # Create table
        col_labels = [c.replace('_', ' ').title() for c in columns]
        table = ax.table(cellText=table_data,
                        colLabels=col_labels,
                        loc='center',
                        cellLoc='right')

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)

        # Style header row
        for i in range(len(columns)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(color='white', fontweight='bold')

        # Style total row (last row)
        if show_total and table_data:
            last_row = len(table_data)
            for i in range(len(columns)):
                table[(last_row, i)].set_text_props(fontweight='bold')

    def _create_transfers_page(self, fig, df: pd.DataFrame, title: str):
        """Create a page showing transfer transactions."""
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        if df.empty:
            ax.text(0.5, 0.5, 'No transfer transactions', ha='center', va='center', fontsize=12)
            return

        # Prepare table data
        col_labels = ['Date', 'Description', 'Amount', 'Account', 'Category']
        table_data = []

        for _, row in df.iterrows():
            table_data.append([
                str(row.get('date', '')),
                str(row.get('description', ''))[:35],  # Truncate long descriptions
                self._format_currency(row.get('amount', 0)),
                str(row.get('account_name', ''))[:15],  # Truncate long account names
                str(row.get('category_name', ''))[:15]  # Show category
            ])

        # Add total row
        total_amount = df['amount'].sum() if 'amount' in df.columns else 0
        table_data.append(['', 'TOTAL', self._format_currency(total_amount), '', ''])

        # Create table
        table = ax.table(cellText=table_data,
                        colLabels=col_labels,
                        loc='center',
                        cellLoc='right')

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.2, 1.3)

        # Style header row
        for i in range(len(col_labels)):
            table[(0, i)].set_facecolor('#C44472')  # Different color for this section
            table[(0, i)].set_text_props(color='white', fontweight='bold')

        # Style total row
        last_row = len(table_data)
        for i in range(len(col_labels)):
            table[(last_row, i)].set_text_props(fontweight='bold')

        # Left-align description column
        for row_idx in range(len(table_data) + 1):
            table[(row_idx, 1)].set_text_props(ha='left')

    def _create_balance_chart(self, fig, account_histories: Dict[str, List[Dict]],
                              start_date: datetime, end_date: datetime, month: str):
        """Create a line chart of cash balances over time."""
        ax = fig.add_subplot(111)

        # Parse and plot each account
        all_dates = set()
        account_data = {}

        for account_name, history in account_histories.items():
            # Handle both dict with 'accountSnapshotHistory' key and direct list
            if isinstance(history, dict):
                snapshots = history.get('accountSnapshotHistory', [])
            elif isinstance(history, list):
                snapshots = history
            else:
                continue

            if not snapshots:
                continue

            dates = []
            balances = []

            for snap in snapshots:
                date_str = snap.get('date')
                if date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    # Filter to the requested month
                    if start_date <= date <= end_date:
                        dates.append(date)
                        balances.append(snap.get('signedBalance', 0))
                        all_dates.add(date)

            if dates:
                account_data[account_name] = {'dates': dates, 'balances': balances}
                ax.plot(dates, balances, marker='.', markersize=3,
                       label=account_name, alpha=0.7, linewidth=1.5)

        # Calculate and plot total
        if account_data:
            # Get all unique dates sorted
            all_dates_sorted = sorted(all_dates)

            # Calculate total for each date
            totals = []
            for date in all_dates_sorted:
                total = 0
                for acc_name, data in account_data.items():
                    # Find balance for this date
                    for i, d in enumerate(data['dates']):
                        if d == date:
                            total += data['balances'][i]
                            break
                totals.append(total)

            ax.plot(all_dates_sorted, totals, marker='o', markersize=4,
                   label='TOTAL', linewidth=2.5, color='black')

        ax.set_title(f'Cash Account Balances - {month}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Balance ($)')

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45, ha='right')

        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        # Legend
        ax.legend(loc='upper left', fontsize=8)

        # Grid
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

    def generate_report(self,
                       filepath: str,
                       metrics: Dict[str, float],
                       income_df: pd.DataFrame,
                       expense_df: pd.DataFrame,
                       cash_balances: Dict[str, Any],
                       account_histories: Dict[str, List[Dict]],
                       start_date: datetime,
                       end_date: datetime,
                       month: str = "",
                       transfers_df: Optional[pd.DataFrame] = None):
        """
        Generate a complete PDF report.

        Args:
            filepath: Output PDF path
            metrics: Top-level metrics dictionary
            income_df: Income breakdown DataFrame
            expense_df: Expense breakdown DataFrame
            cash_balances: Start/end cash balances
            account_histories: Dict mapping account names to their history data
            start_date: Start date of the report period
            end_date: End date of the report period
            month: Month string for title
        """
        with PdfPages(filepath) as pdf:
            # Page 1: Summary metrics
            fig = plt.figure(figsize=(8.5, 11))
            self._create_summary_page(fig, metrics, month)

            # Add cash balance info
            ax = fig.axes[0]
            if cash_balances.get('start_balance') is not None:
                balance_text = f"""
Cash Account Balances:
  Start ({cash_balances.get('start_date', '')}): {self._format_currency(cash_balances['start_balance'])}
  End ({cash_balances.get('end_date', '')}): {self._format_currency(cash_balances['end_balance'])}
  Change: {self._format_currency(cash_balances['end_balance'] - cash_balances['start_balance'])}
"""
                ax.text(0.5, 0.25, balance_text, transform=ax.transAxes,
                       fontsize=11, verticalalignment='center', horizontalalignment='center',
                       fontfamily='monospace')

            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 2: Income table
            fig = plt.figure(figsize=(8.5, 11))
            income_cols = ['category_name', 'actual_amount']
            self._create_table_page(fig, income_df, 'Income', income_cols)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 3: Expenses table
            fig = plt.figure(figsize=(8.5, 11))
            expense_cols = ['category_name', 'actual_amount', 'cc_amount', 'cash_amount']
            self._create_table_page(fig, expense_df, 'Expenses', expense_cols)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 4: Transfer transactions (excluded from expense metrics)
            if transfers_df is not None and not transfers_df.empty:
                fig = plt.figure(figsize=(8.5, 11))
                self._create_transfers_page(
                    fig, transfers_df,
                    'Transfers (Excluded from Expense Metrics)'
                )
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

            # Page 5: Cash balance chart
            if account_histories:
                fig = plt.figure(figsize=(11, 8.5))  # Landscape for chart
                self._create_balance_chart(fig, account_histories, start_date, end_date, month)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
