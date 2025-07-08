#!/bin/bash

# Create necessary directories
mkdir -p data/{uploads,mappings,logs} config

# Build and run with Docker Compose
echo "Building FF2API..."
docker-compose build

echo "Starting FF2API..."
docker-compose up -d

echo "FF2API is running at http://localhost:8501"
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f" 