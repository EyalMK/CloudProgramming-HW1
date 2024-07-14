# ShapeFlow Monitor

ShapeFlow Monitor is a cloud-based web application designed for analyzing and visualizing onShape log data. The application leverages Google Colab, Firebase, and onShape to provide a comprehensive and interactive dashboard for monitoring activity logs and document usage.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Running the Project](#running-the-project)
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

### Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/shapeflow-monitor.git
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

### Running the Project

1. **Set Up Environment Variables**:
    Create a `.env` file in the project root and add your ngrok authentication token and Firebase URL:
    ```env
    RUNTIME_ENVIRONMENT=dev
    DB_CONN_URL=https://your-firebase-db-url
    ```

2. **Run the Application**:
    ```sh
    python main.py
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
