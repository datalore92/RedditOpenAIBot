#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create src directory if it doesn't exist
mkdir -p src

echo "Setup complete! To run the bot:"
echo "1. First activate the virtual environment: source venv/bin/activate"
echo "2. Then run the bot: python -m src.bot"
