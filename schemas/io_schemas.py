from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# IO Matrix Schemas
class IOMatrixBase(BaseModel):
    name: str
    description: Optional[str] = None
    sectors: List[str]  # List of sector names
    is_active: Optional[bool] = True


class IOMatrixCreate(IOMatrixBase):
    intermediate_consumption_data: List[List[float]]  # 2D matrix data
    final_demand_data: List[List[float]]  # 2D matrix data


class IOMatrixUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sectors: Optional[List[str]] = None
    intermediate_consumption_data: Optional[List[List[float]]] = None
    final_demand_data: Optional[List[List[float]]] = None
    is_active: Optional[bool] = None


class IOMatrixResponse(IOMatrixBase):
    id: int
    intermediate_consumption_data: List[List[float]]
    final_demand_data: List[List[float]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Matrix Operation Schemas
class MatrixOperationRequest(BaseModel):
    matrix_id: int
    operation_type: str  # "technical_coefficients", "io_matrix", "intermediate_consumption", "final_demand"


class MatrixOperationResponse(BaseModel):
    operation_type: str
    matrix_data: List[List[float]]
    sectors: List[str]
    metadata: Optional[Dict[str, Any]] = None


# Data Update Schema
class IODataUpdate(BaseModel):
    intermediate_consumption_data: Optional[List[List[float]]] = None
    final_demand_data: Optional[List[List[float]]] = None
    sectors: Optional[List[str]] = None


# Policy Dashboard Schemas
class SectorChange(BaseModel):
    sector: str  # agriculture, manufacturing, construction, transport, services, energy
    demand: str  # final_consumption, capital_formation, exports
    value: float


class PolicyDashboardRequest(BaseModel):
    change_sector_values: List[SectorChange]
