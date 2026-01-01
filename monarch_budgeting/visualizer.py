"""
Visualization module for budgeting data.

This module provides plotting functions for income, expenses, and cash flow analysis.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns


def create_output_dir() -> Path:
    """Create timestamped output directory for this run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / f"analysis_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


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

    def plot_monthly_cc_activity(
        self,
        monthly_data: pd.DataFrame,
        title: str = "Monthly Credit Card Activity",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot monthly credit card payments and purchases over time as line chart.

        Args:
            monthly_data: DataFrame with columns: month, total_payments, total_purchases
            title: Plot title
            save_path: Optional path to save the plot
        """
        if monthly_data.empty:
            print("No monthly data to plot")
            return

        fig, ax = plt.subplots(figsize=self.figsize)

        # Plot lines
        ax.plot(monthly_data['month'], monthly_data['total_payments'],
                'g-', linewidth=2.5, label='Payments', marker='o', markersize=8)
        ax.plot(monthly_data['month'], monthly_data['total_purchases'],
                'r-', linewidth=2.5, label='New Purchases', marker='s', markersize=8)

        # Add zero line
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)

        # Fill between to show net
        ax.fill_between(monthly_data['month'],
                       monthly_data['total_payments'],
                       monthly_data['total_purchases'],
                       alpha=0.2,
                       color='green',
                       where=monthly_data['total_payments'] >= monthly_data['total_purchases'])
        ax.fill_between(monthly_data['month'],
                       monthly_data['total_payments'],
                       monthly_data['total_purchases'],
                       alpha=0.2,
                       color='red',
                       where=monthly_data['total_payments'] < monthly_data['total_purchases'])

        # Formatting
        ax.set_xlabel('Month', fontsize=13, fontweight='bold')
        ax.set_ylabel('Amount ($)', fontsize=13, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        fig.autofmt_xdate(rotation=45)

        # Add value labels on last points
        for col, color in [('total_payments', 'green'), ('total_purchases', 'red')]:
            last_val = monthly_data[col].iloc[-1]
            last_date = monthly_data['month'].iloc[-1]
            ax.annotate(f'${last_val:,.0f}',
                       xy=(last_date, last_val),
                       xytext=(10, 0), textcoords='offset points',
                       fontsize=10, color=color, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_monthly_by_card(
        self,
        monthly_by_card: pd.DataFrame,
        value_col: str = 'total_purchases',
        title: str = "Monthly Purchases by Card",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot monthly values by credit card as multi-line chart.

        Args:
            monthly_by_card: DataFrame with columns: month, account_name, and value_col
            value_col: Column name to plot
            title: Plot title
            save_path: Optional path to save the plot
        """
        if monthly_by_card.empty:
            print("No data to plot")
            return

        fig, ax = plt.subplots(figsize=self.figsize)

        # Get unique accounts and create color palette
        accounts = monthly_by_card['account_name'].unique()
        colors = sns.color_palette("husl", len(accounts))

        # Plot each account as a line
        for account, color in zip(accounts, colors):
            account_data = monthly_by_card[monthly_by_card['account_name'] == account]
            # Shorten account name for legend
            short_name = account.split('(')[0].strip()[:20]
            ax.plot(account_data['month'], account_data[value_col],
                   linewidth=2, label=short_name, marker='o', markersize=6, color=color)

        # Formatting
        ax.set_xlabel('Month', fontsize=13, fontweight='bold')
        ax.set_ylabel('Amount ($)', fontsize=13, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        fig.autofmt_xdate(rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_cumulative_net_debt(
        self,
        monthly_data: pd.DataFrame,
        title: str = "Cumulative Net Debt Change Over Time",
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot cumulative net debt change over time.

        Args:
            monthly_data: DataFrame with columns: month, net_change
            title: Plot title
            save_path: Optional path to save the plot
        """
        if monthly_data.empty:
            print("No data to plot")
            return

        fig, ax = plt.subplots(figsize=self.figsize)

        # Calculate cumulative sum
        df = monthly_data.copy()
        df['cumulative'] = df['net_change'].cumsum()

        # Plot cumulative line
        ax.plot(df['month'], df['cumulative'],
               'b-', linewidth=3, marker='o', markersize=8, label='Cumulative Net Change')

        # Fill area under curve
        ax.fill_between(df['month'], df['cumulative'], 0,
                       where=df['cumulative'] >= 0, alpha=0.3, color='green')
        ax.fill_between(df['month'], df['cumulative'], 0,
                       where=df['cumulative'] < 0, alpha=0.3, color='red')

        # Add monthly change as bars
        ax2 = ax.twinx()
        colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in df['net_change']]
        ax2.bar(df['month'], df['net_change'], width=20, alpha=0.4, color=colors, label='Monthly Change')
        ax2.set_ylabel('Monthly Change ($)', fontsize=11, color='gray')
        ax2.tick_params(axis='y', labelcolor='gray')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:+,.0f}'))

        # Zero line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

        # Formatting
        ax.set_xlabel('Month', fontsize=13, fontweight='bold')
        ax.set_ylabel('Cumulative Net Change ($)', fontsize=13, fontweight='bold')
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:+,.0f}'))
        fig.autofmt_xdate(rotation=45)

        # Add final value annotation
        final_val = df['cumulative'].iloc[-1]
        final_date = df['month'].iloc[-1]
        color = 'green' if final_val >= 0 else 'red'
        ax.annotate(f'${final_val:+,.0f}',
                   xy=(final_date, final_val),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=12, color=color, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='white', edgecolor=color))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        else:
            plt.show()

        plt.close()
