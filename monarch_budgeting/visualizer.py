"""
Visualization module for budgeting data.

This module provides plotting functions for income, expenses, and cash flow analysis.
"""

from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


class BudgetVisualizer:
    """Create visualizations for budget and cash flow data."""

    def __init__(self, figsize: tuple = (14, 7)):
        """
        Initialize the visualizer.

        Args:
            figsize: Figure size as (width, height) in inches
        """
        self.figsize = figsize

    def plot_cash_flow(
        self,
        cash_flow_df: pd.DataFrame,
        title: str = "Cash Flow Analysis Over Time",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot income, expenses, CC expenses, and cash balance over time.

        Args:
            cash_flow_df: DataFrame with columns: date, income, total_expenses,
                         cc_expenses, cash_balance
            title: Plot title
            save_path: Optional path to save the plot (e.g., 'output.png')

        The plot shows:
        1. Income (green line)
        2. Total Expenses (red line)
        3. Credit Card Expenses (orange line)
        4. Cash Balance = Income - (Total Expenses - CC Expenses) (blue line)
        """
        if cash_flow_df.empty:
            print("No data to plot")
            return

        # Create figure and axis
        fig, ax = plt.subplots(figsize=self.figsize)

        # Plot all four lines
        ax.plot(cash_flow_df['date'], cash_flow_df['income'],
                'g-', linewidth=2.5, label='Income', marker='o', markersize=6)
        ax.plot(cash_flow_df['date'], cash_flow_df['total_expenses'],
                'r-', linewidth=2.5, label='Total Expenses', marker='s', markersize=6)
        ax.plot(cash_flow_df['date'], cash_flow_df['cc_expenses'],
                'orange', linewidth=2.5, label='CC Expenses', marker='^', markersize=6)
        ax.plot(cash_flow_df['date'], cash_flow_df['cash_balance'],
                'b-', linewidth=2.5, label='Cash Balance', marker='D', markersize=6)

        # Add zero line for reference
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=1)

        # Formatting
        ax.set_xlabel('Date', fontsize=13, fontweight='bold')
        ax.set_ylabel('Amount ($)', fontsize=13, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate(rotation=45)

        # Format y-axis with currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        # Add value labels on the last point of each line
        for col, label, color in [
            ('income', 'Income', 'green'),
            ('total_expenses', 'Total Exp', 'red'),
            ('cc_expenses', 'CC Exp', 'orange'),
            ('cash_balance', 'Cash Bal', 'blue')
        ]:
            if col in cash_flow_df.columns:
                last_val = cash_flow_df[col].iloc[-1]
                last_date = cash_flow_df['date'].iloc[-1]
                ax.annotate(f'${last_val:,.0f}',
                           xy=(last_date, last_val),
                           xytext=(10, 0),
                           textcoords='offset points',
                           fontsize=10,
                           color=color,
                           fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor='white',
                                   edgecolor=color,
                                   alpha=0.8))

        plt.tight_layout()

        # Save or show
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        else:
            plt.show()

        plt.close()

    def create_summary_table(self, cash_flow_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a summary statistics table for the cash flow data.

        Args:
            cash_flow_df: DataFrame with cash flow data

        Returns:
            DataFrame with summary statistics
        """
        if cash_flow_df.empty:
            return pd.DataFrame()

        # Calculate derived metrics
        non_cc_expenses = cash_flow_df['total_expenses'] - cash_flow_df['cc_expenses']
        net_income = cash_flow_df['income'] - cash_flow_df['total_expenses']

        # Create summary
        summary = pd.DataFrame({
            'Metric': [
                'Total Income',
                'Total Expenses',
                'CC Expenses',
                'Non-CC Expenses',
                'Average Monthly Income',
                'Average Monthly Expenses',
                'Average Monthly CC Expenses',
                'Average Cash Balance',
                'Net Income (Total)',
                'CC % of Total Expenses'
            ],
            'Amount': [
                cash_flow_df['income'].sum(),
                cash_flow_df['total_expenses'].sum(),
                cash_flow_df['cc_expenses'].sum(),
                non_cc_expenses.sum(),
                cash_flow_df['income'].mean(),
                cash_flow_df['total_expenses'].mean(),
                cash_flow_df['cc_expenses'].mean(),
                cash_flow_df['cash_balance'].mean(),
                net_income.sum(),
                (cash_flow_df['cc_expenses'].sum() / cash_flow_df['total_expenses'].sum() * 100)
                if cash_flow_df['total_expenses'].sum() > 0 else 0
            ]
        })

        # Format amounts (except percentage)
        summary['Amount'] = summary.apply(
            lambda row: f"{row['Amount']:.1f}%" if row['Metric'] == 'CC % of Total Expenses'
                       else f"${row['Amount']:,.2f}",
            axis=1
        )

        return summary
