#!/bin/bash

FIREBASE_URI="https://shapeflow-monitor-final-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_PATH="/" # Change this to the path you want to clear
SCRIPT_DIR=$(dirname "$0")
PATTERNS_FILE="$SCRIPT_DIR/jsons/chat_patterns.json" # Path to the JSON file containing chat patterns
GLOSSARY_FILE="$SCRIPT_DIR/jsons/onshape_glossary_words.json" # Path to the JSON file containing glossary words

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help          Show this help message and exit"
    echo "  --chatbot       Clear the Firebase data and post the chat prompts from the JSON file"
    echo "  --glossary      Clear the Firebase data and post the glossary words from the JSON file"
}

# Check for --help flag
for arg in "$@"; do
    if [[ "$arg" == "--help" ]]; then
        show_help
        exit 0
    fi
done

# Initialize flags
POST_CHAT_PROMPTS=False
POST_GLOSSARY_WORDS=False

# Check for flags
for arg in "$@"; do
    if [[ "$arg" == "--chatbot" ]]; then
        POST_CHAT_PROMPTS=True
    fi
    if [[ "$arg" == "--glossary" ]]; then
        POST_GLOSSARY_WORDS=True
    fi
done

# Check if the JSON files exist
if [[ "$POST_CHAT_PROMPTS" && ! -f $PATTERNS_FILE ]]; then
    echo "JSON file $PATTERNS_FILE not found."
    exit 1
fi

if [[ "$POST_GLOSSARY_WORDS" && ! -f $GLOSSARY_FILE ]]; then
    echo "JSON file $GLOSSARY_FILE not found."
    exit 1
fi

# Create a temporary Python script to clear the data and optionally post the new data
PYTHON_SCRIPT=$(mktemp)

cat <<EOF > $PYTHON_SCRIPT
from firebase import firebase
import json
import sys

# Define the Firebase URI and the path to clear
firebase_uri = "$FIREBASE_URI"
firebase_path = "$FIREBASE_PATH"
patterns_file_path = "$PATTERNS_FILE"
glossary_file_path = "$GLOSSARY_FILE"

# Initialize the Firebase application
firebase_app = firebase.FirebaseApplication(firebase_uri, None)

# Function to clear data at the specified path
def clear_data():
    try:
        result = firebase_app.delete(firebase_path, None)
        print("All Data cleared successfully.")
    except Exception as e:
        print(f"Error clearing data: {e}", file=sys.stderr)
        sys.exit(1)

# Function to post data from a JSON file
def post_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        for key, value in data.items():
            firebase_app.put(firebase_path, key, value)
        print(f"{file_path} Data posted successfully.")
    except Exception as e:
        print(f"Error posting data: {e}", file=sys.stderr)
        sys.exit(1)

# Clear data
clear_data()

# Post chat prompts if flag is set
if $POST_CHAT_PROMPTS:
    post_data(patterns_file_path)

# Post glossary words if flag is set
if $POST_GLOSSARY_WORDS:
    post_data(glossary_file_path)
EOF

# Run the Python script
python $PYTHON_SCRIPT

# Remove the temporary Python script
rm $PYTHON_SCRIPT
