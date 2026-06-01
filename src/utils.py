"""
Utility functions for Web Scraping Project
Includes retry logic, delays, and validation helpers
"""

import time
import random
from typing import Callable, Any, TypeVar
from functools import wraps

T = TypeVar('T')


def retry_with_backoff(func: Callable[..., T], max_attempts: int = 3, 
                       initial_delay: float = 1.0, backoff_factor: float = 2.0) -> T:
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Callable to execute
        max_attempts: Maximum number of attempts (default 3)
        initial_delay: Initial delay in seconds (default 1.0)
        backoff_factor: Multiplier for delay between attempts (default 2.0)
    
    Returns:
        Result of function execution
    
    Raises:
        Exception: If all attempts fail, raises the last exception
    
    Example:
        >>> result = retry_with_backoff(
        ...     lambda: requests.get('https://api.example.com'),
        ...     max_attempts=3,
        ...     initial_delay=1.0
        ... )
    """
    attempt = 0
    current_delay = initial_delay
    
    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            time.sleep(current_delay)
            current_delay *= backoff_factor


def retry_decorator(max_attempts: int = 3, initial_delay: float = 1.0, 
                   backoff_factor: float = 2.0) -> Callable:
    """
    Decorator version of retry_with_backoff for use with functions.
    
    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay between attempts
    
    Returns:
        Decorator function
    
    Example:
        @retry_decorator(max_attempts=3, initial_delay=1.0)
        def fetch_data():
            return requests.get('https://api.example.com')
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor
            )
        return wrapper
    return decorator


def delay_random(min_sec: float = 0.5, max_sec: float = 2.0) -> None:
    """
    Sleep for a random duration between min and max seconds.
    Useful for rate limiting between API requests.
    
    Args:
        min_sec: Minimum delay in seconds (default 0.5)
        max_sec: Maximum delay in seconds (default 2.0)
    
    Example:
        >>> delay_random(0.5, 2.0)  # Random delay between 0.5s and 2.0s
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def normalize_column_names(columns: list) -> list:
    """
    Normalize column names by stripping whitespace and standardizing.
    
    Args:
        columns: List of column names
    
    Returns:
        List of normalized column names
    
    Example:
        >>> normalize_column_names(['Produto ', ' Descrição 1', 'Desc 2'])
        ['Produto', 'Descrição 1', 'Desc 2']
    """
    return [col.strip() if isinstance(col, str) else col for col in columns]


def extract_description_number(col_name: str) -> int | None:
    """
    Extract description number from column name.
    
    Args:
        col_name: Column name (e.g., "Descrição 5", "Description 3")
    
    Returns:
        Description number (1-10) or None if not a description column
    
    Example:
        >>> extract_description_number('Descrição 5')
        5
        >>> extract_description_number('Produto')
        None
    """
    col_lower = col_name.lower().strip()
    
    # Check Portuguese variants
    if col_lower.__contains__('descrição'):
        # Extract the number at the end
        words = col_lower.split()
        for word in reversed(words):
            if word.isdigit():
                return int(word)
    
    return None


def is_description_column(col_name: str) -> bool:
    """
    Check if column name is a description column.
    
    Args:
        col_name: Column name to check
    
    Returns:
        True if column is a description (Descrição N or Description N), False otherwise
    
    Example:
        >>> is_description_column('Descrição 1')
        True
        >>> is_description_column('Produto')
        False
    """
    return extract_description_number(col_name) is not None


def concatenate_product_info(produto: str, descricoes: list[str]) -> str:
    """
    Concatenate product name with descriptions, ignoring empty values.
    
    Args:
        produto: Product name (required)
        descricoes: List of description strings (may contain empty/None values)
    
    Returns:
        Concatenated string with spaces, empty values filtered out
    
    Example:
        >>> concatenate_product_info('Luva', ['correr', '20mm', '', None, 'pvc'])
        'Luva correr 20mm pvc'
    """
    # Filter out empty strings and None values
    parts = [str(item).strip() for item in [produto] + descricoes 
             if item is not None and str(item).strip()]
    
    return ' '.join(parts)
