import base64
import json

import dash
import pandas as pd
from dash import MATCH, dcc
from dash.dependencies import Input, Output, State

from chatbot.chat_bot import ChatBot
from config.constants import DatabaseCollections
from dataframes.dataframe_handler import DataFrameHandler
from search_engine.search_engine import SearchEngine
from utils.utilities import Utilities


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
            return [option['value'] for option in options]
        elif 'clear-all' in button_id and clear_all_clicks:
            return []
        return dash.no_update

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

    def update_dynamic_graphs(self, dataframe, graph_type, selected_document, selected_log, selected_user, start_time,
                              end_time):
        filtered_df = self.df_handler.filter_dataframe_for_graphs(dataframe, selected_document,selected_user, start_time, end_time)

        if filtered_df is None or filtered_df.empty:
            return self.page_layouts.create_empty_graph(), None

        if graph_type == 'Project Time Distribution':
            return self.page_layouts.create_project_time_distribution_graph(self.df_handler.setup_project_time_distribution_graph_dataframe(filtered_df)), None
        elif graph_type == 'Advanced vs. Basic Actions':
            collapsible_df = self.df_handler.prepare_data_for_collapsible_list(filtered_df, type='advanced_basic_actions')
            collapsible_list = self.page_layouts.create_collapsible_list(collapsible_df, type='advanced_basic_actions')
            check = self.page_layouts.create_advanced_basic_actions_graph(self.df_handler.setup_advanced_basic_actions_graph_dataframe(filtered_df))
            return check, collapsible_list
        elif graph_type == 'Action Frequency by User':
            return self.page_layouts.create_action_frequency_scatter_graph(self.df_handler.setup_action_frequency_scatter_graph_dataframe(filtered_df,start_time,end_time)), None
        elif graph_type == 'Work Patterns Over Time':
            return self.page_layouts.create_work_patterns_over_time_graph(self.df_handler.setup_work_patterns_over_time_graph_dataframe(filtered_df)), None
        elif graph_type == 'Repeated Actions By User':
            collapsible_df = self.df_handler.prepare_data_for_collapsible_list(filtered_df, type='repeated_actions')
            collapsible_list = self.page_layouts.create_collapsible_list(collapsible_df, type='repeated_actions')
            return self.page_layouts.create_repeated_actions_graph(self.df_handler.setup_repeated_actions_by_user_graph_dataframe(filtered_df)), collapsible_list

        return self.page_layouts.create_empty_graph(), None

    def process_json_filename(self, filename, default_data_source):
        processed_filename = filename
        if default_data_source:
            processed_filename = "default.json"
        else:
            index = 1
            while processed_filename in self.df_handler.filters_data['uploaded-logs']:
                processed_filename = f"{filename.split('.json')[0]} ({index}).json"
                index += 1
        return processed_filename

    def register_callbacks(self):
        # Callback to update graphs
        @self.dash_app.callback(
            [Output('graphs-tabs-container', 'style'),
             Output('dynamic-tabs', 'children'),
             Output('data-source-title', 'children'),
             Output('alerts-count-badge', 'children', allow_duplicate=True),
             Output('start-time', 'value'),
             Output('start-time', 'min'),
             Output('start-time', 'max'),
             Output('end-time', 'value'),
             Output('end-time', 'min'),
             Output('end-time', 'max'),
             Output('processed-df', 'data'),
             Output('pre-processed-df', 'data')],
            [Input('apply-filters', 'n_clicks')],
            [State('processed-df', 'data'),
             State('document-dropdown', 'value'),
             State('logs-dropdown', 'value'),
             State('user-dropdown', 'value'),
             State('start-time', 'value'),
             State('end-time', 'value'),
             State('graphs-dropdown', 'value')],
            prevent_initial_call=True
        )
        def update_all_graphs(n_clicks, data, selected_document, selected_log, selected_user, start_time, end_time,
                              selected_graphs):

            if selected_graphs is None:
                selected_graphs = []

            tabs_style = {'display': 'block'} if selected_graphs else {'display': 'none'}

            dataframe = pd.DataFrame(data)
            value_start_time = start_time
            value_end_time = end_time
            full_range_start_time = self.df_handler.min_date
            full_range_end_time = self.df_handler.max_date

            # If a log is selected, update dataframe handler attributes with the new log data
            # And then update processed-df and pre-processed-df attributes in the graphs_layout
            if selected_log and self.df_handler.selected_log_name != selected_log:
                is_default_source = selected_log.lower() == 'default log'
                collection_name = DatabaseCollections.ONSHAPE_LOGS.value if is_default_source else DatabaseCollections.UPLOADED_LOGS.value
                processed_filename = 'default.json' if is_default_source else selected_log

                self.df_handler.handle_switch_log_source(collection_name, file_name=processed_filename)
                dataframe = self.page_layouts.handle_initial_graph_dataframes()

                full_range_start_time = value_start_time = self.df_handler.min_date  # Get new dates
                full_range_end_time = value_end_time = self.df_handler.max_date

            filtered_df = self.df_handler.filter_dataframe_for_graphs(dataframe, selected_document,
                                                                      selected_user, value_start_time, value_end_time)

            if filtered_df is None or filtered_df.empty:
                return [tabs_style, [], dash.no_update, dash.no_update,
                        value_start_time, full_range_start_time, full_range_end_time,
                        value_end_time, full_range_start_time, full_range_end_time,
                        self.page_layouts.graph_processed_df.to_dict(), self.page_layouts.lightly_refined_df.to_dict()]

            updated_tabs = []
            for graph_type in selected_graphs:
                figure, collapsible = self.update_dynamic_graphs(filtered_df, graph_type, selected_document,
                                                                 selected_log, selected_user, value_start_time, value_end_time)

                if collapsible:
                    collapsible_content = collapsible if isinstance(collapsible, list) else [collapsible]
                else:
                    collapsible_content = []

                tab_content = [dcc.Graph(figure=figure)] + collapsible_content

                updated_tabs.append(dcc.Tab(label=graph_type, children=tab_content))

            new_data_source_title = selected_log if selected_log else self.page_layouts.data_source_title
            data_source_title = f"Current Data Source - {new_data_source_title}"

            return [tabs_style, updated_tabs, data_source_title, str(self.df_handler.get_unread_alerts_count()),
                    value_start_time, full_range_start_time, full_range_end_time,
                    value_end_time, full_range_start_time, full_range_end_time,
                    self.page_layouts.graph_processed_df.to_dict(), self.page_layouts.lightly_refined_df.to_dict()]

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

                        processed_filename = self.process_json_filename(filename, default_data_source)

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
                        processed_filename = self.process_json_filename(filename, default_data_source)

                        self.utils.logger.info(f"Uploaded JSON: {processed_filename} of size: {size_kb:.2f} KB")

                        # Notify DataFrameHandler to update its state
                        self.df_handler.update_with_new_data(collection_name, processed_filename)

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
