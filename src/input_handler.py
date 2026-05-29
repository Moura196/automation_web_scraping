"""
Input handling module for Web Scraping Project
Loads, validates, and parses product input data from Excel files
Supports flexible structure: Produto + 1-10 Descriptions with intelligent validation
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict
from .logger import get_logger, setup_logger
from .utils import normalize_column_names, extract_description_number, is_description_column

logger = get_logger(__name__)


class ValidationWarning:
    """Represents a validation warning (non-critical issue)"""
    
    def __init__(self, level: str, message: str, row_number: Optional[int] = None):
        """
        Args:
            level: 'critical', 'warning', or 'info'
            message: Warning message
            row_number: Row number where issue occurred (if applicable)
        """
        self.level = level  # critical, warning, info
        self.message = message
        self.row_number = row_number
    
    def __repr__(self) -> str:
        row_str = f" (linha {self.row_number})" if self.row_number else ""
        return f"[{self.level.upper()}]{row_str}: {self.message}"


def validate_and_parse_structure(file_path: str) -> Tuple[bool, List[ValidationWarning], Optional[pd.DataFrame]]:
    """
    Validate and parse product input file.
    
    Returns:
        (is_valid, warnings, df_standardized)
        - is_valid: bool - True if file can be processed (False = critical error)
        - warnings: list of ValidationWarning objects
        - df_standardized: DataFrame with standardized columns (None if critical error)
        
    Rules:
        ✅ Column A must be "Produto" (case-sensitive check, but forgiving)
        ✅ Columns B-K should be "Descrição 1" through "Descrição 10"
        ✅ Column A must not be empty in data rows
        ✅ Columns B-K can be empty
        ⚠️ Extra columns (L+) are ignored silently
        ⚠️ Inconsistent column names generate warnings but don't reject
        ⚠️ Missing descriptions in sequence generate warnings
        
    Returns standardized DataFrame with:
        - Column A: "Produto"
        - Columns B-K: "Descrição 1" through "Descrição 10"
    """
    warnings = []
    
    try:
        # Load Excel file
        logger.info(f"Carregando arquivo: {file_path}")
        df = pd.read_excel(file_path, sheet_name=0, dtype=str)
        
        if df.empty:
            critical_warning = ValidationWarning(
                'critical',
                'Arquivo está vazio ou sem dados'
            )
            warnings.append(critical_warning)
            return False, warnings, None
        
        # Normalize column names (strip whitespace)
        original_columns = df.columns.tolist()
        df.columns = normalize_column_names(original_columns)
        
        logger.debug(f"Colunas detectadas: {df.columns.tolist()}")
        
        # Verify first column is "Produto"
        first_col = df.columns[0]
        if first_col.strip().lower() != 'produto':
            critical_warning = ValidationWarning(
                'critical',
                f"Coluna A se chama '{first_col}', esperado 'Produto'. "
                f"Deseja continuar processando?"
            )
            warnings.append(critical_warning)
            # Don't return here - give app chance to ask user
        
        # Extract description columns (B-K) and validate naming
        description_columns = []
        found_descriptions = {}
        
        for col_idx, col_name in enumerate(df.columns[1:11], start=2):  # Columns B-K
            col_letter = chr(64 + col_idx)  # Convert to letter (B, C, D, ...)
            desc_number = extract_description_number(col_name)
            
            if desc_number is not None:
                found_descriptions[desc_number] = (col_idx, col_name)
                description_columns.append((col_idx, desc_number, col_name))
            elif col_name and str(col_name).strip():
                # Column has a name but it's not a description column
                warning = ValidationWarning(
                    'warning',
                    f"Coluna {col_letter} se chama '{col_name}', "
                    f"esperado padrão 'Descrição N'"
                )
                warnings.append(warning)
        
        # Check for gaps in description numbers
        if found_descriptions:
            description_numbers = sorted(found_descriptions.keys())
            expected_numbers = list(range(1, len(description_numbers) + 1))
            
            if description_numbers != expected_numbers:
                missing = set(expected_numbers) - set(description_numbers)
                extra = set(description_numbers) - set(expected_numbers)
                
                if missing:
                    warning = ValidationWarning(
                        'warning',
                        f"Há um salto em numeração de descrições. "
                        f"Esperado: Descrição 1-{len(description_numbers)}, "
                        f"encontrado: Descrição {description_numbers}"
                    )
                    warnings.append(warning)
        
        # Validate data rows
        rows_with_empty_produto = []
        for idx, row in df.iterrows():
            produto = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not produto:
                rows_with_empty_produto.append(idx + 2)  # +2 because header is row 1
        
        if rows_with_empty_produto:
            warning = ValidationWarning(
                'warning',
                f"Linhas com coluna 'Produto' vazia: {rows_with_empty_produto}. "
                f"Estas linhas serão puladas durante processamento."
            )
            warnings.append(warning)
        
        # Build standardized dataframe
        standardized_data = []
        
        for idx, row in df.iterrows():
            produto = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            
            # Skip rows with empty Produto
            if not produto:
                continue
            
            # Extract up to 10 descriptions
            descricoes = []
            for col_idx in range(1, 11):  # Columns B-K (positions 1-10)
                if col_idx < len(row):
                    desc_value = str(row.iloc[col_idx]).strip() if pd.notna(row.iloc[col_idx]) else ""
                    descricoes.append(desc_value)
                else:
                    descricoes.append("")
            
            # Create row with Produto and 10 description slots
            standardized_row = [produto] + descricoes
            standardized_data.append(standardized_row)
        
        # Create standardized dataframe
        columns = ['Produto'] + [f'Descrição {i}' for i in range(1, 11)]
        df_standardized = pd.DataFrame(standardized_data, columns=columns)
        
        logger.info(f"✓ Validação concluída. {len(df_standardized)} linhas processadas")
        
        # Check if we have any critical warnings
        critical_warnings = [w for w in warnings if w.level == 'critical']
        is_valid = len(critical_warnings) == 0
        
        return is_valid, warnings, df_standardized
    
    except FileNotFoundError:
        critical_warning = ValidationWarning(
            'critical',
            f"Arquivo não encontrado: {file_path}"
        )
        warnings.append(critical_warning)
        return False, warnings, None
    
    except Exception as e:
        critical_warning = ValidationWarning(
            'critical',
            f"Erro ao processar arquivo: {str(e)}"
        )
        warnings.append(critical_warning)
        logger.error(f"Erro: {str(e)}", exc_info=True)
        return False, warnings, None


def load_products_dataframe(file_path: str) -> Tuple[Optional[pd.DataFrame], List[Dict]]:
    """
    Load products from Excel file and return standardized dataframe with warnings.
    
    Simplified interface for app.py integration.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        (df_standardized, warnings_list)
        - df_standardized: DataFrame with columns [Produto, Descrição 1-10] or None
        - warnings_list: List of dicts with 'level', 'message', 'row'
    
    Example:
        >>> df, warnings = load_products_dataframe('input.xlsx')
        >>> for w in warnings:
        ...     print(f"[{w['level']}] {w['message']}")
    """
    is_valid, warnings, df = validate_and_parse_structure(file_path)
    
    # Convert ValidationWarning objects to dicts
    warnings_dicts = [
        {
            'level': w.level,
            'message': w.message,
            'row': w.row_number
        }
        for w in warnings
    ]
    
    return df, warnings_dicts


def get_template_path() -> Path:
    """
    Get path to template input file.
    
    Returns:
        Path to template_entrada.xlsx
    """
    template_path = Path(__file__).parent.parent / 'templates' / 'template_entrada.xlsx'
    return template_path


def is_template_available() -> bool:
    """Check if template file is available"""
    return get_template_path().exists()
