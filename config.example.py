# config.example.py
# Copy this file to config.py and fill in your API keys.
# config.py is gitignored and will NOT be committed.
#
# Alternatively, set environment variables and leave config.py as-is.

import os

# EODHD API key — https://eodhd.com/
# Use 'demo' for development with limited symbols (AAPL.US, TSLA.US, AMZN.US)
EODHD_API_KEY = os.environ.get("EODHD_API_KEY", "demo")

# IEX Cloud token (legacy, not used in current pipeline)
IEX_CLOUD_API_TOKEN = os.environ.get("IEX_CLOUD_API_TOKEN", "")