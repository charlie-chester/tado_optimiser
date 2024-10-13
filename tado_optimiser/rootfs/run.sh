echo "Running Tado Optimiser"
echo "Your API key is: $SUPERVISOR_TOKEN"

# Define the file paths
CONFIG_DIR="/config"
CONFIG_FILE="/config/settings.yaml"
DEFAULT_FILE="/settings.yaml"

# Check if the directory exists, if not create it
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Config directory not found, creating it..."
    mkdir -p "$CONFIG_DIR"
fi

# Check if the config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Settings file not found, copying default settings..."
    cp "$DEFAULT_FILE" "$CONFIG_FILE"
else
    echo "Settings file already exists, skipping copy."
fi

python3 /main.py "$SUPERVISOR_TOKEN"