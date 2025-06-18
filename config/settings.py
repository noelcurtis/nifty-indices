"""
Configuration settings for Nifty 100 Index Tracker
"""

# Investment constraints
MIN_INVESTMENT_AMOUNT = 1000  # Minimum ₹1,000
MAX_INVESTMENT_AMOUNT = 100000000  # Maximum ₹10 crores

# Price fetching settings
PRICE_FETCH_TIMEOUT = 10  # seconds per security
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Allocation settings
EQUAL_WEIGHT_PERCENTAGE = 1.0  # 1% for each of 100 securities
TOTAL_SECURITIES = 100

# File paths
NIFTY100_SECURITIES_FILE = "data/nifty100_securities_new.csv"
PRICES_DIR = "data/prices"
OUTPUT_DIR = "data/output"

# Nifty100 Constituents Download
NIFTY100_CONSTITUENTS_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
DEFAULT_CONSTITUENTS_DIR = "data"

# Data formats
PRICE_DECIMAL_PLACES = 2
CURRENCY_DECIMAL_PLACES = 2

# CSV headers - Old format (for backward compatibility)
SECURITY_CSV_HEADERS_OLD = [
    "symbol", "company_name", "isin", "market_cap", "weightage"
]

# CSV headers - New format
SECURITY_CSV_HEADERS_NEW = [
    "Company Name", "Industry", "Symbol", "Series", "ISIN Code"
]

# Default headers (using new format)
SECURITY_CSV_HEADERS = SECURITY_CSV_HEADERS_NEW

OUTPUT_CSV_HEADERS = [
    "company_name", "symbol", "current_price", "target_allocation_pct",
    "target_amount", "shares_to_buy", "actual_allocation_amount",
    "actual_allocation_pct", "unallocated_amount", "timestamp"
] 