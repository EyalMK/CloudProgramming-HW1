import base64
import json

import dash
from dash.dependencies import Input, Output, State
from dataframes.dataframe_handler import DataFrameHandler
from utils.utilities import Utilities


class DashCallbacks:
    def __init__(self, dash_app: dash.Dash, df_handler: DataFrameHandler, db_handler: 'DatabaseHandler', page_layouts: 'DashPageLayouts', utils: Utilities):
        self.dash_app = dash_app
        self.df_handler = df_handler
        self.db_handler = db_handler
        self.page_layouts = page_layouts
        self.utils = utils
        self.register_callbacks()

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

        # Callback to upload JSONs
        @self.dash_app.callback(
            [Output('output-json-upload', 'children'),
            Output('submit-button', 'disabled')],
            [Input('upload-json', 'contents')],
            [State('upload-json', 'filename')]
        )
        def handle_file_upload(contents, filename):
            if contents is not None and filename is not None:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)

                try:
                    json_data = json.loads(decoded)
                    self.page_layouts.uploaded_json = json_data  # Store JSON data
                    return f"{filename}", False  # Enable submit button
                except json.JSONDecodeError:
                    self.utils.logger.error(f"Failed to parse JSON: {filename}")
                    return "Failed to parse JSON file.", True  # Keep submit button disabled

            return "No file uploaded.", True  # Keep submit button disabled

        @self.dash_app.callback(
            Output('submit-status', 'children'),
            [Input('submit-button', 'n_clicks')],
            [State('upload-json', 'contents')],
            prevent_initial_call=True
        )
        def handle_submit(n_clicks, contents):
            if n_clicks is not None and contents is not None:
                try:
                    content_type, content_string = contents.split(',')
                    decoded = base64.b64decode(content_string)
                    size_kb = len(decoded) / 1024  # size in KB

                    self.db_handler.write_to_database("/uploaded-jsons", self.page_layouts.uploaded_json)
                    self.utils.logger.info(f"Loaded JSON of size: {size_kb:.2f} KB")
                    return "File has been uploaded successfully."
                except Exception as e:
                    self.utils.logger.error(f"Error uploading JSON: {str(e)}")
                    return f"Error: {str(e)}"

            return "No data to submit."

        # Callbacks for dynamic content
        @self.dash_app.callback(Output("page-content", "children"),
                      [Input("url", "pathname")])
        def display_page(pathname: str):
            if pathname == "/graphs":
                return self.page_layouts.graphs_layout()
            elif pathname == "/alerts":
                return self.page_layouts.alerts_layout()
            elif pathname == "/activity-log":
                return self.page_layouts.activity_log_layout()
            elif pathname == "/settings":
                return self.page_layouts.settings_layout()
            elif pathname == "/upload-log":
                return self.page_layouts.upload_log_layout()
            else:
                return self.page_layouts.dashboard_layout()
