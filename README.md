# ShapeFlow Monitor

ShapeFlow Monitor is a cloud-based web application designed for analyzing and visualizing onShape log data. The application leverages Google Colab, Firebase, and onShape to provide a comprehensive and interactive dashboard for monitoring activity logs and document usage.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Project Structure](#project-structure)
- [Scripts](#scripts)
- [Dependencies](#dependencies)
- [Development Tools](#development-tools)

## Features

- **Interactive Dashboards**: Visualize onShape log data through interactive charts and graphs.
- **Firebase Integration**: Store and retrieve data from Firebase.
- **Ngrok Integration**: Expose the application to the internet using ngrok.
- **Comprehensive Logging**: Log application events and errors to Firebase.
- **Cloud-Based**: Utilize cloud technologies such as Google Colab, Firebase, and onShape.

## Getting Started

### Prerequisites

- Python 3.8 or higher installed on your local machine.
- Ngrok account and authentication token.
- Firebase database setup with appropriate credentials.

## Installation

### *Using Google Colab*
1. Head to https://colab.research.google.com/
2. Click File in the menu, and open notebook
3. Select GitHub tab
4. Search for GitHub user: ``` EyalMK```
5. Select repository ShapeFlow-Monitor-Cloud
6. Select branch HW3
7. Open main.ipynb
8. Execute all cells.

### *Local Installation*

1. **Clone the repository**:
    ```sh
    git clone https://github.com/EyalMK/ShapeFlow-Monitor-Cloud.git
    cd shapeflow-monitor
    ```

2. **Create and activate a virtual environment**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```sh
    pip install .
    ```

## Environment Configuration

The application supports different settings for development, testing, and production environments. Configure the `RUNTIME_ENVIRONMENT` variable in your `.env` file accordingly.

## Project Structure

```plaintext
ShapeFlow-Monitor/
├── app/
│   ├── __init__.py
│   ├── app.py                   # Main application logic
│   └── dash_layouts.py          # Dashboard layout details
├── config/
│   ├── __init__.py
│   └── constants.py             # Configuration constants
├── database/
│   ├── __init__.py
│   └── handler.py               # Database handling logic
├── dataframes/
│   ├── __init__.py
│   └── dataframe_handler.py     # Dataframe handling logic
├── logger/
│   ├── __init__.py
│   └── database_logger.py       # Custom logging to Firebase
├── search_engine/
│   ├── __init__.py
│   └── search_handler.py        # Search engine logic
├── utils/
│   ├── __init__.py
│   └── utilities.py             # Utility functions
│   └── firebase_curator.sh      # Script to wipe all data in Firebase, --glossary flag to initialize with glossary words.
│   └── default_source.json      # Default json data - Provided by course instructors.
│   └── teamA.json               # Modified json data based on the previously stated default json file.
├── main.py                      # Entry point of the application
├── README.md                    # Project documentation
├── setup.py                     # Project setup script
└── .env                         # Environment variables (not included in repo)
```

## Scripts

* `python main.py`: Starts the application.

## Dependencies

- [dash](https://dash.plotly.com/): Web application framework for Python.
- [dash-bootstrap-components](https://dash-bootstrap-components.opensource.faculty.ai/): Bootstrap components for Dash.
- [firebase](https://firebase.google.com/docs/reference/rest/database): Firebase integration.
- [flask](https://flask.palletsprojects.com/): Web framework for Python.
- [pyngrok](https://pyngrok.readthedocs.io/en/latest/): ngrok integration.
- [pandas](https://pandas.pydata.org/): Data analysis and manipulation library.
- [plotly](https://plotly.com/python/): Graphing library for making interactive charts.
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/): Library for web scraping.
- [nltk](https://www.nltk.org/): Natural Language Toolkit.
- [requests](https://docs.python-requests.org/en/latest/): HTTP library for Python.

## Development Tools

- [venv](https://docs.python.org/3/library/venv.html): Creation of virtual environments.
- [ngrok](https://ngrok.com/): Secure introspectable tunnels to localhost.
- [dotenv](https://pypi.org/project/python-dotenv/): Reads `.env` files for environment variables.
