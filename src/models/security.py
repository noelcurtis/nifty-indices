"""
Security model for representing individual stocks in the Nifty 100 index
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Security:
    """
    Represents a security in the Nifty 100 index
    
    Attributes:
        symbol: Trading symbol (NSE format)
        company_name: Full company name
        isin: International Securities Identification Number
        market_cap: Market capitalization
        weightage: Index weightage percentage
        current_price: Current market price (fetched dynamically)
    """
    symbol: str
    company_name: str
    isin: str
    market_cap: float
    weightage: float
    current_price: Optional[float] = None
    
    def __post_init__(self):
        """Validate security data after initialization"""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.company_name:
            raise ValueError("Company name cannot be empty")
        if self.weightage < 0:
            raise ValueError("Weightage cannot be negative")
    
    def is_price_available(self) -> bool:
        """Check if current price is available"""
        return self.current_price is not None and self.current_price > 0
    
    def __str__(self) -> str:
        return f"{self.symbol} - {self.company_name}"
    
    def __repr__(self) -> str:
        return f"Security(symbol='{self.symbol}', company_name='{self.company_name}', current_price={self.current_price})" 