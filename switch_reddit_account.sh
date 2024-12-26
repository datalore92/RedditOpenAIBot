#!/bin/bash

echo "=== Reddit Bot Account Switching Script ==="
echo "This script helps switch between Reddit accounts by clearing all cached credentials"
echo "Steps:"
echo "1. Stop the bot (Ctrl+C) before running this script"
echo "2. Edit .env file to comment/uncomment desired account"
echo "3. Run this script"
echo "4. Start the bot again"
echo ""
echo "Starting cleanup in 3 seconds..."
sleep 3

echo "1. Clearing PRAW (Reddit API) cached credentials..."
# These files store Reddit authentication tokens
rm -rf ~/.config/praw.ini
rm -rf ~/.cache/praw.*
rm -rf ~/.local/share/praw.*

echo "2. Clearing Python cache files..."
# Remove all compiled Python cache to force fresh imports
rm -rf __pycache__/
rm -rf */__pycache__/
rm -rf src/__pycache__/
rm -rf .pytest_cache/

echo "3. Recreating virtual environment..."
# Delete and recreate Python virtual environment for clean slate
rm -rf venv/
python3 -m venv venv
source venv/bin/activate

echo "4. Installing requirements..."
pip install -r requirements.txt

echo ""
echo "=== Cleanup Complete! ==="
echo "To switch accounts:"
echo "1. Edit .env file to enable desired account"
echo "2. Start bot: python -m src.bot"
echo ""
echo "Note: If still seeing old account,"
echo "try closing and reopening terminal completely"
