"""
Streamlit Budget Editor - Interactive web UI for editing budget categories.

Usage:
    streamlit run budget_editor.py
"""

import os
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
from monarchmoney import MonarchMoney
from monarchmoney.monarchmoney import RequireMFAException

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


class AuthError(Exception):
    """Authentication error with user-friendly message."""
    pass


@st.cache_resource
def get_monarch_money():
    """
    Get a cached MonarchMoney instance.

    Uses Streamlit's cache_resource to maintain a single client across reruns.
    """
    return MonarchMoney()


async def ensure_authenticated() -> MonarchMoney:
    """
    Ensure we have an authenticated MonarchMoney client.

    Uses the same auth logic as CLI tools:
    1. Try saved session first
    2. Fall back to credentials from env vars (MONARCH_EMAIL, MONARCH_PASSWORD)
    3. Use MONARCH_MFA_SECRET for automatic TOTP if MFA is required

    Returns the authenticated MonarchMoney instance.
    Raises AuthError if authentication fails.
    """
    mm = get_monarch_money()

    # Check if already authenticated (has valid token)
    if mm._token:
        return mm

    # Try saved session first
    try:
        await mm.login(use_saved_session=True)
        return mm
    except Exception:
        pass  # Session doesn't exist or is invalid

    # Get credentials from environment
    email = os.environ.get('MONARCH_EMAIL')
    password = os.environ.get('MONARCH_PASSWORD')
    mfa_secret = os.environ.get('MONARCH_MFA_SECRET')

    if not email or not password:
        raise AuthError(
            "No saved session and credentials not found.\n\n"
            "Please set environment variables:\n"
            "  export MONARCH_EMAIL='your-email'\n"
            "  export MONARCH_PASSWORD='your-password'\n"
            "  export MONARCH_MFA_SECRET='your-totp-secret'  # if MFA enabled"
        )

    # Try to login with credentials
    try:
        await mm.login(
            email=email,
            password=password,
            use_saved_session=False,
            mfa_secret_key=mfa_secret
        )
        return mm
    except RequireMFAException:
        if not mfa_secret:
            raise AuthError(
                "MFA required but MONARCH_MFA_SECRET not set.\n\n"
                "Please set the environment variable:\n"
                "  export MONARCH_MFA_SECRET='your-totp-secret'\n\n"
                "Or run `python budget_forecast.py` once to save a session."
            )
        raise AuthError("MFA authentication failed. Check your MONARCH_MFA_SECRET.")
    except Exception as e:
        raise AuthError(f"Login failed: {e}")


async def get_budget_data(mm: MonarchMoney, month: str) -> dict:
    """
    Get budget data for a specific month using custom GraphQL query.

    Args:
        mm: Authenticated MonarchMoney instance
        month: Month in YYYY-MM format (e.g., '2026-01')

    Returns:
        Dictionary with budget data including monthlyAmountsByCategory and totalsByMonth
    """
    from gql import gql

    query = gql('''
        query GetBudgetData($month: Date!) {
            budgetData(startMonth: $month, endMonth: $month) {
                monthlyAmountsByCategory {
                    category {
                        id
                        name
                        group {
                            id
                            name
                            type
                        }
                    }
                    monthlyAmounts {
                        month
                        plannedCashFlowAmount
                        actualAmount
                        remainingAmount
                    }
                }
                totalsByMonth {
                    month
                    totalIncome {
                        plannedAmount
                        actualAmount
                    }
                    totalExpenses {
                        plannedAmount
                        actualAmount
                    }
                }
            }
        }
    ''')

    month_date = f"{month}-01" if len(month) == 7 else month
    client = mm._get_graphql_client()
    result = await client.execute_async(query, variable_values={'month': month_date})
    return result.get('budgetData', {})


async def sync_with_monarch_async(month: str) -> dict:
    """
    Sync with Monarch Money API to fetch starting cash and budget actuals.

    Returns:
        Dict with 'starting_cash', 'income_actuals', 'expense_actuals', 'total_income_actual', 'total_expenses_actual'
    """
    start_date, _ = parse_month(month)
    month_key = start_date.strftime("%Y-%m")

    # Authenticate
    mm = await ensure_authenticated()

    result = {
        'starting_cash': 0,
        'income_actuals': {},  # category_name -> actual_amount
        'expense_actuals': {},  # category_name -> actual_amount
        'total_income_actual': 0,
        'total_expenses_actual': 0,
    }

    # Get starting cash balance
    snapshots = await mm.get_aggregate_snapshots(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=start_date.strftime('%Y-%m-%d'),
        account_type='depository'
    )

    snapshot_list = snapshots.get('aggregateSnapshots', [])
    if snapshot_list:
        result['starting_cash'] = snapshot_list[0].get('balance', 0)
    else:
        # Try previous day if no snapshot for start
        prev_day = start_date - timedelta(days=1)
        snapshots = await mm.get_aggregate_snapshots(
            start_date=prev_day.strftime('%Y-%m-%d'),
            end_date=prev_day.strftime('%Y-%m-%d'),
            account_type='depository'
        )
        snapshot_list = snapshots.get('aggregateSnapshots', [])
        result['starting_cash'] = snapshot_list[0].get('balance', 0) if snapshot_list else 0

    # Get budget data with actuals
    budget_data = await get_budget_data(mm, month_key)

    # Parse totals
    totals = budget_data.get('totalsByMonth', [])
    if totals:
        result['total_income_actual'] = totals[0].get('totalIncome', {}).get('actualAmount', 0)
        result['total_expenses_actual'] = totals[0].get('totalExpenses', {}).get('actualAmount', 0)

    # Parse category actuals
    for cat_data in budget_data.get('monthlyAmountsByCategory', []):
        category = cat_data.get('category', {})
        cat_name = category.get('name', 'Unknown')
        cat_type = category.get('group', {}).get('type', 'expense')
        amounts = cat_data.get('monthlyAmounts', [{}])[0]
        actual = amounts.get('actualAmount', 0)

        if cat_type == 'income':
            result['income_actuals'][cat_name] = actual
        elif cat_type == 'expense':
            result['expense_actuals'][cat_name] = actual

    return result


def sync_with_monarch(month: str) -> dict:
    """Synchronous wrapper to sync with Monarch."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(sync_with_monarch_async(month))


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
    """
    Convert list of category dicts to DataFrame for editing.

    Args:
        categories: List of category dicts with 'name', 'group', 'amount'
        is_income: Whether these are income categories (affects default group)
    """
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
    else:
        # Ensure amount is float
        df['amount'] = df['amount'].astype(float)

    # Return only editable columns
    return df[['name', 'group', 'amount']]


def build_actuals_df(edited_df: pd.DataFrame, actuals: dict) -> pd.DataFrame:
    """
    Build a read-only DataFrame showing actual vs remaining.

    Args:
        edited_df: The edited DataFrame from data_editor (has current planned values)
        actuals: Dict mapping category names to actual amounts

    Returns:
        DataFrame with Actual, Remaining columns (to display alongside editor)
    """
    if edited_df.empty:
        return pd.DataFrame(columns=['Actual', 'Remaining'])

    actual_values = edited_df['name'].apply(lambda x: float(actuals.get(x, 0.0)))
    result = pd.DataFrame({
        'Actual': actual_values,
        'Remaining': edited_df['amount'] - actual_values,
    })

    return result


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
        # Clear monarch data when month changes
        st.session_state.monarch_data = None

    # Initialize monarch data state
    if 'monarch_data' not in st.session_state:
        st.session_state.monarch_data = None

    # Display current month header with Sync button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.header(f"Budget for {selected_month}")
    with header_col2:
        st.write("")  # Spacer to align button with header
        if st.button("Sync with Monarch", use_container_width=True, type="primary"):
            with st.spinner("Syncing with Monarch Money..."):
                try:
                    monarch_data = sync_with_monarch(selected_month)
                    st.session_state.monarch_data = monarch_data
                    st.success("Synced!")
                    st.rerun()
                except AuthError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {e}")

    # Show sync status
    if st.session_state.monarch_data:
        starting_cash = st.session_state.monarch_data.get('starting_cash', 0)
        st.caption(f"Synced with Monarch - Starting Cash: {format_currency(starting_cash)}")
    else:
        st.caption("Click 'Sync with Monarch' to load actuals and starting cash balance")

    # Create two columns for income and expenses
    col1, col2 = st.columns(2)

    # Get actuals if synced
    income_actuals = None
    expense_actuals = None
    if st.session_state.monarch_data:
        income_actuals = st.session_state.monarch_data.get('income_actuals', {})
        expense_actuals = st.session_state.monarch_data.get('expense_actuals', {})

    with col1:
        st.subheader("Income")

        income_df = categories_to_df(
            st.session_state.budget.get('income_categories', []),
            is_income=True
        )

        # Calculate row count for consistent height
        income_row_count = max(len(income_df) + 1, 3)  # +1 for add row, min 3

        # Side-by-side layout: editor (left) | actuals (right)
        if income_actuals is not None:
            editor_col, actuals_col = st.columns([3, 1])
        else:
            editor_col = st.container()
            actuals_col = None

        with editor_col:
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
                        width="small",
                    ),
                    "amount": st.column_config.NumberColumn(
                        "Planned",
                        help="Planned monthly amount",
                        format="$%.2f",
                        min_value=0,
                        width="small",
                    ),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="income_editor",
                height=(income_row_count * 35) + 40,  # Approximate row height
            )

        # Show actuals alongside editor if synced
        if income_actuals is not None and actuals_col is not None:
            with actuals_col:
                actuals_df = build_actuals_df(edited_income, income_actuals)
                st.dataframe(
                    actuals_df,
                    column_config={
                        "Actual": st.column_config.NumberColumn(format="$%.2f"),
                        "Remaining": st.column_config.NumberColumn(format="$%.2f"),
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=(income_row_count * 35) + 40,
                )

        # Calculate and display income total
        total_income = edited_income['amount'].sum() if not edited_income.empty else 0
        if income_actuals is not None:
            total_income_actual = st.session_state.monarch_data.get('total_income_actual', 0)
            st.metric("Total Income", format_currency(total_income),
                     delta=f"Actual: {format_currency(total_income_actual)}")
        else:
            st.metric("Total Income", format_currency(total_income))

    with col2:
        st.subheader("Expenses")

        expense_df = categories_to_df(
            st.session_state.budget.get('expense_categories', []),
        )

        # Calculate row count for consistent height
        expense_row_count = max(len(expense_df) + 1, 3)  # +1 for add row, min 3

        # Side-by-side layout: editor (left) | actuals (right)
        if expense_actuals is not None:
            editor_col, actuals_col = st.columns([3, 1])
        else:
            editor_col = st.container()
            actuals_col = None

        with editor_col:
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
                        width="small",
                    ),
                    "amount": st.column_config.NumberColumn(
                        "Planned",
                        help="Planned monthly amount",
                        format="$%.2f",
                        min_value=0,
                        width="small",
                    ),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="expense_editor",
                height=(expense_row_count * 35) + 40,  # Approximate row height
            )

        # Show actuals alongside editor if synced
        if expense_actuals is not None and actuals_col is not None:
            with actuals_col:
                actuals_df = build_actuals_df(edited_expenses, expense_actuals)
                st.dataframe(
                    actuals_df,
                    column_config={
                        "Actual": st.column_config.NumberColumn(format="$%.2f"),
                        "Remaining": st.column_config.NumberColumn(format="$%.2f"),
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=(expense_row_count * 35) + 40,
                )

        # Calculate and display expense total
        total_expenses = edited_expenses['amount'].sum() if not edited_expenses.empty else 0
        if expense_actuals is not None:
            total_expenses_actual = st.session_state.monarch_data.get('total_expenses_actual', 0)
            st.metric("Total Expenses", format_currency(total_expenses),
                     delta=f"Actual: {format_currency(total_expenses_actual)}")
        else:
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

    # Forecast Preview section (only show if synced)
    if st.session_state.monarch_data:
        st.divider()
        st.subheader("Forecast")

        starting_cash = st.session_state.monarch_data.get('starting_cash', 0)
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
