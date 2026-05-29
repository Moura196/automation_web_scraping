"""
Product query builder module for Web Scraping Project
Builds search queries by concatenating product info with descriptions
"""

import pandas as pd
import logging
from typing import List, Tuple
from .logger import get_logger
from .utils import concatenate_product_info

logger = get_logger(__name__)


def build_query_from_row(produto: str, descricoes: List[str]) -> str:
    """
    Build search query from product name and descriptions.
    
    Intelligently concatenates non-empty values, filters out empty cells.
    
    Args:
        produto: Product name (required)
        descricoes: List of description strings (may contain empty values)
    
    Returns:
        Concatenated query string, spaces normalized
    
    Example:
        >>> build_query_from_row('Luva', ['correr', '20mm', '', None, 'pvc'])
        'Luva correr 20mm pvc'
        
        >>> build_query_from_row('Luva', ['', '', ''])
        'Luva'
    """
    return concatenate_product_info(produto, descricoes)


def build_queries_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build search queries for all products in dataframe.
    
    Adds 'Query' column with concatenated product + descriptions.
    
    Args:
        df: DataFrame with columns [Produto, Descrição 1, ..., Descrição 10]
    
    Returns:
        DataFrame with added 'Query' column
    
    Example:
        >>> df = pd.DataFrame({
        ...     'Produto': ['Luva', 'Meia'],
        ...     'Descrição 1': ['correr', 'algodão'],
        ...     'Descrição 2': ['20mm', ''],
        ...     'Descrição 3': ['', '']
        ... })
        >>> result = build_queries_from_dataframe(df)
        >>> result['Query'].tolist()
        ['Luva correr 20mm', 'Meia algodão']
    """
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Extract product and descriptions columns
    produto_col = df.iloc[:, 0]  # First column is Produto
    descricao_cols = df.iloc[:, 1:11]  # Columns 2-11 are Descrição 1-10
    
    # Build query for each row
    queries = []
    for idx, row in df.iterrows():
        produto = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        
        # Get descriptions as list (convert NaN to empty strings)
        descricoes = [
            str(val).strip() if pd.notna(val) else ""
            for val in row.iloc[1:11]  # Get columns 2-11
        ]
        
        # Build query
        query = build_query_from_row(produto, descricoes)
        queries.append(query)
    
    df['Query'] = queries
    logger.info(f"✓ {len(queries)} queries construídas")
    
    return df


def get_query_column(df: pd.DataFrame) -> List[str]:
    """
    Get list of queries from dataframe.
    
    If 'Query' column doesn't exist, builds it first.
    
    Args:
        df: DataFrame with product data
    
    Returns:
        List of query strings
    """
    if 'Query' not in df.columns:
        df = build_queries_from_dataframe(df)
    
    return df['Query'].tolist()


def validate_queries(queries: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate query list for scraping.
    
    Args:
        queries: List of query strings
    
    Returns:
        (all_valid, invalid_queries)
        - all_valid: bool - True if all queries valid
        - invalid_queries: List of queries that failed validation
    
    Validation rules:
        ✓ Query not empty
        ✓ Query not only whitespace
        ✓ Query length > 2 characters
        ✓ Query length < 500 characters
    """
    invalid_queries = []
    
    for query in queries:
        if not query or not query.strip():
            invalid_queries.append(query)
        elif len(query.strip()) < 2:
            invalid_queries.append(query)
        elif len(query) > 500:
            invalid_queries.append(query)
    
    all_valid = len(invalid_queries) == 0
    
    if not all_valid:
        logger.warning(f"⚠️  {len(invalid_queries)} queries inválidas encontradas")
    else:
        logger.info(f"✓ Todas as {len(queries)} queries são válidas")
    
    return all_valid, invalid_queries
