### DataFrames Handler
import os
from datetime import timedelta, datetime

from config.constants import ONSHAPE_LOGS_PATH, UPLOADED_LOGS_PATH, DEFAULT_MAX_DATE, DEFAULT_MIN_DATE
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
            'uploaded-logs': [],
            'graphs': []
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
            self._convert_time_column(dataframe=self.raw_df)
            self._extract_date_for_grouping()
            self._populate_filters()
            self._group_activity_over_time()
            self._group_document_usage()
            self._group_user_activity()
            self._generate_alerts_df()

    def update_with_new_data(self, collection_name):
        try:
            data = self.db_handler.read_from_database(collection_name)
            self._populate_uploaded_logs(data=data)
            # Only update with new data if it is set to default or if there is no data processed yet
            if data and (collection_name == ONSHAPE_LOGS_PATH or self.raw_df is None):
                # Process the newly uploaded data
                self._dataframes_from_data(data, collection_source=collection_name)
                self.process_df()  # Reprocess the DataFrame
        except Exception as e:
            self.utils.logger.error(f"Error updating with new data: {str(e)}")

    def get_unread_alerts_count(self):
        if self.alerts_df.empty:
            return 0
        return self.alerts_df[self.alerts_df['Status'] == 'unread'].shape[0]

    def get_preprocessed_graphs_dataframe(self):
        if self.df is not None:
            dataframe_copy = self.df.copy()
            dataframe_copy['Action'] = dataframe_copy['Description'].apply(self.utils.categorize_action)
            return dataframe_copy
        # Return an empty DataFrame with expected columns
        return pd.DataFrame(columns=['Description', 'Action', 'Time'])

    def process_graphs_layout_dataframe(self, dataframe):
        if dataframe is None:
            # Return an empty DataFrame with expected columns
            return pd.DataFrame(columns=['Time', 'Action', 'Action Type'])
        # Convert Time column to datetime
        dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')

        # Drop rows with invalid datetime values
        dataframe = dataframe.dropna(subset=['Time'])

        # Create a new column to classify actions as Advanced or Basic
        dataframe['Action Type'] = dataframe['Action'].apply(
            lambda x: 'Advanced' if x in ['Edit', 'Create', 'Delete', 'Add'] else 'Basic')

        return dataframe

    def get_max_min_dates(self, dataframe):
        if dataframe is not None and not dataframe.empty:
            # Calculate time spent on each project (Tab) regardless of the user
            dataframe['Time Diff'] = dataframe.groupby('Tab')['Time'].diff().dt.total_seconds()

            # Determine the latest date and set the default range to the last 7 days
            max_date = dataframe['Time'].max()
            min_date = dataframe['Time'].min()
            start_date = max_date - timedelta(days=7)
        else:
            # If dataframe is None or empty, use default values
            max_date = datetime.strptime(DEFAULT_MAX_DATE, '%d-%m-%Y')
            min_date = datetime.strptime(DEFAULT_MIN_DATE, '%d-%m-%Y')
            start_date = max_date - timedelta(days=7)
        return max_date, min_date, start_date

    def _dataframes_from_data(self, data, collection_source=ONSHAPE_LOGS_PATH):
        self.selected_log_path = collection_source
        first_key = next(iter(data))
        self.df = self.raw_df = pd.DataFrame(data[first_key]['data'])

    def _convert_time_column(self, dataframe):
        # Ensure 'Time' column is properly parsed
        if 'Time' in self.raw_df.columns:
            dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')

    def extract_working_hours_data(self):
        if self.df is None:
            return None

        processed_df = self.df
        if 'Time' in self.raw_df.columns:
            self._convert_time_column(dataframe=processed_df)
            processed_df = processed_df.dropna(subset=['Time'])

            # Extract the hour of the day
            processed_df['Hour'] = processed_df['Time'].dt.hour

            # Group by User and Hour to find the distribution of work hours
            return processed_df.groupby(['User', 'Hour']).size().reset_index(name='ActivityCount')

    def _extract_date_for_grouping(self):
        # Ensure 'Date' column is correctly extracted from 'Time'
        if 'Time' in self.df.columns:
            self.df['Date'] = self.df['Time'].dt.date

    def _populate_uploaded_logs(self, data=None):
        data_to_process = data
        if data_to_process is None:
            data_to_process = self.db_handler.read_from_database(UPLOADED_LOGS_PATH)
        logs = ['Default Log']
        if data_to_process:
            for key in data_to_process:
                logs.append(data_to_process[key]['fileName'])
        self.filters_data['uploaded-logs'] = logs

    def _populate_filters(self):
        if 'Document' in self.raw_df.columns:
            self.filters_data['documents'] = [doc for doc in self.raw_df['Document'].unique()]
        if 'User' in self.raw_df.columns:
            self.filters_data['users'] = [user for user in self.raw_df['User'].unique()]
        if 'Description' in self.raw_df.columns:
            self.filters_data['descriptions'] = [desc for desc in self.raw_df['Description'].unique()]

    def _group_activity_over_time(self):
        if 'Date' in self.df.columns:
            self.activity_over_time = self.df.groupby('Date').size().reset_index(name='ActivityCount')

    def _group_document_usage(self):
        if 'Document' in self.df.columns:
            self.document_usage = self.df['Document'].value_counts().reset_index(name='UsageCount')
            self.document_usage.columns = ['Document', 'UsageCount']

    def _group_user_activity(self):
        if 'User' in self.df.columns:
            self.user_activity = self.df['User'].value_counts().reset_index(name='ActivityCount')
            self.user_activity.columns = ['User', 'ActivityCount']

    def _undo_redo_activity_detection(self):
        # Filter redo and undo actions
        redo_undo_df = self.raw_df[self.raw_df['Description'].str.contains('Undo|Redo', case=False)].copy()

        # Set a time window for detecting high frequency of actions
        redo_undo_df['TimeWindow'] = redo_undo_df['Time'].dt.floor(os.environ["ALERT_TIMEWINDOW"])
        grouped = redo_undo_df.groupby(['User', 'Document', 'TimeWindow']).size().reset_index(name='Count')

        # Filter the groups that exceed the threshold
        alerts = grouped[grouped['Count'] > int(os.environ["UNDO_REDO_THRESHOLD"])].copy()

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
