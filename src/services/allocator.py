"""
Portfolio allocation service for calculating buy orders
"""

import logging
import math
from typing import List
from datetime import datetime

from ..models.security import Security
from ..models.portfolio import Portfolio, AllocationResult
from config.settings import EQUAL_WEIGHT_PERCENTAGE, TOTAL_SECURITIES


class Allocator:
    """
    Service for calculating portfolio allocations and buy orders
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_equal_weight_allocation(self, securities: List[Security], total_investment: float) -> Portfolio:
        """
        Calculate equal weight allocation for all securities
        
        Args:
            securities: List of Security objects with current prices
            total_investment: Total amount to invest in INR
            
        Returns:
            Portfolio object with allocation results
        """
        self.logger.info(f"Calculating equal weight allocation for ₹{total_investment:,.2f}")
        
        portfolio = Portfolio(total_investment=total_investment)
        
        # Calculate per-security allocation amount based on actual number of securities
        num_securities = len(securities)
        per_security_amount = total_investment / num_securities
        allocation_percentage = 100.0 / num_securities  # Equal weight percentage
        
        self.logger.info(f"Target allocation per security: ₹{per_security_amount:,.2f} ({allocation_percentage:.4f}%) for {num_securities} securities")
        
        timestamp = datetime.now()
        
        for security in securities:
            allocation_result = self._calculate_security_allocation(
                security, 
                per_security_amount, 
                allocation_percentage, 
                total_investment,
                timestamp
            )
            portfolio.add_allocation(allocation_result)
        
        # Log summary
        stats = portfolio.get_summary_stats()
        self.logger.info(f"Allocation completed:")
        self.logger.info(f"  - Total investment: ₹{stats['total_investment']:,.2f}")
        self.logger.info(f"  - Total allocated: ₹{stats['total_allocated']:,.2f}")
        self.logger.info(f"  - Total unallocated: ₹{stats['total_unallocated']:,.2f}")
        self.logger.info(f"  - Utilization rate: {stats['utilization_rate']:.2f}%")
        self.logger.info(f"  - Successful securities: {stats['successful_securities']}/{len(securities)}")
        
        return portfolio
    
    def _calculate_security_allocation(
        self, 
        security: Security, 
        target_amount: float, 
        target_pct: float,
        total_investment: float,
        timestamp: datetime
    ) -> AllocationResult:
        """
        Calculate allocation for a single security
        
        Args:
            security: Security object
            target_amount: Target allocation amount in INR
            target_pct: Target allocation percentage
            total_investment: Total portfolio investment
            timestamp: Allocation timestamp
            
        Returns:
            AllocationResult object
        """
        if not security.is_price_available():
            # Handle securities without prices
            self.logger.warning(f"No price available for {security.symbol}")
            return AllocationResult(
                security=security,
                target_allocation_pct=target_pct,
                target_amount=target_amount,
                shares_to_buy=0,
                actual_allocation_amount=0.0,
                actual_allocation_pct=0.0,
                unallocated_amount=target_amount,
                timestamp=timestamp
            )
        
        # Calculate shares to buy (round down to avoid over-investment)
        shares_to_buy = math.floor(target_amount / security.current_price)
        
        # Calculate actual allocation
        actual_allocation_amount = shares_to_buy * security.current_price
        actual_allocation_pct = (actual_allocation_amount / total_investment) * 100
        unallocated_amount = target_amount - actual_allocation_amount
        
        self.logger.debug(
            f"{security.symbol}: Target ₹{target_amount:.2f} → "
            f"{shares_to_buy} shares @ ₹{security.current_price:.2f} = "
            f"₹{actual_allocation_amount:.2f} (unallocated: ₹{unallocated_amount:.2f})"
        )
        
        return AllocationResult(
            security=security,
            target_allocation_pct=target_pct,
            target_amount=target_amount,
            shares_to_buy=shares_to_buy,
            actual_allocation_amount=actual_allocation_amount,
            actual_allocation_pct=actual_allocation_pct,
            unallocated_amount=unallocated_amount,
            timestamp=timestamp
        )
    
    def validate_investment_amount(self, amount: float) -> bool:
        """
        Validate investment amount against constraints
        
        Args:
            amount: Investment amount in INR
            
        Returns:
            True if valid, False otherwise
        """
        from config.settings import MIN_INVESTMENT_AMOUNT, MAX_INVESTMENT_AMOUNT
        
        if amount < MIN_INVESTMENT_AMOUNT:
            self.logger.error(f"Investment amount ₹{amount:,.2f} is below minimum ₹{MIN_INVESTMENT_AMOUNT:,.2f}")
            return False
        
        if amount > MAX_INVESTMENT_AMOUNT:
            self.logger.error(f"Investment amount ₹{amount:,.2f} exceeds maximum ₹{MAX_INVESTMENT_AMOUNT:,.2f}")
            return False
        
        return True 