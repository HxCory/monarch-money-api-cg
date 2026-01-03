"""
Streamlit Budget Editor - Interactive web UI for editing budget categories.

Usage:
    streamlit run budget_editor.py
"""

import streamlit as st
import pandas as pd
import asyncio
import nest_asyncio
from datetime import datetime, timedelta
from pathlib import Path

from monarch_budgeting.utils import (
    format_currency,
    load_custom_budget,
    load_month_budget,
    save_month_budget,
    list_available_budgets,
    parse_month,
    DEFAULT_CUSTOM_BUDGET_PATH,
)
from monarch_budgeting.client import MonarchClient

# Allow nested event loops (needed for Streamlit + asyncio)
nest_asyncio.apply()

# Category groups for dropdown
CATEGORY_GROUPS = [
    "Income",
    "Housing",
    "Food & Dining",
    "Auto & Transport",
    "Bills & Utilities",
    "Financial",
    "Health & Wellness",
    "Travel & Lifestyle",
    "Education",
    "Business",
    "Other",
]

# Page configuration
st.set_page_config(
    page_title="Budget Editor",
    page_icon="💰",
    layout="wide",
)


def get_default_budget() -> dict:
    """Get default budget structure with pre-populated categories."""
    return {
        "total_income": 0,
        "total_expenses": 0,
        "income_categories": [],
        "expense_categories": [
            {"name": "Credit Card Payments", "group": "Financial", "amount": 0},
        ],
    }


@st.cache_resource
def get_monarch_client():
    """
    Get a cached MonarchClient instance.

    Uses Streamlit's cache_resource to maintain a single client across reruns.
    """
    return MonarchClient()


async def _login_client(client: MonarchClient) -> bool:
    """
    Attempt to login the client using saved session.

    Returns True if successful, False if auth failed.
    Does NOT prompt for MFA (can't use input() in Streamlit).
    """
    try:
        # Try saved session first (no credentials needed if session is valid)
        await client.login(use_saved_session=True, prompt_for_mfa=False)
        return True
    except Exception as e:
        # Check if it's an MFA issue or other auth failure
        error_str = str(e).lower()
        if 'mfa' in error_str or 'multi' in error_str or 'factor' in error_str:
            raise AuthError(
                "MFA required. Please authenticate first by running:\n"
                "  python budget_forecast.py\n"
                "This will save a session that the budget editor can use."
            )
        raise AuthError(f"Login failed: {e}")


class AuthError(Exception):
    """Authentication error with user-friendly message."""
    pass


async def fetch_starting_cash_async(month: str) -> float:
    """Fetch starting cash balance from Monarch Money API."""
    start_date, _ = parse_month(month)

    client = get_monarch_client()
    await _login_client(client)

    # Get aggregate snapshot for start of month
    snapshots = await client.get_aggregate_snapshots(
        start_date=start_date,
        end_date=start_date,
        account_type='depository'
    )

    snapshot_list = snapshots.get('aggregateSnapshots', [])
    if snapshot_list:
        return snapshot_list[0].get('balance', 0)

    # Try previous day if no snapshot for start
    prev_day = start_date - timedelta(days=1)
    snapshots = await client.get_aggregate_snapshots(
        start_date=prev_day,
        end_date=prev_day,
        account_type='depository'
    )
    snapshot_list = snapshots.get('aggregateSnapshots', [])
    return snapshot_list[0].get('balance', 0) if snapshot_list else 0


def fetch_starting_cash(month: str) -> float:
    """Synchronous wrapper to fetch starting cash."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(fetch_starting_cash_async(month))


def load_initial_budget(month: str) -> dict:
    """
    Load budget for the given month.

    Priority:
    1. Existing month-specific budget file
    2. custom_budget.json (for migration)
    3. Empty default budget
    """
    # Try month-specific budget first
    budget = load_month_budget(month)
    if budget is not None:
        return budget

    # Try custom_budget.json for migration
    if DEFAULT_CUSTOM_BUDGET_PATH.exists():
        try:
            return load_custom_budget()
        except Exception:
            pass

    # Return empty default
    return get_default_budget()


def df_to_categories(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of category dicts."""
    if df.empty:
        return []
    return df.to_dict('records')


def categories_to_df(categories: list, is_income: bool = False) -> pd.DataFrame:
    """Convert list of category dicts to DataFrame."""
    if not categories:
        return pd.DataFrame(columns=['name', 'group', 'amount'])

    df = pd.DataFrame(categories)

    # Ensure required columns exist
    if 'name' not in df.columns:
        df['name'] = ''
    if 'group' not in df.columns:
        df['group'] = 'Income' if is_income else 'Other'
    if 'amount' not in df.columns:
        df['amount'] = 0.0

    # Reorder columns
    return df[['name', 'group', 'amount']]


def main():
    st.title("Budget Editor")

    # Month selector in sidebar
    st.sidebar.header("Settings")

    # Generate month options (current month + past 12 months + next 3 months)
    today = datetime.now()
    months = []
    for delta in range(-12, 4):
        year = today.year + (today.month + delta - 1) // 12
        month = ((today.month + delta - 1) % 12) + 1
        months.append(f"{year}-{month:02d}")
    months = sorted(set(months), reverse=True)

    # Also include any existing budget months
    existing_budgets = list_available_budgets()
    all_months = sorted(set(months + existing_budgets), reverse=True)

    # Default to current month
    current_month = f"{today.year}-{today.month:02d}"
    default_index = all_months.index(current_month) if current_month in all_months else 0

    selected_month = st.sidebar.selectbox(
        "Select Month",
        options=all_months,
        index=default_index,
    )

    # Show which months have saved budgets
    if existing_budgets:
        st.sidebar.markdown("**Saved budgets:**")
        st.sidebar.markdown(", ".join(existing_budgets))

    # Initialize session state for budget data
    if 'budget' not in st.session_state or st.session_state.get('current_month') != selected_month:
        st.session_state.budget = load_initial_budget(selected_month)
        st.session_state.current_month = selected_month

    # Display current month
    st.header(f"Budget for {selected_month}")

    # Create two columns for income and expenses
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Income")

        income_df = categories_to_df(
            st.session_state.budget.get('income_categories', []),
            is_income=True
        )

        edited_income = st.data_editor(
            income_df,
            column_config={
                "name": st.column_config.TextColumn(
                    "Category",
                    help="Name of the income category",
                    width="medium",
                ),
                "group": st.column_config.SelectboxColumn(
                    "Group",
                    help="Category group",
                    options=CATEGORY_GROUPS,
                    width="medium",
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    help="Monthly amount",
                    format="$%.2f",
                    min_value=0,
                    width="small",
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="income_editor",
        )

        # Calculate and display income total
        total_income = edited_income['amount'].sum() if not edited_income.empty else 0
        st.metric("Total Income", format_currency(total_income))

    with col2:
        st.subheader("Expenses")

        expense_df = categories_to_df(
            st.session_state.budget.get('expense_categories', [])
        )

        edited_expenses = st.data_editor(
            expense_df,
            column_config={
                "name": st.column_config.TextColumn(
                    "Category",
                    help="Name of the expense category",
                    width="medium",
                ),
                "group": st.column_config.SelectboxColumn(
                    "Group",
                    help="Category group",
                    options=CATEGORY_GROUPS,
                    width="medium",
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    help="Monthly amount",
                    format="$%.2f",
                    min_value=0,
                    width="small",
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="expense_editor",
        )

        # Calculate and display expense total
        total_expenses = edited_expenses['amount'].sum() if not edited_expenses.empty else 0
        st.metric("Total Expenses", format_currency(total_expenses))

    # Summary section
    st.divider()
    st.subheader("Summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("Total Income", format_currency(total_income))

    with summary_col2:
        st.metric("Total Expenses", format_currency(total_expenses))

    with summary_col3:
        surplus = total_income - total_expenses
        st.metric(
            "Monthly Surplus",
            format_currency(surplus),
            delta=format_currency(surplus) if surplus != 0 else None,
            delta_color="normal" if surplus >= 0 else "inverse",
        )

    # Forecast Preview section
    st.divider()
    st.subheader("Forecast Preview")

    # Initialize starting cash in session state
    if 'starting_cash' not in st.session_state:
        st.session_state.starting_cash = None
    if 'starting_cash_month' not in st.session_state:
        st.session_state.starting_cash_month = None

    forecast_col1, forecast_col2 = st.columns([3, 1])

    with forecast_col2:
        if st.button("Fetch Starting Cash", use_container_width=True):
            with st.spinner("Connecting to Monarch Money..."):
                try:
                    cash = fetch_starting_cash(selected_month)
                    st.session_state.starting_cash = cash
                    st.session_state.starting_cash_month = selected_month
                    st.success("Fetched!")
                    st.rerun()
                except AuthError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {e}\n\nTry running `python budget_forecast.py` first to authenticate.")

    with forecast_col1:
        # Check if we have a valid starting cash for this month
        if (st.session_state.starting_cash is not None and
            st.session_state.starting_cash_month == selected_month):

            starting_cash = st.session_state.starting_cash
            expected_end = starting_cash + total_income - total_expenses

            # Display forecast calculation
            fc1, fc2, fc3, fc4 = st.columns(4)

            with fc1:
                st.metric("Starting Cash", format_currency(starting_cash))
            with fc2:
                st.metric("+ Income", format_currency(total_income))
            with fc3:
                st.metric("- Expenses", format_currency(total_expenses))
            with fc4:
                st.metric(
                    "= Expected End",
                    format_currency(expected_end),
                    delta=format_currency(expected_end - starting_cash),
                    delta_color="normal" if expected_end >= starting_cash else "inverse",
                )
        else:
            st.info("Click 'Fetch Starting Cash' to load your current cash balance from Monarch Money and see the forecast.")

    # Save and Reset buttons
    st.divider()

    button_col1, button_col2, button_col3 = st.columns([1, 1, 4])

    with button_col1:
        if st.button("Save Budget", type="primary", use_container_width=True):
            # Build budget dict from edited data
            new_budget = {
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "income_categories": df_to_categories(edited_income),
                "expense_categories": df_to_categories(edited_expenses),
            }

            # Save to month-specific file
            save_month_budget(selected_month, new_budget)

            # Update session state
            st.session_state.budget = new_budget

            st.success(f"Budget saved to budgets/{selected_month}.json")

    with button_col2:
        if st.button("Reset", use_container_width=True):
            # Reload from file
            st.session_state.budget = load_initial_budget(selected_month)
            st.rerun()

    # Copy from another month
    st.sidebar.divider()
    st.sidebar.subheader("Copy Budget")

    if existing_budgets:
        copy_from = st.sidebar.selectbox(
            "Copy from month",
            options=[""] + [m for m in existing_budgets if m != selected_month],
            format_func=lambda x: "Select a month..." if x == "" else x,
        )

        if st.sidebar.button("Copy Budget", disabled=copy_from == ""):
            if copy_from:
                source_budget = load_month_budget(copy_from)
                if source_budget:
                    st.session_state.budget = source_budget
                    st.sidebar.success(f"Copied budget from {copy_from}")
                    st.rerun()
    else:
        st.sidebar.info("No saved budgets to copy from yet.")


if __name__ == "__main__":
    main()
