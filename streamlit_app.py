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
    try:
        from src.frontend.app import main
        main()
    except ImportError:
        # Fallback import path
        from frontend.app import main
        main()
else:
    # For Streamlit Cloud (when imported as module)
    try:
        from src.frontend.app import main
        main()
    except ImportError:
        # Fallback import path
        from frontend.app import main
        main() 