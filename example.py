#!/usr/bin/env python3
"""
Example script to run the Monarch Money budgeting analysis.

Usage:
    python example.py

Make sure to set MONARCH_EMAIL and MONARCH_PASSWORD environment variables
or have a saved session from the monarchmoney library.
"""

import asyncio
from monarch_budgeting.main import main

if __name__ == "__main__":
    asyncio.run(main())
