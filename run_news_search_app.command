#!/bin/bash

# Navigate to the project directory
cd "/Users/kerid/Library/CloudStorage/OneDrive-uos.ac.kr/desktopCli/all_in_one"

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

# Run the Streamlit application
echo "Starting the News Search App..."
python3 -m streamlit run streamlit_app.py

echo "Application stopped."
read -p "Press any key to close this window..."