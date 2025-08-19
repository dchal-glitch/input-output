"""Validators specific to Input-Output analysis"""
from typing import List, Dict, Any, Optional
import pandas as pd
from .base_validator import ValidationError, BaseValidator
from schemas.io_schemas import SectorChange


def validate_sector_changes(changes: List[SectorChange]) -> bool:
    """
    Validate sector change data for policy dashboard
    
    Args:
        changes: List of sector changes
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not changes:
        raise ValidationError("At least one sector change is required")
    
    # Valid sectors (should match your data)
    # valid_sectors = {
    #     "agriculture", "manufacturing", "construction", 
    #     "transport", "services", "energy"
    # }
    
    # # Valid demand categories
    # valid_demands = {
    #     "final_consumption", "capital_formation", "exports"
    # }
    
    # for i, change in enumerate(changes):
    #     # Validate sector
    #     if change.sector not in valid_sectors:
    #         raise ValidationError(
    #             f"Invalid sector '{change.sector}'. Must be one of: {', '.join(valid_sectors)}",
    #             field=f"change_sector_values[{i}].sector",
    #             value=change.sector
    #         )
        
    #     # Validate demand
    #     if change.demand not in valid_demands:
    #         raise ValidationError(
    #             f"Invalid demand '{change.demand}'. Must be one of: {', '.join(valid_demands)}",
    #             field=f"change_sector_values[{i}].demand", 
    #             value=change.demand
    #         )
        
    #     # Validate value
    #     if change.value < 0:
    #         raise ValidationError(
    #             f"Value must be non-negative, got {change.value}",
    #             field=f"change_sector_values[{i}].value",
    #             value=change.value
    #         )

    seen_combinations = set()
    sector_changes = []
    total_final_use_changes = []

    for i, change in enumerate(changes):
        # Validate value
        if change.value < 0:
            raise ValidationError(
                f"Value must be non-negative, got {change.value}, for sector '{change.sector}' and demand '{change.demand}'",
                field=f"change_sector_values[{i}].value",
                value=change.value
            )
        
        # Check for duplicates
        combination = (change.sector, change.demand)
        if combination in seen_combinations:
            raise ValidationError(
                f"Duplicate sector-demand combination: {change.sector} - {change.demand}",
                field=f"change_sector_values[{i}]"
            )
        seen_combinations.add(combination)
        
        if change.demand == "total_final_use":
            total_final_use_changes.append(change)
        else:
            sector_changes.append(change)
    
    if not sector_changes and not total_final_use_changes:
        raise ValidationError("Total final use and sector changes cannot be used together")
    
    return True

def validate_sector_mapping(mapping: Dict[str, str]) -> bool:
    """Validate sector mapping dictionary"""
    if not mapping:
        raise ValidationError("Sector mapping cannot be empty")
    
    # Check for duplicate values
    values = list(mapping.values())
    if len(values) != len(set(values)):
        raise ValidationError("Sector mapping contains duplicate display names")
    
    # Check for empty keys or values
    for key, value in mapping.items():
        if not key or not key.strip():
            raise ValidationError("Sector mapping contains empty key")
        if not value or not value.strip():
            raise ValidationError(f"Sector mapping for '{key}' has empty display name")
    
    return True

def validate_policy_dashboard_request(request_data: Any) -> bool:
    """Validate complete policy dashboard request"""
    if not hasattr(request_data, 'change_sector_values'):
        raise ValidationError("Request must contain 'change_sector_values' field")
    
    return validate_sector_changes(request_data.change_sector_values)

class IOValidator(BaseValidator):
    """IO-specific validator class"""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate(self, data: Any) -> bool:
        """Validate IO data"""
        self.errors.clear()
        
        try:
            if hasattr(data, 'change_sector_values'):
                validate_sector_changes(data.change_sector_values)
            return True
        except ValidationError as e:
            self.errors.append(str(e))
            return False
    
    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors.copy()
