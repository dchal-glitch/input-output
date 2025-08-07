import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DataService:
    """Service for fetching Input-Output data from various sources (CSV, database, APIs)"""
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize DataService
        
        Args:
            data_directory: Directory containing CSV files. Defaults to 'data' folder in project root
        """
        if data_directory is None:
            # Default to 'data' directory in project root
            project_root = Path(__file__).parent.parent
            self.data_directory = project_root / "data"
        else:
            self.data_directory = Path(data_directory)
        
        # Create data directory if it doesn't exist
        self.data_directory.mkdir(exist_ok=True)
        
        logger.info(f"DataService initialized with data directory: {self.data_directory}")

    async def get_intermediate_consumption_data(self, file_name: str = "IODATA_dummy.csv", format: str = "list") -> Dict[str, Any]:
        """
        Fetch Intermediate Consumption data from CSV file with sector labels
        
        Args:
            file_name: Name of the CSV file containing IC data
            
        Returns:
            Dictionary containing:
            - 'data': 2D list of intermediate consumption matrix data
            - 'row_sectors': List of row sector names
            - 'column_sectors': List of column sector names
            - 'dimensions': Tuple of (rows, columns)
        """
        try:
            file_path = self.data_directory / file_name
            
            if not file_path.exists():
                logger.warning(f"CSV file not found: {file_path}")
                # Return sample data if file doesn't exist
                return self._get_sample_ic_data()
            
            logger.info(f"Reading intermediate consumption data from: {file_path}")
            
            # Read CSV using pandas for better handling
            df = pd.read_csv(file_path)
            # Extract row sectors (first column, excluding header)
            row_sectors = df.iloc[:, 0].tolist()
            
            # Extract column sectors (header row, excluding first column)
            column_sectors = df.columns[1:].tolist()  # Skip first column name
            
            df = df.set_index(df.columns[0]) 
            # df = df.drop(df.index[-1])

            # # Remove last row if it contains totals (common in IO tables)
            # if len(df) > 0:
            #     # Check if last row contains totals (you can customize this logic)
            #     last_row_name = df.index[-1].lower() if isinstance(df.index[-1], str) else str(df.index[-1]).lower()
            #     if 'total' in last_row_name or 'sum' in last_row_name:
            #         df = df.drop(df.index[-1])
            #         row_sectors = row_sectors[:-1]  # Also remove from row_sectors
            
            # Convert to numeric, replacing commas and handling errors
            df = df.apply(lambda x: pd.to_numeric(
                x.astype(str).str.replace(',', ''), 
                errors='coerce'
            )).fillna(0)
            
            if format == "list":

                # Convert to list of lists
                data_matrix = df.values.tolist()

                result ={
                    'data': data_matrix,
                    'row_sectors': row_sectors,
                    'column_sectors': column_sectors,
                    'dimensions': (len(data_matrix), len(data_matrix[0]) if data_matrix else 0),
                    'matrix_type': 'intermediate_consumption'
                }
            
                logger.info(f"Successfully loaded IC data: {result['dimensions'][0]}x{result['dimensions'][1]} matrix")

            elif format == 'pandas':
                result = df
            logger.info(f"Row sectors: {row_sectors[:3]}{'...' if len(row_sectors) > 3 else ''}")
            logger.info(f"Column sectors: {column_sectors[:3]}{'...' if len(column_sectors) > 3 else ''}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch intermediate consumption data: {str(e)}")
            raise Exception(f"Failed to fetch IO data: {str(e)}")

    async def get_final_demand_data(self, file_name: str = "FD_dummy.csv", format="list") -> List[List[float]]:
        """
        Fetch Final Demand data from CSV file
        
        Args:
            file_name: Name of the CSV file containing FD data
            
        Returns:
            2D list of final demand matrix data
        """
        try:
            file_path = self.data_directory / file_name
            
            if not file_path.exists():
                logger.warning(f"CSV file not found: {file_path}")
                # Return sample data if file doesn't exist
                return self._get_sample_fd_data()
            
            logger.info(f"Reading final demand data from: {file_path}")
            
            # Read CSV using pandas
            df = pd.read_csv(file_path)

            # Extract row sectors (first column, excluding header)
            row_sectors = df.iloc[:, 0].tolist()
            # Extract column sectors (header row, excluding first column)
            column_sectors = df.columns[1:].tolist()


            df = df.set_index(df.columns[0]) 
            
            
            
            # Convert to numeric, replacing commas and handling errors
            df = df.apply(lambda x: pd.to_numeric(
                x.astype(str).str.replace(',', ''), 
                errors='coerce'
            )).fillna(0)
            
            if format == "list":
                # Convert to list of lists
                data_matrix = df.values.tolist()
            elif format == 'pandas':
                data_matrix = df
            logger.info(f"Row sectors: {row_sectors[:3]}{'...' if len(row_sectors) > 3 else ''}")
            logger.info(f"Column sectors: {column_sectors[:3]}{'...' if len(column_sectors) > 3 else ''}")
            return data_matrix
            
        except Exception as e:
            logger.error(f"Failed to fetch final demand data: {str(e)}")
            raise Exception(f"Failed to fetch FD data: {str(e)}")
        
    async def get_updated_final_demand_data(self, change_data =[]) -> pd.DataFrame:
        final_demand_matrix = await self.get_final_demand_data( format='pandas')
        try:
            if not change_data:
                logger.warning("No changes provided for final demand data")
                return final_demand_matrix
            logger.info(f"Applying changes to final demand data: {change_data}")
            for change_conf in change_data:
                sector = change_conf.get("sector")
                demand = change_conf.get("demand")
                value = change_conf.get("value")

                if sector in final_demand_matrix.index and demand in final_demand_matrix.columns:
                    final_demand_matrix.at[sector, demand] = value
                    logger.info(f"Updated FD matrix at ({sector}, {demand}) to {value}")
            return final_demand_matrix
        except Exception as e:
            logger.error(f"Failed to update final demand data: {str(e)}")
            raise Exception(f"Failed to update FD data: {str(e)}")

    async def get_sector_labels(self, file_name: str = "sectors.csv") -> List[str]:
        """
        Fetch sector labels from CSV file
        
        Args:
            file_name: Name of the CSV file containing sector labels
            
        Returns:
            List of sector names/labels
        """
        try:
            file_path = self.data_directory / file_name
            
            if not file_path.exists():
                logger.warning(f"Sector labels file not found: {file_path}")
                return self._get_sample_sector_labels()
            
            logger.info(f"Reading sector labels from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Assume first column contains sector labels
                sectors = [row[0] for row in reader if row]
            
            logger.info(f"Successfully loaded {len(sectors)} sector labels")
            return sectors
            
        except Exception as e:
            logger.error(f"Failed to fetch sector labels: {str(e)}")
            return self._get_sample_sector_labels()

    async def update_io_data(self, matrix_id: int, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update IO data (this would typically update database records)
        
        Args:
            matrix_id: ID of the matrix to update
            updated_data: New data to update
            
        Returns:
            Updated data dictionary
        """
        try:
            # In a real implementation, this would update database records
            # For now, we'll just return the updated data
            logger.info(f"Updating IO data for matrix ID: {matrix_id}")
            
            # TODO: Implement database update logic here
            # This could involve:
            # - Updating records in PostgreSQL
            # - Calling external APIs
            # - Writing to CSV files
            
            updated_data['id'] = matrix_id
            updated_data['updated_at'] = pd.Timestamp.now().isoformat()
            
            logger.info(f"Successfully updated IO data for matrix ID: {matrix_id}")
            return updated_data
            
        except Exception as e:
            logger.error(f"Failed to update IO data: {str(e)}")
            raise Exception(f"Failed to update IO data: {str(e)}")

    async def fetch_from_external_api(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetch IO data from external API
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the API call
            
        Returns:
            API response data
        """
        try:
            import httpx
            
            base_url = settings.external_api_base_url
            if not base_url:
                raise Exception("External API base URL not configured")
            
            headers = {}
            if settings.external_api_key:
                headers["Authorization"] = f"Bearer {settings.external_api_key}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/{endpoint}",
                    params=params or {},
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched data from external API: {endpoint}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to fetch data from external API: {str(e)}")
            raise Exception(f"Failed to fetch data from external API: {str(e)}")

    def _get_sample_ic_data(self) -> List[List[float]]:
        """Return sample intermediate consumption data for testing"""
        logger.info("Returning sample intermediate consumption data")
        return [
            [100.5, 200.0, 150.2],
            [300.1, 400.8, 250.5],
            [150.0, 100.3, 350.7]
        ]

    def _get_sample_fd_data(self) -> List[List[float]]:
        """Return sample final demand data for testing"""
        logger.info("Returning sample final demand data")
        return [
            [500.0, 300.0],
            [600.5, 400.2],
            [450.8, 350.1]
        ]

    def _get_sample_sector_labels(self) -> List[str]:
        """Return sample sector labels for testing"""
        logger.info("Returning sample sector labels")
        return ["Agriculture", "Manufacturing", "Services"]

    async def save_matrix_to_csv(self, matrix: List[List[float]], file_name: str) -> str:
        """
        Save matrix data to CSV file
        
        Args:
            matrix: 2D list of matrix data
            file_name: Name of the output CSV file
            
        Returns:
            Path to the saved file
        """
        try:
            file_path = self.data_directory / file_name
            
            df = pd.DataFrame(matrix)
            df.to_csv(file_path, index=False, header=False)
            
            logger.info(f"Matrix data saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save matrix to CSV: {str(e)}")
            raise Exception(f"Failed to save matrix to CSV: {str(e)}")

    async def validate_matrix_dimensions(self, ic_matrix: List[List[float]], fd_matrix: List[List[float]]) -> bool:
        """
        Validate that IC and FD matrices have compatible dimensions
        
        Args:
            ic_matrix: Intermediate consumption matrix
            fd_matrix: Final demand matrix
            
        Returns:
            True if dimensions are compatible, False otherwise
        """
        try:
            if not ic_matrix or not fd_matrix:
                return False
            
            ic_rows = len(ic_matrix)
            ic_cols = len(ic_matrix[0]) if ic_matrix else 0
            fd_rows = len(fd_matrix)
            
            # IC matrix should be square and FD matrix should have same number of rows
            is_valid = ic_rows == ic_cols and ic_rows == fd_rows
            
            if is_valid:
                logger.info(f"Matrix dimensions validated: IC({ic_rows}x{ic_cols}), FD({fd_rows}x{len(fd_matrix[0]) if fd_matrix else 0})")
            else:
                logger.warning(f"Invalid matrix dimensions: IC({ic_rows}x{ic_cols}), FD({fd_rows}x{len(fd_matrix[0]) if fd_matrix else 0})")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating matrix dimensions: {str(e)}")
            return False
