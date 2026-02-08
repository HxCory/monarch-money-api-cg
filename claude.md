# Monarch Money Custom Budgeting Analysis

## Project Overview
Build a custom budgeting analysis tool using the unofficial Monarch Money API to handle credit card debt payoff accounting more accurately than Monarch Money's native features allow.

## Goals
- Account for credit card debt payoff in budgeting calculations
- Get more accurate budget insights by distinguishing debt payoff from regular spending
- Create custom analysis not currently possible in Monarch Money

## Technical Stack
- **Language**: Python 3.8+
- **API Library**: [monarchmoney](https://github.com/hammem/monarchmoney) - Python library for Monarch Money API
- **Data Processing**: pandas, numpy
- **Visualization** (optional): matplotlib, seaborn
- **Export** (optional): openpyxl for Excel exports

## Project Structure
```
monarch-money-api-cg/
├── monarch_budgeting/          # Main Python package
│   ├── __init__.py            # Package initialization
│   ├── client.py              # Monarch Money API client wrapper
│   ├── analyzer.py            # Credit card debt analysis logic
│   └── main.py                # Main CLI entry point
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Modern Python project configuration
├── cc_analysis.py            # Credit card analysis script
└── README.md                 # Project documentation
```

## Credit Card Debt Analysis (Details TBD)
User will provide more details on specific requirements, but initial considerations include:
- Distinguishing between new credit card purchases vs. paying down existing balances
- Tracking progress toward payoff goals separately from regular spending
- Potentially handling multiple cards with different strategies

## Output Format
To be determined - options include:
- Console reports
- Exported files (CSV/Excel)
- Visualizations
- Simple web dashboard

## Implementation Status

### ✅ Completed
- [x] Set up Python project structure
- [x] Created `MonarchClient` wrapper for API interactions
- [x] Implemented `CreditCardAnalyzer` for debt analysis
- [x] Added basic credit card summary and categorization
- [x] Created example script for running analysis
- [x] Fixed API compatibility (gql<4.0, response format parsing)
- [x] Added time series visualizations (payments vs purchases, by card, cumulative debt)
- [x] Added timestamped output directories for analysis runs
- [x] Tested with real Monarch Money account data

### ✅ Completed - Enhanced Cash-Based Budget Feature
**Branch**: `feature/cc-enhanced-budget`

**Goal**: Show TRUE CASH REMAINING by separating CC spending from actual cash outflows.

**Usage**:
```bash
python cash_budget.py                         # Previous month
python cash_budget.py --month 2025-12         # Specific month
python cash_budget.py --month 2025-12 --save  # Save to file
python cash_budget.py --month 2025-12 --pdf   # Generate PDF report
```

**Top-Level Metrics**:
1. True Cash Remaining = Income - Cash Expenses - CC Payments
2. Total New CC Spending = Sum of all CC transactions
3. Transfer transactions tracked separately (excluded from metrics, shown in PDF)

**Features**:
- [x] Rich terminal display with tables
- [x] PDF report generation with matplotlib
- [x] Cash balance chart over time
- [x] Transfer transactions page in PDF
- [x] Automatic MFA authentication (via MONARCH_MFA_SECRET env var)

### ✅ Completed - Budget Forecast Feature

**Goal**: Show expected cash position at end of month based on budget.

**Usage**:
```bash
python budget_forecast.py                     # Current month
python budget_forecast.py --month 2026-01     # Specific month
python budget_forecast.py --month 2026-01 --pdf  # Generate PDF
```

**Calculation**:
- Starting Cash (from account snapshots)
- + Expected Income (from budget)
- - Expected Expenses (from budget)
- = Expected End Cash

**Features**:
- [x] Custom GraphQL query for budget data (library's get_budgets() fails)
- [x] Rich terminal display
- [x] PDF report with income/expense breakdowns

**Known Issue**: `monarchmoney` library's `get_budgets()` returns server error. Implemented custom GraphQL query that works.

### ✅ Completed - Debt Payoff Projections

**Branch**: `feature/add-debt-reduction-vis`

**Goal**: Show how quickly debt can be paid off at different allocation percentages.

**Usage**:
```bash
python debt_payoff.py                         # CC debt, current month
python debt_payoff.py --type loan             # Loan debt
python debt_payoff.py --type cc --month 2026-01
python debt_payoff.py --use-local-budget      # Use custom_budget.json
```

**Features**:
- [x] Credit card and loan debt types
- [x] Configurable interest rates via `debt_config.json`
- [x] Multiple allocation percentages (25%, 35%, 50%, 60%, 65%, 70%, 75%)
- [x] For loans: base payment from budget + additional allocation
- [x] Payoff timeline plots saved to `output/`
- [x] Custom budget override support (`--use-local-budget`)

**Configuration**:
- `debt_config.json`: Interest rates, payoff percentages, loan category name
- `custom_budget.json`: Override Monarch budgets with local values
- Example files provided (`.example.json`), gitignored for privacy

### ✅ Completed - Streamlit Budget Editor

**Branch**: `feature/streamlit-budget-editor`

**Goal**: Interactive web UI for editing budget categories with live forecast preview and budget vs actual tracking.

**Usage**:
```bash
streamlit run budget_editor.py
```

**Features**:
- [x] Editable tables for income/expense categories
- [x] Auto-calculated totals
- [x] Month selector (past 12 months + next 3 months)
- [x] Per-month budget files in `budgets/` directory
- [x] **Sync with Monarch** - Fetch starting cash AND actual spending from API
- [x] **Budget vs Actual** - Actual and Remaining columns shown alongside Planned
- [x] Remaining column updates reactively when Planned is edited
- [x] Forecast preview (Starting Cash + Income - Expenses = Expected End)
- [x] Copy budget from previous month
- [x] Category group dropdowns
- [x] Cached API client with nest_asyncio for proper async handling
- [x] Side-by-side layout: editable columns (data_editor) + read-only columns (dataframe)

**File Storage**:
- Budgets saved to `budgets/YYYY-MM.json`
- CLI tools (`budget_forecast.py`, `debt_payoff.py`) automatically use month-specific budgets when `--use-local-budget` is specified

**Note**: Requires authentication via CLI first (e.g., `python budget_forecast.py`) since Streamlit cannot prompt for MFA.

### 📋 Future Steps
1. Multi-month trend analysis

## Quick Start

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Set environment variables for authentication:
```bash
export MONARCH_EMAIL="your-email@example.com"
export MONARCH_PASSWORD="your-password"
```

Alternatively, you can use the monarchmoney library's interactive login to save a session.

### Usage
```bash
python cc_analysis.py
```

## User Preferences
- Looking for practical, accurate budgeting insights
- Working on this via Claude Code on iOS mobile initially
