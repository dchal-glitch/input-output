from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.io_schemas import (
    IOMatrixCreate, 
    IOMatrixUpdate, 
    IOMatrixResponse,
    MatrixOperationRequest,
    MatrixOperationResponse,
    IODataUpdate
)
from services.io_service import IOService
from services.matrix_service import MatrixService
from core.auth import get_current_user, get_current_user_optional
from services.table_service import TableService

router = APIRouter(prefix="/io", tags=["input-output"])

@router.get('/table')
async def get_io_table():
    """
    Get the Input-Output table data
    """
    try:
        io_service = await IOService.create()
        io_table = await io_service.get_io_table()
        return {
            "io_table": io_table,
            "message": "IO table retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get IO table: {str(e)}")

@router.get('/calculate-output')
async def calculate_output():
    """
    Calculate comprehensive output analysis
    """
    try:
        sector_mapping = {
            "agriculture": "Agriculture",
            "manufacturing": "Manufacturing",
            "construction": "Construction",
            "transport": "Transport",
            "services": "Services",
            "energy": "Energy"
        }

        # demand_mapping = {
        #     "governmentfinalconsumptionexpenditure": "Government Final Consumption Expenditure",
        #     "householdfinalconsumptionexpenditure": "Household Final Consumption Expenditure",
        #     "exportsgoodstorestofworld": "Exports goods to rest of world",
        #     "exportsgoodstorestofuae": "Exports goods to rest of  UAE",
        #     "exportsservicestorestofworld": "Exports services to rest  of world",
        #     "exportsservicestorestofuae": "Exports services to rest of  UAE",
        #     "changeininventories": "Change in inventories",
        #     "grossfixedcapitalformation": "Gross fixed capital formation"
        # }
        demand_mapping = {
            "final_consumption": "Final Consumption",
            "capital_formation": "Capital Formation",
            "exports": "Exports"
        }

        # final_demand_groups = {
        #     "Final Demand": ["household_expenditure", "government_expenditure", "capital_formation"],
        #     "Exports": ["exports_goods", "exports_services"]
        # }
        final_demand_groups = {
            "Final Demand": ["final_consumption", "capital_formation"],
            "Exports": ["exports"]
        }


        table_service = TableService()
        io_service = await IOService.create()
        output_data = await io_service.calculate_output()
        new_ic_matrix = output_data.get("new_intermediate_consumption", [])
        
        flattened_table = table_service.flatten_io_matrix(new_ic_matrix,sector_mapping,demand_mapping,final_demand_groups)
        tables = []
        tables.append(flattened_table)
        return {
            "data": tables,
            "message": "Output calculations completed successfully",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to calculate output: {str(e)}")

@router.post("/matrices", response_model=IOMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_io_matrix(
    matrix_data: IOMatrixCreate,
    db: Session = Depends(get_db),
    # current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new Input-Output matrix
    Requires authentication
    """
    try:
        matrix = IOService.create_io_matrix(db=db, matrix_data=matrix_data)
        return matrix
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create IO matrix")


@router.get("/matrices", response_model=List[IOMatrixResponse])
async def get_io_matrices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    # current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Get all IO matrices with pagination and filtering
    Optional authentication for enhanced access
    """
    return IOService.get_io_matrices(db=db, skip=skip, limit=limit, is_active=is_active)


@router.get("/matrices/{matrix_id}", response_model=IOMatrixResponse)
async def get_io_matrix(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Get IO matrix by ID
    Public access with optional authentication
    """
    matrix = IOService.get_io_matrix_by_id(db=db, matrix_id=matrix_id)
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IO matrix not found"
        )
    return matrix


@router.put("/matrices/{matrix_id}", response_model=IOMatrixResponse)
async def update_io_matrix(
    matrix_id: int,
    matrix_data: IOMatrixUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update IO matrix by ID
    Requires authentication
    """
    try:
        matrix = IOService.update_io_matrix(db=db, matrix_id=matrix_id, matrix_data=matrix_data)
        if not matrix:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IO matrix not found"
            )
        return matrix
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/matrices/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_io_matrix(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete IO matrix by ID
    Requires authentication
    """
    if not IOService.delete_io_matrix(db=db, matrix_id=matrix_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IO matrix not found"
        )


@router.post("/matrices/{matrix_id}/operations/{operation_type}")
async def perform_matrix_operation(
    matrix_id: int,
    operation_type: str,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Perform matrix operations on IO data
    
    Available operations:
    - io_matrix: Create full IO matrix (intermediate consumption + final demand)
    - intermediate_consumption: Get intermediate consumption matrix
    - final_demand: Get final demand matrix  
    - technical_coefficients: Calculate technical coefficients and Leontief inverse
    - multipliers: Calculate economic multipliers
    
    Equivalent to getIOData() method in your JavaScript controller
    """
    valid_operations = ["io_matrix", "intermediate_consumption", "final_demand", "technical_coefficients", "multipliers"]
    
    if operation_type not in valid_operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation type. Must be one of: {', '.join(valid_operations)}"
        )
    
    try:
        result = await IOService.perform_matrix_operation(
            db=db,
            matrix_id=matrix_id,
            operation_type=operation_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matrix operation failed: {str(e)}"
        )


@router.put("/matrices/{matrix_id}/data")
async def update_io_data(
    matrix_id: int,
    data_update: IODataUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update IO matrix data (intermediate consumption, final demand, or sectors)
    Equivalent to updateIOData() method in your JavaScript controller
    Requires authentication
    """
    try:
        # Convert IODataUpdate to IOMatrixUpdate
        update_data = IOMatrixUpdate(
            intermediate_consumption_data=data_update.intermediate_consumption_data,
            final_demand_data=data_update.final_demand_data,
            sectors=data_update.sectors
        )
        
        matrix = IOService.update_io_matrix(db=db, matrix_id=matrix_id, matrix_data=update_data)
        if not matrix:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IO matrix not found"
            )
        
        return {
            "message": "IO data updated successfully",
            "matrix_id": matrix_id,
            "updated_fields": [k for k, v in data_update.model_dump().items() if v is not None]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update IO data"
        )


@router.get("/matrices/{matrix_id}/intermediate-consumption")
async def get_intermediate_consumption_data(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Get intermediate consumption data for a specific matrix
    """
    try:
        data = await IOService.get_intermediate_consumption_data(db=db, matrix_id=matrix_id)
        matrix = IOService.get_io_matrix_by_id(db=db, matrix_id=matrix_id)
        
        return {
            "matrix_id": matrix_id,
            "sectors": matrix.sectors if matrix else [],
            "intermediate_consumption_data": data,
            "shape": [len(data), len(data[0]) if data else 0]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/matrices/{matrix_id}/final-demand")
async def get_final_demand_data(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Get final demand data for a specific matrix
    """
    try:
        data = await IOService.get_final_demand_data(db=db, matrix_id=matrix_id)
        matrix = IOService.get_io_matrix_by_id(db=db, matrix_id=matrix_id)
        
        return {
            "matrix_id": matrix_id,
            "sectors": matrix.sectors if matrix else [],
            "final_demand_data": data,
            "shape": [len(data), len(data[0]) if data else 0]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/validate-matrix")
async def validate_matrix_data(
    matrix_data: Dict[str, List[List[float]]],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Validate matrix data format and compatibility
    """
    intermediate = matrix_data.get("intermediate_consumption_data", [])
    final_demand = matrix_data.get("final_demand_data", [])
    
    validation_result = {
        "intermediate_consumption_valid": MatrixService.validate_matrix_data(intermediate),
        "final_demand_valid": MatrixService.validate_matrix_data(final_demand),
        "dimensions_compatible": False,
        "intermediate_shape": [0, 0],
        "final_demand_shape": [0, 0]
    }
    
    if intermediate:
        validation_result["intermediate_shape"] = [len(intermediate), len(intermediate[0])]
    
    if final_demand:
        validation_result["final_demand_shape"] = [len(final_demand), len(final_demand[0])]
    
    # Check dimension compatibility
    if (validation_result["intermediate_consumption_valid"] and 
        validation_result["final_demand_valid"] and
        validation_result["intermediate_shape"][0] == validation_result["final_demand_shape"][0]):
        validation_result["dimensions_compatible"] = True
    
    return validation_result


@router.post("/matrices/from-csv", response_model=IOMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_matrix_from_csv(
    name: str,
    description: str,
    ic_file: str = "IODATA.csv",
    fd_file: str = "FD.csv", 
    sectors_file: str = "sectors.csv",
    db: Session = Depends(get_db),
    # current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create IO matrix from CSV files
    Requires authentication
    """
    try:
        matrix = await IOService.create_matrix_from_csv_files(
            db=db,
            name=name,
            description=description,
            ic_file=ic_file,
            fd_file=fd_file,
            sectors_file=sectors_file
        )
        return matrix
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create matrix from CSV")


@router.get("/data/external/{endpoint}")
async def fetch_external_data(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    # current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Fetch data from external API
    Requires authentication
    """
    try:
        data = await IOService.fetch_data_from_external_source(endpoint, params)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch external data: {str(e)}")


@router.post("/matrices/{matrix_id}/export")
async def export_matrix_to_csv(
    matrix_id: int,
    export_type: str = Query("both", regex="^(ic|fd|both)$", description="Type of data to export"),
    db: Session = Depends(get_db),
    # current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Export IO matrix data to CSV files
    Requires authentication
    """
    try:
        exported_files = await IOService.export_matrix_to_csv(db, matrix_id, export_type)
        return {
            "status": "success",
            "matrix_id": matrix_id,
            "export_type": export_type,
            "exported_files": exported_files
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export matrix")


@router.put("/matrices/{matrix_id}/update-from-source")
async def update_matrix_from_external_source(
    matrix_id: int,
    data_source: str,
    source_params: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    # current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update matrix with data from external source
    Requires authentication
    """
    try:
        matrix = await IOService.update_matrix_from_external_data(
            db=db,
            matrix_id=matrix_id,
            data_source=data_source,
            source_params=source_params
        )
        return {"status": "success", "matrix_id": matrix_id, "updated_at": matrix.updated_at}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update matrix")


@router.get("/data/sample/ic")
async def get_sample_intermediate_consumption():
    """
    Get sample intermediate consumption data for testing
    Public endpoint
    """
    from services.data_service import DataService
    data_service = DataService()
    sample_data = data_service._get_sample_ic_data()
    return {
        "data": sample_data,
        "shape": [len(sample_data), len(sample_data[0]) if sample_data else 0],
        "description": "Sample intermediate consumption matrix"
    }


@router.get("/data/sample/fd") 
async def get_sample_final_demand():
    """
    Get sample final demand data for testing
    Public endpoint
    """
    from services.data_service import DataService
    data_service = DataService()
    sample_data = data_service._get_sample_fd_data()
    return {
        "data": sample_data,
        "shape": [len(sample_data), len(sample_data[0]) if sample_data else 0],
        "description": "Sample final demand matrix"
    }


@router.get("/data/sample/sectors")
async def get_sample_sectors():
    """
    Get sample sector labels for testing
    Public endpoint
    """
    from services.data_service import DataService
    data_service = DataService()
    sample_sectors = data_service._get_sample_sector_labels()
    return {
        "sectors": sample_sectors,
        "count": len(sample_sectors),
        "description": "Sample sector labels"
    }
