from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import dcc, dash_table
from dash import html
from app.dash_callbacks import DashCallbacks
from config.constants import PROJECT_NAME
from database.db_handler import DatabaseHandler
from dataframes.dataframe_handler import DataFrameHandler


class DashPageLayouts:
    """
    This class is responsible for defining the layout and callbacks for the Dash application pages.

    Attributes:
        dash_app (dash.Dash): The Dash application instance.
        db_handler (DatabaseHandler): The handler for database interactions.
        df_handler (DataFrameHandler): The handler for data frame operations.
        lightly_refined_df (pd.DataFrame): A DataFrame to store lightly refined data.
        graph_processed_df (pd.DataFrame): A DataFrame to store data processed for graphing.
        uploaded_json (dict): A placeholder for uploaded JSON data.
        data_source_title (str): The title of the selected log for data source.
        utils (Utilities): A utility class instance for logging and other utilities.
    """

    def __init__(self, dash_app: dash.Dash, db_handler: 'DatabaseHandler', utils):
        """
        Initializes the DashPageLayouts class with the given parameters and sets up the layout and callbacks.

        Parameters:
            dash_app (dash.Dash): The Dash application instance.
            db_handler (DatabaseHandler): The handler for database interactions.
            utils: A utility class instance for logging and other utilities.
        """
        self.dash_app = dash_app
        self.db_handler = db_handler
        self.df_handler = DataFrameHandler(db_handler, utils)
        self.lightly_refined_df = pd.DataFrame([])
        self.graph_processed_df = pd.DataFrame([])
        self.uploaded_json = None
        self.data_source_title = self.df_handler.selected_log_name
        self.utils = utils
        self.define_layout()
        self.create_callbacks()
        self.utils.logger.info("Dash app pages loaded, and dataframes processed.")

    def create_callbacks(self):
        """
        Initializes the DashCallbacks class, setting up the callbacks for the Dash application.

        This method creates an instance of the DashCallbacks class, passing necessary parameters to it.
        It is responsible for setting up all the callbacks that handle the interactions within the Dash app.
        """
        DashCallbacks(self.dash_app, self.df_handler, self.db_handler, self, self.utils)

    # Define individual page layouts with graphs and filters
    def dashboard_layout(self):
        """
        Defines the layout for the dashboard page of the Dash application.

        This method creates a structured layout for the dashboard page, including various cards
        that display graphs for activity over time, document usage frequency, and user activity distribution.

        Returns:
            html.Div: A Dash HTML Div component containing the layout of the dashboard page.
        """
        return self._create_layout(
            "Dashboard",
            [
                self._create_card(
                    "Activity Over Time",
                    dcc.Graph(
                        figure=self._create_line_chart(
                            self.df_handler.activity_over_time,
                            x='Date',
                            y='ActivityCount',
                            title='Activity Over Time'
                        )
                    ),
                    width=12
                ),
                self._create_card(
                    "Document Usage Frequency",
                    dcc.Graph(
                        figure=self._create_bar_chart(
                            self.df_handler.document_usage,
                            x='Document',
                            y='UsageCount',
                            title='Document Usage Frequency'
                        )
                    ),
                    width=6
                ),
                self._create_card(
                    "User Activity Distribution",
                    dcc.Graph(
                        figure=self._create_pie_chart(
                            self.df_handler.user_activity,
                            names='User',
                            values='ActivityCount',
                            title='User Activity Distribution'
                        )
                    ),
                    width=6
                )
            ]
        )

    def working_hours_layout(self):
        """
        Defines the layout for the working hours analysis page of the Dash application.

        This method creates a structured layout for the working hours analysis page, including cards
        that display graphs for the working hours overview and the occurrences of work during nights,
        weekends, and holidays.

        Returns:
            html.Div: A Dash HTML Div component containing the layout of the working hours analysis page.
        """
        return self._create_layout(
            "Working Hours Analysis",
            [
                self._create_card(
                    "Working Hours Overview",
                    dcc.Graph(
                        figure=self._create_working_hours_chart()
                    ),
                    width=12
                ),
                self._create_card(
                    "Night & Weekend & Holidays Work Occurrences",
                    dcc.Graph(
                        figure=self._create_stacked_bar_chart(
                            df=self._create_occurrences_chart(),
                            x='Occurrences Count',
                            y='User',
                            title='Night & Weekend & Holidays Work Occurrences',
                            color='Type'
                        )
                    ),
                    width=12
                )
            ]
        )

    def graphs_layout(self):
        self.handle_initial_graph_dataframes()
        return self._create_layout("Advanced Team Activity and Analysis Graphs", [
            html.H4(id='data-source-title', children=f"Current Data Source - {self.data_source_title}",
                    className="mb-4"),
            self._create_card("Filters", self._create_filters(), 12),
            dcc.Store(id='processed-df', data=self.graph_processed_df.to_dict()),
            dcc.Store(id='pre-processed-df', data=self.lightly_refined_df.to_dict()),
            dcc.Store(id='show-graphs', data=False),
            html.Div([
                dcc.Loading(
                    id='loading',
                    type='circle',
                    style={'marginTop': '50px'},
                    children=[
                        html.Div(id='graphs-tabs-container', style={'display': 'none'}, children=[
                            dcc.Tabs(id='dynamic-tabs')
                        ])
                    ]
                )
            ])
        ])

    @staticmethod
    def create_dynamic_tabs(selected_graphs):
        """
        Creates a list of dynamic tabs based on the selected graphs.

        This method generates `dcc.Tab` components for each graph type specified in the selected_graphs list.
        Each tab contains a graph and optionally additional HTML elements like headers and divs.

        Parameters:
            selected_graphs (list): A list of strings representing the graph types to include in the tabs.

        Returns:
            list: A list of `dcc.Tab` components to be included in a Dash layout.
        """
        tabs = []
        graph_mapping = {
            'Project Time Distribution': {
                'label': 'Project Time Distribution',
                'children': [
                    dcc.Graph(id={'type': 'graph', 'index': 'project-time-distribution-graph'})
                ]
            },
            'Advanced vs. Basic Actions': {
                'label': 'Advanced vs. Basic Actions',
                'children': [
                    dcc.Graph(id={'type': 'graph', 'index': 'advanced-basic-actions-graph'}),
                    html.H2('Advanced & Basic Actions'),
                    html.Div(id={'type': 'collapse-div', 'index': 'advanced-basic-actions'})
                ]
            },
            'Action Sequence by User': {
                'label': 'Action Sequence by User',
                'children': [
                    dcc.Graph(id={'type': 'graph', 'index': 'action-sequence-scatter-graph'})
                ]
            },
            'Work Patterns Over Time': {
                'label': 'Work Patterns Over Time',
                'children': [
                    dcc.Graph(id={'type': 'graph', 'index': 'work-patterns-over-time-graph'})
                ]
            },
            'Repeated Actions By User': {
                'label': 'Repeated Actions By User',
                'children': [
                    dcc.Graph(id={'type': 'graph', 'index': 'repeated-actions-by-user-graph'}),
                    html.H2('Grouped Actions Descriptions:'),
                    html.Div(id={'type': 'collapse-div', 'index': 'repeated-actions'})
                ]
            }
        }

        for graph in selected_graphs:
            if graph in graph_mapping:
                tabs.append(dcc.Tab(label=graph_mapping[graph]['label'], children=graph_mapping[graph]['children']))

        return tabs

    def landing_page_layout(self):
        """
        Creates the layout for the landing page of the ShapeFlow Monitor Tool.

        This method generates a layout that includes an overview of the tool and a list of steps for getting started.
        Each step is presented in a styled list item with an icon for better visual representation.

        Returns:
            html.Div: A Div containing the structured layout of the landing page.
        """
        return self._create_layout("Welcome to the ShapeFlow Monitor Tool", [
            self._create_card("Overview",
                              html.P(
                                  "The ShapeFlow Monitor Tool is your go-to solution for monitoring and analyzing the "
                                  "performance of your OnShape team. Designed with managers in mind, this application "
                                  "provides comprehensive insights into team activity, project progress, "
                                  "and collaboration efficiency by processing log files in JSON format from the "
                                  "OnShape platform."),
                              12
                              ),
            self._create_card("How to Get Started:",
                              html.Div([
                                  self._create_styled_list_item(
                                      "Upload Log Files:",
                                      "Begin by navigating to the Setup section. Here, you can upload a new log file "
                                      "from your device and save it to the database.",
                                      icon="fas fa-upload"),
                                  self._create_styled_list_item(
                                      "Select Default Log:",
                                      "Mark an uploaded log to be used as the default for analysis, using the "
                                      "'Default Data Source' checkbox.",
                                      icon="fas fa-check"),
                                  self._create_styled_list_item(
                                      "Explore Visualizations:",
                                      "Head over to the Graphs section to explore various analytical graphs that "
                                      "provide a deep dive into your team's performance and activities.",
                                      icon="fas fa-chart-bar"),
                                  self._create_styled_list_item(
                                      "Analyze Working Hours:",
                                      "Visit the Working Hours section to review detailed analyses of your team's "
                                      "working hours, including patterns and productivity trends.",
                                      icon="fas fa-clock"),
                                  self._create_styled_list_item(
                                      "Stay Informed with Alerts:",
                                      "The Alerts section will keep you updated with important notifications derived "
                                      "from the log file, ensuring you never miss a critical insight.",
                                      icon="fas fa-bell"),
                                  self._create_styled_list_item(
                                      "Chatbot Assistance:",
                                      "Use the Chatbot feature for instant assistance and answers to your questions "
                                      "about the tool and its functionalities.",
                                      icon="fas fa-comments"),
                                  self._create_styled_list_item(
                                      "Search Glossary:",
                                      "Easily find and understand specific terms or features using the Search "
                                      "Glossary option.",
                                      icon="fas fa-search"),
                              ], style={"list-style-type": "none", "padding": "0"}),
                              12
                              ),
        ], style={"max-width": "1200px", "margin": "0 auto", "padding": "20px"})

    def alerts_layout(self):
        """
        Creates the layout for the Operations Alerts page.

        This method generates a layout that displays recent alerts and a button to acknowledge all alerts. The alerts
        are displayed in a styled list, and the "Acknowledge All" button is styled to fit the card.

        Returns:
            html.Div: A Div containing the structured layout of the alerts page.
        """
        alerts_list, unread_alerts_count = self.create_alerts_list()
        return self._create_layout("Operations Alerts", [
            self._create_card("Recent Alerts", html.Div(id='alerts-list', children=alerts_list), 16),
            self._create_card("Acknowledge All", dbc.Button("Acknowledge All", color="success", className="w-100",
                                                            id="acknowledge-all-button"), 16),
        ])

    @staticmethod
    def _create_styled_list_item(header: str, text: str, icon: str = None) -> html.Div:
        """
        Creates a styled list item with an optional icon.

        Parameters:
            header (str): The header text for the list item.
            text (str): The descriptive text for the list item.
            icon (str, optional): The class name for an optional icon to be displayed.

        Returns:
            html.Div: A Div containing the styled list item.
        """
        return html.Div(
            [
                html.I(className=icon, style={"margin-right": "10px", "color": "#007bff"}) if icon else None,
                html.Span(header, style={"font-weight": "bold", "font-size": "1rem"}),
                html.Span(f" {text}", style={"font-size": "1rem", "color": "#343a40"})
            ],
            style={"padding": "10px", "margin-bottom": "5px", "background-color": "#f8f9fa", "border-radius": "5px",
                   "box-shadow": "0 1px 2px rgba(0, 0, 0, 0.1)"}
        )

    @staticmethod
    def text_search_layout() -> html.Div:
        """
        Creates the layout for a text search interface.

        This layout includes an input field for entering search queries and a search button with an icon.
        The search button triggers the search action, and the results are displayed below the input field.

        Returns:
            html.Div: A Div containing the text search input, button, and output area.
        """
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Input(id="input", placeholder="Search...", type="text"),
                            width=8
                        ),
                        dbc.Col(
                            dbc.Button(
                                children=html.I(className="fas fa-search", style={"display": "inline-block"}),
                                id="search-button",
                                n_clicks=0,
                                size='lg',
                                style={"fontSize": '1.7vh', "backgroundColor": "#007BC4", "textAlign": "center"}
                            ),
                            width=4
                        )
                    ],
                    align="center"
                ),
                html.Br(),
                html.P(id="output")
            ]
        )

    def search_glossary_layout(self):
        """
        Creates the layout for searching the OnShape Glossary.

        This layout includes a card with a search interface for the OnShape glossary, allowing users to
        enter search queries and view the results.

        Returns:
            html.Div: A Div containing the search card layout.
        """
        return self._create_layout(
            "Search OnShape Glossary",
            [
                self._create_card("Search", self.text_search_layout(), 10)
            ]
        )

    @staticmethod
    def search_results_table_layout(data):
        """
        Creates a layout for displaying search results in a table.

        This method returns a Div containing a Dash DataTable with columns for search terms and their occurrences.
        The table is styled to have a light background and centered text.

        Parameters:
            data (list of dict): The data to be displayed in the table. Each dictionary represents a row.

        Returns:
            html.Div: A Div containing the styled DataTable.
        """
        return html.Div(
            dash_table.DataTable(
                columns=[
                    {"name": "Index (stemmed)", "id": "term"},
                    {"name": "Occurrences", "id": "occurrences"}
                ],
                data=data,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'backgroundColor': '#f9f9f9'  # Light shade background
                },
                style_header={
                    'backgroundColor': '#e1e1e1',  # Light shade for header
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'term'},
                        'textAlign': 'center'
                    },
                    {
                        'if': {'column_id': 'occurrences'},
                        'textAlign': 'center'
                    }
                ]
            )
        )

    def upload_log_layout(self):
        """
        Creates the layout for the log upload page.

        This method returns a layout for uploading JSON log files. It includes a card with an upload component
        for file selection and upload.

        Returns:
            html.Div: A Div containing the layout for uploading logs.
        """
        return self._create_layout("Upload Log", [
            self._create_card("Upload JSON", self._create_upload_component(), 12)
        ])

    def chatbot_layout(self):
        """
        Creates the layout for the Chatbot Assistant page.

        This method returns a layout that includes a card with a chatbot interface. The chatbot has an initial greeting
        message and provides input and send button components for user interaction.

        Returns:
            html.Div: A Div containing the layout for the Chatbot Assistant page.
        """
        initial_greeting = ("**ShapeFlowBot:** Hello! I'm ShapeFlowBot! I can assist you with various questions "
                            "regarding ShapeFlow Monitor. How can I help you today?")

        return self._create_layout("Chatbot Assistant", [
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Chat with ShapeFlowBot", className="card-title mb-4"),
                            dcc.Markdown(
                                id='chat-history',
                                children=initial_greeting,
                                style={'width': '100%', 'height': '50vh', 'backgroundColor': '#f8f9fa',
                                       'border': '1px solid #ced4da', 'borderRadius': '5px', 'padding': '10px',
                                       'overflowY': 'auto'}
                            ),
                            html.Div([
                                dbc.Input(
                                    id='chat-input',
                                    placeholder='Type a message...',
                                    type='text',
                                    n_submit=0,
                                    style={'width': '85%', 'display': 'inline-block', 'marginRight': '10px'}
                                ),
                                dbc.Button('Send', id='send-button', color='primary',
                                           style={'width': '10%', 'display': 'inline-block'})
                            ], className='mt-3'),
                        ]),
                        className='mb-4',
                        style={'border': '1px solid #ced4da', 'borderRadius': '10px'}
                    ),
                    width=12
                ),
            ])
        ])

    @staticmethod
    def create_empty_graph():
        """
        Creates and returns an empty Plotly graph figure.

        Returns:
            go.Figure: An empty Plotly figure object.
        """
        return go.Figure()

    def create_project_time_distribution_graph(self, dataframe):
        """
        Creates a pie chart showing the distribution of time spent on different project tabs.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame containing the data for the pie chart.
                It should include 'Tab' and 'Time Spent (hours)' columns.

        Returns:
            go.Figure: A Plotly figure object representing the pie chart.
        """
        threshold_percentage = 0.4
        return self._create_pie_chart(
            df=dataframe,
            names='Tab',
            values='Time Spent (hours)',
            title=(
                f'Project Time Distribution (in Hours) - '
                f'Minimum threshold: {threshold_percentage}%'
            ),
            labels={
                'Time Spent (hours)': 'Time Spent (Hours)',
                'Tab': 'Project Tab'
            },
            threshold_percentage=threshold_percentage
        )

    def create_repeated_actions_graph(self, dataframe):
        """
        Creates a stacked bar chart to analyze repeated actions by users.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame containing the data for the stacked bar chart.
                It should include 'User', 'Count', and 'Action' columns.

        Returns:
            go.Figure: A Plotly figure object representing the stacked bar chart.
        """
        if dataframe.empty:
            return go.Figure()  # Return an empty graph

        return self._create_stacked_bar_chart(
            df=dataframe,
            x='User',
            y='Count',
            color='Action',
            title='Repeated Actions Analysis by User',
            orientation='v',
            labels={
                'User': 'User',
                'Count': 'Repetition Count',
                'Action': 'Action Description'
            }
        )

    def create_advanced_basic_actions_graph(self, dataframe):
        """
        Creates a stacked bar chart comparing advanced vs. basic actions by user.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame containing the data for the stacked bar chart.
                It should include 'Action Count', 'User', and 'Action Type' columns.

        Returns:
            go.Figure: A Plotly figure object representing the stacked bar chart.
        """
        if dataframe.empty:
            return go.Figure()  # Return an empty graph

        return self._create_stacked_bar_chart(
            df=dataframe,
            x='Action Count',
            y='User',
            color='Action Type',
            title='Advanced vs. Basic Actions',
            grid=False,
            labels={
                'User': 'User',
                'Action Count': 'Action Count',
                'Action Type': 'Action Type'
            },
            orientation='h'
        )

    def create_action_sequence_scatter_graph(self, dataframe):
        """
        Creates a scatter chart displaying action sequences by user over time.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame containing the data for the scatter chart.
                It should include 'Time', 'Action', and 'User' columns.

        Returns:
            go.Figure: A Plotly figure object representing the scatter chart.
        """
        return self._create_scatter_chart(
            df=dataframe,
            x='Time',
            y='Action',
            color='User',
            title='Action Sequence by User',
            labels={
                'Time': 'Time',
                'User': 'User',
                'Action': 'Action'
            }
        )

    def create_work_patterns_over_time_graph(self, dataframe):
        """
        Creates a stacked bar chart displaying work patterns over different time intervals.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame containing the data for the stacked bar chart.
                It should include 'Time Interval', 'Action Count', and 'Day' columns.

        Returns:
            go.Figure: A Plotly figure object representing the stacked bar chart.
        """
        return self._create_stacked_bar_chart(
            df=dataframe,
            x='Time Interval',
            y='Action Count',
            color='Day',
            orientation='v',
            title='Work Patterns Over Different Time Intervals',
            labels={
                'Time Interval': 'Time of Day',
                'Action Count': 'Action Count',
                'Day': 'Day of Week'
            }
        )

    def handle_initial_graph_dataframes(self):
        """
        Handles the initial setup of dataframes for graphing by obtaining and processing the necessary data.

        Updates:
            self.lightly_refined_df (pd.DataFrame): The DataFrame containing lightly refined data for graphs.
            self.graph_processed_df (pd.DataFrame): The DataFrame processed for use in graph layouts.

        Returns:
            pd.DataFrame: The processed DataFrame ready for graphing.
        """
        self.lightly_refined_df = self.df_handler.get_lightly_refined_graphs_dataframe()
        self.graph_processed_df = self.df_handler.process_graphs_layout_dataframe(dataframe=self.lightly_refined_df)
        return self.graph_processed_df

    @staticmethod
    def create_header():
        """
        Creates a header for the application with a logo, project name, and current date.

        Returns:
            dbc.Navbar: The header component for the application.
        """
        current_date = datetime.now().strftime('%d-%m-%Y')
        logo_path = "/static/SFM-logo.png"
        return dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.Img(src=logo_path, height="40px"), width="auto"),
                    dbc.Col(html.H1(PROJECT_NAME, className="text-white"), width="auto"),
                    dbc.Col(
                        html.H2(
                            current_date,
                            className="text-white mt-2",
                            style={"fontSize": "1.2rem", "color": "lightgrey"}
                        ),
                        width="auto"
                    )
                ], align="center", justify="start"),
            ], fluid=True),
            color="primary",
            dark=True,
            style={"width": "100%"}
        )

    def create_side_menu(self):
        """
        Creates the side menu for the application with navigation links and alert count.

        Returns:
            dbc.Col: The side menu component with navigation links and alert badge.
        """
        alert_count = str(self.df_handler.get_unread_alerts_count())
        return dbc.Col([
            dbc.Nav(
                [
                    self._create_nav_link("fas fa-house", " Home", "/"),
                    self._create_nav_link("fas fa-tachometer-alt", " Dashboard", "/dashboard"),
                    self._create_nav_link("fas fa-chart-line", " Advanced Analytics", "/advanced-analytics"),
                    self._create_nav_link("fas fa-cloud", " Upload Logs", "/upload-log"),
                    self._create_nav_link("fas fa-magnifying-glass", " Search Glossary", "/search-glossary"),
                    self._create_nav_link("fas fa-clock", " Working Hours", "/working-hours"),
                    self._create_nav_link("fas fa-bell", " Alerts", "/alerts",
                                          alert_count,
                                          "danger", "alerts-count-badge"),
                    self._create_nav_link("fas fa-comment", " Chatbot Assistant", "/chatbot"),
                ],
                vertical=True,
                pills=True,
                className="bg-dark h-100 p-3",
                style={"height": "100%"}
            ),
        ], width=2, className="bg-dark", style={"height": "100%", "overflow": "hidden"})

    @staticmethod
    def create_footer():
        """
        Creates the footer component for the application.

        Returns:
            dbc.Navbar: The footer component with copyright information.
        """
        return dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.P(f"© 2024 {PROJECT_NAME}, Inc.", className="text-white text-center mb-0"),
                            width="auto")
                ], align="center", justify="center", className="w-100")
            ]),
            color="primary",
            dark=True,
            style={"width": "100%"}
        )

    def define_layout(self):
        """
        Defines the layout for the Dash application.

        Sets the layout to include:
        - A header created by `create_header()`.
        - A container with a side menu and a content area where pages will be displayed.
        - A footer created by `create_footer()`.

        The layout is structured to fit within the full viewport height and handle overflow appropriately.
        """
        self.dash_app.layout = html.Div([
            self.create_header(),
            dbc.Container([
                dbc.Row([
                    self.create_side_menu(),
                    dcc.Location(id='url'),
                    dbc.Col(html.Div(id="page-content"), width=10, style={"height": "100%", "overflow": "auto"})
                ], style={"flex": "1", "overflow": "hidden", "height": "calc(100vh - 56px)"})
            ], fluid=True,
                style={"display": "flex", "flexDirection": "row", "flexGrow": "1", "height": "calc(100vh - 56px)"}),
            self.create_footer()
        ], style={"display": "flex", "flexDirection": "column", "height": "100vh"})

    @staticmethod
    def _create_layout(title: str, children: list, style: dict = None) -> dbc.Container:
        """
        Creates a layout container for the Dash application.

        Args:
            title (str): The title to be displayed at the top of the layout.
            children (list): The list of Dash components to be included in the layout.
            style (dict, optional): Additional styling for the container. Defaults to None.

        Returns:
            dbc.Container: A Dash Bootstrap Components container with the specified layout.
        """
        return dbc.Container([
            dbc.Row([
                dbc.Col(
                    html.H2(title, style={"fontSize": "2.5rem", "textAlign": "left", "margin": "20px 0"}),
                    width=12
                )
            ]),
            dbc.Row(children)
        ], style=style if style else {"padding": "20px"})

    @staticmethod
    def _create_card(title: str, content: html, width: int) -> dbc.Col:
        """
        Creates a styled card component with a header and body content.

        Parameters:
            title (str): The title displayed in the card header.
            content (html): The content displayed in the card body.
            width (int): The width of the card column.

        Returns:
            dbc.Col: A Bootstrap column containing the card.
        """
        return dbc.Col(dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody([content])
        ]), width=width, className="mb-3 mt-3")

    def _create_filters(self) -> html.Div:
        """
        Creates a filter panel for selecting documents, users, graphs, and logs, as well as specifying time ranges.

        Returns:
            html.Div: A container with filter controls for documents, users, graphs, logs, and time range.
        """
        # If the selected log path is not uploaded logs, then the default value for the logs dropdown should be empty
        # Otherwise, it should be the first uploaded log
        selected_log_name = self.df_handler.selected_log_name
        max_date = self.df_handler.max_date
        min_date = self.df_handler.min_date

        uploaded_logs_options = self.df_handler.filters_data['uploaded-logs']
        if selected_log_name == "None" and len(uploaded_logs_options) > 0:
            default_log_option = uploaded_logs_options[0]
        else:
            default_log_option = selected_log_name

        return html.Div([
            html.Div(id='log-switch-trigger', style={'display': 'none'}),
            self._create_filter_row(
                'document-dropdown',
                'Select Document',
                self.df_handler.filters_data['documents'],
                'select-all-documents',
                'clear-all-documents'
            ),
            self._create_filter_row(
                'user-dropdown',
                'Select User',
                self.df_handler.filters_data['users'],
                'select-all-users',
                'clear-all-users'
            ),
            self._create_filter_row(
                'graphs-dropdown',
                'Select Graphs',
                self.df_handler.filters_data['graphs'],
                'select-all-graphs',
                'clear-all-graphs',
                default_value=self.df_handler.filters_data['graphs']
            ),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id='logs-dropdown',
                        options=uploaded_logs_options,
                        placeholder='Select Log',
                        value=default_log_option
                    ),
                    width=7
                )
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Div([
                    html.Label("Start Time"),
                    dcc.Input(
                        id='start-time',
                        type='datetime-local',
                        min=min_date,
                        max=max_date,
                        value=min_date,
                        className='form-control'
                    )
                ]), width=6),
                dbc.Col(html.Div([
                    html.Label("End Time"),
                    dcc.Input(
                        id='end-time',
                        type='datetime-local',
                        min=min_date,
                        max=max_date,
                        value=max_date,
                        className='form-control'
                    )
                ]), width=6)
            ], className="mb-3"),
            dbc.Button(
                "Apply Filters",
                id='apply-filters',
                color="primary",
                className="w-100"
            )
        ], style={"padding": "10px", "maxWidth": "1200px", "margin": "auto"})

    def create_alerts_list(self) -> tuple:
        """
        Creates a list of alerts for display and counts the number of unread alerts.

        Returns:
            tuple: A tuple containing:
                - html.Ul: An unordered list of alerts formatted for display.
                - str: The count of unread alerts.
        """
        if self.df_handler.alerts_df.shape[0] == 0:
            alerts_list = html.P("No alerts to display", style={"color": "grey"})
        else:
            alerts_list = html.Ul([
                html.Li([
                        html.Span(
                            f"{row['Time']} - {row['Description']} by User: {row['User']} in Document: {row['Document']} - ",
                            style={"color": "grey" if row['Status'] == "read" else "black",
                                   "fontWeight": "bold" if row['Status'] == "unread" else "normal"}),
                        html.Span(f"indicating {row['Indication']}", style={"fontWeight": "normal"})
                    ]) for _, row in self.df_handler.alerts_df.iterrows()
            ], id='alerts-list', className="list-unstyled")

        unread_alerts_count = self.df_handler.get_unread_alerts_count()
        return alerts_list, str(unread_alerts_count)

    @staticmethod
    def _create_nav_link(icon_class: str, text: str, href: str, badge_text: str = "",
                         badge_color: str = "", badge_id: str = "") -> dbc.NavLink:
        """
        Creates a navigation link with optional badge.

        Args:
            icon_class (str): The class name for the icon.
            text (str): The text to display in the link.
            href (str): The URL to link to.
            badge_text (str, optional): The text for the badge. Defaults to "".
            badge_color (str, optional): The color of the badge. Defaults to "".
            badge_id (str, optional): The ID for the badge. Defaults to "".

        Returns:
            dbc.NavLink: A Dash Bootstrap Components navigation link with optional badge.
        """
        children = [html.I(className=icon_class), html.Span(text, className="ml-4")]
        if badge_text:
            children.append(dbc.Badge(badge_text, color=badge_color, className="ml-2", id=badge_id))
        return dbc.NavLink(children, href=href, active="exact", className="text-white gap-6")

    @staticmethod
    def _validate_graph_data(df, *columns):
        """
        Validates and ensures that a DataFrame contains the specified columns.

        Args:
            df (pd.DataFrame): The DataFrame to validate.
            *columns (str): The columns that should be present in the DataFrame.

        Returns:
            tuple: A tuple containing the validated DataFrame and the list of columns.
                   The DataFrame will have all specified columns, which will be empty if they were missing.
        """
        # Ensure columns are provided and are not None
        if not columns or any(col is None for col in columns):
            # Return an empty DataFrame with the expected column names
            return pd.DataFrame({col: [] for col in columns}), columns

        # Check if df is a DataFrame, otherwise create an empty DataFrame with the expected columns
        if not isinstance(df, pd.DataFrame) or df.empty:
            df = pd.DataFrame({col: [] for col in columns})

        # Ensure that the DataFrame has the required columns
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            for col in missing_columns:
                df[col] = []  # Add missing columns as empty

        return df, columns

    def _create_line_chart(self, df: pd.DataFrame, x: str, y: str, title: str) -> px.line:
        """
        Creates a line chart using Plotly Express.

        Args:
            df (pd.DataFrame): The DataFrame containing the data for the chart.
            x (str): The column name for the x-axis.
            y (str): The column name for the y-axis.
            title (str): The title of the chart.

        Returns:
            px.line: A Plotly Express line chart.
        """
        # Validate the graph data by passing df and the columns to _validate_graph_data
        df, validated_columns = self._validate_graph_data(df, x, y)
        x, y = validated_columns  # Unpack the validated columns

        # If the DataFrame is empty after validation, return an empty line chart with just the title
        if df.empty:
            return px.line(title=title)

        # Create and return the line chart using Plotly Express
        return px.line(df, x=x, y=y, title=title)

    def _create_stacked_bar_chart(self, df, x, y, title, color, labels=None, barmode='group', orientation='h',
                                  grid=True):
        """
        Creates a stacked bar chart using Plotly Express.

        Args:
            df (pd.DataFrame): The DataFrame containing the data for the chart.
            x (str): The column name for the x-axis.
            y (str): The column name for the y-axis.
            title (str): The title of the chart.
            color (str): The column name for the color grouping.
            labels (dict, optional): A dictionary to rename axis labels.
            barmode (str, optional): The barmode for the chart (e.g., 'group', 'stack').
            orientation (str, optional): The orientation of the bars ('h' for horizontal, 'v' for vertical).
            grid (bool, optional): Whether to display grid lines on the chart.

        Returns:
            px.bar: A Plotly Express stacked bar chart.
        """
        # Validate the graph data by passing df and the columns to _validate_graph_data
        df, validated_columns = self._validate_graph_data(df, x, y, color)
        x, y, color = validated_columns  # Unpack the validated columns

        # If the DataFrame is empty after validation, return an empty bar chart with just the title
        if df.empty:
            return px.bar(title=title)

        # Create the grouped bar chart with the given parameters
        bar_chart_params = {
            'data_frame': df,
            'x': x,
            'y': y,
            'color': color,
            'title': title,
            'barmode': barmode,
            'orientation': orientation
        }

        if labels:
            bar_chart_params['labels'] = labels

        fig = px.bar(**bar_chart_params)

        # Update layout to enable grid lines if requested
        if grid:
            fig.update_layout(
                xaxis=dict(showgrid=True, gridcolor='white', zeroline=True, zerolinecolor='white'),
                yaxis=dict(showgrid=True, gridcolor='white'),
                plot_bgcolor="rgba(229,236,246,255)"
            )

        return fig

    def _create_bar_chart(self, df: pd.DataFrame, x: str, y: str, title: str) -> px.bar:
        """
        Creates a bar chart using Plotly Express.

        Args:
            df (pd.DataFrame): The DataFrame containing the data for the chart.
            x (str): The column name for the x-axis.
            y (str): The column name for the y-axis.
            title (str): The title of the chart.

        Returns:
            px.bar: A Plotly Express bar chart.
        """
        df, validated_columns = self._validate_graph_data(df, x, y)
        x, y = validated_columns  # Unpack the validated columns

        if df.empty:
            return px.bar(title=title)

        return px.bar(df, x=x, y=y, title=title)

    def _create_scatter_chart(self, df: pd.DataFrame, x: str, y: str, color: str, title: str,
                              labels=None) -> px.scatter:
        """
        Creates a scatter chart using Plotly Express.

        Args:
            df (pd.DataFrame): The DataFrame containing the data for the chart.
            x (str): The column name for the x-axis.
            y (str): The column name for the y-axis.
            color (str): The column name for the color encoding.
            title (str): The title of the chart.
            labels (dict, optional): A dictionary mapping column names to display labels.

        Returns:
            px.scatter: A Plotly Express scatter chart.
        """
        # Validate the graph data by passing df and the columns to _validate_graph_data
        df, validated_columns = self._validate_graph_data(df, x, y, color)
        x, y, color = validated_columns  # Unpack the validated columns

        # If the DataFrame is empty after validation, return an empty scatter chart with just the title
        if df.empty:
            return px.scatter(title=title)

        # Create the scatter chart with the given parameters
        scatter_chart_params = {
            'data_frame': df,
            'x': x,
            'y': y,
            'color': color,
            'title': title
        }

        if labels:
            scatter_chart_params['labels'] = labels

        return px.scatter(**scatter_chart_params)

    def _create_pie_chart(self, df: pd.DataFrame, names: str, values: str, title: str, labels=None,
                          threshold_percentage=0.0) -> px.pie:
        """
        Creates a pie chart using Plotly Express.

        Args:
            df (pd.DataFrame): The DataFrame containing the data for the chart.
            names (str): The column name for the slice names.
            values (str): The column name for the slice values.
            title (str): The title of the chart.
            labels (dict, optional): A dictionary mapping column names to display labels.
            threshold_percentage (float, optional): Minimum percentage of the total for slices to be included.

        Returns:
            px.pie: A Plotly Express pie chart.
        """
        # Validate the graph data by passing df and the columns to _validate_graph_data
        df, validated_columns = self._validate_graph_data(df, names, values)
        names, values = validated_columns  # Unpack the validated columns

        # Private function to return an empty pie chart with just the title
        def return_empty_pie_chart():
            fig = go.Figure()
            fig.update_layout(
                title=title,
                showlegend=True
            )
            fig.add_trace(go.Pie(labels=['No Data'], values=[1], hoverinfo='label'))
            return fig

        # If the DataFrame is empty after validation, return an empty pie chart with just the title
        if df.empty:
            return return_empty_pie_chart()

        # Calculate the total and the percentage for each slice
        total = df[values].sum()
        df['percentage'] = (df[values] / total) * 100

        # Filter the DataFrame to only include slices above the threshold percentage
        df = df[df['percentage'] >= threshold_percentage]

        # If the DataFrame is empty after filtering, return an empty pie chart with just the title
        if df.empty:
            return return_empty_pie_chart()

        # Create the pie chart with the given parameters
        pie_chart_params = {
            'data_frame': df,
            'names': names,
            'values': values,
            'title': title
        }

        if labels:
            pie_chart_params['labels'] = labels

        return px.pie(**pie_chart_params)

    def _create_working_hours_chart(self):
        """
        Creates a bar chart visualizing the distribution of working hours by user.

        Returns:
            px.bar: A Plotly Express bar chart showing working hours' distribution.
        """
        working_hours = self.df_handler.extract_working_hours_data()

        # Ensure 'Time' column is correctly parsed and drop rows with NaT values
        if working_hours is not None:
            # Define custom tick labels for the x-axis
            tick_vals = list(range(0, 24, 1))  # Values: 0, 1, 2, ..., 23
            tick_text = [f"{hour}:00" for hour in tick_vals]  # Labels: "0:00", "2:00", ..., "22:00"

            # Create the bar chart with custom tick labels
            fig = px.bar(working_hours, x='Hour', y='ActivityCount', color='User', barmode='group',
                         title='Working Hours Distribution by Student')

            # Update the x-axis with custom tick labels
            fig.update_layout(xaxis=dict(
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text
            ))

            return fig
        else:
            print("Error: 'Time' column not found in DataFrame.")
            return self._create_bar_chart(pd.DataFrame(), x='Hour', y='ActivityCount',
                                          title="Working Hours Overview")

    def _create_occurrences_chart(self):
        """
        Creates a DataFrame showing the occurrences of work during night, weekend, and holiday periods
        for each user.

        Returns:
            pd.DataFrame: A DataFrame with counts of occurrences categorized by night, weekend, and holiday.
        """
        df = self.df_handler.loaded_df  # Access the preprocessed DataFrame directly
        if df is None:
            df = pd.DataFrame(columns=['Time', 'User'])
        df['Time'] = pd.to_datetime(df['Time'])

        # Extract night, weekend, and holiday occurrences
        df['Night'] = df['Time'].dt.hour.isin(range(0, 6)) | df['Time'].dt.hour.isin(range(20, 24))
        df['Weekend'] = df['Time'].dt.weekday.isin([5, 6])
        df['Holiday'] = df['Time'].dt.date == pd.to_datetime('2023-05-15').date()

        # Count the occurrences of night, weekend, and holiday work
        occurrences = df.groupby('User').agg({'Night': 'sum', 'Weekend': 'sum', 'Holiday': 'sum'}).reset_index()

        # Melt the DataFrame to get it in a suitable format for plotting
        occurrences_melted = pd.melt(occurrences, id_vars=['User'], value_vars=['Night', 'Weekend', 'Holiday'],
                                     var_name='Type', value_name='Occurrences Count')

        return occurrences_melted

    @staticmethod
    def create_collapsible_list(actions, action_type=''):
        """
        Creates a list of collapsible cards based on the specified action type.

        Depending on the action type, this method generates a list of `dbc.Card` components that display actions in a
        collapsible format.

        Parameters:
            actions: The DataFrame containing action data. It should include columns relevant to the action type.
            action_type: The type of action to display. It can be either 'repeated_actions' or 'advanced_basic_actions'.

        Returns:
            A list of Dash Bootstrap Components cards, each containing a header and collapsible body.
        """

        def create_header(button_label, card_id):
            """
            Creates a header button for the collapsible card.

            Parameters:
                button_label: The label for the button.
                card_id: The index of the card used for creating a unique ID.

            Returns:
                A Dash Bootstrap Components Button configured as a collapsible card header.
            """
            return dbc.Button(
                button_label,
                id={'type': 'toggle', 'index': card_id, 'category': action_type},
                color="link",
                n_clicks=0,
                style={'text-align': 'left', 'width': '100%', 'padding': '10px', 'border': '1px solid #ddd'}
            )

        def create_body(description_data, card_id):
            """
            Creates the body for the collapsible card.

            Parameters:
                description_data: List of descriptions to display in the collapsible body.
                card_id: The index of the card used for creating a unique ID.

            Returns:
                A Dash Bootstrap Components Collapse containing the card body.
            """
            return dbc.Collapse(
                dbc.CardBody(html.Ul([
                    html.Li(html.Span([
                        html.Strong("User: "), f"{desc[0]}, ",
                        html.Strong("Action: "), f"{desc[1]}, ",
                        html.Strong("Count: "), f"{desc[2]}"
                    ])) for desc in description_data
                ])),
                id={'type': 'collapse', 'index': card_id, 'category': action_type},
                is_open=False
            )

        items = []
        if action_type == 'repeated_actions':
            for idx, (action_key, group) in enumerate(actions.groupby('Action')):
                user_descriptions = group[['User', 'Description', 'Count']].values.tolist()
                header = create_header(action_key, idx)
                body = create_body(user_descriptions, idx)
                items.append(dbc.Card([header, body]))

        elif action_type == 'advanced_basic_actions':
            advanced_actions = actions[actions['Action Type'] == 'Advanced']
            basic_actions = actions[actions['Action Type'] == 'Basic']
            categories = {
                'Advanced': advanced_actions,
                'Basic': basic_actions
            }
            for idx, (category_key, group) in enumerate(categories.items()):
                action_descriptions = group[['User', 'Action', 'Action Count']].values.tolist()
                header = create_header(category_key, idx)
                body = create_body(action_descriptions, idx)
                items.append(dbc.Card([header, body]))

        return items

    @staticmethod
    def _create_filter_row(dropdown_id, placeholder, options, select_all_id, clear_all_id,
                           default_value=None) -> dbc.Row:
        """
        Creates a filter row consisting of a dropdown and buttons for selecting and clearing all options.

        Args:
            dropdown_id (str): The ID for the dropdown component.
            placeholder (str): The placeholder text for the dropdown.
            options (list): List of options for the dropdown.
            select_all_id (str): The ID for the 'Select All' button.
            clear_all_id (str): The ID for the 'Clear All' button.
            default_value (list, optional): The default selected values for the dropdown.

        Returns:
            dbc.Row: A row containing the dropdown and action buttons.
        """
        return dbc.Row([
            dbc.Col(
                dcc.Dropdown(id=dropdown_id, options=options, placeholder=placeholder, value=default_value, multi=True, disabled=False),
                width=7),
            dbc.Col(dbc.Button([html.I(className="fas fa-check-double", style={"margin-right": "5px"}), "Select All"],
                               id=select_all_id, color="secondary",
                               className="d-flex align-items-center justify-content-center w-100"), width=2),
            dbc.Col(dbc.Button([html.I(className="fas fa-minus", style={"margin-right": "5px"}), "Clear All"],
                               id=clear_all_id, color="secondary",
                               className="d-flex align-items-center justify-content-center w-100"), width=2)
        ], className="mb-3")

    @staticmethod
    def _create_upload_component() -> html.Div:
        """
        Creates an upload component for JSON files with a loading spinner, a file upload area,
        a default data source checkbox, a submit button, and a status display.

        Returns:
            html.Div: A div containing the upload component and its associated elements.
        """
        return html.Div([
            dcc.Loading(
                id='loading',
                type='circle',
                children=[
                    dcc.Upload(
                        id='upload-json',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px 0'
                        },
                        multiple=False,  # Single file upload
                        accept='.json'  # Accept only JSON files
                    ),
                    html.Div(id='output-json-upload', style={'margin': '10px 0'}),
                    dbc.Checkbox(
                        id='default-data-source',
                        className="mb-0",
                        label="Default data source"
                    ),
                    html.Div(
                        "* Default data source logs are loaded automatically."
                        "Beware: Uploading a new default log will overwrite the existing one.",
                        style={'margin': '0', 'padding': '0', 'fontSize': 'small', 'lineHeight': '1',
                               'marginLeft': '25px'}
                    ),
                    dbc.Button(
                        "Submit",
                        id='submit-button',
                        color="primary",
                        className="w-100",
                        disabled=True,
                        style={'margin-top': '30px'}
                    ),
                    html.Div(
                        id='submit-status',
                        style={'margin': '10px 0'}
                    )
                ]
            )
        ])
