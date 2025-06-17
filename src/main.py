#!/usr/bin/env python3
"""
Nifty 100 Index Tracker - Main Application

This application replicates the Nifty 100 index by creating proportional buy orders
based on user-specified investment amounts.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.csv_handler import CSVHandler
from src.services.price_fetcher import PriceFetcher
from src.services.allocator import Allocator
from src.utils.helpers import setup_logging, print_separator, print_summary_table, parse_user_input
from src.utils.validators import validate_investment_amount
from config.settings import MIN_INVESTMENT_AMOUNT


class Nifty100Tracker:
    """
    Main application class for Nifty 100 Index Tracker
    """
    
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.price_fetcher = PriceFetcher()
        self.allocator = Allocator()
        self.logger = logging.getLogger(__name__)
    
    def run(self, investment_amount: float, securities_file: str = None, exclusion_file: str = None) -> str:
        """
        Run the complete index tracking process
        
        Args:
            investment_amount: Total amount to invest in INR
            securities_file: Path to securities CSV file (optional)
            exclusion_file: Path to exclusion list CSV file (optional)
            
        Returns:
            Path to generated output file
        """
        try:
            print_separator("NIFTY 100 INDEX TRACKER", "=", 60)
            print(f"Investment Amount: ₹{investment_amount:,.2f}")
            print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if exclusion_file:
                print(f"Exclusion List: {exclusion_file}")
            print_separator()
            
            # Step 1: Load securities
            self.logger.info("Step 1: Loading securities data")
            securities = self.csv_handler.load_securities_from_csv(securities_file)
            print(f"✓ Loaded {len(securities)} securities")
            
            # Step 1.5: Filter out excluded securities if exclusion list provided
            if exclusion_file:
                self.logger.info("Step 1.5: Filtering excluded securities")
                securities = self.csv_handler.filter_excluded_securities(securities, exclusion_file)
                print(f"✓ Filtered securities: {len(securities)} remaining after exclusions")
            
            # Step 2: Fetch current prices
            self.logger.info("Step 2: Fetching current market prices")
            print("\nFetching current market prices...")
            securities_with_prices = self.price_fetcher.fetch_prices_batch(securities)
            
            # Price fetch summary
            fetch_summary = self.price_fetcher.get_fetch_summary()
            print(f"\n✓ Price fetch completed: {fetch_summary['successful_fetches']}/{fetch_summary['total_securities']} successful ({fetch_summary['success_rate']:.1f}%)")
            
            if fetch_summary['failed_securities'] > 0:
                print(f"⚠ Failed to fetch prices for {fetch_summary['failed_securities']} securities")
                if fetch_summary['failed_symbols']:
                    print(f"Failed symbols: {', '.join(fetch_summary['failed_symbols'])}")
            
            # Step 3: Calculate allocations
            self.logger.info("Step 3: Calculating portfolio allocations")
            print("\nCalculating portfolio allocations...")
            portfolio = self.allocator.calculate_equal_weight_allocation(securities_with_prices, investment_amount)
            
            # Step 4: Generate output
            self.logger.info("Step 4: Generating output files")
            print("\nGenerating output files...")
            output_file = self.csv_handler.save_portfolio_to_csv(portfolio)
            
            # Display summary
            self._display_results_summary(portfolio, output_file)
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            raise
    
    def _display_results_summary(self, portfolio, output_file: str):
        """Display final results summary"""
        stats = portfolio.get_summary_stats()
        
        print_separator("RESULTS SUMMARY", "=", 60)
        print_summary_table(stats, "Portfolio Statistics")
        
        print(f"\n📁 Output Files Generated:")
        print(f"   • Portfolio Details: {output_file}")
        print(f"   • Summary Report: {output_file.replace('.csv', '_summary.txt')}")
        
        # Display top allocations
        successful_allocations = [a for a in portfolio.allocation_results if a.security.is_price_available()]
        if successful_allocations:
            print(f"\n📊 Sample Allocations (First 5):")
            for i, allocation in enumerate(successful_allocations[:5], 1):
                print(f"   {i}. {allocation.security.symbol:<12} - "
                      f"{allocation.shares_to_buy:>4} shares @ ₹{allocation.security.current_price:>8.2f} = "
                      f"₹{allocation.actual_allocation_amount:>10,.2f}")
        
        print_separator()


def create_sample_data():
    """Create sample securities data file for testing"""
    csv_handler = CSVHandler()
    csv_handler.create_sample_securities_csv()
    print("✓ Sample securities data created")


def create_sample_exclusion_data():
    """Create sample exclusion list data file for testing"""
    csv_handler = CSVHandler()
    exclusion_file = csv_handler.create_sample_exclusion_csv()
    print(f"✓ Sample exclusion data created at {exclusion_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Nifty 100 Index Tracker - Generate proportional buy orders for index replication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --amount 100000                    # Invest ₹1,00,000
  %(prog)s --amount 50000 --securities data/custom.csv  # Use custom securities file
  %(prog)s --amount 100000 --exclusion data/exclusions.csv  # Exclude specific securities
  %(prog)s --create-sample                    # Create sample data file
  %(prog)s --create-exclusion-sample          # Create sample exclusion file
  %(prog)s --interactive                      # Interactive mode
        """
    )
    
    parser.add_argument(
        '--amount', '-a',
        type=float,
        help=f'Investment amount in INR (minimum ₹{MIN_INVESTMENT_AMOUNT:,})'
    )
    
    parser.add_argument(
        '--securities', '-s',
        type=str,
        help='Path to securities CSV file (optional)'
    )
    
    parser.add_argument(
        '--exclusion', '-e',
        type=str,
        help='Path to exclusion list CSV file (optional)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create sample securities CSV file and exit'
    )
    
    parser.add_argument(
        '--create-exclusion-sample',
        action='store_true',
        help='Create sample exclusion list CSV file and exit'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path (optional)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Handle sample data creation
    if args.create_sample:
        create_sample_data()
        return
    
    # Handle sample exclusion data creation
    if args.create_exclusion_sample:
        create_sample_exclusion_data()
        return
    
    # Get investment amount
    if args.interactive or args.amount is None:
        print_separator("NIFTY 100 INDEX TRACKER", "=", 60)
        print("Welcome to the Nifty 100 Index Tracker!")
        print("This tool helps you create buy orders to replicate the Nifty 100 index.")
        print_separator()
        
        amount = parse_user_input(
            f"Enter investment amount (minimum ₹{MIN_INVESTMENT_AMOUNT:,}): ₹",
            float
        )
    else:
        amount = args.amount
    
    # Validate investment amount
    is_valid, error_msg = validate_investment_amount(amount)
    if not is_valid:
        print(f"❌ {error_msg}")
        sys.exit(1)
    
    # Run the tracker
    try:
        tracker = Nifty100Tracker()
        output_file = tracker.run(amount, args.securities, args.exclusion)
        
        print(f"\n🎉 Index tracking completed successfully!")
        print(f"📁 Output saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n\n⏹ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Application failed: {str(e)}")
        logging.error(f"Application failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 