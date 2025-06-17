# Nifty 100 Index Tracker - Product Requirements Document

## 1. Executive Summary

The Nifty 100 Index Tracker is a Python-based application designed to replicate the composition of the Nifty 100 index by creating proportional buy orders based on user-specified investment amounts. The application will generate detailed portfolio allocation reports and buy order recommendations.

## 2. Product Overview

### 2.1 Purpose
To provide retail investors with a tool to replicate the Nifty 100 index performance by calculating exact share quantities and allocations based on their investment budget.

### 2.2 Target Users
- Individual retail investors
- Portfolio managers
- Financial advisors
- Investment enthusiasts

## 3. Functional Requirements

### 3.1 Core Features

#### 3.1.1 Index Composition Management
- **FR-001**: The system shall maintain the complete list of Nifty 100 constituent securities
- **FR-002**: The system shall store security details including:
  - Company name
  - Trading symbol (NSE format)
  - ISIN code
  - Market capitalization
  - Index weightage percentage
- **FR-003**: The system shall support manual updates to the index composition via CSV file input

#### 3.1.2 Real-time Price Fetching
- **FR-004**: The system shall integrate with yfinance library to fetch current market prices
- **FR-005**: The system shall retrieve Last Traded Price (LTP) for all Nifty 100 securities
- **FR-006**: The system shall handle API failures gracefully with appropriate error messages
- **FR-007**: The system shall implement retry mechanisms for failed price fetches

#### 3.1.3 Portfolio Allocation Engine
- **FR-008**: The system shall accept user input for total INR investment amount
- **FR-009**: The system shall distribute the investment amount equally across all 100 securities (1% each)
- **FR-010**: The system shall calculate the number of shares to purchase for each security based on:
  - Individual allocation amount = Total Investment ÷ 100
  - Shares to buy = floor(Individual allocation ÷ Current price per share)
- **FR-011**: The system shall handle fractional shares by rounding down to the nearest whole number
- **FR-012**: The system shall calculate actual allocated amount vs. intended allocation
- **FR-013**: The system shall track unallocated amount due to fractional share constraints

#### 3.1.4 Output Generation
- **FR-014**: The system shall generate a CSV output file containing:
  - Security name
  - Trading symbol
  - Current price per share
  - Target allocation percentage (1% for equal weighting)
  - Target allocation amount (INR)
  - Number of shares to buy
  - Actual allocation amount (shares × price)
  - Actual allocation percentage
  - Unallocated amount per security
- **FR-015**: The system shall include summary statistics in the output:
  - Total investment amount
  - Total allocated amount
  - Total unallocated amount
  - Number of securities successfully processed

### 3.2 Data Management

#### 3.2.1 Data Storage
- **FR-016**: The system shall use CSV files for all data persistence
- **FR-017**: The system shall maintain separate CSV files for:
  - Nifty 100 constituent securities master data
  - Current prices (with timestamp)
  - Generated buy orders
  - Execution history
- **FR-018**: The system shall implement proper CSV headers and data validation

#### 3.2.2 Data Processing
- **FR-019**: The system shall validate input data formats and ranges
- **FR-020**: The system shall handle missing or invalid price data
- **FR-021**: The system shall maintain data integrity across all operations

## 4. Non-Functional Requirements

### 4.1 Performance
- **NFR-001**: The system shall process all 100 securities within 60 seconds
- **NFR-002**: The system shall support investment amounts from ₹1,000 to ₹10,00,00,000
- **NFR-003**: Price fetching shall have a timeout of 10 seconds per security

### 4.2 Reliability
- **NFR-004**: The system shall have 95% success rate in price fetching
- **NFR-005**: The system shall continue processing even if some securities fail to fetch prices
- **NFR-006**: All calculations shall be accurate to 2 decimal places for currency amounts

### 4.3 Usability
- **NFR-007**: The system shall provide clear command-line interface
- **NFR-008**: Error messages shall be user-friendly and actionable
- **NFR-009**: Output files shall be human-readable with proper formatting

### 4.4 Maintainability
- **NFR-010**: Code shall be modular with separate classes for different functionalities
- **NFR-011**: The system shall support easy addition/removal of securities
- **NFR-012**: Configuration parameters shall be externalized

## 5. Technical Requirements

### 5.1 Technology Stack
- **Programming Language**: Python 3.8+
- **Key Libraries**:
  - yfinance (for NSE data)
  - pandas (for data manipulation)
  - csv (for file operations)
  - datetime (for timestamps)
  - logging (for error tracking)

### 5.2 System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Business Logic │    │   Output Layer  │
│                 │    │                 │    │                 │
│ • CSV Files     │◄──►│ • Price Fetcher │◄──►│ • CSV Generator │
│ • Index Master  │    │ • Allocator     │    │ • Report Writer │
│ • Price Cache   │    │ • Calculator    │    │ • Formatter     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 5.3 File Structure
```
nifty100_tracker/
├── src/
│   ├── main.py
│   ├── models/
│   │   ├── security.py
│   │   └── portfolio.py
│   ├── services/
│   │   ├── price_fetcher.py
│   │   ├── allocator.py
│   │   └── csv_handler.py
│   └── utils/
│       ├── validators.py
│       └── helpers.py
├── data/
│   ├── nifty100_securities.csv
│   ├── prices/
│   └── output/
├── config/
│   └── settings.py
└── tests/
```

## 6. Input/Output Specifications

### 6.1 Input Requirements
- **Investment Amount**: Positive integer/float in INR (minimum ₹1,000)
- **Index Composition File**: CSV with columns:
  - symbol, company_name, isin, market_cap, weightage

### 6.2 Output Format
CSV file with columns:
```
company_name, symbol, current_price, target_allocation_pct, 
target_amount, shares_to_buy, actual_allocation_amount, 
actual_allocation_pct, unallocated_amount, timestamp
```

## 7. Error Handling

### 7.1 Error Scenarios
- Network connectivity issues
- Invalid security symbols
- Market closed scenarios
- Insufficient investment amount
- File I/O errors

### 7.2 Error Response
- Log all errors with timestamps
- Continue processing remaining securities
- Provide summary of failed operations
- Generate partial results when possible

## 8. Future Enhancements

### 8.1 Phase 2 Features
- Support for market cap-weighted allocation
- Integration with multiple data sources
- Real-time portfolio tracking
- Tax optimization suggestions
- Rebalancing recommendations

### 8.2 Phase 3 Features
- Web-based user interface
- Database integration
- Portfolio performance analytics
- Automated execution via broker APIs

## 9. Success Criteria

### 9.1 Functional Success
- Successfully processes all 100 Nifty securities
- Generates accurate buy order calculations
- Produces properly formatted CSV output
- Handles edge cases gracefully

### 9.2 Business Success
- Enables users to replicate Nifty 100 index easily
- Provides transparency in allocation decisions
- Reduces manual calculation errors
- Supports various investment amounts

## 10. Timeline and Milestones

### Phase 1 (Weeks 1-2)
- Set up project structure
- Implement basic CSV handling
- Create security and portfolio models

### Phase 2 (Weeks 3-4)
- Integrate yfinance for price fetching
- Implement allocation algorithms
- Add error handling and validation

### Phase 3 (Weeks 5-6)
- Generate output reports
- Add comprehensive testing
- Documentation and deployment

## 11. Risk Assessment

### 11.1 Technical Risks
- **yfinance API changes**: Mitigation - Abstract API calls, implement fallback options
- **Data quality issues**: Mitigation - Input validation, data cleaning routines
- **Performance bottlenecks**: Mitigation - Implement caching, parallel processing

### 11.2 Business Risks
- **Market data accuracy**: Mitigation - Multiple data source validation
- **Regulatory compliance**: Mitigation - Add disclaimers, ensure data usage compliance