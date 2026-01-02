"""
Monarch Money API client wrapper.

This module provides a convenient interface to the Monarch Money API
using the monarchmoney library.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from monarchmoney import MonarchMoney
from monarchmoney.monarchmoney import RequireMFAException


class MonarchClient:
    """Wrapper for Monarch Money API client."""

    def __init__(self):
        """Initialize the Monarch Money client."""
        self.mm = MonarchMoney()
        self._authenticated = False
        self._email = None
        self._password = None

    async def _do_login(self, email: str, password: str,
                        use_saved_session: bool, mfa_secret_key: Optional[str],
                        prompt_for_mfa: bool) -> None:
        """Internal login helper that handles MFA."""
        try:
            await self.mm.login(
                email=email,
                password=password,
                use_saved_session=use_saved_session,
                mfa_secret_key=mfa_secret_key
            )
        except RequireMFAException:
            if not prompt_for_mfa:
                raise
            if not email or not password:
                raise ValueError("Email and password required for MFA. Set MONARCH_EMAIL and MONARCH_PASSWORD env vars.")

            # Prompt user for MFA code
            mfa_code = input("Enter MFA code: ").strip()
            await self.mm.multi_factor_authenticate(email, password, mfa_code)

    async def login(self, email: Optional[str] = None, password: Optional[str] = None,
                   use_saved_session: bool = True, mfa_secret_key: Optional[str] = None,
                   prompt_for_mfa: bool = True) -> bool:
        """
        Login to Monarch Money.

        Args:
            email: User email (uses MONARCH_EMAIL env var if not provided)
            password: User password (uses MONARCH_PASSWORD env var if not provided)
            use_saved_session: Whether to try using a saved session first
            mfa_secret_key: TOTP secret for MFA (optional)
            prompt_for_mfa: If True, prompt user for MFA code when required

        Returns:
            True if login successful
        """
        # Get credentials from env vars if not provided
        self._email = email or os.environ.get('MONARCH_EMAIL')
        self._password = password or os.environ.get('MONARCH_PASSWORD')

        if use_saved_session:
            # First, try to use saved session WITHOUT passing credentials
            # This prevents the library from attempting a fresh login
            try:
                await self.mm.login(use_saved_session=True)
                self._authenticated = True
                return True
            except Exception:
                # Session doesn't exist or is invalid, fall through to credential login
                pass

        # No valid session, need to login with credentials
        await self._do_login(self._email, self._password,
                            use_saved_session=False, mfa_secret_key=mfa_secret_key,
                            prompt_for_mfa=prompt_for_mfa)
        self._authenticated = True
        return True

    async def _ensure_authenticated(self) -> None:
        """Re-authenticate if session has expired (called on 401 errors)."""
        if self._email and self._password:
            print("Session expired, re-authenticating...")
            # Create new client to clear stale session
            self.mm = MonarchMoney()
            await self._do_login(self._email, self._password,
                               use_saved_session=False, mfa_secret_key=None, prompt_for_mfa=True)
            self._authenticated = True

    async def _api_call_with_retry(self, api_func, *args, **kwargs):
        """Make an API call, retrying with re-auth on 401."""
        from gql.transport.exceptions import TransportServerError
        try:
            return await api_func(*args, **kwargs)
        except TransportServerError as e:
            if '401' in str(e):
                await self._ensure_authenticated()
                return await api_func(*args, **kwargs)
            raise

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts."""
        if not self._authenticated:
            raise RuntimeError("Must login first")
        result = await self._api_call_with_retry(self.mm.get_accounts)
        # API returns {'accounts': [...], 'householdPreferences': ...}
        return result.get('accounts', [])

    async def get_credit_card_accounts(self) -> List[Dict[str, Any]]:
        """Get only credit card accounts."""
        accounts = await self.get_accounts()
        # type.name is 'credit' for credit cards
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

        result = await self._api_call_with_retry(
            self.mm.get_transactions,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            account_ids=account_ids,
            limit=limit
        )
        # API returns {'allTransactions': {'totalCount': N, 'results': [...]}, ...}
        return result.get('allTransactions', {}).get('results', [])

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

        return await self._api_call_with_retry(
            self.mm.get_budgets, start_date=start_date, end_date=end_date
        )

    async def get_transaction_categories(self) -> List[Dict[str, Any]]:
        """Get all transaction categories."""
        if not self._authenticated:
            raise RuntimeError("Must login first")
        return await self._api_call_with_retry(self.mm.get_transaction_categories)

    async def get_aggregate_snapshots(self,
                                      start_date: Optional[datetime] = None,
                                      end_date: Optional[datetime] = None,
                                      account_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get daily aggregate account snapshots.

        Args:
            start_date: Start date for snapshots
            end_date: End date for snapshots
            account_type: Filter by account type (e.g., 'depository' for cash accounts)

        Returns:
            Dictionary with snapshot data
        """
        if not self._authenticated:
            raise RuntimeError("Must login first")

        return await self._api_call_with_retry(
            self.mm.get_aggregate_snapshots,
            start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
            end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
            account_type=account_type
        )

    async def get_account_history(self, account_id: str) -> Dict[str, Any]:
        """
        Get historical balance snapshots for a specific account.

        Args:
            account_id: The account ID

        Returns:
            Dictionary with historical snapshot data
        """
        if not self._authenticated:
            raise RuntimeError("Must login first")

        return await self._api_call_with_retry(
            self.mm.get_account_history,
            account_id=int(account_id)
        )
