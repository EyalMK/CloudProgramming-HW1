#!/bin/bash

FIREBASE_URI="https://shapeflow-monitor-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_PATH="/" # Change this to the path you want to clear
SCRIPT_DIR=$(dirname "$0")
JSON_FILE="$SCRIPT_DIR/onshape_glossary_words.json" # Path to the JSON file

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help          Show this help message and exit"
    echo "  --glossary      Clear the Firebase data and post the glossary words from the JSON file"
}

# Check for --help flag
for arg in "$@"; do
    if [[ "$arg" == "--help" ]]; then
        show_help
        exit 0
    fi
done

# Check if the JSON file exists
if [[ ! -f $JSON_FILE ]]; then
    echo "JSON file $JSON_FILE not found."
    exit 1
fi

# Check for the --glossary flag
POST_GLOSSARY_WORDS=False
for arg in "$@"; do
    if [[ "$arg" == "--glossary" ]]; then
        POST_GLOSSARY_WORDS=True
        break
    fi
done

# Create a temporary Python script to clear the data and optionally post the new data
PYTHON_SCRIPT=$(mktemp)

cat <<EOF > $PYTHON_SCRIPT
from firebase import firebase
import json
import sys

# Define the Firebase URI and the path to clear
firebase_uri = "$FIREBASE_URI"
firebase_path = "$FIREBASE_PATH"
json_file_path = "$JSON_FILE"

# Initialize the Firebase application
firebase_app = firebase.FirebaseApplication(firebase_uri, None)

# Clear the data at the specified path
try:
    result = firebase_app.delete(firebase_path, None)
    print("Data cleared successfully.")
except Exception as e:
    print(f"Error clearing data: {e}", file=sys.stderr)
    sys.exit(1)

# Post the data if the flag is set
if $POST_GLOSSARY_WORDS:
    # Read the JSON file
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        sys.exit(1)

    # Post the data to Firebase
    try:
        for key, value in data.items():
            firebase_app.put(firebase_path, key, value)
        print("Data posted successfully.")
    except Exception as e:
        print(f"Error posting data: {e}", file=sys.stderr)
        sys.exit(1)
EOF

# Run the Python script
python $PYTHON_SCRIPT

# Remove the temporary Python script
rm $PYTHON_SCRIPT
