#!/bin/bash
# Run the Therapy Bot application

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with your GOOGLE_API_KEY"
    exit 1
fi

# Run the application
uv run chainlit run src/app.py
