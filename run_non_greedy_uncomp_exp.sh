#!/bin/bash

# Path to your virtual environment
# Update this path to your actual venv location
VENV_PATH=".venv"

# Paths to your script and config folders
# Update these paths based on your project structure
SCRIPTS_DIR="./evaluation_scripts"
SCRIPT="eval_non_greedy_uncomp.py"
CONFIG_DIR="./eval_configs"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Check if activation was successful
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment at $VENV_PATH"
    exit 1
fi

echo "Virtual environment activated successfully"

# Check if config directory exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Config directory not found: $CONFIG_DIR"
    exit 1
fi

# Process each config file
for config_file in "$CONFIG_DIR"/*; do
    # Skip if not a regular file
    if [ ! -f "$config_file" ]; then
        continue
    fi
    
    # Get the base filename
    config_name=$(basename "$config_file")
    
    echo "Running experiment on config: $config_name"
    
    # Run the Python script with the config file as argument
    # Modify this line based on your actual script name and argument structure
    python "$SCRIPTS_DIR/$SCRIPT" "$config_file"
    
    # Check if the script executed successfully
    if [ $? -ne 0 ]; then
        echo "Error running script with config: $config_name"
    else
        echo "Successfully ran script with config: $config_name"
    fi
    
    echo "------------------------"
done

# Deactivate the virtual environment
deactivate

echo "All configs processed. Virtual environment deactivated."