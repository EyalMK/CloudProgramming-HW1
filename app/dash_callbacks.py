import base64
import json
import pandas as pd
import dash
from dash.dependencies import Input, Output, State

from chatbot.chat_bot import ChatBot
from config.constants import DatabaseCollections
from dataframes.dataframe_handler import DataFrameHandler
from search_engine.search_engine import SearchEngine
from utils.utilities import Utilities


class DashCallbacks:
    def __init__(self, dash_app: dash.Dash, df_handler: DataFrameHandler, db_handler: 'DatabaseHandler', page_layouts: 'DashPageLayouts', utils: Utilities):
        self.dash_app = dash_app
        self.df_handler = df_handler
        self.db_handler = db_handler
        self.page_layouts = page_layouts
        self.utils = utils
        self.search_engine = SearchEngine(db_handler, utils)
        self.chat_bot = ChatBot(db_handler, utils)
        self.register_callbacks()

    def _update_selection(self, select_all_clicks, clear_all_clicks, options):
        ctx = dash.callback_context

        if not ctx.triggered:
            return dash.no_update

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'select-all' in button_id and select_all_clicks:
            return [option for option in options]
        elif 'clear-all' in button_id and clear_all_clicks:
            return []

    def register_callbacks(self):
        # Callback to update graphs
        @self.dash_app.callback(
            [Output('activity-over-time', 'figure'),
             Output('document-usage-frequency', 'figure'),
             Output('user-activity-distribution', 'figure')],
            [Input('apply-filters', 'n_clicks')],
            [dash.dependencies.State('document-dropdown', 'value'),
             dash.dependencies.State('user-dropdown', 'value'),
             dash.dependencies.State('description-dropdown', 'value'),
             dash.dependencies.State('date-picker-range', 'start_date'),
             dash.dependencies.State('date-picker-range', 'end_date')]
        )
        def update_graphs(n_clicks: int, selected_document: str, selected_user: str, selected_description: str, start_date: str, end_date: str):
            filtered_df = self.df_handler.df.copy()

            if selected_document:
                filtered_df = filtered_df[filtered_df['Document'] == selected_document]

            if selected_user:
                filtered_df = filtered_df[filtered_df['User'] == selected_user]

            if selected_description:
                filtered_df = filtered_df[filtered_df['Description'] == selected_description]

            if start_date and end_date:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
                filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

            # Group by date and count activities
            activity_over_time = filtered_df.groupby('Date').size().reset_index(name='ActivityCount')

            # Group by document and count usage
            document_usage = filtered_df['Document'].value_counts().reset_index(name='UsageCount')
            document_usage.columns = ['Document', 'UsageCount']

            # Group by user and count activities
            user_activity = filtered_df['User'].value_counts().reset_index(name='ActivityCount')
            user_activity.columns = ['User', 'ActivityCount']

            fig_activity = self.page_layouts._create_line_chart(activity_over_time, 'Date', 'ActivityCount', 'Activity Over Time')
            fig_documents = self.page_layouts._create_bar_chart(document_usage, 'Document', 'UsageCount', 'Document Usage Frequency')
            fig_users = self.page_layouts._create_pie_chart(user_activity, 'User', 'ActivityCount', 'User Activity Distribution')

            return fig_activity, fig_documents, fig_users

        # Combined callback to handle file upload and submit
        @self.dash_app.callback(
            [Output('output-json-upload', 'children'),
             Output('submit-button', 'disabled'),
             Output('submit-status', 'children')],
            [Input('upload-json', 'contents'),
             Input('submit-button', 'n_clicks')],
            [State('upload-json', 'filename'),
             State('default-data-source', 'value')]
        )
        def handle_file_upload_and_submit(contents, n_clicks, filename, default_data_source):
            ctx = dash.callback_context
            if not ctx.triggered:
                return "No file uploaded.", True, ''  # Initial state

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if trigger_id == 'upload-json':
                if contents is not None and filename is not None:
                    content_type, content_string = contents.split(',')
                    decoded = base64.b64decode(content_string)

                    try:
                        json_data = json.loads(decoded)

                        processed_filename = filename
                        while processed_filename in self.df_handler.filters_data['uploaded-logs']:
                            processed_filename = processed_filename.split('.json')[0] + " - Copy.json"

                        data_to_store = {
                            "fileName": processed_filename,
                            "data": json_data
                        }
                        self.page_layouts.uploaded_json = data_to_store  # Store JSON data
                        return f"{filename}", False, ''  # Enable submit button and clear status
                    except json.JSONDecodeError:
                        self.utils.logger.error(f"Failed to parse JSON: {filename}")
                        return "Failed to parse JSON file.", True, ''  # Keep submit button disabled and clear status

                return "No file uploaded.", True, ''  # Keep submit button disabled and clear status

            elif trigger_id == 'submit-button':
                if n_clicks is not None and contents is not None:
                    try:
                        content_type, content_string = contents.split(',')
                        decoded = base64.b64decode(content_string)
                        size_kb = len(decoded) / 1024  # size in KB

                        collection_name = DatabaseCollections.onshape_logs.value if default_data_source else DatabaseCollections.uploaded_logs.value

                        self.db_handler.write_to_database(collection_name, self.page_layouts.uploaded_json)
                        self.utils.logger.info(f"Uploaded JSON of size: {size_kb:.2f} KB")

                        # Notify DataFrameHandler to update its state
                        self.df_handler.update_with_new_data(collection_name)

                        return dash.no_update, dash.no_update, "File has been uploaded successfully."
                    except Exception as e:
                        self.utils.logger.error(f"Error uploading JSON: {str(e)}")
                        return dash.no_update, dash.no_update, f"Error: {str(e)}"

                return dash.no_update, dash.no_update, "No data to submit."

        # Callback to Search onShape Glossary
        @self.dash_app.callback(
            Output("output", "children"),
            [Input('search-button', 'n_clicks')],
            [State("input", "value")]
        )
        def search_term_in_glossary(n_clicks, value):
            if n_clicks > 0 and value:
                results = self.search_engine.perform_search(value)
                if results:
                    if isinstance(results, int):
                        data = [
                            {"term": value, "occurrences": results}
                        ]
                        return self.page_layouts.search_results_table_layout(data=data)

                    data = [{"term": key, "occurrences": val} for key, val in results.items()]
                    return self.page_layouts.search_results_table_layout(data=data)
                else:
                    return f"{value} is not a term in the glossary."
            return "Enter a search term and click the search button."

        # Callback to acknowledge all alerts
        @self.dash_app.callback(
            [Output('alerts-list', 'children'),
             Output('alerts-count-badge', 'children')],
            [Input('acknowledge-all-button', 'n_clicks')]
        )
        def update_alerts(n_clicks):
            # Always update the alerts list and badge count
            alerts_list, unread_alerts_count = self.page_layouts.create_alerts_list()

            # If acknowledge-all button was clicked, update the status of all alerts to 'read'
            if n_clicks is not None:
                self.df_handler.alerts_df['Status'] = 'read'
                alerts_list, unread_alerts_count = self.page_layouts.create_alerts_list()

            return alerts_list, unread_alerts_count

        @self.dash_app.callback(
            Output('chat-history', 'value'),
            [Input('send-button', 'n_clicks'), Input('chat-input', 'n_submit')],  # Include n_submit
            [State('chat-input', 'value'), State('chat-history', 'value')]
        )
        def update_chat(n_clicks, n_submit, user_input, chat_history):
            if (n_clicks is None and n_submit is None) or user_input is None or user_input.strip() == "":
                return chat_history

            response = self.chat_bot.respond(user_input)
            new_history = f"{chat_history}\n\nYou: {user_input}\n\nShapeFlowBot: {response}"
            return new_history


        @self.dash_app.callback(
            Output('chat-input', 'value'),
            [Input('send-button', 'n_clicks'), Input('chat-input', 'n_submit')]
        )
        def clear_input(n_clicks, n_submit):
            # If either button is clicked or Enter is pressed, clear the input
            if n_clicks or n_submit:
                return ''
            return dash.no_update



        @self.dash_app.callback(
            Output('document-dropdown', 'value'),
            [Input('select-all-documents', 'n_clicks'),
             Input('clear-all-documents', 'n_clicks')],
            [State('document-dropdown', 'options')]
        )
        def update_document_selection(select_all_clicks, clear_all_clicks, options):
            return self._update_selection(select_all_clicks, clear_all_clicks, options)

        @self.dash_app.callback(
            Output('user-dropdown', 'value'),
            [Input('select-all-users', 'n_clicks'),
             Input('clear-all-users', 'n_clicks')],
            [State('user-dropdown', 'options')]
        )
        def update_user_selection(select_all_clicks, clear_all_clicks, options):
            return self._update_selection(select_all_clicks, clear_all_clicks, options)

        @self.dash_app.callback(
            Output('logs-dropdown', 'value'),
            [Input('select-all-logs', 'n_clicks'),
             Input('clear-all-logs', 'n_clicks')],
            [State('logs-dropdown', 'options')]
        )
        def update_logs_selection(select_all_clicks, clear_all_clicks, options):
            return self._update_selection(select_all_clicks, clear_all_clicks, options)

        @self.dash_app.callback(
            Output('graphs-dropdown', 'value'),
            [Input('select-all-graphs', 'n_clicks'),
             Input('clear-all-graphs', 'n_clicks')],
            [State('graphs-dropdown', 'options')]
        )
        def update_graphs_selection(select_all_clicks, clear_all_clicks, options):
            return self._update_selection(select_all_clicks, clear_all_clicks, options)

        # 1. Project Time Distribution Graph
        @self.dash_app.callback(
            Output('project-time-distribution-graph', 'figure'),
            Input('project-time-distribution-graph', 'id'),
            State('processed-df', 'data')
        )
        def update_project_time_distribution_graph(_, data):
            df = pd.DataFrame(data)

            # Ensure Time column is datetime
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

            # Drop rows with invalid datetime values
            df = df.dropna(subset=['Time'])

            # Sort the data by Tab and Time to ensure proper diff calculation
            df_sorted = df.sort_values(by=['Tab', 'Time'])

            # Calculate the time differences after sorting
            df_sorted['Time Diff'] = df_sorted.groupby('Tab')['Time'].diff().dt.total_seconds()

            # Filter out rows with NaN in Time Diff or negative Time Diff
            filtered_df = df_sorted.dropna(subset=['Time Diff'])
            filtered_df = filtered_df[filtered_df['Time Diff'] > 0]
            filtered_df = filtered_df[filtered_df['Time Diff'] <= 1800]  # Ignore gaps longer than 30 minutes

            # Check if there is any data left after filtering
            if filtered_df.empty:
                return self.page_layouts.create_empty_graph()

            # Recalculate the Time Spent (summing time differences for each Tab)
            project_time = filtered_df.groupby('Tab')['Time Diff'].sum().reset_index(name='Time Spent (seconds)')

            # Convert seconds to hours for better readability
            project_time['Time Spent (hours)'] = (project_time['Time Spent (seconds)'] / 3600).round(2)

            # Create the pie chart with the updated Time Spent in hours
            return self.page_layouts.create_piechart_time_dist(dataframe=project_time)

        # 2. Advanced vs. Basic Actions (Grouped Bar Chart)
        @self.dash_app.callback(
            Output('advanced-basic-actions-graph', 'figure'),
            Input('advanced-basic-actions-graph', 'id'),
            State('processed-df', 'data')
        )
        def update_advanced_basic_actions_graph(_, data):
            df = pd.DataFrame(data)
            action_data = df.groupby(['User', 'Action Type']).size().reset_index(name='Action Count')
            return self.page_layouts.create_advanced_basic_actions_graph(dataframe=action_data)

        # 3. Action Frequency by User (Scatter Plot with DatePickerRange)
        @self.dash_app.callback(
            Output('action-frequency-scatter-graph', 'figure'),
            [Input('date-picker-range-action-frequency-scatter', 'start_date'),
             Input('date-picker-range-action-frequency-scatter', 'end_date')],
            State('processed-df', 'data')
        )
        def update_action_frequency_scatter_graph(start_date, end_date, data):
            # Filter the data based on the selected date range
            df = pd.DataFrame(data)
            filtered_df = df[(df['Time'] >= start_date) & (df['Time'] <= end_date)]

            # Create the scatter plot
            return self.page_layouts.create_action_frequency_scatter_graph(dataframe=filtered_df)

        # 4. Work Patterns Over Different Time Intervals (Bar Chart)
        @self.dash_app.callback(
            Output('work-patterns-over-time-graph', 'figure'),
            Input('work-patterns-over-time-graph', 'id'),
            State('processed-df', 'data')
        )
        def update_work_patterns_over_time_graph(_, data):
            df = pd.DataFrame(data)

            # Ensure Time column is datetime
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

            # Drop rows with invalid datetime values
            df = df.dropna(subset=['Time'])

            work_patterns = df.groupby(
                [df['Time'].dt.day_name().rename('Day'), df['Time'].dt.hour.rename('Hour')]
            ).size().reset_index(name='Action Count')

            work_patterns['Time Interval'] = work_patterns['Hour'].astype(str) + ":00 - " + (
                    work_patterns['Hour'] + 1).astype(str) + ":00"

            return self.page_layouts.create_work_patterns_over_time_graph(dataframe=work_patterns)

        # 5. Repeated Actions Frequencies Graph
        @self.dash_app.callback(
            [Output('repeated-actions-by-user-graph', 'figure'),
             Output('grouped-actions-div', 'children')],
            Input('repeated-actions-by-user-graph', 'id'),
            State('pre-processed-df', 'data')
        )
        def update_repeated_actions_by_user_graph(_, data):
            df = pd.DataFrame(data)
            df = df.sort_values(by=['User', 'Time'])
            grouped_actions = df.groupby(['Action', 'User', 'Description']).size().reset_index(name='Count')

            figure = self.page_layouts.create_repeated_actions_graph(dataframe=grouped_actions)
            collapsible_list = self.page_layouts.create_collapsible_list(grouped_actions)

            return figure, collapsible_list

        # Callbacks for dynamic content
        @self.dash_app.callback(
            Output("page-content", "children"),
            [Input("url", "pathname")]
        )
        def display_page(pathname: str):
            if pathname == "/graphs":
                return self.page_layouts.graphs_layout()
            elif pathname == "/dashboard":
                return self.page_layouts.dashboard_layout()
            elif pathname == "/alerts":
                return self.page_layouts.alerts_layout()
            elif pathname == '/working-hours':  # New Route for Working Hours
                return self.page_layouts.working_hours_layout()
            elif pathname == "/search-glossary":
                return self.page_layouts.search_glossary_layout()
            elif pathname == "/upload-log":
                return self.page_layouts.upload_log_layout()
            elif pathname == "/chatbot":
                return self.page_layouts.chatbot_layout()
            else:
                return self.page_layouts.landing_page_layout()
