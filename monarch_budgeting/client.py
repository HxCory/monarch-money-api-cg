"""
Monarch Money API client wrapper.

This module provides a convenient interface to the Monarch Money API
using the monarchmoney library.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from monarchmoney import MonarchMoney


class MonarchClient:
    """Wrapper for Monarch Money API client."""

    def __init__(self):
        """Initialize the Monarch Money client."""
        self.mm = MonarchMoney()
        self._authenticated = False

    async def login(self, email: Optional[str] = None, password: Optional[str] = None,
                   use_saved_session: bool = True) -> bool:
        """
        Login to Monarch Money.

        Args:
            email: User email (optional if using saved session)
            password: User password (optional if using saved session)
            use_saved_session: Whether to try using a saved session first

        Returns:
            True if login successful
        """
        if use_saved_session:
            try:
                await self.mm.load_session()
                self._authenticated = True
                return True
            except Exception:
                pass

        if email and password:
            await self.mm.login(email, password)
            self._authenticated = True
            return True

        raise ValueError("Must provide email and password or have a saved session")

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts."""
        if not self._authenticated:
            raise RuntimeError("Must login first")
        return await self.mm.get_accounts()

    async def get_credit_card_accounts(self) -> List[Dict[str, Any]]:
        """Get only credit card accounts."""
        accounts = await self.get_accounts()
        return [acc for acc in accounts if acc.get('type', {}).get('name') == 'credit']

    async def get_transactions(self, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              account_ids: Optional[List[str]] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get transactions with optional filters.

        Args:
            start_date: Start date for transactions
            end_date: End date for transactions
            account_ids: List of account IDs to filter by
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dictionaries
        """
        if not self._authenticated:
            raise RuntimeError("Must login first")

        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        return await self.mm.get_transactions(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            account_ids=account_ids,
            limit=limit
        )

    async def get_budgets(self, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get budget data.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Budget data dictionary
        """
        if not self._authenticated:
            raise RuntimeError("Must login first")

        return await self.mm.get_budgets(start_date=start_date, end_date=end_date)

    async def get_transaction_categories(self) -> List[Dict[str, Any]]:
        """Get all transaction categories."""
        if not self._authenticated:
            raise RuntimeError("Must login first")
        return await self.mm.get_transaction_categories()
