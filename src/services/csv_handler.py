"""
CSV handling service for reading securities data and writing output files
"""

import csv
import logging
import os
import json
import requests
from typing import List, Optional
from datetime import datetime

from ..models.security import Security
from ..models.portfolio import Portfolio
from config.settings import (
    SECURITY_CSV_HEADERS, SECURITY_CSV_HEADERS_OLD, SECURITY_CSV_HEADERS_NEW,
    OUTPUT_CSV_HEADERS, NIFTY100_SECURITIES_FILE, OUTPUT_DIR,
    NIFTY100_CONSTITUENTS_URL, DEFAULT_CONSTITUENTS_DIR
)


class CSVHandler:
    """
    Service for handling CSV operations - reading securities and writing outputs
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_securities_from_csv(self, file_path: Optional[str] = None) -> List[Security]:
        """
        Load securities from CSV file
        
        Args:
            file_path: Path to CSV file (uses default if None)
            
        Returns:
            List of Security objects
        """
        if file_path is None:
            file_path = NIFTY100_SECURITIES_FILE
        
        self.logger.info(f"Loading securities from {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"Securities file not found: {file_path}")
            raise FileNotFoundError(f"Securities file not found: {file_path}")
        
        securities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate headers
                if not self._validate_security_headers(reader.fieldnames):
                    raise ValueError("Invalid CSV headers")
                
                for row_num, row in enumerate(reader, start=2):  # Start from 2 (after header)
                    try:
                        security = self._create_security_from_row(row)
                        securities.append(security)
                    except Exception as e:
                        self.logger.warning(f"Error processing row {row_num}: {str(e)}")
                        continue
            
            self.logger.info(f"Successfully loaded {len(securities)} securities")
            return securities
            
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {str(e)}")
            raise
    
    def filter_excluded_securities(self, securities: List[Security], exclusion_file: str) -> List[Security]:
        """
        Filter out excluded securities from the main securities list
        
        Args:
            securities: List of Security objects to filter
            exclusion_file: Path to exclusion list CSV file
            
        Returns:
            Filtered list of Security objects with exclusions removed
        """
        self.logger.info(f"Loading exclusion list from {exclusion_file}")
        
        if not os.path.exists(exclusion_file):
            self.logger.error(f"Exclusion file not found: {exclusion_file}")
            raise FileNotFoundError(f"Exclusion file not found: {exclusion_file}")
        
        # Load exclusion list
        excluded_securities = self.load_securities_from_csv(exclusion_file)
        
        # Create sets for efficient lookup
        excluded_symbols = {sec.symbol.upper() for sec in excluded_securities}
        excluded_isins = {sec.isin for sec in excluded_securities}
        
        self.logger.info(f"Loaded {len(excluded_securities)} securities to exclude")
        self.logger.info(f"Excluded symbols: {', '.join(sorted(excluded_symbols))}")
        
        # Filter out excluded securities
        original_count = len(securities)
        filtered_securities = []
        excluded_count = 0
        
        for security in securities:
            if (security.symbol.upper() in excluded_symbols or 
                security.isin in excluded_isins):
                self.logger.info(f"Excluding security: {security.symbol} ({security.company_name})")
                excluded_count += 1
            else:
                filtered_securities.append(security)
        
        self.logger.info(f"Filtered {excluded_count} securities from original {original_count}")
        self.logger.info(f"Remaining securities: {len(filtered_securities)}")
        
        return filtered_securities
    
    def save_portfolio_to_csv(self, portfolio: Portfolio, output_filename: Optional[str] = None) -> str:
        """
        Save portfolio allocation results to CSV
        
        Args:
            portfolio: Portfolio object with allocation results
            output_filename: Custom output filename (generated if None)
            
        Returns:
            Path to created output file
        """
        # Generate filename if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"nifty100_allocation_{timestamp}.csv"
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        self.logger.info(f"Saving portfolio allocation to {output_path}")
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_CSV_HEADERS)
                writer.writeheader()
                
                for allocation in portfolio.allocation_results:
                    row = self._create_output_row(allocation)
                    writer.writerow(row)
            
            # Save summary statistics
            self._save_portfolio_summary(portfolio, output_path)
            
            self.logger.info(f"Successfully saved {len(portfolio.allocation_results)} allocations to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error writing CSV file: {str(e)}")
            raise RuntimeError(f"Error writing CSV file: {str(e)}") from e
    
    def _validate_security_headers(self, headers: List[str]) -> bool:
        """Validate that CSV has required headers"""
        if not headers:
            return False
        
        file_headers = set(headers)
        
        # Check if it matches new format
        required_headers_new = set(SECURITY_CSV_HEADERS_NEW)
        if required_headers_new.issubset(file_headers):
            self.logger.info("Detected new CSV format")
            return True
        
        # Check if it matches old format
        required_headers_old = set(SECURITY_CSV_HEADERS_OLD)
        if required_headers_old.issubset(file_headers):
            self.logger.info("Detected old CSV format")
            return True
        
        # Neither format matches
        self.logger.error(f"CSV headers don't match expected format. Found: {list(headers)}")
        self.logger.error(f"Expected new format: {SECURITY_CSV_HEADERS_NEW}")
        self.logger.error(f"Expected old format: {SECURITY_CSV_HEADERS_OLD}")
        return False
    
    def _create_security_from_row(self, row: dict) -> Security:
        """Create Security object from CSV row"""
        try:
            # Detect format based on available columns
            if 'Symbol' in row and 'Company Name' in row:
                # New format
                security = Security(
                    symbol=row['Symbol'].strip(),
                    company_name=row['Company Name'].strip(),
                    isin=row['ISIN Code'].strip(),
                    market_cap=0.0,  # Default value for new format
                    weightage=1.0    # Default equal weight (1% for 100 securities)
                )
            else:
                # Old format
                security = Security(
                    symbol=row['symbol'].strip(),
                    company_name=row['company_name'].strip(),
                    isin=row['isin'].strip(),
                    market_cap=float(row['market_cap']) if row['market_cap'] else 0.0,
                    weightage=float(row['weightage']) if row['weightage'] else 0.0
                )
            
            # Check if CSV already contains financial data
            has_financial_data = False
            
            # Check for price data
            if 'price' in row and row['price'] and row['price'] != 'N/A':
                try:
                    price_value = float(row['price'])
                    if price_value > 0:
                        security.current_price = price_value
                        has_financial_data = True
                        self.logger.debug(f"Loaded price from CSV for {security.symbol}: ₹{price_value:.2f}")
                except (ValueError, TypeError):
                    self.logger.debug(f"Invalid price value in CSV for {security.symbol}: {row['price']}")
            
            # Check for P/E ratio data
            if 'pe_ratio' in row and row['pe_ratio'] and row['pe_ratio'] != 'N/A':
                try:
                    pe_value = float(row['pe_ratio'])
                    if pe_value > 0:
                        security.pe_ratio = pe_value
                        has_financial_data = True
                        self.logger.debug(f"Loaded P/E ratio from CSV for {security.symbol}: {pe_value:.2f}")
                except (ValueError, TypeError):
                    self.logger.debug(f"Invalid P/E ratio value in CSV for {security.symbol}: {row['pe_ratio']}")
            
            # Set flag if any financial data was loaded from CSV
            if has_financial_data:
                security.data_loaded_from_csv = True
                self.logger.info(f"Financial data loaded from CSV for {security.symbol}")
            
            return security
            
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid security data: {str(e)}") from e
    
    def _create_output_row(self, allocation) -> dict:
        """Create output CSV row from AllocationResult"""
        return {
            'company_name': allocation.security.company_name,
            'symbol': allocation.security.symbol,
            'current_price': f"{allocation.security.current_price:.2f}" if allocation.security.current_price else "N/A",
            'target_allocation_pct': f"{allocation.target_allocation_pct:.2f}",
            'target_amount': f"{allocation.target_amount:.2f}",
            'shares_to_buy': allocation.shares_to_buy,
            'actual_allocation_amount': f"{allocation.actual_allocation_amount:.2f}",
            'actual_allocation_pct': f"{allocation.actual_allocation_pct:.4f}",
            'unallocated_amount': f"{allocation.unallocated_amount:.2f}",
            'timestamp': allocation.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _save_portfolio_summary(self, portfolio: Portfolio, output_path: str):
        """Save portfolio summary to separate file"""
        summary_path = output_path.replace('.csv', '_summary.txt')
        
        stats = portfolio.get_summary_stats()
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("NIFTY 100 INDEX TRACKER - PORTFOLIO SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Investment Amount: ₹{stats['total_investment']:,.2f}\n")
            f.write(f"Total Allocated Amount:  ₹{stats['total_allocated']:,.2f}\n")
            f.write(f"Total Unallocated:       ₹{stats['total_unallocated']:,.2f}\n")
            f.write(f"Utilization Rate:        {stats['utilization_rate']:.2f}%\n\n")
            f.write(f"Total Shares to Buy:     {stats['total_shares']:,}\n")
            f.write(f"Successful Securities:   {stats['successful_securities']}\n")
            f.write(f"Failed Securities:       {stats['failed_securities']}\n")
            f.write(f"Success Rate:            {stats['success_rate']:.1f}%\n")
        
        self.logger.info(f"Portfolio summary saved to {summary_path}")
    
    def create_sample_securities_csv(self) -> str:
        """
        Create a sample securities CSV file with a few securities for testing
        """
        sample_data = [
            {
                'Company Name': 'Reliance Industries Limited',
                'Industry': 'Oil Gas & Consumable Fuels',
                'Symbol': 'RELIANCE',
                'Series': 'EQ',
                'ISIN Code': 'INE002A01018'
            },
            {
                'Company Name': 'Tata Consultancy Services Limited',
                'Industry': 'Information Technology',
                'Symbol': 'TCS',
                'Series': 'EQ',
                'ISIN Code': 'INE467B01029'
            },
            {
                'Company Name': 'Infosys Limited',
                'Industry': 'Information Technology',
                'Symbol': 'INFY',
                'Series': 'EQ',
                'ISIN Code': 'INE009A01021'
            },
            {
                'Company Name': 'HDFC Bank Limited',
                'Industry': 'Financial Services',
                'Symbol': 'HDFCBANK',
                'Series': 'EQ',
                'ISIN Code': 'INE040A01034'
            },
            {
                'Company Name': 'ICICI Bank Limited',
                'Industry': 'Financial Services',
                'Symbol': 'ICICIBANK',
                'Series': 'EQ',
                'ISIN Code': 'INE090A01021'
            }
        ]
        
        os.makedirs(os.path.dirname(NIFTY100_SECURITIES_FILE), exist_ok=True)
        
        with open(NIFTY100_SECURITIES_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=SECURITY_CSV_HEADERS)
            writer.writeheader()
            writer.writerows(sample_data)
        
        self.logger.info(f"Sample securities CSV created at {NIFTY100_SECURITIES_FILE}")
        return NIFTY100_SECURITIES_FILE
    
    def create_sample_exclusion_csv(self, exclusion_file: str = "data/sample_exclusions.csv") -> str:
        """
        Create a sample exclusion list CSV file for testing
        
        Args:
            exclusion_file: Path for the exclusion file (default: data/sample_exclusions.csv)
            
        Returns:
            Path to created exclusion file
        """
        sample_exclusion_data = [
            {
                'Company Name': 'Adani Enterprises Ltd.',
                'Industry': 'Metals & Mining',
                'Symbol': 'ADANIENT',
                'Series': 'EQ',
                'ISIN Code': 'INE423A01024'
            },
            {
                'Company Name': 'Adani Ports and Special Economic Zone Ltd.',
                'Industry': 'Services',
                'Symbol': 'ADANIPORTS',
                'Series': 'EQ',
                'ISIN Code': 'INE742F01042'
            }
        ]
        
        os.makedirs(os.path.dirname(exclusion_file), exist_ok=True)
        
        with open(exclusion_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=SECURITY_CSV_HEADERS)
            writer.writeheader()
            writer.writerows(sample_exclusion_data)
        
        self.logger.info(f"Sample exclusion CSV created at {exclusion_file}")
        return exclusion_file

    def hydrate_securities_data(self, input_file: str, output_file: Optional[str] = None) -> str:
        """
        Hydrate securities data with P/E ratios and prices
        
        Args:
            input_file: Path to input CSV file with securities data
            output_file: Path to output CSV file (generated if None)
            
        Returns:
            Path to created output file
        """
        from ..services.price_fetcher import PriceFetcher
        
        self.logger.info(f"Starting data hydration for {input_file}")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"data/output/{base_name}_hydrated_{timestamp}.csv"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Read original CSV data
        self.logger.info("Reading original securities data...")
        securities_data = []
        
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            original_headers = reader.fieldnames
            
            for row in reader:
                securities_data.append(row)
        
        self.logger.info(f"Loaded {len(securities_data)} securities from input file")
        
        # Initialize price fetcher
        price_fetcher = PriceFetcher()
        
        # Create enhanced data with P/E ratios and prices
        enhanced_data = []
        successful_fetches = 0
        
        for i, row in enumerate(securities_data, 1):
            symbol = row.get('Symbol') or row.get('symbol', '')
            
            self.logger.info(f"Processing {i}/{len(securities_data)}: {symbol}")
            
            # Fetch financial metrics
            metrics = price_fetcher.fetch_financial_metrics(symbol)
            
            # Create enhanced row
            enhanced_row = row.copy()
            
            if metrics:
                enhanced_row['pe_ratio'] = metrics.get('pe_ratio') or 'N/A'
                enhanced_row['price'] = metrics.get('current_price') or 'N/A'
                successful_fetches += 1
                self.logger.info(f"✓ {symbol}: P/E={enhanced_row['pe_ratio']}, Price=₹{enhanced_row['price']}")
            else:
                enhanced_row['pe_ratio'] = 'N/A'
                enhanced_row['price'] = 'N/A'
                self.logger.warning(f"✗ {symbol}: Failed to fetch data")
            
            enhanced_data.append(enhanced_row)
        
        # Write enhanced data to output file
        enhanced_headers = list(original_headers) + ['pe_ratio', 'price']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=enhanced_headers)
            writer.writeheader()
            writer.writerows(enhanced_data)
        
        success_rate = (successful_fetches / len(securities_data)) * 100
        self.logger.info(f"Data hydration completed: {successful_fetches}/{len(securities_data)} successful ({success_rate:.1f}%)")
        self.logger.info(f"Enhanced data saved to {output_file}")
        
        return output_file

    def save_portfolio_to_json(self, portfolio: Portfolio, base_filename: Optional[str] = None) -> List[str]:
        """
        Save portfolio allocation results to batched JSON files
        
        Args:
            portfolio: Portfolio object with allocation results
            base_filename: Base filename for JSON files (generated if None)
            
        Returns:
            List of paths to created JSON files
        """
        # Generate base filename if not provided
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"nifty100_allocation_{timestamp}"
        
        # Create JSON output directory
        json_output_dir = os.path.join(OUTPUT_DIR, "json_batches")
        os.makedirs(json_output_dir, exist_ok=True)
        
        self.logger.info(f"Saving portfolio allocation to JSON files in {json_output_dir}")
        
        # Filter successful allocations (securities with valid prices and shares to buy)
        successful_allocations = [
            allocation for allocation in portfolio.allocation_results
            if allocation.security.is_price_available() and allocation.shares_to_buy > 0
        ]
        
        if not successful_allocations:
            self.logger.warning("No successful allocations to save to JSON")
            return []
        
        # Batch allocations into groups of 20
        batch_size = 20
        batches = [
            successful_allocations[i:i + batch_size]
            for i in range(0, len(successful_allocations), batch_size)
        ]
        
        json_files = []
        
        for batch_num, batch in enumerate(batches, 1):
            # Create filename for this batch
            json_filename = f"{base_filename}_batch_{batch_num:02d}.json"
            json_path = os.path.join(json_output_dir, json_filename)
            
            # Create JSON data for this batch
            json_data = []
            
            for allocation in batch:
                order_entry = {
                    "instrument": {
                        "exchange": "NSE",
                        "symbol": allocation.security.symbol,
                        "tradingsymbol": allocation.security.symbol,
                        "type": "EQ"
                    },
                    "params": {
                        "disclosedQuantity": 0,
                        "gtt": None,
                        "orderType": "MARKET",
                        "price": 0,
                        "product": "CNC",
                        "quantity": allocation.shares_to_buy,
                        "tags": [],
                        "transactionType": "BUY",
                        "triggerPrice": 0,
                        "validity": "DAY",
                        "validityTTL": 1,
                        "variety": "regular"
                    },
                    "weight": 0
                }
                json_data.append(order_entry)
            
            # Write JSON file
            try:
                with open(json_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
                
                json_files.append(json_path)
                self.logger.info(f"Saved batch {batch_num}/{len(batches)} with {len(batch)} securities to {json_filename}")
                
            except Exception as e:
                self.logger.error(f"Error writing JSON file {json_path}: {str(e)}")
                continue
        
        total_securities = sum(len(batch) for batch in batches)
        self.logger.info(f"Successfully created {len(json_files)} JSON batch files with {total_securities} total securities")
        
        return json_files

    def download_nifty100_constituents(self, destination_dir: Optional[str] = None) -> str:
        """
        Download the official Nifty 100 constituents CSV file from NSE website

        Args:
            destination_dir: Directory to save the file (uses default if None)

        Returns:
            Path to downloaded file
        """
        if destination_dir is None:
            destination_dir = DEFAULT_CONSTITUENTS_DIR

        # Ensure destination directory exists
        os.makedirs(destination_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ind_nifty100list_{timestamp}.csv"
        output_path = os.path.join(destination_dir, filename)

        self.logger.info(f"Downloading Nifty 100 constituents from {NIFTY100_CONSTITUENTS_URL}")
        self.logger.info(f"Saving to: {output_path}")

        try:
            # Download the file with proper headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(NIFTY100_CONSTITUENTS_URL, headers=headers, timeout=30)
            response.raise_for_status()  # Raises an HTTPError for bad responses

            # Check if the response contains CSV data
            content_type = response.headers.get('content-type', '').lower()
            if 'text/csv' not in content_type and 'application/csv' not in content_type:
                # Check if content looks like CSV by examining first few lines
                content_preview = response.text[:500]
                if ',' not in content_preview or 'Company Name' not in content_preview:
                    raise ValueError(f"Downloaded content does not appear to be CSV data. Content-Type: {content_type}")

            # Save the downloaded content
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                f.write(response.text)

            # Validate the downloaded file by trying to read it
            self._validate_downloaded_csv(output_path)

            self.logger.info(f"✓ Successfully downloaded Nifty 100 constituents to {output_path}")
            self.logger.info(f"File size: {len(response.text):,} characters")

            return output_path

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while downloading Nifty 100 constituents: {str(e)}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Error downloading Nifty 100 constituents: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _validate_downloaded_csv(self, file_path: str):
        """
        Validate that the downloaded file is a proper CSV with expected structure

        Args:
            file_path: Path to the CSV file to validate
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames

                # Check for expected headers
                expected_headers = ['Company Name', 'Symbol', 'ISIN Code']
                missing_headers = [h for h in expected_headers if h not in headers]

                if missing_headers:
                    raise ValueError(f"Downloaded CSV is missing expected headers: {missing_headers}")

                # Try to read at least one row to ensure file is not empty/corrupt
                first_row = next(reader, None)
                if not first_row:
                    raise ValueError("Downloaded CSV file appears to be empty")

                self.logger.info(f"✓ CSV validation passed. Headers: {list(headers)}")

        except Exception as e:
            self.logger.error(f"CSV validation failed: {str(e)}")
            raise