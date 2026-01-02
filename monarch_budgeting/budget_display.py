"""
Rich terminal display for cash-based budget view.

This module provides beautiful terminal output using the `rich` library
to display budget metrics and category breakdowns.
"""

from typing import Dict, Any, Optional
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


class BudgetDisplay:
    """Display budget information using rich terminal formatting."""

    def __init__(self):
        self.console = Console()

    def _format_currency(self, amount: float, show_sign: bool = False) -> str:
        """Format a number as currency."""
        if show_sign:
            return f"${amount:+,.2f}"
        return f"${amount:,.2f}"

    def _color_amount(self, amount: float, invert: bool = False) -> str:
        """Return color based on amount (green=positive, red=negative)."""
        if invert:
            return "red" if amount > 0 else "green"
        return "green" if amount >= 0 else "red"

    def display_top_metrics(self, metrics: Dict[str, float], month: str = ""):
        """
        Display the top-level budget metrics in a panel.

        Args:
            metrics: Dictionary with keys: total_income, total_expenses,
                    cc_expenses, cash_expenses, cc_payments, true_cash_remaining,
                    total_new_cc_spending
            month: Optional month string for title
        """
        title = f"Cash Budget Summary - {month}" if month else "Cash Budget Summary"

        # Build the metrics text
        true_cash = metrics['true_cash_remaining']
        cash_color = self._color_amount(true_cash)

        content = Text()

        # Main metric - TRUE CASH REMAINING
        content.append("TRUE CASH REMAINING: ", style="bold")
        content.append(f"{self._format_currency(true_cash)}\n", style=f"bold {cash_color}")
        content.append("(Income - Cash Expenses - CC Payments)\n\n", style="dim")

        # Secondary metrics
        content.append("New CC Spending:     ", style="bold yellow")
        content.append(f"{self._format_currency(metrics['total_new_cc_spending'])}\n\n",
                      style="yellow")

        # Breakdown
        content.append("Income:              ", style="green")
        content.append(f"{self._format_currency(metrics['total_income'])}\n")

        content.append("Total Expenses:      ", style="red")
        content.append(f"{self._format_currency(metrics['total_expenses'])}\n")

        content.append("  CC Expenses:       ", style="dim")
        content.append(f"{self._format_currency(metrics['cc_expenses'])}\n", style="yellow")

        content.append("  Cash Expenses:     ", style="dim")
        content.append(f"{self._format_currency(metrics['cash_expenses'])}\n")

        content.append("CC Payments:         ", style="cyan")
        content.append(f"{self._format_currency(metrics['cc_payments'])}\n")

        panel = Panel(
            content,
            title=f"[bold blue]{title}[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def display_income_table(self, income_df: pd.DataFrame):
        """
        Display income categories table.

        Args:
            income_df: DataFrame with columns: category_name, actual_amount
        """
        if income_df.empty:
            self.console.print("[dim]No income data[/dim]")
            return

        table = Table(
            title="Income",
            box=box.ROUNDED,
            title_style="bold green",
            header_style="bold"
        )

        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Actual", justify="right", style="green")

        total = 0
        for _, row in income_df.iterrows():
            amount = row['actual_amount']
            total += amount
            table.add_row(
                row['category_name'],
                self._format_currency(amount)
            )

        # Add total row
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold green]{self._format_currency(total)}[/bold green]",
            style="bold"
        )

        self.console.print(table)
        self.console.print()

    def display_expense_table(self, expense_df: pd.DataFrame):
        """
        Display expenses table with Credit Card column.

        Args:
            expense_df: DataFrame with columns: category_name, actual_amount,
                       cc_amount, cash_amount
        """
        if expense_df.empty:
            self.console.print("[dim]No expense data[/dim]")
            return

        table = Table(
            title="Expenses",
            box=box.ROUNDED,
            title_style="bold red",
            header_style="bold"
        )

        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Actual", justify="right")
        table.add_column("Credit Card", justify="right", style="yellow")
        table.add_column("Cash", justify="right")

        total_actual = 0
        total_cc = 0
        total_cash = 0

        for _, row in expense_df.iterrows():
            actual = row['actual_amount']
            cc = row['cc_amount']
            cash = row['cash_amount']

            total_actual += actual
            total_cc += cc
            total_cash += cash

            # Highlight rows with significant CC spending
            cc_str = self._format_currency(cc) if cc > 0 else "-"
            cash_str = self._format_currency(cash) if cash > 0 else "-"

            table.add_row(
                row['category_name'],
                self._format_currency(actual),
                cc_str,
                cash_str
            )

        # Add total row
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{self._format_currency(total_actual)}[/bold]",
            f"[bold yellow]{self._format_currency(total_cc)}[/bold yellow]",
            f"[bold]{self._format_currency(total_cash)}[/bold]",
            style="bold"
        )

        self.console.print(table)
        self.console.print()

    def display_cash_balances(self, cash_balances: Dict[str, Any]):
        """
        Display cash account balance at start and end of month.

        Args:
            cash_balances: Dict with start_balance, end_balance, start_date, end_date
        """
        start_bal = cash_balances.get('start_balance')
        end_bal = cash_balances.get('end_balance')

        if start_bal is None and end_bal is None:
            return

        table = Table(
            title="Cash Account Balances",
            box=box.ROUNDED,
            title_style="bold cyan",
            header_style="bold"
        )

        table.add_column("Date", style="cyan")
        table.add_column("Balance", justify="right")

        if start_bal is not None:
            start_date = cash_balances.get('start_date', '')
            table.add_row(f"Start ({start_date})", self._format_currency(start_bal))

        if end_bal is not None:
            end_date = cash_balances.get('end_date', '')
            table.add_row(f"End ({end_date})", self._format_currency(end_bal))

        # Show change if both values exist
        if start_bal is not None and end_bal is not None:
            change = end_bal - start_bal
            change_color = self._color_amount(change)
            table.add_row(
                "[bold]Change[/bold]",
                f"[bold {change_color}]{self._format_currency(change, show_sign=True)}[/bold {change_color}]"
            )

        self.console.print(table)
        self.console.print()

    def display_full_budget(self,
                           metrics: Dict[str, float],
                           income_df: pd.DataFrame,
                           expense_df: pd.DataFrame,
                           cash_balances: Optional[Dict[str, Any]] = None,
                           month: str = ""):
        """
        Display the complete budget view.

        Args:
            metrics: Top-level metrics dictionary
            income_df: Income breakdown DataFrame
            expense_df: Expense breakdown DataFrame
            cash_balances: Optional dict with start/end cash balances
            month: Optional month string for title
        """
        self.console.print()
        self.console.rule("[bold blue]Cash-Based Budget View[/bold blue]")
        self.console.print()

        self.display_top_metrics(metrics, month)
        self.display_income_table(income_df)
        self.display_expense_table(expense_df)

        if cash_balances:
            self.display_cash_balances(cash_balances)

        # Footer
        self.console.print()
        self.console.rule(style="dim")
        self.console.print(
            "[dim]True Cash Remaining = Income - Cash Expenses - CC Payments[/dim]",
            justify="center"
        )
        self.console.print()
