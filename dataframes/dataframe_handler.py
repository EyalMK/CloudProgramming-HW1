### DataFrames Handler
from config.constants import ONSHAPE_LOGS_PATH, UPLOADED_LOGS_PATH
import pandas as pd


class DataFrameHandler:
    def __init__(self, db_handler, utils):
        self.raw_df = None
        self.df = None
        self.utils = utils
        self.filters_data = {
            'documents': [],
            'users': [],
            'descriptions': [],
            'uploaded-logs': []
        }
        self.activity_over_time = []
        self.document_usage = []
        self.user_activity = []
        self.selected_log_path = ONSHAPE_LOGS_PATH  # Default data source
        self.alerts_df = pd.DataFrame()
        self.db_handler = db_handler
        self.initialize_df()
        self.process_df()

    def initialize_df(self):
        try:
            data = self.db_handler.read_from_database(ONSHAPE_LOGS_PATH)  # OnShape logs path acts as the default
            # data source
            if data is not None:
                self._dataframes_from_data(data)
        except Exception as e:
            raise e

    def process_df(self):
        self._populate_uploaded_logs()
        if self.raw_df is not None:
            self._convert_time_column()
            self._extract_date_for_grouping()
            self._populate_filters()
            self._group_activity_over_time()
            self._group_document_usage()
            self._group_user_activity()
            self._generate_alerts_df()

    def update_with_new_data(self, collection_name):
        try:
            data = self.db_handler.read_from_database(collection_name)
            # Only update with new data if it is set to default or if there is no data processed yet
            if data is not None and (collection_name == ONSHAPE_LOGS_PATH or self.raw_df is None):
                # Process the newly uploaded data
                self._dataframes_from_data(data, collection_source=collection_name)
                self.process_df()  # Reprocess the DataFrame
        except Exception as e:
            self.utils.logger.error(f"Error updating with new data: {str(e)}")

    def get_unread_alerts_count(self):
        return self.alerts_df[self.alerts_df['Status'] == 'unread'].shape[0]

    def _dataframes_from_data(self, data, collection_source=ONSHAPE_LOGS_PATH):
        self.selected_log_path = collection_source
        first_key = next(iter(data))
        self.df = self.raw_df = pd.DataFrame(data[first_key]['data'])

    def _convert_time_column(self):
        self.df['Time'] = pd.to_datetime(self.raw_df['Time'])

    def _extract_date_for_grouping(self):
        self.df['Date'] = self.raw_df['Time'].dt.date

    def _populate_uploaded_logs(self):
        data = self.db_handler.read_from_database(UPLOADED_LOGS_PATH)
        logs = []
        if data:
            for key in data:
                logs.append(data[key]['fileName'])
            if self.raw_df is None:  # if the default path is not populated with data, populate it with the uploaded
                # logs
                self._dataframes_from_data(data, collection_source=UPLOADED_LOGS_PATH)
        self.filters_data['uploaded-logs'] = logs

    def _populate_filters(self):
        self.filters_data['documents'] = [doc for doc in self.raw_df['Document'].unique()]
        self.filters_data['users'] = [user for user in self.raw_df['User'].unique()]
        self.filters_data['descriptions'] = [desc for desc in self.raw_df['Description'].unique()]

    def _group_activity_over_time(self):
        self.activity_over_time = self.raw_df.groupby('Date').size().reset_index(name='ActivityCount')

    def _group_document_usage(self):
        self.document_usage = self.raw_df['Document'].value_counts().reset_index(name='UsageCount')
        self.document_usage.columns = ['Document', 'UsageCount']

    def _group_user_activity(self):
        self.user_activity = self.raw_df['User'].value_counts().reset_index(name='ActivityCount')
        self.user_activity.columns = ['User', 'ActivityCount']

    def _undo_redo_activity_detection(self):
        # Filter redo and undo actions
        redo_undo_df = self.raw_df[self.raw_df['Description'].str.contains('Undo|Redo', case=False)]

        # Set a time window (e.g., 1 hour) for detecting high frequency of actions
        time_window = '1h'
        redo_undo_df['TimeWindow'] = redo_undo_df['Time'].dt.floor(time_window)
        grouped = redo_undo_df.groupby(['User', 'Document', 'TimeWindow']).size().reset_index(name='Count')

        # Filter the groups that exceed the threshold
        alerts = grouped[grouped['Count'] > 15]

        # Prepare the alerts DataFrame
        if not alerts.empty:
            alerts['Time'] = alerts['TimeWindow'].dt.strftime('%H:%M:%S %d-%m-%Y')
            alerts['Description'] = 'Many redos/undos detected within a short time period'
            alerts['Status'] = 'unread'
            self.alerts_df = alerts[['Time', 'User', 'Description', 'Document', 'Status']]
        else:
            self.alerts_df = pd.DataFrame(columns=['Time', 'User', 'Description', 'Document', 'Status'])

    def _generate_alerts_df(self):
        self._undo_redo_activity_detection()

    # def append_demo_alerts(self):
    #     if self.df is not None:
    #         # Create demo logs for bugs
    #         demo_bug_logs = pd.DataFrame([
    #             {'Time': pd.Timestamp('2024-07-01 10:00:00'), 'User': 'user1',
    #              'Description': 'Detected a bug in feature X', 'Document': 'doc1'},
    #             {'Time': pd.Timestamp('2024-07-01 11:00:00'), 'User': 'user2', 'Description': 'Bug found in module Y',
    #              'Document': 'doc2'},
    #             {'Time': pd.Timestamp('2024-07-01 12:00:00'), 'User': 'user3',
    #              'Description': 'Critical bug in processing unit', 'Document': 'doc3'},
    #             {'Time': pd.Timestamp('2024-07-01 13:00:00'), 'User': 'user4', 'Description': 'Minor bug in UI',
    #              'Document': 'doc4'},
    #             {'Time': pd.Timestamp('2024-07-01 14:00:00'), 'User': 'user5',
    #              'Description': 'Bug affecting performance', 'Document': 'doc5'}
    #         ])
    #
    #         # Append demo bug logs to the existing DataFrame
    #         self.df = pd.concat([self.df, demo_bug_logs], ignore_index=True)
    #
    #         # Create a sample alerts DataFrame
    #         self.alerts_df = self.df[(self.df['Description'].str.contains("bug", case=False)) |
    #                                  (self.df['Description'].str.contains("undo", case=False))]
    #
    #         self.alerts_df = self.alerts_df[['Time', 'User', 'Description', 'Document']].sort_values(by='Time',
    #                                                                                                  ascending=False).head(
    #             5)
    #         self.alerts_df['Time'] = self.alerts_df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    #
    #         # Mark the first two as read and the rest as unread
    #         self.alerts_df['Status'] = ['read', 'read'] + ['unread'] * (len(self.alerts_df) - 2)
