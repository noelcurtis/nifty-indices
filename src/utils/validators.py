"""
Validation utilities for input data and constraints
"""

import re
from typing import Union


def validate_investment_amount(amount: Union[str, float, int]) -> tuple[bool, str]:
    """
    Validate investment amount
    
    Args:
        amount: Investment amount to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        return False, "Investment amount must be a valid number"
    
    if amount_float <= 0:
        return False, "Investment amount must be positive"
    
    from config.settings import MIN_INVESTMENT_AMOUNT, MAX_INVESTMENT_AMOUNT
    
    if amount_float < MIN_INVESTMENT_AMOUNT:
        return False, f"Investment amount must be at least ₹{MIN_INVESTMENT_AMOUNT:,.2f}"
    
    if amount_float > MAX_INVESTMENT_AMOUNT:
        return False, f"Investment amount cannot exceed ₹{MAX_INVESTMENT_AMOUNT:,.2f}"
    
    return True, ""


def validate_symbol(symbol: str) -> tuple[bool, str]:
    """
    Validate NSE trading symbol format
    
    Args:
        symbol: Trading symbol to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symbol or not isinstance(symbol, str):
        return False, "Symbol cannot be empty"
    
    symbol = symbol.strip().upper()
    
    # Basic NSE symbol validation - alphanumeric, hyphens allowed
    if not re.match(r'^[A-Z0-9\-&]+$', symbol):
        return False, "Invalid symbol format"
    
    if len(symbol) < 1 or len(symbol) > 20:
        return False, "Symbol length must be between 1 and 20 characters"
    
    return True, ""


def validate_isin(isin: str) -> tuple[bool, str]:
    """
    Validate ISIN format
    
    Args:
        isin: ISIN to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isin or not isinstance(isin, str):
        return False, "ISIN cannot be empty"
    
    isin = isin.strip().upper()
    
    # ISIN format: 2 letters + 9 alphanumeric + 1 check digit
    if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin):
        return False, "Invalid ISIN format (should be 12 characters: 2 letters + 9 alphanumeric + 1 digit)"
    
    return True, ""


def validate_percentage(percentage: Union[str, float, int]) -> tuple[bool, str]:
    """
    Validate percentage value
    
    Args:
        percentage: Percentage to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        pct_float = float(percentage)
    except (ValueError, TypeError):
        return False, "Percentage must be a valid number"
    
    if pct_float < 0:
        return False, "Percentage cannot be negative"
    
    if pct_float > 100:
        return False, "Percentage cannot exceed 100%"
    
    return True, "" 