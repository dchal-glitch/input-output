import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from core.custom_typing import FinalDemandMatrix, IOMatrix, IntermediateConsumptionMatrix, LeontiefInverseMatrix, TechnicalCoefficientsMatrix
from core.logging import get_logger
import pandas as pd

logger = get_logger(__name__)


class MatrixService:
    """Service for matrix operations on Input-Output tables"""
    
    def __init__(self, intermediate_consumption_data: pd.DataFrame, final_demand_data: pd.DataFrame):
        # Store original data as pandas DataFrames
        self.ic_df = intermediate_consumption_data.copy()
        self.fd_df = final_demand_data.copy()
        
        # Also store as numpy arrays for compatibility
        self.ic_data = self.ic_df.values
        self.fd_data = self.fd_df.values
        
        # Validate matrix dimensions
        self._validate_matrices()
        
        # Initialize computed matrices as instance variables (calculated on demand)
        self._io_matrix = None
        self._technical_coefficients = None
        self._leontief_inverse = None
        self._economic_multipliers = None
    
    @classmethod
    def from_lists(cls, intermediate_consumption_data: List[List[float]], final_demand_data: List[List[float]]):
        """
        Factory method to create MatrixService from list data (for backward compatibility)
        """
        ic_df = pd.DataFrame(intermediate_consumption_data)
        fd_df = pd.DataFrame(final_demand_data)
        return cls(ic_df, fd_df)
    
    @classmethod
    def from_numpy(cls, intermediate_consumption_data: np.ndarray, final_demand_data: np.ndarray):
        """
        Factory method to create MatrixService from numpy arrays
        """
        ic_df = pd.DataFrame(intermediate_consumption_data)
        fd_df = pd.DataFrame(final_demand_data)
        return cls(ic_df, fd_df)
    
    # ===== INSTANCE METHODS (Using shared instance variables) =====
    
    async def get_io_matrix(self) -> IOMatrix:
        """
        Create the full Input-Output matrix using instance data
        Cached for performance - calculated once and reused
        """
        if self._io_matrix is None:
            try:
                # Ensure both matrices have the same row indices
                if not self.ic_df.index.equals(self.fd_df.index):
                    logger.warning("IC and FD matrices have different row indices, using IC indices")
                    self.fd_df = self.fd_df.reindex(self.ic_df.index)
                
                # Combine horizontally
                self._io_matrix = pd.concat([self.ic_df, self.fd_df], axis=1)
                logger.info("IO matrix created", shape=self._io_matrix.shape)
            except Exception as error:
                logger.error(f"Error creating IO matrix: {error}")
                raise error
        
        return self._io_matrix
    
    async def get_io_matrix_with_new_fd(self, new_fd_data: pd.DataFrame) -> IOMatrix:
        """
        Create IO matrix with new final demand data (for scenario analysis)
        Does not cache - used for temporary calculations
        """
        try:
            # Ensure both matrices have the same row indices
            if not self.ic_df.index.equals(new_fd_data.index):
                logger.warning("IC and new FD matrices have different row indices, using IC indices")
                new_fd_data = new_fd_data.reindex(self.ic_df.index)
            
            io_matrix = pd.concat([self.ic_df, new_fd_data], axis=1)
            logger.info("IO matrix with new FD created", shape=io_matrix.shape)
            return io_matrix
        except Exception as error:
            logger.error(f"Error creating IO matrix with new FD: {error}")
            raise error
    
    async def get_technical_coefficients(self) -> TechnicalCoefficientsMatrix:
        """
        Create technical coefficients matrix using instance data
        Cached for performance - calculated once and reused
        """
        if self._technical_coefficients is None:
            try:
                io_matrix = await self.get_io_matrix()
                n_sectors = self.ic_df.shape[1]  # Number of sectors from IC matrix
                
                # Calculate total output (row sums)
                total_output = io_matrix.sum(axis=1, numeric_only=True)
                # Avoid division by zero
                total_output = total_output.replace(0, 1)
                
                # Extract only the intermediate consumption part
                ic_part = io_matrix.iloc[:, :n_sectors]
                
                # Calculate technical coefficients: A = IC / total_output
                self._technical_coefficients = ic_part.div(total_output, axis=0)
                
                logger.info("Technical coefficients created", shape=self._technical_coefficients.shape)
            except Exception as error:
                logger.error(f"Error creating technical coefficients: {error}")
                raise error
        
        return self._technical_coefficients
    
    async def get_technical_coefficients_with_new_output(self, new_output: pd.Series) -> TechnicalCoefficientsMatrix:
        """
        Create technical coefficients matrix with new output levels
        Useful for scenario analysis with different production levels
        Does not cache - used for temporary calculations
        """
        try:
            # Calculate technical coefficients with new output: A = IC / new_output
            tech_coeffs = self.ic_df.div(new_output, axis=0)
            logger.info("Technical coefficients with new output created", shape=tech_coeffs.shape)
            return tech_coeffs
        except Exception as error:
            logger.error(f"Error creating technical coefficients with new output: {error}")
            raise error
    
    async def get_leontief_inverse(self) -> LeontiefInverseMatrix:
        """
        Create Leontief inverse matrix using instance data
        Cached for performance - calculated once and reused
        """
        if self._leontief_inverse is None:
            try:
                tech_coeffs = await self.get_technical_coefficients()
                n_sectors = tech_coeffs.shape[0]
                
                # Create identity matrix
                identity = pd.DataFrame(
                    np.eye(n_sectors), 
                    index=tech_coeffs.index, 
                    columns=tech_coeffs.columns
                )
                
                # Calculate (I - A) matrix
                leontief_matrix = identity - tech_coeffs
                
                # Calculate (I - A)^(-1)
                self._leontief_inverse = pd.DataFrame(
                    np.linalg.inv(leontief_matrix.values),
                    index=tech_coeffs.index,
                    columns=tech_coeffs.columns
                )
                
                logger.info("Leontief inverse created", shape=self._leontief_inverse.shape)
            except Exception as error:
                logger.error(f"Error creating Leontief inverse: {error}")
                raise error
        
        return self._leontief_inverse
    
    async def calculate_output_scenarios(self, fd_scenarios: List[pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Calculate output for multiple final demand scenarios using shared matrices
        Leverages cached technical coefficients and Leontief inverse
        """
        try:
            # Use cached technical coefficients and Leontief inverse
            leontief_inv = await self.get_leontief_inverse()
            
            results = []
            for i, fd_scenario in enumerate(fd_scenarios):
                # Calculate new output using shared Leontief inverse
                fd_vector = fd_scenario.sum(axis=1)  # Sum across final demand categories
                new_output = leontief_inv.values @ fd_vector.values
                
                results.append({
                    'scenario': i + 1,
                    'final_demand': fd_scenario.values.tolist(),
                    'total_output': new_output.tolist(),
                    'output_change': (new_output - self.fd_df.sum(axis=1).values).tolist()
                })
            
            logger.info(f"Calculated {len(fd_scenarios)} output scenarios using shared matrices")
            return results
            
        except Exception as error:
            logger.error(f"Error calculating output scenarios: {error}")
            raise error
    
    async def get_intermediate_consumption_matrix(self) -> IntermediateConsumptionMatrix:
        """
        Return the intermediate consumption matrix as DataFrame
        """
        try:
            logger.info("Intermediate consumption matrix accessed", shape=self.ic_df.shape)
            return self.ic_df.copy()
        except Exception as error:
            logger.error(f"Error accessing intermediate consumption matrix: {error}")
            raise error

    async def get_final_demand_matrix(self) -> FinalDemandMatrix:
        """
        Return the final demand matrix as DataFrame
        """
        try:
            logger.info("Final demand matrix accessed", shape=self.fd_df.shape)
            return self.fd_df.copy()
        except Exception as error:
            logger.error(f"Error accessing final demand matrix: {error}")
            raise error
    
    async def get_economic_multipliers(self) -> Dict[str, List[float]]:
        """
        Calculate various economic multipliers using shared Leontief inverse
        Cached for performance
        """
        if self._economic_multipliers is None:
            try:
                leontief_inv = await self.get_leontief_inverse()
                leontief_matrix = leontief_inv.values
                
                # Output multipliers (column sums)
                output_multipliers = np.sum(leontief_matrix, axis=0).tolist()
                
                # Type I multipliers (direct + indirect effects)
                type_i_multipliers = output_multipliers
                
                self._economic_multipliers = {
                    "output_multipliers": output_multipliers,
                    "type_i_multipliers": type_i_multipliers,
                    "matrix_shape": leontief_matrix.shape
                }
                
                logger.info("Economic multipliers calculated and cached")
            except Exception as error:
                logger.error(f"Error calculating multipliers: {error}")
                raise error
        
        return self._economic_multipliers
    
    async def calculate_output_with_new_fd(self, new_final_demand: np.ndarray) -> np.ndarray:
        """
        Calculate new output given new final demand using shared Leontief inverse
        Formula: X = (I - A)^(-1) * Y
        """
        try:
            leontief_inv = await self.get_leontief_inverse()
            # new_output = leontief_inv.values @ new_final_demand
            new_output = leontief_inv.dot(new_final_demand)
            logger.info("Output calculated with new final demand")
            return new_output
        except Exception as error:
            logger.error(f"Error calculating output with new FD: {error}")
            raise error
    
    def reset_cache(self):
        """
        Reset all cached calculations - useful when underlying data changes
        """
        self._io_matrix = None
        self._technical_coefficients = None
        self._leontief_inverse = None
        self._economic_multipliers = None
        logger.info("Matrix calculation cache reset")
    
    def update_data(self, intermediate_consumption_data: pd.DataFrame = None, final_demand_data: pd.DataFrame = None):
        """
        Update underlying data and reset cache
        """
        if intermediate_consumption_data is not None:
            self.ic_df = intermediate_consumption_data.copy()
            self.ic_data = self.ic_df.values
        
        if final_demand_data is not None:
            self.fd_df = final_demand_data.copy()
            self.fd_data = self.fd_df.values
        
        # Validate updated matrices
        self._validate_matrices()
        
        # Reset cache since data changed
        self.reset_cache()
        
        logger.info("Matrix data updated and cache reset")
    
    def _validate_matrices(self) -> None:
        """Validate that matrices have compatible dimensions"""
        ic_rows, ic_cols = self.ic_df.shape
        fd_rows, fd_cols = self.fd_df.shape
        
        if ic_rows != fd_rows:
            raise ValueError(f"Intermediate consumption matrix rows ({ic_rows}) must equal final demand matrix rows ({fd_rows})")
        
        # Check for non-numeric data
        if not self.ic_df.select_dtypes(include=[np.number]).shape == self.ic_df.shape:
            raise ValueError("Intermediate consumption matrix contains non-numeric data")
            
        if not self.fd_df.select_dtypes(include=[np.number]).shape == self.fd_df.shape:
            raise ValueError("Final demand matrix contains non-numeric data")
        
        logger.info(
            "Matrix dimensions validated",
            ic_shape=(ic_rows, ic_cols),
            fd_shape=(fd_rows, fd_cols)
        )

    @staticmethod
    def validate_matrix_data(data: pd.DataFrame) -> bool:
        """Validate that matrix data is well-formed DataFrame"""
        if data is None or not isinstance(data, pd.DataFrame):
            return False
        
        # Check for empty DataFrame
        if data.empty:
            return False
        
        # Check that all data is numeric
        try:
            pd.to_numeric(data.values.flatten())
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_matrix_data_legacy(data: List[List[float]]) -> bool:
        """Validate that matrix data is well-formed (legacy list-based version)"""
        if not data or not isinstance(data, list):
            return False
        
        if not all(isinstance(row, list) for row in data):
            return False
        
        # Check that all rows have the same length
        if len(set(len(row) for row in data)) > 1:
            return False
        
        # Check that all elements are numbers
        try:
            for row in data:
                for element in row:
                    float(element)
            return True
        except (ValueError, TypeError):
            return False
