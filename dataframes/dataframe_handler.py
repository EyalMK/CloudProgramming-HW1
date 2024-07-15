### DataFrames Handler
from config.constants import ONSHAPE_LOGS_PATH, UPLOADED_LOGS_PATH
import pandas as pd


class DataFrameHandler:
    def __init__(self, db_handler):
        self.raw_df = None
        self.df = None
        self.filters_data = {}
        self.activity_over_time = []
        self.document_usage = []
        self.user_activity = []
        self.alerts_df = None
        self.db_handler = db_handler
        self.initialize_df()
        self.process_df()
        self.append_demo_alerts()

    def initialize_df(self):
        try:
            data = self.db_handler.read_from_database(ONSHAPE_LOGS_PATH)
            if data is not None:
                self.df = self.raw_df = pd.DataFrame(data)
        except Exception as e:
            raise e

    def process_df(self):
        if self.raw_df is not None:
            self._convert_time_column()
            self._extract_date_for_grouping()
            self._populate_filters()
            self._group_activity_over_time()
            self._group_document_usage()
            self._group_user_activity()

    def _convert_time_column(self):
        self.df['Time'] = pd.to_datetime(self.raw_df['Time'])

    def _extract_date_for_grouping(self):
        self.df['Date'] = self.raw_df['Time'].dt.date

    def _populate_uploaded_logs(self):
        data = self.db_handler.read_from_database(UPLOADED_LOGS_PATH)
        logs = []
        if data:
            for key in data:
                logs.append(data[key].fileName)  # Append only file names.
        self.filters_data['uploaded-logs'] = logs

    def _populate_filters(self):
        self.filters_data['documents'] = [doc for doc in self.raw_df['Document'].unique()]
        self.filters_data['users'] = [user for user in self.raw_df['User'].unique()]
        self.filters_data['descriptions'] = [desc for desc in self.raw_df['Description'].unique()]
        self._populate_uploaded_logs()

    def _group_activity_over_time(self):
        self.activity_over_time = self.raw_df.groupby('Date').size().reset_index(name='ActivityCount')

    def _group_document_usage(self):
        self.document_usage = self.raw_df['Document'].value_counts().reset_index(name='UsageCount')
        self.document_usage.columns = ['Document', 'UsageCount']

    def _group_user_activity(self):
        self.user_activity = self.raw_df['User'].value_counts().reset_index(name='ActivityCount')
        self.user_activity.columns = ['User', 'ActivityCount']

    def append_demo_alerts(self):
        if self.df is not None:
            # Create demo logs for bugs
            demo_bug_logs = pd.DataFrame([
                {'Time': pd.Timestamp('2024-07-01 10:00:00'), 'User': 'user1',
                 'Description': 'Detected a bug in feature X', 'Document': 'doc1'},
                {'Time': pd.Timestamp('2024-07-01 11:00:00'), 'User': 'user2', 'Description': 'Bug found in module Y',
                 'Document': 'doc2'},
                {'Time': pd.Timestamp('2024-07-01 12:00:00'), 'User': 'user3',
                 'Description': 'Critical bug in processing unit', 'Document': 'doc3'},
                {'Time': pd.Timestamp('2024-07-01 13:00:00'), 'User': 'user4', 'Description': 'Minor bug in UI',
                 'Document': 'doc4'},
                {'Time': pd.Timestamp('2024-07-01 14:00:00'), 'User': 'user5',
                 'Description': 'Bug affecting performance', 'Document': 'doc5'}
            ])

            # Append demo bug logs to the existing DataFrame
            self.df = pd.concat([self.df, demo_bug_logs], ignore_index=True)

            # Create a sample alerts DataFrame
            self.alerts_df = self.df[(self.df['Description'].str.contains("bug", case=False)) |
                                     (self.df['Description'].str.contains("undo", case=False))]

            self.alerts_df = self.alerts_df[['Time', 'User', 'Description', 'Document']].sort_values(by='Time',
                                                                                                     ascending=False).head(
                5)
            self.alerts_df['Time'] = self.alerts_df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Mark the first two as read and the rest as unread
            self.alerts_df['Status'] = ['read', 'read'] + ['unread'] * (len(self.alerts_df) - 2)
