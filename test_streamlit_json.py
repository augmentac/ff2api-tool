#!/usr/bin/env python3
"""
Test script to isolate Streamlit st.json() behavior
"""

import streamlit as st
import json

def main():
    st.title("Streamlit JSON Display Test")
    
    # Create test data with arrays to see how st.json handles them
    test_data = {
        "load": {
            "route": [
                {
                    "address": {
                        "city": "HOT SPRINGS"
                    },
                    "sequence": 1,
                    "stopActivity": "PICKUP"  
                },
                {
                    "address": {
                        "city": "SELLERSBURG"
                    },
                    "sequence": 2,
                    "stopActivity": "DELIVERY"
                }
            ],
            "loadNumber": "58164307"
        },
        "customer": {
            "name": "GE Current Lighting"
        }
    }
    
    st.header("Test Data:")
    st.write("Data type:", type(test_data))
    st.write("Route type:", type(test_data["load"]["route"]))
    st.write("Route length:", len(test_data["load"]["route"]))
    
    st.header("Using st.json():")
    st.json(test_data)
    
    st.header("Using st.code() with JSON dumps:")
    st.code(json.dumps(test_data, indent=2), language="json")
    
    st.header("Raw Python print:")
    st.text(str(test_data))

if __name__ == "__main__":
    main()