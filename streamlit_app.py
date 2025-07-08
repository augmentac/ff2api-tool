"""
FF2API - Streamlit Cloud Entry Point

This is the main entry point for Streamlit Cloud deployment.
It imports and runs the main application from src/frontend/app.py
"""

import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
if __name__ == "__main__":
    from frontend.app import main
    main() 