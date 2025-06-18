# Nifty 100 Index Tracker

A Python application that replicates the Nifty 100 index by generating proportional buy orders based on user-specified investment amounts.

## Overview

The Nifty 100 Index Tracker helps retail investors replicate the performance of the Nifty 100 index by calculating exact share quantities and allocations based on their investment budget. The application fetches real-time prices from NSE and generates detailed portfolio allocation reports.

## Features

- **Equal Weight Allocation**: Distributes investment equally across all 100 securities (1% each)
- **Real-time Price Fetching**: Uses yfinance library to fetch current NSE prices
- **Detailed Reporting**: Generates CSV reports with buy orders and portfolio summary
- **Error Handling**: Graceful handling of API failures and network issues
- **Flexible Input**: Supports custom securities files and various investment amounts
- **Interactive Mode**: User-friendly command-line interface

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd nifty-indices
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create sample data** (for testing):
   ```bash
   python src/main.py --create-sample
   ```

## Usage

### Command Line Interface


#### Example Usage for Application
```bash  
# Scenario: Invest ₹1100000 in with equal weight allocation into a filtered list of securities from the Nifty 100

# remove the old nifty100 securities files
rm -rf data/nifty100_securities.csv
rm -rf data/nifty100_enhanced_securities.csv

# download the new nifty 100 securities file
[Nifty100](https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv)   

# hydrate the nifty100 securities file with price and pe ratio data
python src/main.py --hydratedata data/ind_nifty100list.csv --output data/nifty100_enhanced_securities.csv

# move over to google sheets to exclude relevant securities Or use the nifty100_exclusions.csv

# create the index list
python src/main.py --amount 1100000 --securities data/nifty100_enhanced_securities.csv --exclusion data/nifty100_exclusions.csv
```

#### Basic Usage
```bash
# Invest ₹1,00,000 with equal weight allocation
python src/main.py --amount 100000

# Use a custom securities file
python src/main.py --amount 50000 --securities data/custom_securities.csv

# Exclude specific securities from the index
python src/main.py --amount 100000 --exclusion data/exclusions.csv

# Combine custom securities and exclusion lists
python src/main.py --amount 1100000 --securities data/nifty100_securities.csv --exclusion data/nifty100_exclusions.csv

# Interactive mode
python src/main.py --interactive

# Basic usage - hydrate the default nifty100 file
python src/main.py --hydratedata data/nifty100_securities.csv

# Custom output file
python src/main.py --hydratedata data/nifty100_securities.csv --output data/enhanced_securities.csv

# With logging
python src/main.py --hydratedata data/securities.csv --log-level DEBUG
```

#### Advanced Options
```bash
# Enable debug logging
python src/main.py --amount 100000 --log-level DEBUG

# Save logs to file
python src/main.py --amount 100000 --log-file tracker.log

# Create sample securities data
python src/main.py --create-sample

# Create sample exclusion list
python src/main.py --create-exclusion-sample
```

### Interactive Mode

Run the application in interactive mode for a guided experience:

```bash
python src/main.py --interactive
```

### Input Requirements

- **Investment Amount**: Minimum ₹1,000, Maximum ₹10,00,00,000
- **Securities File**: CSV with columns: `Company Name`, `Industry`, `Symbol`, `Series`, `ISIN Code`
- **Exclusion File** (Optional): CSV with same format as securities file containing securities to exclude from the index

### Security Exclusion Feature

The application supports an optional exclusion list that allows you to filter out specific securities from the index:

- **Format**: Same CSV format as the main securities file
- **Matching**: Securities are matched by both Symbol and ISIN Code for accuracy
- **Allocation**: Investment is redistributed equally among remaining securities
- **Use Cases**: 
  - Exclude sectors you don't want (e.g., tobacco, fossil fuels)
  - Remove specific companies due to ESG concerns
  - Filter out highly volatile or speculative stocks
  - Create custom thematic indices

### Output Files

The application generates:

1. **Portfolio CSV**: Detailed buy orders with allocations
   - `data/output/nifty100_allocation_YYYYMMDD_HHMMSS.csv`

2. **Summary Report**: Portfolio statistics and summary
   - `data/output/nifty100_allocation_YYYYMMDD_HHMMSS_summary.txt`

## Project Structure

```
nifty-indices/
├── src/
│   ├── main.py                 # Main application entry point
│   ├── models/
│   │   ├── security.py         # Security data model
│   │   └── portfolio.py        # Portfolio and allocation models
│   ├── services/
│   │   ├── price_fetcher.py    # NSE price fetching service
│   │   ├── allocator.py        # Portfolio allocation engine
│   │   └── csv_handler.py      # CSV read/write operations
│   └── utils/
│       ├── validators.py       # Input validation utilities
│       └── helpers.py          # Helper functions and formatting
├── config/
│   └── settings.py             # Application configuration
├── data/
│   ├── nifty100_securities.csv # Securities master data
│   ├── prices/                 # Price cache (optional)
│   └── output/                 # Generated reports
├── tests/                      # Unit tests (future)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Configuration

Application settings can be modified in `config/settings.py`:

- Investment amount constraints
- Price fetching timeouts and retries
- File paths and formats
- CSV headers and data formats

## Sample Output

### Console Output
```
============== NIFTY 100 INDEX TRACKER ==============
Investment Amount: ₹1,00,000.00
Start Time: 2024-01-15 14:30:00
====================================================

✓ Loaded 5 securities

Fetching current market prices...
✓ Price fetch completed: 5/5 successful (100.0%)

Calculating portfolio allocations...

Generating output files...

================ RESULTS SUMMARY ================
Total Investment                : ₹1,00,000.00
Total Allocated                 : ₹99,847.50
Total Unallocated              : ₹152.50
Utilization Rate               : 99.85%
Total Shares                   : 156
Successful Securities          : 5
Failed Securities              : 0
Success Rate                   : 100.0%

📁 Output Files Generated:
   • Portfolio Details: data/output/nifty100_allocation_20240115_143245.csv
   • Summary Report: data/output/nifty100_allocation_20240115_143245_summary.txt

📊 Sample Allocations (First 5):
   1. RELIANCE     -    8 shares @ ₹2,450.75 = ₹19,606.00
   2. TCS          -    5 shares @ ₹3,890.25 = ₹19,451.25
   3. INFY         -   13 shares @ ₹1,534.80 = ₹19,952.40
   4. HDFCBANK     -   12 shares @ ₹1,678.90 = ₹20,146.80
   5. ICICIBANK    -   18 shares @ ₹1,129.15 = ₹20,324.70
====================================================
```

### CSV Output Structure
```csv
company_name,symbol,current_price,target_allocation_pct,target_amount,shares_to_buy,actual_allocation_amount,actual_allocation_pct,unallocated_amount,timestamp
Reliance Industries Limited,RELIANCE,2450.75,1.00,1000.00,0,0.00,0.0000,1000.00,2024-01-15 14:32:45
```

## Error Handling

The application handles various error scenarios:

- **Network Connectivity**: Retries with exponential backoff
- **Invalid Symbols**: Continues processing remaining securities
- **Market Closed**: Graceful handling with appropriate messages
- **File I/O Errors**: Clear error messages and recovery suggestions

## Requirements

- Python 3.8+
- yfinance (for NSE data)
- pandas (for data manipulation)
- python-dateutil (for date handling)
- requests (for HTTP requests)

## Limitations

- Requires internet connection for real-time price fetching
- NSE API availability dependent on market hours and connectivity
- Equal weight allocation only (market cap weighting planned for future)
- Manual execution (automated trading integration planned for future)

## Future Enhancements

- Market cap-weighted allocation
- Multiple data source integration
- Portfolio rebalancing recommendations
- Web-based user interface
- Broker API integration for automated execution
- Tax optimization suggestions

## Contributing

Please read the Product Requirements Document (`nifty100_prd.md`) for detailed specifications and implementation guidelines.

## License

This project is for educational and personal use only. Please ensure compliance with NSE data usage policies and local regulations.

## Disclaimer

This tool is for informational purposes only and does not constitute financial advice. Users should conduct their own research and consult with financial advisors before making investment decisions. 

================= DATA HYDRATION =================
Input File: data/nifty100_securities.csv
Start Time: 2024-01-15 10:30:45
===============================================

Processing 1/100: RELIANCE
✓ RELIANCE: P/E=12.45, Price=₹2,847.30
Processing 2/100: TCS
✓ TCS: P/E=28.76, Price=₹4,123.50
...

Data hydration completed: 95/100 successful (95.0%)
Enhanced data saved to data/output/nifty100_securities_hydrated_20240115_103045.csv

=============== HYDRATION COMPLETE ===============
🎉 Data hydration completed successfully!
📁 Enhanced data saved to: data/output/nifty100_securities_hydrated_20240115_103045.csv
=============================================== 