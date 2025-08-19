"""Base validation utilities and custom exceptions"""
from typing import Any, List, Dict, Optional
from abc import ABC, abstractmethod


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class BaseValidator(ABC):
    """Base validator class"""
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data and return True if valid"""
        pass
    
    @abstractmethod
    def get_errors(self) -> List[str]:
        """Get list of validation errors"""
        pass
    
    def is_valid(self, data: Any) -> bool:
        """Check if data is valid without raising exceptions"""
        try:
            return self.validate(data)
        except ValidationError:
            return False
