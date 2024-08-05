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
from dash import MATCH


class DashCallbacks:
    def __init__(self, dash_app: dash.Dash, df_handler: DataFrameHandler, db_handler: 'DatabaseHandler',
                 page_layouts: 'DashPageLayouts', utils: Utilities):
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

    def _update_graph(self, data, setup_dataframe_callback, create_graph_callback, *setup_dataframe_args, graph_type = '',
                      collapsible_list=False):
        df = pd.DataFrame(data)
        filtered_df = setup_dataframe_callback(df, *setup_dataframe_args)
        if filtered_df is None:
            return self.page_layouts.create_empty_graph()

        if collapsible_list:
            collapsible_df = self.df_handler.prepare_data_for_collapsible_list(df, type=graph_type)
            collapsible_list_component = self.page_layouts.create_collapsible_list(collapsible_df, type=graph_type)
            return create_graph_callback(dataframe=filtered_df), collapsible_list_component

        return create_graph_callback(dataframe=filtered_df)

    def register_callbacks(self):
        # Callback to update graphs
        @self.dash_app.callback(
            [Output('action-frequency-scatter-graph', 'figure'),
             Output('work-patterns-over-time-graph', 'figure'),
             Output('project-time-distribution-graph', 'figure'),
             Output('advanced-basic-actions-graph', 'figure'),
             Output('repeated-actions-by-user-graph', 'figure'),
             Output('grouped-actions-div', 'children'),
             Output('grouped-actions-divergence', 'children'),
             Output('data-source-title', 'children'),
             Output('alerts-count-badge', 'children', allow_duplicate=True)],
            [Input('apply-filters', 'n_clicks')],
            [State('processed-df', 'data'),
             dash.dependencies.State('document-dropdown', 'value'),
             dash.dependencies.State('logs-dropdown', 'value'),
             dash.dependencies.State('user-dropdown', 'value'),
             dash.dependencies.State('start-time', 'value'),
             dash.dependencies.State('end-time', 'value')],
            prevent_initial_call='initial_duplicate'
        )
        def update_all_graphs(n_clicks, data, selected_document, selected_log, selected_user, start_time, end_time):
            dataframe = pd.DataFrame(data)
            # If a log is selected, update dataframe handler attributes with the new log data
            # And then update processed-df and pre-processed-df attributes in the graphs_layout
            if selected_log and self.df_handler.selected_log_name != selected_log:
                is_default_source = selected_log.lower() == 'default log'
                collection_data = self.db_handler.read_from_database(
                    DatabaseCollections.ONSHAPE_LOGS.value if is_default_source else DatabaseCollections.UPLOADED_LOGS.value)
                if collection_data is None:
                    self.utils.logger.error(f"No log data available for selected log: {selected_log}")
                    return [dash.no_update] * 8
                self.df_handler.handle_switch_log_source(collection_data, file_name=selected_log)
                dataframe, _ = self.page_layouts.handle_initial_graph_dataframes()

            filtered_df = self.df_handler.filter_dataframe_for_graphs(dataframe, selected_document,
                                                                      selected_user, start_time, end_time)

            if filtered_df is None:
                return [dash.no_update] * 8

            ctx = dash.callback_context
            if not ctx.triggered:
                return [dash.no_update] * 8
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]

            fig_action_frequency = fig_work_patterns = fig_project_time = fig_repeated_actions = fig_advanced_basics_actions = self.page_layouts.create_empty_graph()
            collapsible_list = "No data available"
            collapsible_actions_list = "No data available"
            # print all columns of filtered_df
            if input_id == 'apply-filters':
                fig_action_frequency = self._update_graph(
                    filtered_df,
                    self.df_handler.setup_action_frequency_scatter_graph_dataframe,
                    self.page_layouts.create_action_frequency_scatter_graph,
                    start_time,
                    end_time
                )
                fig_work_patterns = self._update_graph(
                    filtered_df,
                    self.df_handler.setup_work_patterns_over_time_graph_dataframe,
                    self.page_layouts.create_work_patterns_over_time_graph,
                    graph_type='work_patterns'
                )
                fig_project_time = self._update_graph(
                    filtered_df,
                    self.df_handler.setup_project_time_distribution_graph_dataframe,
                    self.page_layouts.create_project_time_distribution_graph,
                    graph_type='project_time_distribution'
                )
                fig_repeated_actions, collapsible_list = self._update_graph(
                    filtered_df,
                    self.df_handler.setup_repeated_actions_by_user_graph_dataframe,
                    self.page_layouts.create_repeated_actions_graph,
                    graph_type='repeated_actions',
                    collapsible_list=True
                )
                fig_advanced_basics_actions, collapsible_actions_list = self._update_graph(
                    filtered_df,
                    self.df_handler.setup_advanced_basic_actions_graph_dataframe,
                    self.page_layouts.create_advanced_basic_actions_graph,
                    graph_type='advanced_basic_actions',
                    collapsible_list=True
                )

            # Update the data source title if filters are applied
            new_data_source_title = selected_log if selected_log else self.page_layouts.data_source_title
            data_source_title = f"Current Data Source - {new_data_source_title}"

            return fig_action_frequency, \
                fig_work_patterns, \
                fig_project_time, \
                fig_advanced_basics_actions, \
                fig_repeated_actions, \
                collapsible_list, \
                collapsible_actions_list, \
                data_source_title, \
                str(self.df_handler.get_unread_alerts_count())

        # Combined callback to handle file upload and submit
        @self.dash_app.callback(
            [Output('output-json-upload', 'children'),
             Output('submit-button', 'disabled'),
             Output('submit-status', 'children'),
             Output('alerts-count-badge', 'children', allow_duplicate=True)],
            [Input('upload-json', 'contents'),
             Input('submit-button', 'n_clicks')],
            [State('upload-json', 'filename'),
             State('default-data-source', 'value')],
            prevent_initial_call='initial_duplicate'
        )
        def handle_file_upload_and_submit(contents, n_clicks, filename, default_data_source):
            ctx = dash.callback_context
            if not ctx.triggered:
                return "No file uploaded.", True, '', dash.no_update  # Initial state

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if trigger_id == 'upload-json':
                if contents is not None and filename is not None:
                    content_type, content_string = contents.split(',')
                    decoded = base64.b64decode(content_string)

                    try:
                        json_data = json.loads(decoded)

                        processed_filename = filename
                        index = 1
                        while processed_filename in self.df_handler.filters_data['uploaded-logs']:
                            processed_filename = f"{filename.split('.json')[0]} ({index}).json"
                            index += 1

                        data_to_store = {
                            "fileName": processed_filename,
                            "data": json_data
                        }
                        self.page_layouts.uploaded_json = data_to_store  # Store JSON data
                        return f"{filename}", False, '', str(self.df_handler.get_unread_alerts_count())
                    except json.JSONDecodeError:
                        self.utils.logger.error(f"Failed to parse JSON: {filename}")
                        return "Failed to parse JSON file.", True, '', dash.no_update

                return "No file uploaded.", True, '', dash.no_update

            elif trigger_id == 'submit-button':
                if n_clicks is not None and contents is not None:
                    try:
                        content_type, content_string = contents.split(',')
                        decoded = base64.b64decode(content_string)
                        size_kb = len(decoded) / 1024  # size in KB

                        collection_name = DatabaseCollections.ONSHAPE_LOGS.value if default_data_source else DatabaseCollections.UPLOADED_LOGS.value

                        self.db_handler.write_to_database(collection_name, self.page_layouts.uploaded_json)
                        self.utils.logger.info(f"Uploaded JSON of size: {size_kb:.2f} KB")

                        # Notify DataFrameHandler to update its state
                        self.df_handler.update_with_new_data(collection_name)

                        return dash.no_update, dash.no_update, "File has been uploaded successfully.", str(
                            self.df_handler.get_unread_alerts_count())
                    except Exception as e:
                        self.utils.logger.error(f"Error uploading JSON: {str(e)}")
                        return dash.no_update, dash.no_update, f"Error: {str(e)}", dash.no_update

                return dash.no_update, dash.no_update, "No data to submit.", dash.no_update

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
             Output('alerts-count-badge', 'children', allow_duplicate=True)],
            [Input('acknowledge-all-button', 'n_clicks')],
            prevent_initial_call='initial_duplicate'
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

        @self.dash_app.callback(
            Output({'type': 'collapse', 'index': MATCH, 'category': MATCH}, 'is_open'),
            Input({'type': 'toggle', 'index': MATCH, 'category': MATCH}, 'n_clicks'),
            State({'type': 'collapse', 'index': MATCH, 'category': MATCH}, 'is_open')
        )
        def toggle_collapsible_list(n_clicks, is_open):
            if n_clicks:
                return not is_open
            return is_open
