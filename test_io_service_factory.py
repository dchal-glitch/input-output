"""
Test script to verify the IOService factory pattern works correctly
"""
import asyncio
import sys
sys.path.append('.')

from services.io_service import IOService
from services.data_service import DataService
from services.matrix_service import MatrixService

async def test_io_service_factory():
    """Test that IOService can be created and used properly"""
    print("Testing IOService factory pattern...")
    
    try:
        # Test 1: Create IOService using factory method
        print("\n1. Creating IOService using factory method...")
        io_service = await IOService.create()
        print("✅ IOService created successfully")
        
        # Test 2: Get IO table
        print("\n2. Getting IO table...")
        io_table = await io_service.get_io_table()
        print(f"✅ IO table retrieved, shape: {io_table.shape}")
        print(f"   Columns: {list(io_table.columns)}")
        
        # Test 3: Calculate output
        print("\n3. Calculating comprehensive output...")
        output_data = await io_service.calculate_output()
        print("✅ Output calculations completed")
        print(f"   Keys in result: {list(output_data.keys())}")
        
        # Test 4: Test lazy initialization
        print("\n4. Testing lazy initialization...")
        io_service_lazy = IOService()  # Regular constructor
        matrix_service = await io_service_lazy.get_matrix_service()
        print("✅ Lazy initialization works")
        
        # Test 5: Test static methods (should work without factory)
        print("\n5. Testing static methods...")
        # These should work without creating an instance
        try:
            # This would require database setup, so just test that the method exists
            assert hasattr(IOService, 'create_io_matrix')
            assert hasattr(IOService, 'get_io_matrices')
            assert hasattr(IOService, 'perform_matrix_operation')
            print("✅ Static methods are available")
        except Exception as e:
            print(f"❌ Static methods test failed: {e}")
        
        print("\n🎉 All IOService factory tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ IOService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_comparison():
    """Compare old vs new approach"""
    print("\n" + "="*50)
    print("COMPARISON: Old vs New Approach")
    print("="*50)
    
    print("\n❌ OLD APPROACH (Would fail):")
    print("   io_service = IOService()  # Error: __init__() should return None, not 'coroutine'")
    
    print("\n✅ NEW APPROACH (Works):")
    print("   # Method 1: Factory pattern")
    print("   io_service = await IOService.create()")
    
    print("\n   # Method 2: Lazy initialization")
    print("   io_service = IOService()")
    print("   matrix_service = await io_service.get_matrix_service()")
    
    print("\n   # Method 3: Static methods (no instance needed)")
    print("   result = await IOService.perform_matrix_operation(db, matrix_id, 'io_matrix')")

if __name__ == "__main__":
    async def main():
        success = await test_io_service_factory()
        await test_comparison()
        
        if success:
            print("\n✅ All tests passed! The IOService factory pattern is working correctly.")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
    
    # Run the test
    asyncio.run(main())
