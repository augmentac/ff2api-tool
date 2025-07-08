#!/bin/bash

# Local startup script for FF2API (without Docker)

echo "{CSV} Starting FF2API locally..."

# Create necessary directories
mkdir -p data/{uploads,mappings,logs} config

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if required packages are installed
python3 -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip3 install -r requirements.txt
fi

# Run tests to verify everything works
echo "🧪 Running component tests..."
python3 test_app.py

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "🚀 Starting Streamlit application..."
    echo "📖 Open your browser to http://localhost:8501"
    echo "🛑 Press Ctrl+C to stop the application"
    
    # Add streamlit to PATH if needed
    export PATH="$HOME/Library/Python/3.9/bin:$PATH"
    
    # Start the application
    streamlit run src/frontend/app.py --server.port=8501 --server.address=0.0.0.0
else
    echo "❌ Tests failed! Please check the error messages above."
    exit 1
fi 