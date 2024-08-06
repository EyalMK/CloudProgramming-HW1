# ShapeFlow Monitor

ShapeFlow Monitor is a cloud-based web application designed for analyzing and visualizing onShape log data. The application leverages Google Colab, Firebase, and onShape to provide a comprehensive and interactive dashboard for monitoring activity logs and document usage.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Project Structure](#project-structure)
- [Key Classes](#key-classes)
- [Key Functions](#key-functions)
- [Scripts](#scripts)
- [Dependencies](#dependencies)
- [Development Tools](#development-tools)

## Features

- **Interactive Dashboards**: Visualize onShape log data through interactive charts and graphs.
- **Firebase Integration**: Store and retrieve data from Firebase.
- **Ngrok Integration**: Expose the application to the internet using ngrok.
- **Comprehensive Logging**: Log application events and errors to Firebase.
- **Cloud-Based**: Utilize cloud technologies such as Google Colab, Firebase, and onShape.
- **Log Uploading**: Upload log files for analysis and visualization.
- **Chatbot Assistant**: Interact with a chatbot assistant for help and information.
- **Search Engine**: Search the stemmed indices of sentences and words in the onShape glossary.

## Getting Started

### Prerequisites

- Python 3.8 or higher installed on your local machine.
- Ngrok account and authentication token (Optional).
- Firebase realtime database setup.

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
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

3. **Install the dependencies**:
    ```sh
    pip install .
    ```

## Environment Configuration
Environment variables are stored in the constants.py file located in the config directory of the project. 
The required variables are:

- `NGROK_TOKEN`: Your Ngrok authentication token.
- `DB_CONN_URL`: Your Firebase realtime database connection url.

## Project Structure
ShapeFlow Monitor/
```
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── dash_callbacks.py
│   └── dash_layouts.py
├── chatbot/
│   ├── __init__.py
│   ├── chat_bot.py
│   └── patterns_handler.py
├── config/
│   ├── __init__.py
│   └── constants.py
├── database/
│   ├── __init__.py
│   ├── db_handler.py
├── dataframes/
│   ├── __init__.py
│   └── dataframe_handler.py
├── logger/
│   ├── __init__.py
│   └── database_logger.py
├── search_engine/
│   ├── __init__.py
│   └── scraper.py
│   └── search_engine.py
├── utils/
│   ├── __init__.py
│   └── utilities.py
│   └── firebase_curator.sh
├── main.py
├── main.ipynb
├── README.md
└──  setup.py
```

## Key Classes 

### App
- **app/app.py**
- Main class that initializes and runs the Dash application.

### DashPageLayouts
- **app/dash_layouts.py**
- Manages the layouts and graphs of the Dash application.

### DashCallbacks
- **app/dash_callbacks.py**
- Manages the callbacks for the Dash application.

### ChatBot
- **chatbot/chat_bot.py**
- Represents the chatbot that uses predefined patterns and reflections to respond to user inputs.

### PatternsHandler
- **chatbot/patterns_handler.py**
- Manages the retrieval and storage of chatbot patterns from the database.

### DatabaseHandler
- **database/db_handler.py**
- Manages database operations with Firebase.

### DatabaseLogger
- **logger/database_logger.py**
- Custom logging handler that sends log messages to a database.

### Scraper
- **search_engine/scraper.py**
- Simple web scraper class to fetch and parse HTML pages.

### SearchEngine
- **search_engine/search_engine.py**
- Implements a search engine for indexing and querying words from a glossary.

### DataFrameHandler
- **dataframes/dataframe_handler.py**
- Manages data frame operations, including filtering, processing, analyzing and caching data from logs.

### Utilities
- **utils/utilities.py**
- Provides various utility functions and objects such as logger.

## Key Functions

**main.py**:
*  setup_ngrok_auth(): Configures Ngrok authentication if the runtime environment is production or testing.
*  main(): Main entry point for the application.

**app/app.py**:
* _initialize_database(self): Configures the database logger and connects to Firebase.
* run(self): Starts the Dash application server.

**app/dash_callbacks.py**:
* register_callbacks(self): Registers all callbacks for the Dash application.
    * update_all_graphs(n_clicks, data, selected_document, selected_log, selected_user, start_time, end_time,
                              selected_graphs): Updates the graphs layout and handles the selected filters.
    * handle_file_upload_and_submit(contents, n_clicks, filename, default_data_source): Handles the loading of uploaded json files and saving them to the database.
    * search_term_in_glossary(n_clicks, value): Handles the search results in the glossary.
    * update_alerts(n_clicks): Handles the update of the alerts layout.
    * update_chat(n_clicks, n_submit, user_input, chat_history): Handles the update of the chatbot history.
    * display_page(pathname: str): Handles the routing callback for the entire application.
* _update_selection(self, select_all_clicks, clear_all_clicks, options): Updates selection options based on button clicks.
* _update_graph(self, data, setup_dataframe_callback, create_graph_callback, *setup_dataframe_args, graph_type='', collapsible_list=False): Updates the graph based on provided data and callbacks.

**app/dash_layouts.py**:
* define_layout(self): Defines the overall layout of the application.
* create_callbacks(self): Creates and registers the callbacks for the application.
* handle_initial_graph_dataframes(self): Handles the initial setup of the graph dataframes.

* Layout Creations:
  * dashboard_layout(self): Creates the layout for the dashboard with graphs.
  * working_hours_layout(self): Creates the layout for the working hours graphs.
  * alerts_layout(self): Creates the layout for the alerts.
  * chat_layout(self): Creates the layout for the chatbot.
  * glossary_layout(self): Creates the layout for the glossary search.
  * upload_layout(self): Creates the layout for the file upload.
  * graphs_layout(self): Creates the layout for the graphs.
  * landing_page_layout(self): Creates the layout for the landing page.
  
* Graphs Creations:
  * create_project_time_distribution_graph(self): Creates the project time distribution graph.
  * create_repeated_actions_graph(self): Creates the repeated actions graph.
  * create_advanced_basic_actions_graph(self): Creates the advanced basic actions graph.
  * create_action_sequence_scatter_graph(self): Creates the action sequence scatter graph.
  * create_work_patterns_over_time_graph(self): Creates the work patterns over time graph.

**chatbot/chat_bot.py**:
* respond(self, user_input): Generates a response to user input.

**chatbot/patterns_handler.py**:
* get_patterns(self): Returns the list of loaded chatbot patterns.

**database/db_handler.py**:
* read_from_database(self, collection_name): Reads data from a specific collection in the database.
* write_to_database(self, collection_name, data): Writes data to a specific collection in the database.

**logger/database_logger.py**:
* emit(self, record): Sends a log message to the database.

**search_engine/search_engine.py**:
* perform_search(self, query): Performs a search using the given query.
* _initialize_base_words(self): Initializes the list of chosen words from the database.

**dataframes/dataframe_handler.py**:
* initialize_df(self): Reads and loads the default data source from the database.
* handle_switch_log_source(self, collection_name, file_name): Handles the switch between the default data source and the uploaded file.
* process_df(self): Processes the DataFrame including time conversion, filtering, and generating alerts.
* update_with_new_data(self, collection_name, file_name): Updates the DataFrame with new data.
* get_lightly_refined_graphs_dataframe(self): Returns the lightly refined DataFrame for the graphs.
* process_graphs_layout_dataframe(self, selected_document, selected_log, selected_user, start_time, end_time): Processes the DataFrame completely for the graphs layout.
* filter_dataframe_for_graphs(self, selected_document, selected_log, selected_user, start_time, end_time): Filters the DataFrame based on the selected filters.
* _undo_redo_activity_detection(self, df): Detects undo and redo activities in the DataFrame.
* Graph Specific DataFrames:
  * get_project_time_distribution_dataframe(self): Returns the DataFrame for the project time distribution graph.
  * get_repeated_actions_dataframe(self): Returns the DataFrame for the repeated actions graph.
  * get_advanced_basic_actions_dataframe(self): Returns the DataFrame for the advanced basic actions graph.
  * get_action_sequence_scatter_dataframe(self): Returns the DataFrame for the action sequence scatter graph.
  * get_work_patterns_over_time_dataframe(self): Returns the DataFrame for the work patterns over time graph.

**utils/utilities.py**:
* setup_logger(self): Sets up logging to console and database.
* get_supported_graphs(self): Returns a list of the supported graphs.

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
