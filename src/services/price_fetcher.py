"""
Price fetching service using yfinance library for NSE data
"""

import logging
import time
from typing import List, Optional
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    logging.warning("yfinance not installed. Price fetching will not work.")
    yf = None

from ..models.security import Security
from config.settings import PRICE_FETCH_TIMEOUT, MAX_RETRIES, RETRY_DELAY


class PriceFetcher:
    """
    Service for fetching real-time prices from NSE using yfinance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.failed_securities = []
        self.successful_fetches = 0
        self.total_fetches = 0
    
    def fetch_price(self, symbol: str, retries: int = MAX_RETRIES) -> Optional[float]:
        """
        Fetch current price for a single security using yfinance
        
        Args:
            symbol: NSE trading symbol
            retries: Number of retry attempts
            
        Returns:
            Last available price from recent trading data or None if failed
        """
        if yf is None:
            self.logger.error("yfinance not available. Cannot fetch prices.")
            return None
        
        for attempt in range(retries + 1):
            try:
                self.logger.debug(f"Fetching price for {symbol} (attempt {attempt + 1})")
                
                # For NSE stocks, yfinance requires .NS suffix
                yf_symbol = symbol if symbol.endswith('.NS') else f"{symbol}.NS"
                
                self.logger.debug(f"Using yfinance symbol: {yf_symbol}")
                
                # Create ticker object
                ticker = yf.Ticker(yf_symbol)
                
                # Get recent historical data (last 30 days)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                self.logger.debug(f"Fetching history for {yf_symbol} from {start_date.date()} to {end_date.date()}")
                
                # Fetch historical data
                history_data = ticker.history(start=start_date, end=end_date)
                
                self.logger.debug(f"History data type: {type(history_data)}")
                self.logger.debug(f"History data shape: {history_data.shape if history_data is not None else 'None'}")
                
                if history_data is not None and not history_data.empty:
                    self.logger.debug(f"Available columns: {list(history_data.columns)}")
                    self.logger.debug(f"Last few rows:\n{history_data.tail()}")
                    
                    # Get the last available close price
                    last_price = history_data['Close'].iloc[-1]
                    
                    if last_price > 0:
                        last_date = history_data.index[-1].date()
                        self.logger.info(f"Successfully fetched price for {symbol}: ₹{last_price:.2f} (from {last_date})")
                        return float(last_price)
                    else:
                        self.logger.warning(f"Invalid price for {symbol}: {last_price}")
                else:
                    self.logger.warning(f"No historical data available for {yf_symbol}")
                    
                    # If original symbol didn't have .NS, we already tried with it
                    # Try without .NS if we originally added it
                    if symbol.endswith('.NS'):
                        original_symbol = symbol[:-3]  # Remove .NS
                        self.logger.info(f"Retrying without .NS suffix: {original_symbol}")
                        
                        ticker_no_ns = yf.Ticker(original_symbol)
                        history_data_no_ns = ticker_no_ns.history(start=start_date, end=end_date)
                        
                        if history_data_no_ns is not None and not history_data_no_ns.empty:
                            last_price = history_data_no_ns['Close'].iloc[-1]
                            if last_price > 0:
                                last_date = history_data_no_ns.index[-1].date()
                                self.logger.info(f"Successfully fetched price for {original_symbol}: ₹{last_price:.2f} (from {last_date})")
                                return float(last_price)
                        else:
                            self.logger.warning(f"No data for {original_symbol} either")
                
            except Exception as e:
                self.logger.warning(f"Error fetching price for {symbol} (attempt {attempt + 1}): {str(e)}")
                
                if attempt < retries:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    self.logger.error(f"Failed to fetch price for {symbol} after {retries + 1} attempts")
                    break
        
        return None
    
    def fetch_prices_batch(self, securities: List[Security]) -> List[Security]:
        """
        Fetch prices for a batch of securities
        
        Args:
            securities: List of Security objects
            
        Returns:
            List of Security objects with updated prices
        """
        self.logger.info(f"Starting batch price fetch for {len(securities)} securities")
        self.total_fetches = len(securities)
        self.successful_fetches = 0
        self.failed_securities = []
        
        updated_securities = []
        
        for i, security in enumerate(securities, 1):
            self.logger.info(f"Fetching price {i}/{len(securities)}: {security.symbol}")
            
            price = self.fetch_price(security.symbol)
            
            if price is not None:
                security.current_price = price
                self.successful_fetches += 1
                self.logger.info(f"✓ {security.symbol}: ₹{price:.2f}")
            else:
                self.failed_securities.append(security.symbol)
                self.logger.error(f"✗ {security.symbol}: Price fetch failed")
            
            updated_securities.append(security)
            
            # Small delay between requests to avoid overwhelming the API
            time.sleep(0.1)
        
        success_rate = (self.successful_fetches / self.total_fetches) * 100
        self.logger.info(f"Batch fetch completed: {self.successful_fetches}/{self.total_fetches} successful ({success_rate:.1f}%)")
        
        if self.failed_securities:
            self.logger.warning(f"Failed securities: {', '.join(self.failed_securities)}")
        
        return updated_securities
    
    def get_fetch_summary(self) -> dict:
        """Get summary of the last batch fetch operation"""
        return {
            "total_securities": self.total_fetches,
            "successful_fetches": self.successful_fetches,
            "failed_securities": len(self.failed_securities),
            "success_rate": (self.successful_fetches / self.total_fetches) * 100 if self.total_fetches > 0 else 0,
            "failed_symbols": self.failed_securities.copy()
        } 