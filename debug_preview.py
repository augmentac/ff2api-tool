#!/usr/bin/env python3
"""
Debug script to trace the exact issue with JSON preview display
"""

import sys
import os
sys.path.append('/Users/augiecon2025/Documents/SEDev/CSVv2')

from src.backend.data_processor import DataProcessor
from src.frontend.ui_components import generate_sample_api_preview
import pandas as pd
import json

def debug_preview_generation():
    """Debug the preview generation process step by step"""
    
    # Create test data similar to the actual use case
    test_data = {
        'load.route.0.address.city': 'HOT SPRINGS',
        'load.route.0.sequence': 1,
        'load.route.0.stopActivity': 'PICKUP',
        'load.route.0.expectedArrivalWindowStart': '2024-05-16T00:00:00.000Z',
        'load.route.0.expectedArrivalWindowEnd': '2024-05-16T00:00:00.000Z',
        'load.route.1.address.city': 'SELLERSBURG',
        'load.route.1.sequence': 2,
        'load.route.1.stopActivity': 'DELIVERY',
        'load.route.1.expectedArrivalWindowStart': '2024-05-17T00:00:00.000Z',
        'load.route.1.expectedArrivalWindowEnd': '2024-05-17T00:00:00.000Z',
        'load.loadNumber': '58164307',
        'customer.name': 'GE Current Lighting'
    }
    
    # Create field mappings (similar to what the UI would create)
    field_mappings = {field: field for field in test_data.keys()}
    
    # Create DataFrame
    df = pd.DataFrame([test_data])
    
    print("=== Step 1: Input Data ===")
    print("DataFrame columns:", list(df.columns))
    print("Field mappings:", field_mappings)
    
    # Create data processor
    data_processor = DataProcessor()
    
    print("\n=== Step 2: Generate API Preview ===")
    api_preview_data = generate_sample_api_preview(df, field_mappings, data_processor)
    
    print("Preview message:", api_preview_data["message"])
    print("Preview keys:", list(api_preview_data.keys()))
    
    if "preview" in api_preview_data:
        preview = api_preview_data["preview"]
        print("\n=== Step 3: Preview Structure ===")
        print("Preview type:", type(preview))
        print("Preview JSON:")
        print(json.dumps(preview, indent=2))
        
        # Check specifically the route structure
        if "load" in preview and "route" in preview["load"]:
            route = preview["load"]["route"]
            print(f"\n=== Step 4: Route Analysis ===")
            print(f"Route type: {type(route)}")
            print(f"Route value: {route}")
            if isinstance(route, list):
                print(f"Route is a list with {len(route)} items")
                for i, item in enumerate(route):
                    print(f"  Item {i}: {type(item)} -> {item}")
            else:
                print("Route is NOT a list")
                if hasattr(route, 'keys'):
                    print(f"Route keys: {list(route.keys())}")

if __name__ == '__main__':
    debug_preview_generation()