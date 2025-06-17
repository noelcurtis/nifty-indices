"""
Portfolio model for managing investment allocation and buy orders
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import math

from .security import Security


@dataclass
class AllocationResult:
    """
    Represents the allocation result for a single security
    """
    security: Security
    target_allocation_pct: float
    target_amount: float
    shares_to_buy: int
    actual_allocation_amount: float
    actual_allocation_pct: float
    unallocated_amount: float
    timestamp: datetime


@dataclass
class Portfolio:
    """
    Represents a portfolio with allocation results and summary statistics
    """
    total_investment: float
    allocation_results: List[AllocationResult] = field(default_factory=list)
    
    def add_allocation(self, allocation: AllocationResult):
        """Add an allocation result to the portfolio"""
        self.allocation_results.append(allocation)
    
    @property
    def total_allocated_amount(self) -> float:
        """Calculate total amount actually allocated"""
        return sum(result.actual_allocation_amount for result in self.allocation_results)
    
    @property
    def total_unallocated_amount(self) -> float:
        """Calculate total unallocated amount due to fractional shares"""
        return sum(result.unallocated_amount for result in self.allocation_results)
    
    @property
    def total_shares_to_buy(self) -> int:
        """Calculate total number of shares to buy across all securities"""
        return sum(result.shares_to_buy for result in self.allocation_results)
    
    @property
    def successful_allocations(self) -> int:
        """Count of securities with successful price fetch and allocation"""
        return len([r for r in self.allocation_results if r.security.is_price_available()])
    
    @property
    def failed_allocations(self) -> int:
        """Count of securities that failed price fetch"""
        return len([r for r in self.allocation_results if not r.security.is_price_available()])
    
    def get_summary_stats(self) -> Dict:
        """Get portfolio summary statistics"""
        return {
            "total_investment": self.total_investment,
            "total_allocated": self.total_allocated_amount,
            "total_unallocated": self.total_unallocated_amount,
            "utilization_rate": (self.total_allocated_amount / self.total_investment) * 100,
            "total_shares": self.total_shares_to_buy,
            "successful_securities": self.successful_allocations,
            "failed_securities": self.failed_allocations,
            "success_rate": (self.successful_allocations / len(self.allocation_results)) * 100 if self.allocation_results else 0
        }
    
    def __str__(self) -> str:
        stats = self.get_summary_stats()
        return f"Portfolio: ₹{stats['total_investment']:,.2f} investment, {stats['successful_securities']} securities, ₹{stats['total_allocated']:,.2f} allocated" 