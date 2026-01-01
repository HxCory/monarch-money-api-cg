# Monarch Money Custom Budgeting Analysis

![Monarch Image](https://github.com/pbassham/monarch-money-api/raw/main/monarch-image-blue.png)

A Python-based budgeting analysis tool for Monarch Money with enhanced credit card debt tracking and payoff analysis.

> **Note**: This is an unofficial tool using the unofficial Monarch Money API. It is not endorsed by Monarch Money and may break at any time. Use at your own risk.

## Why This Tool?

Monarch Money is great, but tracking credit card debt payoff can be tricky. This tool helps you:

- **Distinguish debt payoff from spending**: See how much you're actually paying down vs. new purchases
- **Track multiple cards**: Monitor progress across all your credit cards
- **Get accurate insights**: Separate debt reduction from regular spending in your budget analysis
- **Keep it local**: All your financial data stays on your machine

## Features

✅ Credit card account identification and tracking
✅ Transaction categorization (purchases vs. payments)
✅ Debt payoff progress calculation
✅ Text-based reporting
🔄 Monthly trends (coming soon)
🔄 Payoff projections (coming soon)
🔄 Export to CSV/Excel (coming soon)

## Installation

### Prerequisites

- Python 3.8 or higher
- A Monarch Money account

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/HxCory/monarch-money-api-cg.git
   cd monarch-money-api-cg
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Authentication

You have two options for authentication:

#### Option 1: Environment Variables

```bash
export MONARCH_EMAIL="your-email@example.com"
export MONARCH_PASSWORD="your-password"
```

#### Option 2: `.env` File (Recommended)

Create a `.env` file in the project root:

```env
MONARCH_EMAIL=your-email@example.com
MONARCH_PASSWORD=your-password
```

> **Security Note**: The `.env` file is in `.gitignore` and will never be committed. See [SECURITY.md](SECURITY.md) for more details.

### Session Caching

After your first successful login, the `monarchmoney` library will save a session token. You won't need to provide credentials again until the session expires!

## Usage

### Quick Start

Run the example script:

```bash
python example.py
```

This will:
1. Login to your Monarch Money account
2. Fetch your accounts and transactions
3. Analyze your credit card debt
4. Display a summary report

### Example Output

```
Monarch Money - Custom Budgeting Analysis
============================================================

Logging in to Monarch Money...
✓ Login successful

Fetching account data...
✓ Found 12 accounts
✓ Found 3 credit card accounts

Fetching transactions from 2025-01-01 to 2025-01-31...
✓ Found 145 transactions

============================================================
CREDIT CARD DEBT ANALYSIS REPORT
============================================================

Account Summary:
------------------------------------------------------------
  Chase Sapphire: $-1,245.67
  Capital One: $-850.32
  Discover: $-0.00

Total Credit Card Debt: $-2,095.99

Transaction Summary:
------------------------------------------------------------
  New Purchases: 42 transactions
  Payments: 3 transactions

  Total New Purchases: $1,892.45
  Total Payments: $2,500.00
============================================================
```

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
├── test_basic.py             # Basic tests (no auth required)
├── SECURITY.md               # Security guidelines
├── claude.md                 # Project planning document
└── README.md                 # This file
```

## Advanced Usage

### Using as a Library

```python
import asyncio
from monarch_budgeting.client import MonarchClient
from monarch_budgeting.analyzer import CreditCardAnalyzer
from datetime import datetime, timedelta

async def analyze():
    # Initialize and login
    client = MonarchClient()
    await client.login(use_saved_session=True)

    # Fetch data
    accounts = await client.get_accounts()
    transactions = await client.get_transactions(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )

    # Analyze
    analyzer = CreditCardAnalyzer(transactions, accounts)
    summary = analyzer.get_credit_card_summary()
    progress = analyzer.calculate_debt_payoff_progress(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )

    print(summary)
    print(progress)

asyncio.run(analyze())
```

### Running Tests

Run basic tests without authentication:

```bash
python test_basic.py
```

## Security

🔒 **Your credentials are safe!**

- Passwords never stored in code or logs
- Credentials only via environment variables or `.env` file
- Session tokens stored locally in `.mm/` (excluded from git)
- All financial data stays on your machine
- No third-party data sharing

See [SECURITY.md](SECURITY.md) for complete security guidelines.

## Development

### Contributing

This is a personal project, but contributions are welcome! If you have ideas for improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Roadmap

- [x] Basic credit card debt analysis
- [x] Transaction categorization
- [x] CLI reporting
- [ ] Monthly trend analysis
- [ ] Debt payoff projections
- [ ] Category-level breakdowns
- [ ] CSV/Excel export
- [ ] Data visualization
- [ ] Web dashboard (maybe)

## Tech Stack

- **Python 3.8+**
- **[monarchmoney](https://github.com/hammem/monarchmoney)** - Python library for Monarch Money API
- **pandas** - Data processing and analysis
- **numpy** - Numerical computations

## Credits

This project uses the [monarchmoney](https://github.com/hammem/monarchmoney) Python library by @hammem for accessing the Monarch Money API.

The original JavaScript implementation (now in `tmp/JS/`) was forked from [pbassham/monarch-money-api](https://github.com/pbassham/monarch-money-api).

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is provided "as is" without warranty of any kind. It uses an unofficial API that could break at any time. Users are responsible for:

- Securing their own credentials
- Reviewing code before running it
- Understanding the risks of using unofficial APIs
- Complying with Monarch Money's Terms of Service

Use at your own risk!

---

**Questions or issues?** Open an issue on GitHub or check the [claude.md](claude.md) file for project planning details.
