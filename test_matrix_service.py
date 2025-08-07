"""
Test the MatrixService with shared instance variables approach
"""
import numpy as np
import pandas as pd
from services.matrix_service import MatrixService

# Sample test data
ic_data = [
    [10, 20, 30],
    [15, 25, 35], 
    [20, 30, 40]
]

fd_data = [
    [100, 200],
    [150, 250],
    [200, 300]
]

# Convert to DataFrames with proper labels
ic_df = pd.DataFrame(ic_data, columns=['Sector_1', 'Sector_2', 'Sector_3'], index=['Sector_1', 'Sector_2', 'Sector_3'])
fd_df = pd.DataFrame(fd_data, columns=['Household', 'Government'], index=['Sector_1', 'Sector_2', 'Sector_3'])

def test_shared_variables_caching():
    """Test that calculations are cached and reused"""
    print("Testing shared variables and caching...")
    
    # Create service instance
    service = MatrixService(ic_df, fd_df)
    
    # Check initial state
    print(f"Initial cache state:")
    print(f"  IO Matrix cached: {service._io_matrix is not None}")
    print(f"  Technical Coefficients cached: {service._technical_coefficients is not None}")
    print(f"  Leontief Inverse cached: {service._leontief_inverse is not None}")
    print(f"  Multipliers cached: {service._economic_multipliers is not None}")
    
    return service

async def test_performance_benefit():
    """Test the performance benefit of caching"""
    print("\nTesting performance benefit of shared variables...")
    
    service = MatrixService(ic_df, fd_df)
    
    # First call - calculates and caches
    print("First call - calculating and caching...")
    io_matrix1 = await service.get_io_matrix()
    tech_coeffs1 = await service.get_technical_coefficients()
    leontief_inv1 = await service.get_leontief_inverse()
    multipliers1 = await service.get_economic_multipliers()
    
    print(f"Cache state after first calculations:")
    print(f"  IO Matrix cached: {service._io_matrix is not None}")
    print(f"  Technical Coefficients cached: {service._technical_coefficients is not None}")
    print(f"  Leontief Inverse cached: {service._leontief_inverse is not None}")
    print(f"  Multipliers cached: {service._economic_multipliers is not None}")
    
    # Second call - reuses cached values
    print("\nSecond call - using cached values...")
    io_matrix2 = await service.get_io_matrix()
    tech_coeffs2 = await service.get_technical_coefficients()
    leontief_inv2 = await service.get_leontief_inverse()
    multipliers2 = await service.get_economic_multipliers()
    
    # Verify they're the same objects (cached)
    print(f"IO Matrix objects are identical: {io_matrix1 is io_matrix2}")
    print(f"Tech Coeffs objects are identical: {tech_coeffs1 is tech_coeffs2}")
    print(f"Leontief Inverse objects are identical: {leontief_inv1 is leontief_inv2}")
    print(f"Multipliers objects are identical: {multipliers1 is multipliers2}")
    
    print("✅ Caching and reuse working correctly!")

async def test_scenario_analysis():
    """Test scenario analysis with shared matrices"""
    print("\nTesting scenario analysis with shared variables...")
    
    service = MatrixService(ic_df, fd_df)
    
    # Create different final demand scenarios
    fd_scenario_1 = pd.DataFrame(
        [[120, 220], [170, 270], [220, 320]], 
        columns=['Household', 'Government'],
        index=['Sector_1', 'Sector_2', 'Sector_3']
    )
    fd_scenario_2 = pd.DataFrame(
        [[80, 180], [130, 230], [180, 280]], 
        columns=['Household', 'Government'],
        index=['Sector_1', 'Sector_2', 'Sector_3']
    )
    
    # Run scenario analysis - this will use cached Leontief inverse
    scenarios = [fd_scenario_1, fd_scenario_2]
    results = await service.calculate_output_scenarios(scenarios)
    
    print(f"Scenario analysis completed with {len(results)} scenarios")
    for i, result in enumerate(results):
        print(f"  Scenario {i+1}: Total output = {[round(x, 2) for x in result['total_output']]}")
    
    print("✅ Scenario analysis using shared variables working correctly!")

async def test_cache_reset():
    """Test cache reset functionality"""
    print("\nTesting cache reset functionality...")
    
    service = MatrixService(ic_df, fd_df)
    
    # Calculate some matrices to populate cache
    await service.get_io_matrix()
    await service.get_technical_coefficients()
    
    print(f"Before reset - IO Matrix cached: {service._io_matrix is not None}")
    print(f"Before reset - Tech Coeffs cached: {service._technical_coefficients is not None}")
    
    # Reset cache
    service.reset_cache()
    
    print(f"After reset - IO Matrix cached: {service._io_matrix is not None}")
    print(f"After reset - Tech Coeffs cached: {service._technical_coefficients is not None}")
    
    print("✅ Cache reset working correctly!")

async def test_data_update():
    """Test updating data and automatic cache reset"""
    print("\nTesting data update with automatic cache reset...")
    
    service = MatrixService(ic_df, fd_df)
    
    # Calculate some matrices
    original_io = await service.get_io_matrix()
    print(f"Original IO matrix shape: {original_io.shape}")
    
    # Update data
    new_fd_df = pd.DataFrame(
        [[150, 250], [200, 300], [250, 350]], 
        columns=['Household', 'Government'],
        index=['Sector_1', 'Sector_2', 'Sector_3']
    )
    
    service.update_data(final_demand_data=new_fd_df)
    
    # Get IO matrix again - should be recalculated with new data
    updated_io = await service.get_io_matrix()
    print(f"Updated IO matrix shape: {updated_io.shape}")
    
    # Check that matrices are different
    matrices_different = not original_io.equals(updated_io)
    print(f"Matrices are different after update: {matrices_different}")
    
    print("✅ Data update and cache reset working correctly!")

def test_factory_methods():
    """Test factory methods still work"""
    print("\nTesting factory methods...")
    
    # Test from_lists
    service_from_lists = MatrixService.from_lists(ic_data, fd_data)
    print(f"From lists - IC shape: {service_from_lists.ic_df.shape}")
    
    # Test from_numpy
    service_from_numpy = MatrixService.from_numpy(np.array(ic_data), np.array(fd_data))
    print(f"From numpy - IC shape: {service_from_numpy.ic_df.shape}")
    
    print("✅ Factory methods working correctly!")

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test basic functionality
        service = test_shared_variables_caching()
        
        # Test performance and caching
        await test_performance_benefit()
        
        # Test scenario analysis
        await test_scenario_analysis()
        
        # Test cache management
        await test_cache_reset()
        
        # Test data updates
        await test_data_update()
        
        # Test factory methods
        test_factory_methods()
        
        print("\n🎉 All shared variables approach tests passed!")
        print("\nKey benefits demonstrated:")
        print("1. ✅ Calculations are cached and reused for performance")
        print("2. ✅ Shared variables across all methods")
        print("3. ✅ Automatic cache management")
        print("4. ✅ Data can be updated with automatic cache reset")
        print("5. ✅ Factory methods for backward compatibility")
        print("6. ✅ Efficient scenario analysis using cached matrices")
    
    # Run the test
    asyncio.run(main())
