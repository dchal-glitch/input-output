"""
Example usage of the updated MatrixService with pandas DataFrames
"""
import pandas as pd
import numpy as np
from services.matrix_service import MatrixService

# Example 1: Creating MatrixService with pandas DataFrames
def example_dataframe_usage():
    """Demonstrate how to use MatrixService with pandas DataFrames"""
    
    # Create sample intermediate consumption matrix with proper labels
    ic_data = pd.DataFrame(
        [[10, 15, 20], [25, 30, 35], [40, 45, 50]],
        columns=['Agriculture', 'Manufacturing', 'Services'],
        index=['Agriculture', 'Manufacturing', 'Services']
    )
    
    # Create sample final demand matrix with proper labels
    fd_data = pd.DataFrame(
        [[100, 50], [200, 75], [300, 100]],
        columns=['Household', 'Government'],
        index=['Agriculture', 'Manufacturing', 'Services']
    )
    
    print("=== Pandas DataFrame MatrixService Example ===")
    print(f"IC Matrix:\n{ic_data}")
    print(f"\nFD Matrix:\n{fd_data}")
    
    # Create MatrixService instance
    matrix_service = MatrixService(ic_data, fd_data)
    
    # Use static methods for pure calculations
    io_matrix = MatrixService.combine_matrices(ic_data, fd_data)
    print(f"\nCombined IO Matrix:\n{io_matrix}")
    
    # Calculate technical coefficients
    tech_coeffs = MatrixService.calculate_technical_coefficients(io_matrix, ic_data.shape[1])
    print(f"\nTechnical Coefficients:\n{tech_coeffs.round(4)}")
    
    # Calculate Leontief inverse
    leontief_inv = MatrixService.create_leontief_inverse(tech_coeffs)
    print(f"\nLeontief Inverse:\n{leontief_inv.round(4)}")
    
    return matrix_service

# Example 2: Backward compatibility with lists
def example_backward_compatibility():
    """Demonstrate backward compatibility with list data"""
    
    ic_list = [[10, 15, 20], [25, 30, 35], [40, 45, 50]]
    fd_list = [[100, 50], [200, 75], [300, 100]]
    
    print("\n=== Backward Compatibility Example ===")
    
    # Use factory method for list data
    matrix_service = MatrixService.from_lists(ic_list, fd_list)
    print(f"IC DataFrame from lists:\n{matrix_service.ic_df}")
    print(f"FD DataFrame from lists:\n{matrix_service.fd_df}")
    
    return matrix_service

# Example 3: Scenario analysis with different final demand
def example_scenario_analysis():
    """Demonstrate scenario analysis with different final demand scenarios"""
    
    print("\n=== Scenario Analysis Example ===")
    
    # Base matrices
    ic_data = pd.DataFrame(
        [[10, 15, 20], [25, 30, 35], [40, 45, 50]],
        columns=['Agriculture', 'Manufacturing', 'Services'],
        index=['Agriculture', 'Manufacturing', 'Services']
    )
    
    fd_base = pd.DataFrame(
        [[100, 50], [200, 75], [300, 100]],
        columns=['Household', 'Government'],
        index=['Agriculture', 'Manufacturing', 'Services']
    )
    
    # Scenario 1: Increased household demand
    fd_scenario1 = pd.DataFrame(
        [[120, 50], [240, 75], [360, 100]],
        columns=['Household', 'Government'],
        index=['Agriculture', 'Manufacturing', 'Services']
    )
    
    # Scenario 2: Increased government demand
    fd_scenario2 = pd.DataFrame(
        [[100, 70], [200, 105], [300, 140]],
        columns=['Household', 'Government'],
        index=['Agriculture', 'Manufacturing', 'Services']
    )
    
    # Calculate base technical coefficients and Leontief inverse once
    base_io = MatrixService.combine_matrices(ic_data, fd_base)
    tech_coeffs = MatrixService.calculate_technical_coefficients(base_io, ic_data.shape[1])
    leontief_inv = MatrixService.create_leontief_inverse(tech_coeffs)
    
    scenarios = [
        ("Base", fd_base),
        ("Increased Household", fd_scenario1),
        ("Increased Government", fd_scenario2)
    ]
    
    for name, fd_scenario in scenarios:
        # Calculate total output for this scenario
        fd_vector = fd_scenario.sum(axis=1).values
        new_output = MatrixService.calculate_output_with_new_fd(leontief_inv, fd_vector)
        
        print(f"\n{name} Scenario:")
        print(f"Final Demand Total: {fd_vector}")
        print(f"Required Output: {new_output.round(2)}")
        
        # Calculate multipliers
        multipliers = MatrixService.calculate_multipliers(leontief_inv)
        print(f"Output Multipliers: {[round(m, 3) for m in multipliers['output_multipliers']]}")

# Example 4: Data validation
def example_validation():
    """Demonstrate data validation features"""
    
    print("\n=== Data Validation Example ===")
    
    # Valid DataFrame
    valid_df = pd.DataFrame([[1, 2, 3], [4, 5, 6]], columns=['A', 'B', 'C'])
    print(f"Valid DataFrame validation: {MatrixService.validate_matrix_data(valid_df)}")
    
    # Invalid DataFrame (empty)
    empty_df = pd.DataFrame()
    print(f"Empty DataFrame validation: {MatrixService.validate_matrix_data(empty_df)}")
    
    # Invalid DataFrame (mixed types)
    mixed_df = pd.DataFrame([['a', 2, 3], [4, 5, 6]], columns=['A', 'B', 'C'])
    print(f"Mixed types DataFrame validation: {MatrixService.validate_matrix_data(mixed_df)}")
    
    # Legacy list validation
    valid_list = [[1, 2, 3], [4, 5, 6]]
    invalid_list = [[1, 2], [4, 5, 6]]  # Different row lengths
    
    print(f"Valid list validation: {MatrixService.validate_matrix_data_legacy(valid_list)}")
    print(f"Invalid list validation: {MatrixService.validate_matrix_data_legacy(invalid_list)}")

if __name__ == "__main__":
    # Run all examples
    matrix_service1 = example_dataframe_usage()
    matrix_service2 = example_backward_compatibility()
    example_scenario_analysis()
    example_validation()
    
    print("\n🎉 All examples completed successfully!")
    print("\nKey benefits of the updated MatrixService:")
    print("1. Native pandas DataFrame support with preserved indices and column names")
    print("2. Backward compatibility with list and numpy array data")
    print("3. Better data validation and error handling")
    print("4. More efficient matrix operations using pandas methods")
    print("5. Hybrid architecture with pure static functions for maximum reusability")
