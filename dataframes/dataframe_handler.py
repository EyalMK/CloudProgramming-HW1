# DataFrames Handler
import os
from datetime import timedelta, datetime
import pandas as pd
from config.constants import DatabaseCollections, DEFAULT_MAX_DATE, DEFAULT_MIN_DATE


class DataFrameHandler:
    """
    A class to handle various operations on data frames including filtering, processing, and
    analyzing data from logs. This handler reads data from a database, processes it into pandas
    DataFrames, and performs various analyses.

    Attributes:
        db_handler (DatabaseHandler): An instance for interacting with the database.
        utils (Utilities): An instance providing utility functions such as logging.
        raw_df (pd.DataFrame): The raw data frame from the logs.
        df (pd.DataFrame): The processed data frame.
        filters_data (dict): A dictionary holding filter data for documents, users, descriptions,
            uploaded logs, and graphs.
        activity_over_time (list): A list holding the activity data over time.
        document_usage (list): A list holding the document usage data.
        user_activity (list): A list holding the user activity data.
        selected_log_path (str): The path to the selected log data in the database.
        alerts_df (pd.DataFrame): A data frame holding alerts data.
    """

    def __init__(self, db_handler, utils):
        """
        Initialize the DataFrameHandler with the necessary database handler and utilities.

        Parameters:
            db_handler (DatabaseHandler): An instance of DatabaseHandler for database operations.
            utils (Utilities): An instance of Utilities for various utility functions.
        """
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
        self.selected_log_path = DatabaseCollections.ONSHAPE_LOGS.value  # Default data source
        self.alerts_df = pd.DataFrame()
        self.db_handler = db_handler
        self.initialize_df()

    def initialize_df(self):
        """
        Initialize the data frame by reading the default data source from the database.
        """
        try:
            data = self.db_handler.read_from_database(
                DatabaseCollections.ONSHAPE_LOGS.value)  # OnShape logs path acts as the default
            # data source
            if data is not None:
                self.handle_switch_log_source(data)
        except Exception as e:
            raise e

    def process_df(self):
        """
        Process the raw data frame by performing various operations such as time conversion,
        filtering, grouping, and generating alerts.
        """
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
        """
        Update the data frame with new data from the specified collection.

        Parameters:
            collection_name (str): The name of the collection to update data from.
        """
        try:
            data = self.db_handler.read_from_database(collection_name)
            self._populate_uploaded_logs(data=data)
            # Only update with new data if it is set to default or if there is no data processed yet
            if data and (collection_name == DatabaseCollections.ONSHAPE_LOGS.value or self.raw_df is None):
                # Process the newly uploaded data
                self.handle_switch_log_source(data)
        except Exception as e:
            self.utils.logger.error(f"Error updating with new data: {str(e)}")

    def handle_switch_log_source(self, data, file_name=None):
        """
        Handle the switch of the log source and process the new data.

        Parameters:
            data (dict): The new data to process.
            file_name (str, optional): The name of the file containing the new data.
        """  # Process the newly uploaded data
        self._dataframes_from_data(data, file_name)
        self.process_df()  # Reprocess the DataFrame

    def get_unread_alerts_count(self):
        """
        Get the count of unread alerts.

        Returns:
            int: The count of unread alerts.
        """
        if self.alerts_df.empty:
            return 0
        return self.alerts_df[self.alerts_df['Status'] == 'unread'].shape[0]

    def get_lightly_refined_graphs_dataframe(self):
        """
        Get a lightly refined data frame for graphs with categorized actions.

        Returns:
            pd.DataFrame: A data frame with 'Description', 'Action', and 'Time' columns.
        """
        if self.df is not None:
            dataframe_copy = self.df.copy()
            dataframe_copy['Action'] = dataframe_copy['Description'].apply(self.utils.categorize_action)
            return dataframe_copy
        # Return an empty DataFrame with expected columns
        return pd.DataFrame(columns=['Description', 'Action', 'Time'])

    @staticmethod
    def process_graphs_layout_dataframe(dataframe):
        """
        Process the layout data frame for graphs by converting the time column and classifying actions.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process.

        Returns:
            pd.DataFrame: The processed data frame with 'Time', 'Action', and 'Action Type' columns.
        """
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

    @staticmethod
    def get_max_min_dates(dataframe):
        """
        Get the maximum and minimum dates from the data frame, and determine the default start date range.

        Parameters:
            dataframe (pd.DataFrame): The data frame to analyze.

        Returns:
            tuple: The maximum date, minimum date, and the default start date.
        """
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

    @staticmethod
    def filter_dataframe_for_graphs(dataframe, selected_document, selected_log, selected_user, start_time, end_time):
        """
        Filter the data frame for graph data based on selected document, log, user, and time range.

        Parameters:
            dataframe (pd.DataFrame): The data frame to filter.
            selected_document (str or list): The selected document(s) to filter.
            selected_log (str): The selected log to filter.
            selected_user (str or list): The selected user(s) to filter.
            start_time (str): The start time for filtering.
            end_time (str): The end time for filtering.

        Returns:
            pd.DataFrame: The filtered data frame.
        """
        filtered_df = dataframe

        if selected_document:
            if isinstance(selected_document, list):
                filtered_df = filtered_df[filtered_df['Document'].isin(selected_document)]
            else:
                filtered_df = filtered_df[filtered_df['Document'] == selected_document]

        if selected_user:
            if isinstance(selected_user, list):
                filtered_df = filtered_df[filtered_df['User'].isin(selected_user)]
            else:
                filtered_df = filtered_df[filtered_df['User'] == selected_user]

        if start_time and end_time and filtered_df is not None:
            filtered_df['Time'] = pd.to_datetime(filtered_df['Time'], errors='coerce')
            start_date = pd.to_datetime(start_time)
            end_date = pd.to_datetime(end_time)
            filtered_df = filtered_df[(filtered_df['Time'] >= start_date) & (filtered_df['Time'] <= end_date)]

        # Group by date and count activities
        return filtered_df

    @staticmethod
    def setup_project_time_distribution_graph_dataframe(dataframe):
        """
        Setup the data frame for project time distribution graph.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process.

        Returns:
            pd.DataFrame or None: The processed data frame with time spent on each project.
        """
        if 'Time' not in dataframe.columns or 'Tab' not in dataframe.columns:
            return None

        dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')
        df = dataframe.dropna(subset=['Time'])

        df_sorted = df.sort_values(by=['Tab', 'Time'])
        df_sorted['Time Diff'] = df_sorted.groupby('Tab')['Time'].diff().dt.total_seconds()

        filtered_df = df_sorted.dropna(subset=['Time Diff'])
        filtered_df = filtered_df[filtered_df['Time Diff'] > 0]
        filtered_df = filtered_df[filtered_df['Time Diff'] <= 1800]

        if filtered_df.empty:
            return None

        project_time = filtered_df.groupby('Tab')['Time Diff'].sum().reset_index(name='Time Spent (seconds)')
        project_time['Time Spent (hours)'] = (project_time['Time Spent (seconds)'] / 3600).round(2)

        return project_time

    @staticmethod
    def setup_advanced_basic_actions_graph_dataframe(dataframe):
        """
        Setup the data frame for advanced and basic actions graph.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process.

        Returns:
            pd.DataFrame or None: The processed data frame with action counts.
        """
        if 'User' not in dataframe.columns or 'Action Type' not in dataframe.columns:
            return None
        return dataframe.groupby(['User', 'Action Type']).size().reset_index(name='Action Count')

    @staticmethod
    def setup_action_frequency_scatter_graph_dataframe(dataframe, start_date, end_date):
        """
        Setup the data frame for the action frequency scatter graph by filtering
        based on the provided date range.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process. It must contain 'Time' and 'User' columns.
            start_date (str or pd.Timestamp): The start date for filtering.
            end_date (str or pd.Timestamp): The end date for filtering.

        Returns:
            pd.DataFrame or None: The filtered data frame containing actions within the specified date range,
            or None if the required columns are not present in the data frame.
        """
        if 'Time' not in dataframe.columns or 'User' not in dataframe.columns:
            return None

        dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        return dataframe[(dataframe['Time'] >= start_date) & (dataframe['Time'] <= end_date)]

    @staticmethod
    def setup_work_patterns_over_time_graph_dataframe(dataframe):
        """
        Setup the data frame for the work patterns over time graph.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process. It must contain a 'Time' column.

        Returns:
            pd.DataFrame or None: The data frame containing the count of actions grouped by day and hour,
            or None if the 'Time' column is not present.
        """
        if 'Time' not in dataframe.columns:
            return None

        dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')
        df = dataframe.dropna(subset=['Time'])

        work_patterns = df.groupby(
            [df['Time'].dt.day_name().rename('Day'), df['Time'].dt.hour.rename('Hour')]
        ).size().reset_index(name='Action Count')

        work_patterns['Time Interval'] = work_patterns['Hour'].astype(str) + ":00 - " + (
                work_patterns['Hour'] + 1).astype(str) + ":00"
        return work_patterns

    @staticmethod
    def setup_repeated_actions_by_user_graph_dataframe(dataframe):
        """
        Prepares a DataFrame for plotting repeated actions by users.

        This method sorts the input DataFrame by 'User' and 'Time', then groups the data by 'Action', 'User', and
        'Description' to count the occurrences of each combination. It returns a DataFrame with the counts of
        repeated actions.

        Args:
            dataframe (pd.DataFrame): The input DataFrame containing action data.

        Returns:
            pd.DataFrame: A DataFrame with columns ['Action', 'User', 'Description', 'Count'] showing the count
            of repeated actions grouped by user.
        """
        if 'User' not in dataframe.columns or 'Time' not in dataframe.columns:
            return None
        df = dataframe.sort_values(by=['User', 'Time'])
        return df.groupby(['Action', 'User', 'Description']).size().reset_index(name='Count')

    def _dataframes_from_data(self, data, file_name=None):
        """
        Initialize the raw and processed DataFrames from the provided data.

        Parameters:
            data (dict): A dictionary containing the data to be processed.
            file_name (str, optional): The name of the file to locate the specific data. Defaults to None.
        """
        data_key = None
        if file_name:
            for key, value in data.items():
                if value['fileName'] == file_name:
                    data_key = key
                    break
        if data_key is None:
            data_key = next(iter(data))  # First key
        self.df = self.raw_df = pd.DataFrame(data[data_key]['data'])

    @staticmethod
    def prepare_data_for_collapsible_list(dataframe, type = ''):
        """
        Prepare data frame for collapsible list creation with action counts.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process.

        Returns:
            pd.DataFrame or None: The processed data frame with action counts.
        """
        if type == 'repeated_actions':
            df = dataframe.sort_values(by=['User', 'Time'])
            return df.groupby(['Action', 'User', 'Description']).size().reset_index(name='Count')

        # Group by User, Action, and Action Type to get the count
        return dataframe.groupby(['User', 'Action', 'Action Type']).size().reset_index(name='Action Count')

    def _convert_time_column(self, dataframe):
        """
        Ensure the 'Time' column in the provided DataFrame is properly parsed to datetime.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame to process.
        """
        # Ensure 'Time' column is properly parsed
        if 'Time' in self.raw_df.columns:
            dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')

    def extract_working_hours_data(self):
        """
        Extract and process working hours data from the DataFrame.

        Returns:
            pd.DataFrame or None: A DataFrame with the distribution of work hours by user and hour,
                                  or None if the main DataFrame is not initialized.
        """
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
        """
        Extract the 'Date' from the 'Time' column and add it to the DataFrame.

        This method ensures that a 'Date' column is created from the 'Time' column for grouping purposes.
        """
        # Ensure 'Date' column is correctly extracted from 'Time'
        if 'Time' in self.df.columns:
            self.df['Date'] = self.df['Time'].dt.date

    def _populate_uploaded_logs(self, data=None):
        """
        Populate the uploaded logs filter with file names from the database.

        This method reads log data from the database and updates the 'uploaded-logs' filter
        with the file names of the uploaded logs.

        Args:
            data (dict, optional): The data to process. If None, reads data from the database.
        """
        data_to_process = data
        if data_to_process is None:
            data_to_process = self.db_handler.read_from_database(DatabaseCollections.UPLOADED_LOGS.value)
        logs = ['Default Log']
        if data_to_process:
            for key in data_to_process:
                logs.append(data_to_process[key]['fileName'])
        self.filters_data['uploaded-logs'] = logs

    def _populate_filters(self):
        """
        Populates the `filters_data` dictionary with unique values from the columns of `self.raw_df`.
        The dictionary includes lists of unique documents, users, and descriptions found in the DataFrame.
        """
        if 'Document' in self.raw_df.columns:
            self.filters_data['documents'] = [doc for doc in self.raw_df['Document'].unique()]
        if 'User' in self.raw_df.columns:
            self.filters_data['users'] = [user for user in self.raw_df['User'].unique()]
        if 'Description' in self.raw_df.columns:
            self.filters_data['descriptions'] = [desc for desc in self.raw_df['Description'].unique()]

    def _group_activity_over_time(self):
        """
        Groups the DataFrame by 'Date' and calculates the count of activities for each date.
        Updates the `activity_over_time` attribute with the resulting DataFrame.
        """
        if 'Date' in self.df.columns:
            self.activity_over_time = self.df.groupby('Date').size().reset_index(name='ActivityCount')

    def _group_document_usage(self):
        """
        Groups the DataFrame by 'Document' and counts the occurrences of each document.
        Updates the `document_usage` attribute with the resulting DataFrame.
        """
        if 'Document' in self.df.columns:
            self.document_usage = self.df['Document'].value_counts().reset_index(name='UsageCount')
            self.document_usage.columns = ['Document', 'UsageCount']

    def _group_user_activity(self):
        """
        Groups the DataFrame by 'User' and counts the occurrences of each user.
        Updates the `user_activity` attribute with the resulting DataFrame.
        """
        if 'User' in self.df.columns:
            self.user_activity = self.df['User'].value_counts().reset_index(name='ActivityCount')
            self.user_activity.columns = ['User', 'ActivityCount']

    def _undo_redo_activity_detection(self):
        """
        Detects and generates alerts for high frequency of 'Undo' and 'Redo' actions within a time window.
        Updates the `alerts_df` attribute with detected alerts.
        """
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
        """
        Generates alerts DataFrame by detecting high frequency of 'Undo' and 'Redo' actions.
        Updates the `alerts_df` attribute with the generated alerts.
        """
        self._undo_redo_activity_detection()
