"""
Helper utilities for formatting, logging, and common operations
"""

import logging
import sys
from datetime import datetime
from typing import Union


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def format_currency(amount: Union[float, int], currency_symbol: str = "₹") -> str:
    """
    Format amount as currency with proper thousands separators
    
    Args:
        amount: Amount to format
        currency_symbol: Currency symbol to use
        
    Returns:
        Formatted currency string
    """
    return f"{currency_symbol}{amount:,.2f}"


def format_percentage(value: Union[float, int], decimal_places: int = 2) -> str:
    """
    Format value as percentage
    
    Args:
        value: Value to format
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimal_places}f}%"


def format_number(value: Union[float, int], thousands_separator: bool = True) -> str:
    """
    Format number with optional thousands separator
    
    Args:
        value: Number to format
        thousands_separator: Whether to use thousands separator
        
    Returns:
        Formatted number string
    """
    if thousands_separator:
        return f"{value:,}"
    return str(value)


def safe_divide(numerator: Union[float, int], denominator: Union[float, int], default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division by zero
        
    Returns:
        Division result or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator


def print_separator(title: str = "", char: str = "=", width: int = 60) -> None:
    """
    Print a formatted separator line with optional title
    
    Args:
        title: Optional title to center in separator
        char: Character to use for separator
        width: Total width of separator
    """
    if title:
        title = f" {title} "
        remaining_width = width - len(title)
        left_padding = remaining_width // 2
        right_padding = remaining_width - left_padding
        print(f"{char * left_padding}{title}{char * right_padding}")
    else:
        print(char * width)


def print_summary_table(stats: dict, title: str = "Summary") -> None:
    """
    Print a formatted summary table
    
    Args:
        stats: Dictionary of statistics to display
        title: Table title
    """
    print_separator(title)
    
    # Calculate max key length for alignment
    max_key_length = max(len(str(key)) for key in stats.keys()) if stats else 0
    
    for key, value in stats.items():
        formatted_key = str(key).replace('_', ' ').title()
        
        # Format value based on type
        if isinstance(value, float):
            if 'rate' in key.lower() or 'percentage' in key.lower():
                formatted_value = format_percentage(value)
            elif 'amount' in key.lower() or 'investment' in key.lower():
                formatted_value = format_currency(value)
            else:
                formatted_value = f"{value:,.2f}"
        elif isinstance(value, int):
            formatted_value = format_number(value)
        else:
            formatted_value = str(value)
        
        print(f"{formatted_key:<{max_key_length + 2}}: {formatted_value}")
    
    print_separator()


def get_timestamp_string(format_string: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get current timestamp as formatted string
    
    Args:
        format_string: strftime format string
        
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_string)


def parse_user_input(prompt: str, input_type: type = str, default=None):
    """
    Parse user input with type conversion and default value
    
    Args:
        prompt: Input prompt to display
        input_type: Type to convert input to
        default: Default value if input is empty
        
    Returns:
        Parsed input value
    """
    while True:
        try:
            user_input = input(prompt).strip()
            
            if not user_input and default is not None:
                return default
            
            if input_type == str:
                return user_input
            elif input_type == float:
                return float(user_input)
            elif input_type == int:
                return int(user_input)
            else:
                return input_type(user_input)
                
        except ValueError:
            print(f"Invalid input. Please enter a valid {input_type.__name__}.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0) 