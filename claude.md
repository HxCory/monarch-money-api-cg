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
├── tmp/JS/                    # Original JavaScript implementation (archived)
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Modern Python project configuration
├── example.py                # Example usage script
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
- [x] Moved original JavaScript implementation to `tmp/JS/`
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

### 📋 Future Steps
1. Add user-defined budget targets (JSON config)
2. Add export functionality (CSV/Excel)
3. Consider payoff projections
4. Multi-month trend analysis
5. Budget vs actual comparison reports

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
python example.py
```

## User Preferences
- Prefers Python over JavaScript
- Looking for practical, accurate budgeting insights
- Working on this via Claude Code on iOS mobile initially
