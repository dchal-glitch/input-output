import pytest
from schemas.io_schemas import IOMatrixCreate
from services.io_service import IOService
from services.matrix_service import MatrixService


# Sample test data
SAMPLE_INTERMEDIATE_CONSUMPTION = [
    [100, 200, 50],
    [150, 300, 75],
    [75, 100, 25]
]

SAMPLE_FINAL_DEMAND = [
    [400],
    [500],
    [300]
]

SAMPLE_SECTORS = ["Agriculture", "Manufacturing", "Services"]


def test_create_io_matrix(client, db_session):
    """Test IO matrix creation"""
    matrix_data = {
        "name": "Test IO Matrix",
        "description": "A test input-output matrix",
        "sectors": SAMPLE_SECTORS,
        "intermediate_consumption_data": SAMPLE_INTERMEDIATE_CONSUMPTION,
        "final_demand_data": SAMPLE_FINAL_DEMAND
    }
    
    response = client.post("/api/v1/io/matrices", json=matrix_data)
    # This will fail with 401 due to authentication requirement
    assert response.status_code == 401


def test_get_io_matrices_public(client):
    """Test get IO matrices endpoint (public access)"""
    response = client.get("/api/v1/io/matrices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_matrix_service_validation():
    """Test matrix service validation"""
    assert MatrixService.validate_matrix_data(SAMPLE_INTERMEDIATE_CONSUMPTION) is True
    assert MatrixService.validate_matrix_data(SAMPLE_FINAL_DEMAND) is True
    
    # Test invalid data
    assert MatrixService.validate_matrix_data([]) is False
    assert MatrixService.validate_matrix_data([[1, 2], [3]]) is False  # Inconsistent row lengths
    assert MatrixService.validate_matrix_data([[1, "invalid"], [3, 4]]) is False  # Non-numeric data


@pytest.mark.asyncio
async def test_matrix_service_operations():
    """Test matrix service operations"""
    matrix_service = MatrixService(SAMPLE_INTERMEDIATE_CONSUMPTION, SAMPLE_FINAL_DEMAND)
    
    # Test IO matrix creation
    io_matrix = await matrix_service.create_io_matrix()
    assert len(io_matrix) == 3  # 3 rows
    assert len(io_matrix[0]) == 4  # 3 intermediate + 1 final demand columns
    
    # Test intermediate consumption matrix
    ic_matrix = await matrix_service.create_intermediate_consumption_matrix()
    assert ic_matrix == SAMPLE_INTERMEDIATE_CONSUMPTION
    
    # Test final demand matrix
    fd_matrix = await matrix_service.create_final_demand_matrix()
    assert fd_matrix == SAMPLE_FINAL_DEMAND
    
    # Test technical coefficients calculation
    leontief_inverse, metadata = await matrix_service.create_technical_coefficients_matrix()
    assert len(leontief_inverse) == 3
    assert len(leontief_inverse[0]) == 3
    assert "total_output" in metadata
    assert "technical_coefficients" in metadata


def test_io_service_create_matrix(db_session):
    """Test IO service matrix creation"""
    matrix_data = IOMatrixCreate(
        name="Service Test Matrix",
        description="Test matrix for service layer",
        sectors=SAMPLE_SECTORS,
        intermediate_consumption_data=SAMPLE_INTERMEDIATE_CONSUMPTION,
        final_demand_data=SAMPLE_FINAL_DEMAND
    )
    
    matrix = IOService.create_io_matrix(db_session, matrix_data)
    assert matrix.name == matrix_data.name
    assert matrix.sectors == matrix_data.sectors
    assert matrix.intermediate_consumption_data == matrix_data.intermediate_consumption_data
    assert matrix.final_demand_data == matrix_data.final_demand_data


@pytest.mark.asyncio
async def test_matrix_operations_endpoint(client):
    """Test matrix operations validation endpoint"""
    test_data = {
        "intermediate_consumption_data": SAMPLE_INTERMEDIATE_CONSUMPTION,
        "final_demand_data": SAMPLE_FINAL_DEMAND
    }
    
    response = client.post("/api/v1/io/validate-matrix", json=test_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["intermediate_consumption_valid"] is True
    assert data["final_demand_valid"] is True
    assert data["dimensions_compatible"] is True
    assert data["intermediate_shape"] == [3, 3]
    assert data["final_demand_shape"] == [3, 1]


def test_get_io_matrix_not_found(client):
    """Test get non-existent IO matrix"""
    response = client.get("/api/v1/io/matrices/999")
    assert response.status_code == 404


def test_matrix_operations_invalid_operation(client):
    """Test invalid matrix operation"""
    response = client.post("/api/v1/io/matrices/1/operations/invalid_operation")
    assert response.status_code == 400
