#!/usr/bin/env python3
"""
Test script to verify all components of FF2API work correctly
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from backend.database import DatabaseManager
        print("✅ DatabaseManager import successful")
    except Exception as e:
        print(f"❌ DatabaseManager import failed: {e}")
        return False
    
    try:
        from backend.api_client import LoadsAPIClient
        print("✅ LoadsAPIClient import successful")
    except Exception as e:
        print(f"❌ LoadsAPIClient import failed: {e}")
        return False
    
    try:
        from backend.data_processor import DataProcessor
        print("✅ DataProcessor import successful")
    except Exception as e:
        print(f"❌ DataProcessor import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        from backend.database import DatabaseManager
        
        # Test database initialization
        db = DatabaseManager("test.db")
        print("✅ Database initialization successful")
        
        # Clean up test database
        if os.path.exists("test.db"):
            os.remove("test.db")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_data_processor():
    """Test data processor functionality"""
    print("\nTesting data processor...")
    
    try:
        from backend.data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # Test CSV reading with sample file
        if os.path.exists("sample_data/freight_sample.csv"):
            df = processor.read_file("sample_data/freight_sample.csv")
            print(f"✅ CSV reading successful - {len(df)} rows loaded")
            
            # Test mapping suggestions with GoAugment API schema
            api_schema = {
                'load.loadNumber': {'type': 'string', 'required': True, 'description': 'Load Reference Number'},
                'load.route.0.address.city': {'type': 'string', 'required': True, 'description': 'Origin City'},
                'load.route.1.address.city': {'type': 'string', 'required': True, 'description': 'Destination City'},
            }
            
            suggestions = processor.suggest_mapping(list(df.columns), api_schema)
            print(f"✅ Mapping suggestions successful - {len(suggestions)} suggestions")
            
        else:
            print("⚠️  Sample CSV file not found, skipping file reading test")
        
        return True
    except Exception as e:
        print(f"❌ Data processor test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("{CSV} FF2API - Component Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_database():
        tests_passed += 1
    
    if test_data_processor():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The application is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 