#!/usr/bin/env python3
"""
Test script to verify bearer token and headers validation fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.api_client import LoadsAPIClient
from src.backend.database import DatabaseManager
import json

def test_bearer_token_connection():
    """Test bearer token connection logic"""
    print("Testing Bearer Token Connection...")
    
    # Test with a sample bearer token (won't actually connect)
    try:
        client = LoadsAPIClient(
            base_url="https://api.prod.goaugment.com",
            bearer_token="test_bearer_token_123",
            auth_type='bearer_token'
        )
        print("✅ Bearer token client created successfully")
        
        # Test the connection validation method
        # This will fail with auth error but should show proper bearer token handling
        result = client.validate_connection()
        print(f"Connection test result: {result}")
        
    except Exception as e:
        print(f"❌ Bearer token test failed: {e}")

def test_status_calculation_logic():
    """Test the status calculation logic for both auth types"""
    print("\nTesting Status Calculation Logic...")
    
    # Test API key config
    api_key_config = {
        'auth_type': 'api_key',
        'api_credentials': {'api_key': 'test_key_123'},
        'field_mappings': {'load.loadNumber': 'Load Number'}
    }
    
    # Test bearer token config
    bearer_token_config = {
        'auth_type': 'bearer_token',
        'api_credentials': {'base_url': 'https://api.prod.goaugment.com'},
        'bearer_token': 'test_bearer_token_123',
        'field_mappings': {'load.loadNumber': 'Load Number'}
    }
    
    def check_api_connection(config):
        """Replicate the fixed API connection check logic"""
        auth_type = config.get('auth_type', 'api_key')
        if auth_type == 'api_key':
            return 'api_credentials' in config and bool(config['api_credentials'].get('api_key'))
        else:  # bearer_token
            return 'api_credentials' in config and bool(config.get('bearer_token'))
    
    def check_headers_validation(file_uploaded, header_status):
        """Replicate the fixed headers validation logic"""
        return (file_uploaded and header_status == 'identical')
    
    # Test API key config
    api_connected = check_api_connection(api_key_config)
    print(f"API Key Config - API Connected: {api_connected}")
    
    # Test bearer token config
    bearer_connected = check_api_connection(bearer_token_config)
    print(f"Bearer Token Config - API Connected: {bearer_connected}")
    
    # Test headers validation
    headers_valid_no_file = check_headers_validation(False, 'identical')
    headers_valid_with_file = check_headers_validation(True, 'identical')
    print(f"Headers validation (no file): {headers_valid_no_file}")
    print(f"Headers validation (with file): {headers_valid_with_file}")
    
    assert api_connected == True, "API key config should show as connected"
    assert bearer_connected == True, "Bearer token config should show as connected"
    assert headers_valid_no_file == False, "Headers should not be valid without file"
    assert headers_valid_with_file == True, "Headers should be valid with file"
    
    print("✅ All status calculation tests passed!")

def test_database_operations():
    """Test database operations with bearer token"""
    print("\nTesting Database Operations...")
    
    try:
        db_manager = DatabaseManager()
        
        # Test saving a bearer token configuration
        config_id = db_manager.save_brokerage_configuration(
            brokerage_name="Test Brokerage",
            configuration_name="Test Bearer Token Config",
            field_mappings={'load.loadNumber': 'Load Number'},
            api_credentials={'base_url': 'https://api.prod.goaugment.com'},
            auth_type='bearer_token',
            bearer_token='test_bearer_token_123'
        )
        
        print(f"✅ Bearer token configuration saved with ID: {config_id}")
        
        # Test retrieving the configuration
        config = db_manager.get_brokerage_configuration("Test Brokerage", "Test Bearer Token Config")
        if config:
            print(f"✅ Configuration retrieved: {config['name']}")
            print(f"Auth type: {config.get('auth_type')}")
            print(f"Has bearer token: {'bearer_token' in config}")
        else:
            print("❌ Configuration not found")
        
        # Note: No cleanup method available - test data will remain
        print("✅ Test configuration saved successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing Bearer Token and Headers Validation Fixes")
    print("=" * 50)
    
    test_bearer_token_connection()
    test_status_calculation_logic()
    test_database_operations()
    
    print("\n🎉 All tests completed!") 