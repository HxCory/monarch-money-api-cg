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

### 🔄 In Progress
- [ ] Test with real Monarch Money account
- [ ] Refine transaction categorization logic
- [ ] Validate data format assumptions

### 📋 Next Steps
1. Install dependencies and test authentication
2. Run initial analysis to understand data structure
3. Refine credit card debt payoff calculations based on actual data
4. Add more detailed reporting features:
   - Monthly trends
   - Payoff projections
   - Category breakdowns
5. Add export functionality (CSV/Excel)
6. Consider visualization options

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
