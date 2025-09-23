#!/usr/bin/env python3
"""
Script to pull and display all CSV mappings from the database.
"""

import sys
import os
import json
import sqlite3
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from database import DatabaseManager

def format_mapping_data(config):
    """Format configuration data for display."""
    print(f"\n{'='*80}")
    print(f"BROKERAGE: {config['brokerage_name']}")
    print(f"CONFIGURATION: {config.get('name', config.get('configuration_name', 'N/A'))}")
    print(f"{'='*80}")
    
    # Basic Info
    print(f"ID: {config['id']}")
    print(f"Description: {config.get('description', 'N/A')}")
    print(f"Auth Type: {config.get('auth_type', 'N/A')}")
    print(f"Version: {config.get('version', 'N/A')}")
    
    # Timestamps
    print(f"Created: {config.get('created_at', 'N/A')}")
    print(f"Updated: {config.get('updated_at', 'N/A')}")
    print(f"Last Used: {config.get('last_used_at', 'N/A')}")
    
    # Field Mappings
    print(f"\nFIELD MAPPINGS:")
    print(f"-" * 40)
    
    if config.get('field_mappings'):
        try:
            mappings = json.loads(config['field_mappings']) if isinstance(config['field_mappings'], str) else config['field_mappings']
            for api_field, csv_column in mappings.items():
                print(f"  {api_field:<40} → {csv_column}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"  Error parsing field mappings: {e}")
            print(f"  Raw data: {config['field_mappings']}")
    else:
        print("  No field mappings found")
    
    # File Headers
    print(f"\nFILE HEADERS:")
    print(f"-" * 40)
    
    if config.get('file_headers'):
        try:
            headers = json.loads(config['file_headers']) if isinstance(config['file_headers'], str) else config['file_headers']
            if isinstance(headers, list):
                for i, header in enumerate(headers, 1):
                    print(f"  {i:2d}. {header}")
            else:
                print(f"  {headers}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"  Error parsing file headers: {e}")
            print(f"  Raw data: {config['file_headers']}")
    else:
        print("  No file headers found")
    
    # API Credentials (masked for security)
    print(f"\nAPI CREDENTIALS:")
    print(f"-" * 40)
    if config.get('api_credentials'):
        try:
            creds = json.loads(config['api_credentials']) if isinstance(config['api_credentials'], str) else config['api_credentials']
            for key, value in creds.items():
                if value:
                    masked_value = f"{value[:4]}{'*' * (len(str(value)) - 4)}" if len(str(value)) > 4 else "****"
                    print(f"  {key}: {masked_value}")
                else:
                    print(f"  {key}: (empty)")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"  Error parsing API credentials: {e}")
    else:
        print("  No API credentials found")
    
    # Bearer Token (masked)
    if config.get('bearer_token'):
        token = config['bearer_token']
        masked_token = f"{token[:10]}...{token[-4:]}" if len(token) > 14 else "****"
        print(f"  bearer_token: {masked_token}")

def main():
    """Main function to retrieve and display all CSV mappings."""
    print("CSV Mappings Retrieval Tool")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Get all brokerage configurations
        print("\nRetrieving all brokerage configurations...")
        
        # Get database stats to match UI display
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        # Count configurations from both tables
        cursor.execute("SELECT COUNT(*) FROM brokerage_configurations")
        brokerage_configs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_mappings")
        legacy_configs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM upload_history")
        upload_count = cursor.fetchone()[0]
        
        print(f"Database stats: {brokerage_configs_count} brokerage configs, {legacy_configs_count} legacy configs, {upload_count} uploads")
        print(f"Total configurations: {brokerage_configs_count + legacy_configs_count}")
        
        # Get unique brokerage names from modern table
        cursor.execute("SELECT DISTINCT brokerage_name FROM brokerage_configurations ORDER BY brokerage_name")
        brokerages = [row[0] for row in cursor.fetchall()]
        
        # Get legacy customer mappings
        cursor.execute("SELECT customer_name, field_mappings, api_credentials, created_at, updated_at FROM customer_mappings")
        legacy_mappings = cursor.fetchall()
        
        conn.close()
        
        if not brokerages and not legacy_mappings:
            print("No configurations found in database.")
            return
        
        print(f"\nFound {len(brokerages)} brokerages with modern configurations:")
        
        total_configs = 0
        
        # Process modern brokerage configurations
        for brokerage in brokerages:
            configs = db_manager.get_brokerage_configurations(brokerage)
            
            if configs:
                print(f"\n{brokerage}: {len(configs)} configuration(s)")
                total_configs += len(configs)
                
                for config in configs:
                    format_mapping_data(config)
            else:
                print(f"\n{brokerage}: No configurations found")
        
        # Process legacy customer mappings
        if legacy_mappings:
            print(f"\n{'='*80}")
            print("LEGACY CUSTOMER MAPPINGS")
            print(f"{'='*80}")
            
            for mapping in legacy_mappings:
                customer_name, field_mappings, api_creds, created_at, updated_at = mapping
                
                # Format legacy mapping to match modern structure
                legacy_config = {
                    'id': 'legacy',
                    'brokerage_name': customer_name,
                    'name': 'Legacy Configuration',
                    'field_mappings': field_mappings,
                    'api_credentials': api_creds,
                    'created_at': created_at,
                    'updated_at': updated_at,
                    'auth_type': 'legacy',
                    'version': 'N/A',
                    'description': 'Legacy customer mapping',
                    'last_used_at': None,
                    'bearer_token': None,
                    'file_headers': None
                }
                
                format_mapping_data(legacy_config)
                total_configs += 1
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: {total_configs} total configurations ({brokerage_configs_count} modern + {legacy_configs_count} legacy)")
        print(f"Upload history: {upload_count} uploads")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"Error retrieving CSV mappings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()