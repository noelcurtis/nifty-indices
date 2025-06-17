"""
CSV handling service for reading securities data and writing output files
"""

import csv
import logging
import os
from typing import List, Optional
from datetime import datetime
import pandas as pd

from ..models.security import Security
from ..models.portfolio import Portfolio
from config.settings import (
    SECURITY_CSV_HEADERS, SECURITY_CSV_HEADERS_OLD, SECURITY_CSV_HEADERS_NEW,
    OUTPUT_CSV_HEADERS, NIFTY100_SECURITIES_FILE, OUTPUT_DIR
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
            raise
    
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
                return Security(
                    symbol=row['Symbol'].strip(),
                    company_name=row['Company Name'].strip(),
                    isin=row['ISIN Code'].strip(),
                    market_cap=0.0,  # Default value for new format
                    weightage=1.0    # Default equal weight (1% for 100 securities)
                )
            else:
                # Old format
                return Security(
                    symbol=row['symbol'].strip(),
                    company_name=row['company_name'].strip(),
                    isin=row['isin'].strip(),
                    market_cap=float(row['market_cap']) if row['market_cap'] else 0.0,
                    weightage=float(row['weightage']) if row['weightage'] else 0.0
                )
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid security data: {str(e)}")
    
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