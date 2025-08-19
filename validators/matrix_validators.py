"""Validators for matrix operations"""
from typing import List, Any, Tuple
import numpy as np
import pandas as pd
from .base_validator import ValidationError, BaseValidator


def validate_matrix_dimensions(ic_matrix: Any, fd_matrix: Any) -> bool:
    """
    Validate that IC and FD matrices have compatible dimensions
    
    Args:
        ic_matrix: Intermediate consumption matrix
        fd_matrix: Final demand matrix
        
    Returns:
        bool: True if dimensions are compatible
        
    Raises:
        ValidationError: If dimensions are incompatible
    """
    # Convert to numpy arrays for dimension checking
    if isinstance(ic_matrix, pd.DataFrame):
        ic_array = ic_matrix.values
    elif isinstance(ic_matrix, list):
        ic_array = np.array(ic_matrix)
    else:
        ic_array = ic_matrix
    
    if isinstance(fd_matrix, pd.DataFrame):
        fd_array = fd_matrix.values
    elif isinstance(fd_matrix, list):
        fd_array = np.array(fd_matrix)
    else:
        fd_array = fd_matrix
    
    # Check if both are 2D
    if ic_array.ndim != 2:
        raise ValidationError(f"IC matrix must be 2-dimensional, got {ic_array.ndim}D")
    
    if fd_array.ndim != 2:
        raise ValidationError(f"FD matrix must be 2-dimensional, got {fd_array.ndim}D")
    
    # Check row compatibility
    ic_rows = ic_array.shape[0]
    fd_rows = fd_array.shape[0]
    
    if ic_rows != fd_rows:
        raise ValidationError(
            f"IC and FD matrices must have same number of rows. "
            f"IC: {ic_rows}, FD: {fd_rows}"
        )
    
    # Check that IC matrix is square
    ic_cols = ic_array.shape[1]
    if ic_rows != ic_cols:
        raise ValidationError(
            f"IC matrix must be square. Got {ic_rows}x{ic_cols}"
        )
    
    return True


def validate_matrix_data_compatibility(data: List[List[float]]) -> bool:
    """Validate that matrix data is properly formatted"""
    if not data:
        raise ValidationError("Matrix data cannot be empty")
    
    # Check that all rows have same length
    row_lengths = [len(row) for row in data]
    if len(set(row_lengths)) > 1:
        raise ValidationError(
            f"All matrix rows must have same length. Got lengths: {row_lengths}"
        )
    
    # Check for non-numeric values
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            if not isinstance(value, (int, float)):
                raise ValidationError(
                    f"Matrix contains non-numeric value at position [{i}][{j}]: {value}"
                )
            if np.isnan(value) or np.isinf(value):
                raise ValidationError(
                    f"Matrix contains invalid numeric value at position [{i}][{j}]: {value}"
                )
    
    return True


def validate_technical_coefficients(tech_coeffs: Any) -> bool:
    """Validate technical coefficients matrix"""
    if isinstance(tech_coeffs, pd.DataFrame):
        values = tech_coeffs.values
    else:
        values = np.array(tech_coeffs)
    
    # Check for negative values
    if np.any(values < 0):
        raise ValidationError("Technical coefficients cannot contain negative values")
    
    # Check for values > 1 (usually indicates an error)
    if np.any(values > 1):
        raise ValidationError("Technical coefficients should not exceed 1.0")
    
    return True


class MatrixValidator(BaseValidator):
    """Matrix-specific validator class"""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate(self, data: Any) -> bool:
        """Validate matrix data"""
        self.errors.clear()
        
        try:
            if isinstance(data, dict):
                if 'intermediate_consumption_data' in data and 'final_demand_data' in data:
                    ic_data = data['intermediate_consumption_data']
                    fd_data = data['final_demand_data']
                    
                    validate_matrix_data_compatibility(ic_data)
                    validate_matrix_data_compatibility(fd_data)
                    validate_matrix_dimensions(ic_data, fd_data)
                    
            elif isinstance(data, list):
                validate_matrix_data_compatibility(data)
                
            return True
        except ValidationError as e:
            self.errors.append(str(e))
            return False
    
    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors.copy()
