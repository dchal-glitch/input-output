"""
Sample data creation script for Input-Output matrices

This script provides sample data that can be used to test the IO functionality.
It includes realistic economic data for a simple 3-sector economy.
"""

# Sample 3-sector economy: Agriculture, Manufacturing, Services
SAMPLE_SECTORS = ["Agriculture", "Manufacturing", "Services"]

# Intermediate Consumption Matrix (3x3)
# Shows how much each sector consumes from other sectors
SAMPLE_INTERMEDIATE_CONSUMPTION = [
    [50, 200, 100],   # Agriculture: consumes from Agri(50), Mfg(200), Services(100)
    [100, 300, 150],  # Manufacturing: consumes from Agri(100), Mfg(300), Services(150)  
    [25, 150, 200]    # Services: consumes from Agri(25), Mfg(150), Services(200)
]

# Final Demand Matrix (3x1) 
# Shows final demand for each sector's output
SAMPLE_FINAL_DEMAND = [
    [400],  # Agriculture final demand
    [500],  # Manufacturing final demand
    [300]   # Services final demand
]

# Larger 5-sector example
SAMPLE_5_SECTORS = ["Agriculture", "Mining", "Manufacturing", "Construction", "Services"]

SAMPLE_5_INTERMEDIATE_CONSUMPTION = [
    [20, 30, 50, 10, 40],    # Agriculture
    [5, 100, 200, 50, 25],   # Mining
    [15, 150, 300, 100, 80], # Manufacturing
    [5, 20, 80, 50, 30],     # Construction
    [10, 40, 100, 60, 150]   # Services
]

SAMPLE_5_FINAL_DEMAND = [
    [350],  # Agriculture
    [200],  # Mining
    [450],  # Manufacturing
    [400],  # Construction
    [600]   # Services
]

# Test cases with validation issues
INVALID_MATRICES = {
    "empty": [],
    "inconsistent_rows": [[1, 2, 3], [4, 5]],
    "non_numeric": [[1, 2, "invalid"], [4, 5, 6]],
    "incompatible_dimensions": {
        "intermediate": [[1, 2], [3, 4]],  # 2x2
        "final_demand": [[100], [200], [300]]  # 3x1 - incompatible
    }
}

def create_sample_io_matrix_data():
    """Create sample IO matrix data for API testing"""
    return {
        "name": "Sample 3-Sector Economy",
        "description": "A sample input-output matrix for testing purposes with Agriculture, Manufacturing, and Services sectors",
        "sectors": SAMPLE_SECTORS,
        "intermediate_consumption_data": SAMPLE_INTERMEDIATE_CONSUMPTION,
        "final_demand_data": SAMPLE_FINAL_DEMAND
    }

def create_large_sample_io_matrix_data():
    """Create larger sample IO matrix data for performance testing"""
    return {
        "name": "Sample 5-Sector Economy",
        "description": "A larger sample input-output matrix with 5 economic sectors",
        "sectors": SAMPLE_5_SECTORS,
        "intermediate_consumption_data": SAMPLE_5_INTERMEDIATE_CONSUMPTION,
        "final_demand_data": SAMPLE_5_FINAL_DEMAND
    }

def get_expected_results():
    """Get expected calculation results for validation"""
    # For the 3-sector sample data, these are the expected results
    return {
        "total_output": [750, 1050, 725],  # Sum of intermediate + final demand for each sector
        "technical_coefficients_sample": [
            [50/750, 200/750, 100/750],   # Agriculture coefficients
            [100/1050, 300/1050, 150/1050], # Manufacturing coefficients  
            [25/725, 150/725, 200/725]    # Services coefficients
        ]
    }

if __name__ == "__main__":
    # Print sample data for manual testing
    print("Sample 3-Sector IO Matrix Data:")
    print(f"Sectors: {SAMPLE_SECTORS}")
    print(f"Intermediate Consumption: {SAMPLE_INTERMEDIATE_CONSUMPTION}")
    print(f"Final Demand: {SAMPLE_FINAL_DEMAND}")
    print()
    
    print("Expected Results:")
    results = get_expected_results()
    print(f"Total Output: {results['total_output']}")
    print(f"Sample Technical Coefficients (first row): {results['technical_coefficients_sample'][0]}")
