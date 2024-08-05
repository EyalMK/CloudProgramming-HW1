from datetime import datetime

from app.dash_callbacks import DashCallbacks
from dataframes.dataframe_handler import DataFrameHandler
from config.constants import START_DATE, END_DATE, PROJECT_NAME, DatabaseCollections
import dash
from dash import dcc, dash_table, Output, Input, State
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class DashPageLayouts:
    def __init__(self, dash_app: dash.Dash, db_handler: 'DatabaseHandler', utils):
        self.dash_app = dash_app
        self.db_handler = db_handler
        self.df_handler = DataFrameHandler(db_handler, utils)
        self.lightly_refined_df = pd.DataFrame([])
        self.graph_processed_df = pd.DataFrame([])
        self.uploaded_json = None
        self.data_source_title = "Default Log"
        self.utils = utils
        self.define_layout()
        self.create_callbacks()
        self.utils.logger.info("Dash app pages loaded, and dataframes processed.")

    def create_callbacks(self):
        DashCallbacks(self.dash_app, self.df_handler, self.db_handler, self, self.utils)

    # Define individual page layouts with graphs and filters
    def dashboard_layout(self):
        return self._create_layout("Dashboard", [
            self._create_card("Activity Over Time", dcc.Graph(figure=self._create_line_chart(
                self.df_handler.activity_over_time, 'Date', 'ActivityCount', 'Activity Over Time')
            ), 12),
            self._create_card("Document Usage Frequency", dcc.Graph(figure=self._create_bar_chart(
                self.df_handler.document_usage, 'Document', 'UsageCount', 'Document Usage Frequency')
            ), 6),
            self._create_card("User Activity Distribution", dcc.Graph(figure=self._create_pie_chart(
                self.df_handler.user_activity, 'User', 'ActivityCount', 'User Activity Distribution')
            ), 6)
        ])

    def working_hours_layout(self):
        return self._create_layout("Working Hours Analysis", [
            self._create_card("Working Hours Overview", dcc.Graph(
                figure=self._create_working_hours_chart()  # Directly use the figure from _create_working_hours_chart
            ), 12),
            self._create_card("Night & Weekend & Holidays Work Occurrences",
                              dcc.Graph(figure=self._create_stacked_bar_chart(
                                  self._create_occurrences_chart(), y='User', x='Occurrences Count',
                                  title='Night & Weekend & Holidays Work Occurrences', color='Type')
                              ), 12)
        ])

    def graphs_layout(self):
        _, _ = self.handle_initial_graph_dataframes()
        return self._create_layout("Advanced Team Activity and Analysis Graphs", [
            html.H4(id='data-source-title', children=f"Current Data Source - {self.data_source_title}",
                    className="mb-4"),
            self._create_card("Filters", self._create_filters(), 12),
            dcc.Store(id='processed-df', data=self.graph_processed_df.to_dict()),
            dcc.Store(id='pre-processed-df', data=self.lightly_refined_df.to_dict()),
            dcc.Tabs([
                dcc.Tab(label='Project Time Distribution', children=[
                    dcc.Graph(id='project-time-distribution-graph')
                ]),
                dcc.Tab(label='Advanced vs. Basic Actions', children=[
                    dcc.Graph(id='advanced-basic-actions-graph')
                ]),
                dcc.Tab(label='Action Frequency by User', children=[
                    dcc.Graph(id='action-frequency-scatter-graph')
                ]),
                dcc.Tab(label='Work Patterns Over Time', children=[
                    dcc.Graph(id='work-patterns-over-time-graph')
                ]),
                dcc.Tab(label='Repeated Actions By User', children=[
                    dcc.Graph(id='repeated-actions-by-user-graph'),
                    html.H2('Grouped Actions Descriptions:'),
                    html.Div(id='grouped-actions-div')
                ]),
            ])
        ])

    def landing_page_layout(self):
        image_path = "/static/homepage_image.jpg"
        return self._create_layout("Welcome to the ShapeFlow Monitor Tool", [
            self._create_card("Overview",
                              html.P(
                                  "The ShapeFlow Monitor Tool is your go-to solution for monitoring and analyzing the performance of your OnShape team. Designed with managers in mind, this application provides comprehensive insights into team activity, project progress, and collaboration efficiency by processing log files in JSON format from the OnShape platform."),
                              12
                              ),

            self._create_card("How to Get Started:",
                              html.Div([
                                  self._create_styled_list_item(
                                      "Upload Log Files:",
                                      "Begin by navigating to the Setup section. Here, you can upload a new log file from your device and save it to the database.",
                                      icon="fas fa-upload"),
                                  self._create_styled_list_item(
                                      "Select Default Log:",
                                      "If you want the uploaded log to be used as the default for analysis, simply choose the 'Set as Default' option.",
                                      icon="fas fa-check"),
                                  self._create_styled_list_item(
                                      "Explore Visualizations:",
                                      "Head over to the Graphs section to explore various analytical graphs that provide a deep dive into your team's performance and activities.",
                                      icon="fas fa-chart-bar"),
                                  self._create_styled_list_item(
                                      "Analyze Working Hours:",
                                      "Visit the Working Hours section to review detailed analyses of your team's working hours, including patterns and productivity trends.",
                                      icon="fas fa-clock"),
                                  self._create_styled_list_item(
                                      "Stay Informed with Alerts:",
                                      "The Alerts section will keep you updated with important notifications derived from the log file, ensuring you never miss a critical insight.",
                                      icon="fas fa-bell"),
                                  self._create_styled_list_item(
                                      "Chatbot Assistance:",
                                      "Use the Chatbot feature for instant assistance and answers to your questions about the tool and its functionalities.",
                                      icon="fas fa-comments"),
                                  self._create_styled_list_item(
                                      "Search Glossary:",
                                      "Easily find and understand specific terms or features using the Search Glossary option.",
                                      icon="fas fa-search"),
                              ], style={"list-style-type": "none", "padding": "0"}),
                              12
                              ),

        ], style={"max-width": "1200px", "margin": "0 auto", "padding": "20px"})

    def alerts_layout(self):
        alerts_list, unread_alerts_count = self.create_alerts_list()
        return self._create_layout("Operations Alerts", [
            self._create_card("Recent Alerts", html.Div(id='alerts-list', children=alerts_list), 12),
            self._create_card("Acknowledge All", dbc.Button("Acknowledge All", color="success", className="w-100",
                                                            id="acknowledge-all-button"), 12),
        ])

    def _create_styled_list_item(self, header: str, text: str, icon: str = None) -> html.Div:
        return html.Div(
            [
                html.I(className=icon, style={"margin-right": "10px", "color": "#007bff"}) if icon else None,
                html.Span(header, style={"font-weight": "bold", "font-size": "1rem"}),
                html.Span(f" {text}", style={"font-size": "1rem", "color": "#343a40"})
            ],
            style={"padding": "10px", "margin-bottom": "5px", "background-color": "#f8f9fa", "border-radius": "5px",
                   "box-shadow": "0 1px 2px rgba(0, 0, 0, 0.1)"}
        )

    def text_search_layout(self):
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Input(id="input", placeholder="Search...", type="text"),
                            width=8
                        ),
                        dbc.Col(
                            dbc.Button(children=html.I(className="fas fa-search", style=dict(display="inline-block")),
                                       id="search-button",
                                       n_clicks=0, size='lg',
                                       style=dict(fontSize='1.7vh', backgroundColor="#007BC4", textAlign="center")),
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
        return self._create_layout("Search OnShape Glossary", [
            self._create_card("Search", self.text_search_layout(), 10)
        ])

    def search_results_table_layout(self, data):
        return html.Div(
            dash_table.DataTable(
                columns=[
                    {"name": "Term", "id": "term"},
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
        return self._create_layout("Upload Log", [
            self._create_card("Upload JSON", self._create_upload_component(), 12)
        ])

    def chatbot_layout(self):
        initial_greeting = "\nShapeFlowBot: Hello! I'm ShapeFlowBot! I can assist you with various questions regarding ShapeFlow Monitor. How can I help you today?"

        return self._create_layout("Chatbot Assistant", [
            dbc.Row([
                dbc.Col(
                    html.Div([
                        html.H5("Chat with ShapeFlowBot", className="card-title mb-5"),
                        dcc.Textarea(
                            id='chat-history',
                            value=initial_greeting,
                            readOnly=True,
                            style={'width': '100%', 'height': '65vh'}
                        ),
                        dbc.Input(
                            id='chat-input',
                            placeholder='Type a message...',
                            type='text',
                            n_submit=0
                        ),
                        dbc.Button('Send', id='send-button', color='primary', className='mt-2'),
                    ]),
                    width=12
                ),
            ])
        ])

    def create_empty_graph(self):
        return go.Figure()

    def create_project_time_distribution_graph(self, dataframe):
        threshold_percentage = 0.4
        return self._create_pie_chart(df=dataframe,
                                      names='Tab',
                                      values='Time Spent (hours)',
                                      title=f'Project Time Distribution (in Hours) - Minimum threshold: {threshold_percentage}%',
                                      labels={'Time Spent (hours)': 'Time Spent (Hours)', 'Tab': 'Project Tab'},
                                      threshold_percentage=threshold_percentage)

    def create_repeated_actions_graph(self, dataframe):
        return self._create_stacked_bar_chart(df=dataframe,
                                              x='User',
                                              y='Count',
                                              color='Action',
                                              title='Repeated Actions Analysis by User',
                                              orientation='v',
                                              labels={'User': 'User', 'Count': 'Repetition Count',
                                                      'Action': 'Action Description'})

    def create_advanced_basic_actions_graph(self, dataframe):
        return self._create_stacked_bar_chart(df=dataframe,
                                              x='Action Count',
                                              y='User',
                                              color='Action Type',
                                              title='Advanced vs. Basic Actions',
                                              grid=False,
                                              labels={'User': 'User', 'Action Count': 'Action Count',
                                                      'Action Type': 'Action Type'},
                                              orientation='h')

    def create_action_frequency_scatter_graph(self, dataframe):
        return self._create_scatter_chart(df=dataframe,
                                          x='Time',
                                          y='User',
                                          color='Action',
                                          title='Action Frequency by User',
                                          labels={'Time': 'Time', 'User': 'User', 'Action': 'Action'})

    def create_work_patterns_over_time_graph(self, dataframe):
        return self._create_stacked_bar_chart(df=dataframe,
                                              x='Time Interval',
                                              y='Action Count',
                                              color='Day',
                                              orientation='v',
                                              title='Work Patterns Over Different Time Intervals',
                                              labels={'Time Interval': 'Time of Day', 'Action Count': 'Action Count',
                                                      'Day': 'Day of Week'})

    def handle_initial_graph_dataframes(self):
        self.lightly_refined_df = self.df_handler.get_lightly_refined_graphs_dataframe()
        self.graph_processed_df = self.df_handler.process_graphs_layout_dataframe(dataframe=self.lightly_refined_df)
        return self.graph_processed_df, self.lightly_refined_df

    def create_header(self):
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
        alert_count = str(self.df_handler.get_unread_alerts_count())
        return dbc.Col([
            dbc.Nav(
                [
                    self._create_nav_link("fas fa-house", " Home", "/"),
                    self._create_nav_link("fas fa-tachometer-alt", " Dashboard", "/dashboard"),
                    self._create_nav_link("fas fa-chart-line", " Graphs", "/graphs"),
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

    def create_footer(self):
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

    def _create_layout(self, title: str, children: list, style: dict = None) -> dbc.Container:
        return dbc.Container([
            dbc.Row([
                dbc.Col(
                    html.H2(title, style={"fontSize": "2.5rem", "textAlign": "left", "margin": "20px 0"}),
                    width=12
                )
            ]),
            dbc.Row(children)
        ], style=style if style else {"padding": "20px"})

    def _create_card(self, title: str, content: html, width: int) -> dbc.Col:
        return dbc.Col(dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody([content])
        ]), width=width, className="mb-3 mt-3")

    def _create_filters(self) -> html.Div:
        # If the selected log path is not uploaded logs, then the default value for the logs dropdown should be empty
        # Otherwise, it should be the first uploaded log
        default_log_value = ""
        if self.df_handler.filters_data['uploaded-logs']:
            default_log_value = self.df_handler.filters_data['uploaded-logs'][
                0] if self.df_handler.selected_log_path == DatabaseCollections.UPLOADED_LOGS.value else ""

        now = datetime.now().strftime('%Y-%m-%dT%H:%M')

        return html.Div([
            self._create_filter_row('document-dropdown', 'Select Document', self.df_handler.filters_data['documents'],
                                    'select-all-documents', 'clear-all-documents'),
            self._create_filter_row('user-dropdown', 'Select User', self.df_handler.filters_data['users'],
                                    'select-all-users', 'clear-all-users'),
            self._create_filter_row('graphs-dropdown', 'Select Graphs', self.df_handler.filters_data['graphs'],
                                    'select-all-graphs', 'clear-all-graphs'),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(id='logs-dropdown',
                                 options=self.df_handler.filters_data['uploaded-logs'],
                                 placeholder='Select Log',
                                 value=self.df_handler.filters_data['uploaded-logs'][0]),
                    width=7)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(html.Div([
                    html.Label("Start Time"),
                    dcc.Input(id='start-time', type='datetime-local',
                              min=datetime.strptime(START_DATE, '%d-%m-%Y').strftime('%Y-%m-%dT%H:%M'), max=now,
                              value=datetime.strptime(START_DATE, '%d-%m-%Y').strftime('%Y-%m-%dT%H:%M'),
                              className='form-control')
                ]), width=6),
                dbc.Col(html.Div([
                    html.Label("End Time"),
                    dcc.Input(id='end-time', type='datetime-local',
                              min=datetime.strptime(START_DATE, '%d-%m-%Y').strftime('%Y-%m-%dT%H:%M'), max=now,
                              value=now, className='form-control')
                ]), width=6)
            ], className="mb-3"),
            dbc.Button("Apply Filters", id='apply-filters', color="primary", className="w-100")
        ], style={"padding": "10px", "maxWidth": "1200px", "margin": "auto"})

    def create_alerts_list(self) -> tuple:
        if self.df_handler.alerts_df.shape[0] == 0:
            alerts_list = html.P("No alerts to display", style={"color": "grey"})
        else:
            alerts_list = html.Ul([
                html.Li(
                    f"{row['Time']} - {row['Description']} by User: {row['User']} in Document: {row['Document']}",
                    style={"color": "grey" if row['Status'] == "read" else "black",
                           "fontWeight": "bold" if row['Status'] == "unread" else "normal"}
                ) for _, row in self.df_handler.alerts_df.iterrows()
            ], id='alerts-list', className="list-unstyled")

        unread_alerts_count = self.df_handler.get_unread_alerts_count()
        return alerts_list, str(unread_alerts_count)

    def _create_nav_link(self, icon_class: str, text: str, href: str, badge_text: str = "",
                         badge_color: str = "", badge_id: str = "") -> dbc.NavLink:
        children = [html.I(className=icon_class), html.Span(text, className="ml-4")]
        if badge_text:
            children.append(dbc.Badge(badge_text, color=badge_color, className="ml-2", id=badge_id))
        return dbc.NavLink(children, href=href, active="exact", className="text-white gap-6")

    def _validate_graph_data(self, df, *columns):
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
        df, validated_columns = self._validate_graph_data(df, x, y)
        x, y = validated_columns  # Unpack the validated columns

        if df.empty:
            return px.bar(title=title)

        return px.bar(df, x=x, y=y, title=title)

    def _create_scatter_chart(self, df: pd.DataFrame, x: str, y: str, color: str, title: str,
                              labels=None) -> px.scatter:
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

    def _create_pie_chart(self, df: pd.DataFrame, names: str, values: str, title: str, labels=None, threshold_percentage=0.0) -> px.pie:
        # Validate the graph data by passing df and the columns to _validate_graph_data
        df, validated_columns = self._validate_graph_data(df, names, values)
        names, values = validated_columns  # Unpack the validated columns

        # If the DataFrame is empty after validation, return an empty pie chart with just the title
        if df.empty:
            return px.pie(title=title)

        # Calculate the total and the percentage for each slice
        total = df[values].sum()
        df['percentage'] = (df[values] / total) * 100

        # Filter the DataFrame to only include slices above the threshold percentage
        df = df[df['percentage'] >= threshold_percentage]

        # If the DataFrame is empty after filtering, return an empty pie chart with just the title
        if df.empty:
            return px.pie(title=title)

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
        working_hours = self.df_handler.extract_working_hours_data()

        # Ensure 'Time' column is correctly parsed and drop rows with NaT values
        if working_hours is not None:
            # Define custom tick labels for the x-axis
            tickvals = list(range(0, 24, 1))  # Values: 0, 1, 2, ..., 23
            ticktext = [f"{hour}:00" for hour in tickvals]  # Labels: "0:00", "2:00", ..., "22:00"

            # Create the bar chart with custom tick labels
            fig = px.bar(working_hours, x='Hour', y='ActivityCount', color='User', barmode='group',
                         title='Working Hours Distribution by Student')

            # Update the x-axis with custom tick labels
            fig.update_layout(xaxis=dict(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext
            ))

            return fig
        else:
            print("Error: 'Time' column not found in DataFrame.")
            return self._create_bar_chart(pd.DataFrame(), x='Hour', y='ActivityCount',
                                          title="Working Hours Overview")

    def _create_occurrences_chart(self):
        df = self.df_handler.df  # Access the preprocessed DataFrame directly
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

    def create_collapsible_list(self, actions):
        items = []
        for index, (action, group) in enumerate(actions.groupby('Action')):
            user_descriptions = group[['User', 'Description', 'Count']].values.tolist()

            header = dbc.Button(
                action,
                id=f"group-{index}-toggle",
                color="link",
                n_clicks=0,
                style={'text-align': 'left', 'width': '100%', 'padding': '10px', 'border': '1px solid #ddd'}
            )

            body = dbc.Collapse(
                dbc.CardBody(html.Ul([
                    html.Li(html.Span([
                        html.Strong("User: "), f"{desc[0]}, ",
                        html.Strong("Action: "), f"{desc[1]}, ",
                        html.Strong("Count: "), f"{desc[2]}"
                    ])) for desc in user_descriptions
                ])),
                id=f"group-{index}-collapse",
                is_open=False
            )

            items.append(dbc.Card([header, body]))

            self.dash_app.callback(
                Output(f"group-{index}-collapse", "is_open"),
                [Input(f"group-{index}-toggle", "n_clicks")],
                [State(f"group-{index}-collapse", "is_open")]
            )(lambda n, is_open: not is_open if n else is_open)

        return items

    def _create_filter_row(self, dropdown_id, placeholder, options, select_all_id, clear_all_id,
                           default_value=None) -> dbc.Row:
        return dbc.Row([
            dbc.Col(
                dcc.Dropdown(id=dropdown_id, options=options, placeholder=placeholder, value=default_value, multi=True),
                width=7),
            dbc.Col(dbc.Button([html.I(className="fas fa-check-double", style={"margin-right": "5px"}), "Select All"],
                               id=select_all_id, color="secondary",
                               className="d-flex align-items-center justify-content-center w-100"), width=2),
            dbc.Col(dbc.Button([html.I(className="fas fa-minus", style={"margin-right": "5px"}), "Clear All"],
                               id=clear_all_id, color="secondary",
                               className="d-flex align-items-center justify-content-center w-100"), width=2)
        ], className="mb-3")

    def _create_upload_component(self) -> html.Div:
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
                        "Default data source will be used when you start the program.",
                        style={'margin': '0', 'padding': '0', 'fontSize': 'small', 'lineHeight': '1', 'marginLeft': '25px'}
                    ),
                    dbc.Button(
                        "Submit",
                        id='submit-button',
                        color="primary",
                        className="w-100",
                        disabled=True,
                        style={'marginTop': '30px'}
                    ),
                    html.Div(
                        id='submit-status',
                        style={'margin': '10px 0'}
                    )
                ]
            )
        ])
