from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import pandas as pd
from core.constants import TOTAL_FINAL_USE_COLUMN
from models.models import IOMatrix
from schemas.io_schemas import IOMatrixCreate, IOMatrixUpdate
from services.matrix_service import MatrixService
from services.data_service import DataService
from core.logging import get_logger

logger = get_logger(__name__)


class IOService:
    """Service layer for Input-Output operations"""

    def __init__(self):
        self.__data_service = DataService()
        self.__matrix_service = None
    
    @classmethod
    async def create(cls):
        """Async factory method to create IOService with initialized MatrixService"""
        service = cls()
        await service._initialize_matrix_service()
        return service
    
    async def _initialize_matrix_service(self):
        """Initialize the MatrixService with data from DataService"""
        ic_data = await self.__data_service.get_intermediate_consumption_data(format="pandas")
        fd_data = await self.__data_service.get_final_demand_data(format="pandas")
        self.__matrix_service = MatrixService(ic_data, fd_data)
    
    async def get_matrix_service(self):
        """Get or initialize the MatrixService"""
        if self.__matrix_service is None:
            await self._initialize_matrix_service()
        return self.__matrix_service

    async def get_io_table(self):
        """Get the IO table data"""
        matrix_service = await self.get_matrix_service()
        return await matrix_service.get_io_matrix()
    
    async def get_ic_table(self):
        """Get the intermediate consumption table data"""
        matrix_service = await self.get_matrix_service()
        return await matrix_service.get_intermediate_consumption_matrix()

    async def get_fd_table(self,with_total_final_use=False,change_data =[], only_total_final_use=False):
        """Get the final demand table data"""
        matrix_service = await self.get_matrix_service()
        fd_matrix = await matrix_service.get_final_demand_matrix()
        is_total_final_use_change = False
        if change_data:
            logger.info(f"Applying changes to final demand data: {change_data}")
            is_total_final_use_change = change_data[0].get("demand") == TOTAL_FINAL_USE_COLUMN
            if not is_total_final_use_change:
                for change_conf in change_data:
                    sector = change_conf.get("sector")
                    demand = change_conf.get("demand")
                    value = change_conf.get("value")

                    if sector in fd_matrix.index and demand in fd_matrix.columns:
                        fd_matrix.at[sector, demand] = value
                        logger.info(f"Updated FD matrix at ({sector}, {demand}) to {value}")

        if with_total_final_use:
            total_final_use = await self.get_total_final_use(change_data)
            if is_total_final_use_change:
                for change_conf in change_data:
                    sector = change_conf.get("sector")
                    demand = TOTAL_FINAL_USE_COLUMN
                    value = change_conf.get("value")
                    if sector in total_final_use.index:
                        total_final_use.at[sector] = value
                        logger.info(f"Updated FD matrix at ({sector}, {demand}) to {value}")
            if only_total_final_use:
                fd_matrix =  total_final_use
            else:
                fd_matrix = pd.concat([fd_matrix, total_final_use], axis=1)
        return fd_matrix

    async def get_total_final_use(self, change_data=[]):
        """Get the total final use"""
        matrix_service = await self.get_matrix_service()
        io_matrix = await matrix_service.get_io_matrix()
        if change_data:
            logger.info(f"Applying changes to IO matrix for total final use: {change_data}")
            for change_conf in change_data:
                sector = change_conf.get("sector")
                demand = change_conf.get("demand")
                value = change_conf.get("value")
                if sector in io_matrix.index and demand in io_matrix.columns:
                    io_matrix.at[sector, demand] = value
                    logger.info(f"Updated IO matrix at ({sector}, {demand}) to {value}")
        total_final_use = io_matrix.sum(axis=1).rename("total_final_use")

        return total_final_use
    
    async def calculate_output(self,change_sector_values):
        """Calculate output using technical coefficients and Leontief inverse"""
        try:
            if not change_sector_values:
                raise ValueError("No sector changes provided for output calculation")
            matrix_service = await self.get_matrix_service()
            
            # Get technical coefficients matrix
            tech_coeffs = await matrix_service.get_technical_coefficients()
            
            # Get Leontief inverse matrix
            leontief_inverse = await matrix_service.get_leontief_inverse()
            
            # Get economic multipliers
            multipliers = await matrix_service.get_economic_multipliers()
            
            # Calculate output using technical coefficients and Leontief inverse

            changed_fd_matrix = await self.get_fd_table(change_data=change_sector_values)
            changed_fd_matrix_with_total_final_use = await self.get_fd_table(change_data=change_sector_values, with_total_final_use=True,only_total_final_use=False)

            fd_change_type = await self.check_change_fd_type(change_sector_values)
            if fd_change_type == "total_final_use_change":
                changed_total_final_use = await self.get_fd_table(change_data=change_sector_values, with_total_final_use=True,only_total_final_use=True)
                changed_total_final_use = changed_total_final_use.to_frame(TOTAL_FINAL_USE_COLUMN)
                output = await matrix_service.calculate_output_with_new_fd(use_total_final_use=True,new_total_final_use=changed_total_final_use)
            else:
                output = await matrix_service.calculate_output_with_new_fd(use_fd=True,new_final_demand=changed_fd_matrix)

            new_ic_matrix = tech_coeffs.multiply(output.sum(axis=1), axis=0)
            # Return comprehensive output calculation results
            return {
                "technical_coefficients": tech_coeffs,
                "leontief_inverse": leontief_inverse,
                "multipliers": multipliers,
                "io_matrix": await matrix_service.get_io_matrix(),
                "new_ic_matrix": new_ic_matrix,
                "changed_fd_matrix_with_total_final_use": changed_fd_matrix_with_total_final_use,
                "new_output": output,
                "changed_fd_in_perc": ((output - changed_fd_matrix).div(changed_fd_matrix))*100
            }
            
        except Exception as error:
            logger.error(f"Error calculating output: {error}")
            raise error
    
    @staticmethod
    def get_io_matrix_by_id(db: Session, matrix_id: int) -> Optional[IOMatrix]:
        """Get IO matrix by ID"""
        matrix = db.query(IOMatrix).filter(IOMatrix.id == matrix_id).first()
        if matrix:
            logger.info("IO matrix retrieved", matrix_id=matrix_id, name=matrix.name)
        return matrix
    
    @staticmethod
    def get_io_matrices(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[IOMatrix]:
        """Get multiple IO matrices with pagination and filtering"""
        query = db.query(IOMatrix)
        
        if is_active is not None:
            query = query.filter(IOMatrix.is_active == is_active)
        
        matrices = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(matrices)} IO matrices")
        return matrices
    
    @staticmethod
    def update_io_matrix(db: Session, matrix_id: int, matrix_data: IOMatrixUpdate) -> Optional[IOMatrix]:
        """Update IO matrix information"""
        db_matrix = db.query(IOMatrix).filter(IOMatrix.id == matrix_id).first()
        if not db_matrix:
            return None
        
        update_data = matrix_data.model_dump(exclude_unset=True)
        
        # Validate matrix data if provided
        if "intermediate_consumption_data" in update_data:
            # Convert to DataFrame for validation if it's list data
            ic_data = update_data["intermediate_consumption_data"]
            if isinstance(ic_data, list):
                ic_df = pd.DataFrame(ic_data)
            else:
                ic_df = ic_data
            
            if not MatrixService.validate_matrix_data(ic_df):
                raise ValueError("Invalid intermediate consumption matrix data")
        
        if "final_demand_data" in update_data:
            # Convert to DataFrame for validation if it's list data
            fd_data = update_data["final_demand_data"]
            if isinstance(fd_data, list):
                fd_df = pd.DataFrame(fd_data)
            else:
                fd_df = fd_data
                
            if not MatrixService.validate_matrix_data(fd_df):
                raise ValueError("Invalid final demand matrix data")
        
        try:
            for field, value in update_data.items():
                setattr(db_matrix, field, value)
            
            db.commit()
            db.refresh(db_matrix)
            
            logger.info(
                "IO matrix updated",
                matrix_id=matrix_id,
                updated_fields=list(update_data.keys())
            )
            
            return db_matrix
            
        except IntegrityError as error:
            db.rollback()
            logger.error(f"Database integrity error updating IO matrix: {error}")
            raise ValueError("IO matrix name already exists")
    
    @staticmethod
    def delete_io_matrix(db: Session, matrix_id: int) -> bool:
        """Delete IO matrix"""
        db_matrix = db.query(IOMatrix).filter(IOMatrix.id == matrix_id).first()
        if not db_matrix:
            return False
        
        db.delete(db_matrix)
        db.commit()
        
        logger.info("IO matrix deleted", matrix_id=matrix_id, name=db_matrix.name)
        return True
    
    @staticmethod
    def create_io_matrix(db: Session, matrix_data: IOMatrixCreate) -> IOMatrix:
        """Create a new IO matrix"""
        try:
            # Validate matrix data using pandas DataFrames
            ic_data = matrix_data.intermediate_consumption_data
            fd_data = matrix_data.final_demand_data
            
            # Convert to DataFrames if they're lists
            if isinstance(ic_data, list):
                ic_df = pd.DataFrame(ic_data)
            else:
                ic_df = ic_data
                
            if isinstance(fd_data, list):
                fd_df = pd.DataFrame(fd_data)
            else:
                fd_df = fd_data
            
            # Validate using MatrixService
            if not MatrixService.validate_matrix_data(ic_df):
                raise ValueError("Invalid intermediate consumption matrix data")
            
            if not MatrixService.validate_matrix_data(fd_df):
                raise ValueError("Invalid final demand matrix data")
            
            # Create database record
            db_matrix = IOMatrix(
                name=matrix_data.name,
                description=matrix_data.description,
                sectors=matrix_data.sectors,
                intermediate_consumption_data=matrix_data.intermediate_consumption_data,
                final_demand_data=matrix_data.final_demand_data,
                is_active=matrix_data.is_active if hasattr(matrix_data, 'is_active') else True
            )
            
            db.add(db_matrix)
            db.commit()
            db.refresh(db_matrix)
            
            logger.info(
                "IO matrix created",
                matrix_id=db_matrix.id,
                name=db_matrix.name,
                sectors_count=len(matrix_data.sectors) if matrix_data.sectors else 0
            )
            
            return db_matrix
            
        except IntegrityError as error:
            db.rollback()
            logger.error(f"Database integrity error creating IO matrix: {error}")
            raise ValueError("IO matrix name already exists")
        except Exception as error:
            db.rollback()
            logger.error(f"Error creating IO matrix: {error}")
            raise error
    
    @staticmethod
    async def get_intermediate_consumption_data(db: Session, matrix_id: int) -> List[List[float]]:
        """Get intermediate consumption data for a specific matrix"""
        matrix = IOService.get_io_matrix_by_id(db, matrix_id)
        if not matrix:
            raise ValueError(f"IO matrix with id {matrix_id} not found")
        
        return matrix.intermediate_consumption_data
    
    @staticmethod
    async def get_final_demand_data(db: Session, matrix_id: int) -> List[List[float]]:
        """Get final demand data for a specific matrix"""
        matrix = IOService.get_io_matrix_by_id(db, matrix_id)
        if not matrix:
            raise ValueError(f"IO matrix with id {matrix_id} not found")
        
        return matrix.final_demand_data
    
    @staticmethod
    async def perform_matrix_operation(
        db: Session, 
        matrix_id: int, 
        operation_type: str
    ) -> Dict[str, Any]:
        """Perform matrix operations on IO data"""
        matrix = IOService.get_io_matrix_by_id(db, matrix_id)
        if not matrix:
            raise ValueError(f"IO matrix with id {matrix_id} not found")
        
        # Create matrix service instance using factory method for list data
        matrix_service = MatrixService.from_lists(
            matrix.intermediate_consumption_data,
            matrix.final_demand_data
        )
        
        try:
            if operation_type == "io_matrix":
                result_data = await matrix_service.get_io_matrix()
                metadata = {"operation": "Full IO Matrix"}
                
            elif operation_type == "intermediate_consumption":
                result_data = await matrix_service.get_intermediate_consumption_matrix()
                metadata = {"operation": "Intermediate Consumption Matrix"}
                
            elif operation_type == "final_demand":
                result_data = await matrix_service.get_final_demand_matrix()
                metadata = {"operation": "Final Demand Matrix"}
                
            elif operation_type == "technical_coefficients":
                result_data = await matrix_service.get_technical_coefficients()
                metadata = {"operation": "Technical Coefficients Matrix"}
                
            elif operation_type == "leontief_inverse":
                result_data = await matrix_service.get_leontief_inverse()
                metadata = {"operation": "Leontief Inverse Matrix"}
                
            elif operation_type == "multipliers":
                result_data = await matrix_service.get_economic_multipliers()
                metadata = {"operation": "Economic Multipliers"}
                
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")
            
            logger.info(
                "Matrix operation completed",
                matrix_id=matrix_id,
                operation=operation_type
            )
            
            return {
                "operation_type": operation_type,
                "matrix_data": result_data,
                "sectors": matrix.sectors,
                "metadata": metadata
            }
            
        except Exception as error:
            logger.error(f"Matrix operation failed: {error}")
            raise error

    @staticmethod
    async def create_matrix_from_csv_files(
        db: Session,
        name: str,
        description: str,
        ic_file: str = "IODATA.csv",
        fd_file: str = "FD.csv",
        sectors_file: str = "sectors.csv"
    ) -> IOMatrix:
        """
        Create IO matrix from CSV files using DataService
        
        Args:
            db: Database session
            name: Name for the new matrix
            description: Description for the new matrix
            ic_file: Intermediate consumption CSV file name
            fd_file: Final demand CSV file name
            sectors_file: Sectors CSV file name
            
        Returns:
            Created IOMatrix instance
        """
        try:
            data_service = DataService()
            
            # Fetch data from CSV files as lists for database storage
            ic_result = await data_service.get_intermediate_consumption_data(ic_file, format="list")
            fd_data = await data_service.get_final_demand_data(fd_file, format="list")
            sectors = await data_service.get_sector_labels(sectors_file)
            
            # Extract the actual data from the result dictionary
            ic_data = ic_result['data'] if isinstance(ic_result, dict) else ic_result
            
            # Create MatrixService to validate dimensions
            matrix_service = MatrixService.from_lists(ic_data, fd_data)
            
            # Create matrix using existing create method
            matrix_create = IOMatrixCreate(
                name=name,
                description=description,
                sectors=sectors,
                intermediate_consumption_data=ic_data,
                final_demand_data=fd_data,
                is_active=True
            )
            
            matrix = IOService.create_io_matrix(db, matrix_create)
            
            logger.info(
                "IO matrix created from CSV files",
                matrix_id=matrix.id,
                ic_file=ic_file,
                fd_file=fd_file,
                sectors_count=len(sectors)
            )
            
            return matrix
            
        except Exception as error:
            logger.error(f"Error creating matrix from CSV files: {error}")
            raise error

    @staticmethod
    async def fetch_data_from_external_source(
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch IO data from external API using DataService
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the API
            
        Returns:
            External data response
        """
        try:
            data_service = DataService()
            data = await data_service.fetch_from_external_api(endpoint, params)
            
            logger.info("External data fetched successfully", endpoint=endpoint)
            return data
            
        except Exception as error:
            logger.error(f"Error fetching external data: {error}")
            raise error

    @staticmethod
    async def export_matrix_to_csv(
        db: Session,
        matrix_id: int,
        export_type: str = "both"
    ) -> Dict[str, str]:
        """
        Export IO matrix data to CSV files using DataService
        
        Args:
            db: Database session
            matrix_id: ID of the matrix to export
            export_type: Type of data to export ("ic", "fd", or "both")
            
        Returns:
            Dictionary with paths to exported files
        """
        try:
            matrix = IOService.get_io_matrix_by_id(db, matrix_id)
            if not matrix:
                raise ValueError(f"Matrix with ID {matrix_id} not found")
            
            data_service = DataService()
            exported_files = {}
            
            if export_type in ["ic", "both"]:
                ic_filename = f"matrix_{matrix_id}_ic.csv"
                ic_path = await data_service.save_matrix_to_csv(
                    matrix.intermediate_consumption_data,
                    ic_filename
                )
                exported_files["intermediate_consumption"] = ic_path
            
            if export_type in ["fd", "both"]:
                fd_filename = f"matrix_{matrix_id}_fd.csv"
                fd_path = await data_service.save_matrix_to_csv(
                    matrix.final_demand_data,
                    fd_filename
                )
                exported_files["final_demand"] = fd_path
            
            logger.info(
                "Matrix data exported to CSV",
                matrix_id=matrix_id,
                export_type=export_type,
                files=list(exported_files.keys())
            )
            
            return exported_files
            
        except Exception as error:
            logger.error(f"Error exporting matrix to CSV: {error}")
            raise error

    @staticmethod
    async def update_matrix_from_external_data(
        db: Session,
        matrix_id: int,
        data_source: str,
        source_params: Optional[Dict[str, Any]] = None
    ) -> IOMatrix:
        """
        Update existing matrix with data from external source
        
        Args:
            db: Database session
            matrix_id: ID of the matrix to update
            data_source: Source of external data (API endpoint or file name)
            source_params: Parameters for data source
            
        Returns:
            Updated IOMatrix instance
        """
        try:
            matrix = IOService.get_io_matrix_by_id(db, matrix_id)
            if not matrix:
                raise ValueError(f"Matrix with ID {matrix_id} not found")
            
            data_service = DataService()
            
            # Update the matrix data using DataService
            updated_data = await data_service.update_io_data(matrix_id, {
                "data_source": data_source,
                "source_params": source_params or {},
                "matrix_name": matrix.name
            })
            
            logger.info(
                "Matrix updated from external data",
                matrix_id=matrix_id,
                data_source=data_source
            )
            
            return matrix
            
        except Exception as error:
            logger.error(f"Error updating matrix from external data: {error}")
            raise error

    @staticmethod
    async def analyze_scenarios(
        db: Session,
        matrix_id: int,
        fd_scenarios: List[List[List[float]]]
    ) -> Dict[str, Any]:
        """
        Analyze multiple final demand scenarios using MatrixService
        
        Args:
            db: Database session
            matrix_id: ID of the base matrix
            fd_scenarios: List of final demand scenarios (each as 2D list)
            
        Returns:
            Dictionary containing scenario analysis results
        """
        try:
            matrix = IOService.get_io_matrix_by_id(db, matrix_id)
            if not matrix:
                raise ValueError(f"Matrix with ID {matrix_id} not found")
            
            # Create matrix service instance
            matrix_service = MatrixService.from_lists(
                matrix.intermediate_consumption_data,
                matrix.final_demand_data
            )
            
            # Convert scenarios to pandas DataFrames for MatrixService
            fd_scenarios_df = []
            for scenario in fd_scenarios:
                fd_df = pd.DataFrame(scenario)
                fd_scenarios_df.append(fd_df)
            
            # Run scenario analysis
            scenario_results = await matrix_service.calculate_output_scenarios(fd_scenarios_df)
            
            # Get base calculations for comparison
            base_multipliers = await matrix_service.get_economic_multipliers()
            base_io_matrix = await matrix_service.get_io_matrix()
            
            logger.info(
                "Scenario analysis completed",
                matrix_id=matrix_id,
                scenarios_count=len(fd_scenarios)
            )
            
            return {
                "matrix_id": matrix_id,
                "matrix_name": matrix.name,
                "base_multipliers": base_multipliers,
                "scenarios": scenario_results,
                "base_io_matrix_shape": base_io_matrix.shape,
                "sectors": matrix.sectors
            }
            
        except Exception as error:
            logger.error(f"Error analyzing scenarios: {error}")
            raise error

    @staticmethod
    async def get_matrix_calculations(
        db: Session,
        matrix_id: int,
        calculations: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive calculations for a matrix
        
        Args:
            db: Database session
            matrix_id: ID of the matrix
            calculations: List of calculations to perform
                         ["io_matrix", "technical_coefficients", "leontief_inverse", "multipliers"]
            
        Returns:
            Dictionary containing all requested calculations
        """
        try:
            matrix = IOService.get_io_matrix_by_id(db, matrix_id)
            if not matrix:
                raise ValueError(f"Matrix with ID {matrix_id} not found")
            
            if calculations is None:
                calculations = ["io_matrix", "technical_coefficients", "leontief_inverse", "multipliers"]
            
            # Create matrix service instance
            matrix_service = MatrixService.from_lists(
                matrix.intermediate_consumption_data,
                matrix.final_demand_data
            )
            
            results = {"matrix_id": matrix_id, "matrix_name": matrix.name}
            
            if "io_matrix" in calculations:
                results["io_matrix"] = await matrix_service.get_io_matrix()
            
            if "technical_coefficients" in calculations:
                results["technical_coefficients"] = await matrix_service.get_technical_coefficients()
            
            if "leontief_inverse" in calculations:
                results["leontief_inverse"] = await matrix_service.get_leontief_inverse()
            
            if "multipliers" in calculations:
                results["multipliers"] = await matrix_service.get_economic_multipliers()
            
            if "intermediate_consumption" in calculations:
                results["intermediate_consumption"] = await matrix_service.get_intermediate_consumption_matrix()
                
            if "final_demand" in calculations:
                results["final_demand"] = await matrix_service.get_final_demand_matrix()
            
            logger.info(
                "Matrix calculations completed",
                matrix_id=matrix_id,
                calculations=calculations
            )
            
            return results
            
        except Exception as error:
            logger.error(f"Error performing matrix calculations: {error}")
            raise error

    @staticmethod
    async def check_change_fd_type(change_sector_values: List[Dict[str, Any]]) -> bool:
        """
        Check if the changed final demand is component wise or total final use
        """
        try:
            if not change_sector_values:
                raise ValueError("No sector changes provided for FD type check")
            is_total_final_use_change = change_sector_values[0].get("demand") == TOTAL_FINAL_USE_COLUMN
            if is_total_final_use_change:
                logger.info("Change is for total final use")
                return "total_final_use_change"
            else:
                logger.info("Change is for component wise final demand")
                return "component_change"
        except Exception as error:
            logger.error(f"Error checking change FD type: {error}")
            raise error