#!/bin/bash

FIREBASE_URI="https://shapeflow-monitor-default-rtdb.europe-west1.firebasedatabase.app/"
FIREBASE_PATH="/" # Change this to the path you want to clear

# Create a temporary Python script to clear the data
PYTHON_SCRIPT=$(mktemp)

cat <<EOF > $PYTHON_SCRIPT
from firebase import firebase
import sys

# Define the Firebase URI and the path to clear
firebase_uri = "$FIREBASE_URI"
firebase_path = "$FIREBASE_PATH"

# Initialize the Firebase application
firebase_app = firebase.FirebaseApplication(firebase_uri, None)

# Clear the data at the specified path
try:
    result = firebase_app.delete(firebase_path, None)
    print("Data cleared successfully.")
except Exception as e:
    print(f"Error clearing data: {e}", file=sys.stderr)
    sys.exit(1)
EOF

# Run the Python script
python $PYTHON_SCRIPT

# Remove the temporary Python script
rm $PYTHON_SCRIPT
