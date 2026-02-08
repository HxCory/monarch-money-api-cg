#!/usr/bin/env python3
"""
Credit Card Analysis - Analyzes credit card debt and generates visualizations.

Analyzes the last 6 months of credit card activity including:
- Payments vs purchases by month
- Purchases by card
- Cumulative net debt change

Usage:
    python cc_analysis.py

Outputs plots to output/analysis_<timestamp>/
"""

import asyncio
from monarch_budgeting.main import main

if __name__ == "__main__":
    asyncio.run(main())
