#!/usr/bin/env python3
"""
Debug script to check database counts and compare with UI display
"""

import sys
import os
import sqlite3

# Add the project paths
sys.path.append('/Users/augiecon2025/Documents/SEDev/CSVv2')
sys.path.append('/Users/augiecon2025/Documents/SEDev/CSVv2/src')

from src.backend.database import DatabaseManager

def check_database_counts():
    """Check all database counts to match UI display"""
    print("Database Count Analysis")
    print("=" * 50)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Get stats using the same method as the UI
        stats = db_manager.get_database_stats()
        
        print("Using get_database_stats() method (same as UI):")
        print(f"  brokerage_configurations: {stats['brokerage_configurations']}")
        print(f"  customer_mappings (legacy): {stats['customer_mappings']}")
        print(f"  upload_history: {stats['upload_history']}")
        
        # Now check what the UI would display
        legacy_configs = stats['customer_mappings']
        brokerage_configs = stats['brokerage_configurations']
        uploads = stats['upload_history']
        
        summary_parts = []
        if brokerage_configs > 0:
            summary_parts.append(f"{brokerage_configs} brokerage configs")
        if legacy_configs > 0:
            summary_parts.append(f"{legacy_configs} legacy configs")
        if uploads > 0:
            summary_parts.append(f"{uploads} uploads")
        
        ui_display = ', '.join(summary_parts)
        print(f"\nUI would display: '{ui_display}'")
        
        # Let's also check if there might be any combined logic
        print(f"\nDetailed breakdown:")
        print(f"  - Pure brokerage configs: {brokerage_configs}")
        print(f"  - Legacy customer mappings: {legacy_configs}")
        print(f"  - Total configurations: {brokerage_configs + legacy_configs}")
        print(f"  - Upload history entries: {uploads}")
        
        # Now let's manually query the database to double check
        print(f"\nManual database queries:")
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        # Check brokerage_configurations table
        cursor.execute('SELECT COUNT(*) FROM brokerage_configurations')
        manual_brokerage_count = cursor.fetchone()[0]
        print(f"  Manual brokerage_configurations count: {manual_brokerage_count}")
        
        # Check customer_mappings table  
        cursor.execute('SELECT COUNT(*) FROM customer_mappings')
        manual_legacy_count = cursor.fetchone()[0]
        print(f"  Manual customer_mappings count: {manual_legacy_count}")
        
        # Check upload_history table
        cursor.execute('SELECT COUNT(*) FROM upload_history')
        manual_upload_count = cursor.fetchone()[0]
        print(f"  Manual upload_history count: {manual_upload_count}")
        
        # Let's see what's actually in these tables
        print(f"\nActual brokerage configurations:")
        cursor.execute('SELECT brokerage_name, configuration_name FROM brokerage_configurations ORDER BY brokerage_name, configuration_name')
        brokerage_rows = cursor.fetchall()
        for i, (brokerage, config_name) in enumerate(brokerage_rows, 1):
            print(f"  {i}. {brokerage} -> {config_name}")
        
        print(f"\nActual customer mappings (legacy):")
        cursor.execute('SELECT customer_name, COUNT(*) as config_count FROM customer_mappings GROUP BY customer_name ORDER BY customer_name')
        legacy_rows = cursor.fetchall()
        for i, (customer, count) in enumerate(legacy_rows, 1):
            print(f"  {i}. {customer} -> {count} mapping(s)")
            
        conn.close()
        
        print(f"\n" + "="*50)
        print(f"ANALYSIS:")
        print(f"If the UI shows '13 brokerage configs', it might be:")
        print(f"  - Combining brokerage_configurations ({brokerage_configs}) + customer_mappings ({legacy_configs}) = {brokerage_configs + legacy_configs}")
        print(f"  - Or there might be a bug in your script's counting logic")
        print(f"  - Or the database was different when you ran your script")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_counts()