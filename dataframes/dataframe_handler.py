# DataFrames Handler
import os
import pandas as pd

from datetime import datetime
from config.constants import DatabaseCollections, DEFAULT_MAX_DATE, DEFAULT_MIN_DATE

# Suppress the SettingWithCopyWarning from pandas.
pd.options.mode.chained_assignment = None


class DataFrameHandler:
    """
    A class to handle various operations on data frames including filtering, processing, and
    analyzing data from logs. This handler reads data from a database, processes it into pandas
    DataFrames, and performs various analyses.

    Attributes:
        db_handler (DatabaseHandler): An instance for interacting with the database.
        utils (Utilities): An instance providing utility functions such as logging.
        loaded_df (pd.DataFrame): The processed data frame.
        max_date (datetime): The maximum date for filtering data.
        min_date (datetime): The minimum date for filtering data.
        filters_data (dict): A dictionary holding filter data for documents, users, descriptions,
            uploaded logs, and graphs.
        activity_over_time (list): A list holding the activity data over time.
        document_usage (list): A list holding the document usage data.
        user_activity (list): A list holding the user activity data.
        log_cache (dict): A dictionary holding the log cache data.
        selected_log_name (str): The path to the selected log data in the database.
        alerts_df (pd.DataFrame): A data frame holding alerts data.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DataFrameHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_handler, utils):
        """
        Initialize the DataFrameHandler with the necessary database handler and utilities.

        Parameters:
            db_handler (DatabaseHandler): An instance of DatabaseHandler for database operations.
            utils (Utilities): An instance of Utilities for various utility functions.
        """
        if not hasattr(self, 'initialized'):
            self.loaded_df = None
            self.missing_default_log = False
            self.max_date = datetime.strptime(DEFAULT_MAX_DATE, '%d-%m-%Y')
            self.min_date = datetime.strptime(DEFAULT_MIN_DATE, '%d-%m-%Y')
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
            self.log_cache = {}
            self.selected_log_name = "None"
            self.alerts_df = pd.DataFrame()
            self.db_handler = db_handler
            self.initialize_df()
            self.initialized = True

    def initialize_df(self):
        """
        Initialize the data frame by reading the default data source from the database.
        """
        try:
            self.handle_switch_log_source(DatabaseCollections.ONSHAPE_LOGS.value, file_name='default.json')
        except Exception as e:
            raise e

    def process_df(self):
        """
        Process the raw data frame by performing various operations such as time conversion,
        filtering, grouping, and generating alerts.
        """
        self._populate_uploaded_logs()
        if self.loaded_df is not None:
            self._convert_time_column(dataframe=self.loaded_df)
            self._extract_date_for_grouping()
            self._populate_filters()
            self._group_activity_over_time()
            self._group_document_usage()
            self._group_user_activity()
            self._generate_alerts_df()
            self.set_max_min_dates()

    def update_with_new_data(self, collection_name, file_name):
        """
        Update the data frame with new data from the specified collection and file.

        This method processes and updates the data frame with new data if:
        - The collection name is set to the default collection.
        - The `loaded_df` is `None`, indicating no data has been processed yet.

        Parameters:
            collection_name (str): The name of the database collection from which to fetch new data.
            file_name (str): The name of the file containing the new data.

        Raises:
            Exception: If an error occurs while updating with new data, an error is logged.
        """
        try:
            # Only update with new data if it is set to default or if there is no data processed yet
            if collection_name == DatabaseCollections.ONSHAPE_LOGS.value or self.loaded_df is None:
                # Process the newly uploaded data
                self.handle_switch_log_source(collection_name, file_name)
            self._populate_uploaded_logs()
        except Exception as e:
            self.utils.logger.error(f"Error updating with new data: {str(e)}")

    def handle_switch_log_source(self, collection_name, file_name):
        """
        Handle the switch of the log source and process the new data from cache or database.

        Parameters:
            collection_name (str): The collection name containing the data belonging to file_name.
            file_name (str): The name of the file containing the new data.
        """
        # Process the newly uploaded data
        # Don't cache default data source, since it can be overridden later
        # (the overriding file is also called default.json,
        # a solution would be to add key field to log_cache where key is the key from Firebase collections).
        if file_name in self.log_cache and file_name != "default.json":
            data = self.log_cache[file_name]
            self._dataframes_from_data(data, file_name)
            self.utils.logger.info(f"Loaded {file_name} from cache.")
        else:
            # Read data from the database if not available in cache
            data = self.db_handler.read_from_database(collection_name)
            if data is not None:
                self._dataframes_from_data(data, file_name)
                self.log_cache[file_name] = data  # Cache the data
                self.utils.logger.info(f"Loaded {file_name} from database and cached it.")
            else:
                # Handle case when data is None
                if collection_name == DatabaseCollections.UPLOADED_LOGS.value:
                    self.utils.logger.error(f"No data found for {file_name} in {collection_name}.")
                else:
                    self.missing_default_log = True
                    self.utils.logger.warn(f"No default source log data found for graph initialization.")
                data = {}
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
        if self.loaded_df is not None:
            dataframe_copy = self.loaded_df.copy()
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

    def set_max_min_dates(self):
        """
        Set the maximum and minimum dates from the data frame.
        """
        dataframe = self.loaded_df.copy()
        if dataframe is not None and not dataframe.empty:
            # Calculate time spent on each project (Tab) regardless of the user
            dataframe['Time Diff'] = dataframe.groupby('Tab')['Time'].diff().dt.total_seconds()

            # Determine the latest date and set the default range to the last 7 days
            self.max_date = dataframe['Time'].max().strftime('%Y-%m-%dT%H:%M')
            self.min_date = dataframe['Time'].min().strftime('%Y-%m-%dT%H:%M')
            return

        # If dataframe is None or empty, use default values
        self.max_date = datetime.strptime(DEFAULT_MAX_DATE, '%d-%m-%Y').strftime('%Y-%m-%dT%H:%M')
        self.min_date = datetime.strptime(DEFAULT_MIN_DATE, '%d-%m-%Y').strftime('%Y-%m-%dT%H:%M')

    def filter_dataframe_for_graphs(self, dataframe, selected_document, selected_user, start_time, end_time):
        """
        Filter the data frame for graph data based on selected document, log, user, and time range.

        Parameters:
            dataframe (pd.DataFrame): The data frame to filter.
            selected_document (str or list): The selected document(s) to filter.
            selected_user (str or list): The selected user(s) to filter.
            start_time (datetime.pyi): The start time for filtering.
            end_time (datetime.pyi): The end time for filtering.

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
            self._convert_time_column(dataframe=filtered_df)
            start_date = pd.to_datetime(start_time)
            end_date = pd.to_datetime(end_time)
            filtered_df = filtered_df[(filtered_df['Time'] >= start_date) & (filtered_df['Time'] <= end_date)]
        # Group by date and count activities
        return filtered_df

    @staticmethod
    def setup_project_time_distribution_graph_dataframe(dataframe):
        """
        Set up the data frame for project time distribution graph.

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
        Set up the data frame for advanced and basic actions graph.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process.

        Returns:
            pd.DataFrame or None: The processed data frame with action counts.
        """
        if 'User' not in dataframe.columns or 'Action Type' not in dataframe.columns:
            return None
        return dataframe.groupby(['User', 'Action Type']).size().reset_index(name='Action Count')

    @staticmethod
    def setup_action_sequence_scatter_graph_dataframe(dataframe, start_date, end_date):
        """
        Set up the data frame for the action sequence scatter graph by filtering
        based on the provided date range.

        Parameters:
            dataframe (pd.DataFrame): The data frame to process. It must contain 'Time' and 'User' columns.
            start_date (datetime.pyi): The start date for filtering.
            end_date (datetime.pyi): The end date for filtering.

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
        Set up the data frame for the work patterns over time graph.

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

    @staticmethod
    def prepare_data_for_collapsible_list(dataframe, list_type=''):
        """
        Prepare data for a collapsible list based on the specified type.

        This method processes the provided data frame and returns a summary data frame that can be used
        to generate a collapsible list in the user interface. The data is grouped based on the type of list
        requested.

        Parameters:
            dataframe (pd.DataFrame): The input data frame to process.
            list_type (str): The type of collapsible list to prepare.
                             Possible values are:
                             - 'repeated_actions': Prepares a list of actions repeated by users.
                             - Default: Groups by user, action, and action type.

        Returns:
            pd.DataFrame: A data frame grouped and aggregated based on the specified list type.
                          - For 'repeated_actions': Groups by Action, User, and Description with counts.
                          - For other types: Groups by User, Action, and Action Type with counts.
        """
        if list_type == 'repeated_actions':
            df = dataframe.sort_values(by=['User', 'Time'])
            return df.groupby(['Action', 'User', 'Description']).size().reset_index(name='Count')

        # Group by User, Action, and Action Type to get the count
        return dataframe.groupby(['User', 'Action', 'Action Type']).size().reset_index(name='Action Count')

    def extract_working_hours_data(self):
        """
        Extract and process working hours data from the DataFrame.

        Returns:
            pd.DataFrame or None: A DataFrame with the distribution of work hours by user and hour,
                                  or None if the main DataFrame is not initialized.
        """
        if self.loaded_df is None:
            return None

        processed_df = self.loaded_df
        if 'Time' in processed_df.columns:
            self._convert_time_column(dataframe=processed_df)
            processed_df = processed_df.dropna(subset=['Time'])

            # Extract the hour of the day
            processed_df['Hour'] = processed_df['Time'].dt.hour

            # Group by User and Hour to find the distribution of work hours
            return processed_df.groupby(['User', 'Hour']).size().reset_index(name='ActivityCount')

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
                    self.selected_log_name = file_name
                    data_key = key
                    break
        if data_key is None:
            if hasattr(data, '__iter__') and len(data) > 0:
                self.selected_log_name = 'Default Log'
                data_key = next(iter(data))  # First key
            else:
                self.loaded_df = None
                return
        self.loaded_df = pd.DataFrame(data[data_key]['data'])

    @staticmethod
    def _convert_time_column(dataframe):
        """
        Ensure the 'Time' column in the provided DataFrame is properly parsed to datetime.

        Parameters:
            dataframe (pd.DataFrame): The DataFrame to process.
        """
        # Ensure 'Time' column is properly parsed
        if 'Time' in dataframe.columns:
            dataframe['Time'] = pd.to_datetime(dataframe['Time'], errors='coerce')

    def _extract_date_for_grouping(self):
        """
        Extract the 'Date' from the 'Time' column and add it to the DataFrame.

        This method ensures that a 'Date' column is created from the 'Time' column for grouping purposes.
        """
        # Ensure 'Date' column is correctly extracted from 'Time'
        if 'Time' in self.loaded_df.columns:
            self.loaded_df['Date'] = self.loaded_df['Time'].dt.date

    def _populate_uploaded_logs(self):
        """
        Populate the uploaded logs filter with file names from the database.

        This method reads log data from the database and updates the 'uploaded-logs' filter
        with the file names of the uploaded logs.
        """

        data_to_process = self.db_handler.read_from_database(DatabaseCollections.UPLOADED_LOGS.value)
        logs = ['Default Log'] if not self.missing_default_log else []
        if data_to_process:
            for key in data_to_process:
                logs.append(data_to_process[key]['fileName'])
        self.filters_data['uploaded-logs'] = logs

    def _populate_filters(self):
        """
        Populates the `filters_data` dictionary with unique values from the columns of `self.loaded_df`.
        The dictionary includes lists of unique documents, users, and descriptions found in the DataFrame.
        """
        if 'Document' in self.loaded_df.columns:
            self.filters_data['documents'] = [doc for doc in self.loaded_df['Document'].unique()]
        if 'User' in self.loaded_df.columns:
            self.filters_data['users'] = [user for user in self.loaded_df['User'].unique()]
        if 'Description' in self.loaded_df.columns:
            self.filters_data['descriptions'] = [desc for desc in self.loaded_df['Description'].unique()]

        graph_options = self.utils.get_supported_graphs()
        self.filters_data['graphs'] = [option['value'] for option in graph_options]

    def _group_activity_over_time(self):
        """
        Groups the DataFrame by 'Date' and calculates the count of activities for each date.
        Updates the `activity_over_time` attribute with the resulting DataFrame.
        """
        if 'Date' in self.loaded_df.columns:
            self.activity_over_time = self.loaded_df.groupby('Date').size().reset_index(name='ActivityCount')

    def _group_document_usage(self):
        """
        Groups the DataFrame by 'Document' and counts the occurrences of each document.
        Updates the `document_usage` attribute with the resulting DataFrame.
        """
        if 'Document' in self.loaded_df.columns:
            self.document_usage = self.loaded_df['Document'].value_counts().reset_index(name='UsageCount')
            self.document_usage.columns = ['Document', 'UsageCount']

    def _group_user_activity(self):
        """
        Groups the DataFrame by 'User' and counts the occurrences of each user.
        Updates the `user_activity` attribute with the resulting DataFrame.
        """
        if 'User' in self.loaded_df.columns:
            self.user_activity = self.loaded_df['User'].value_counts().reset_index(name='ActivityCount')
            self.user_activity.columns = ['User', 'ActivityCount']

    @staticmethod
    def _format_time_window(time_window):
        """
        Format the time window as "X minutes" or "Y hours".

        Parameters:
            time_window (str or timedelta): The time window to format.

        Returns:
            str: The formatted time window.
        """
        if isinstance(time_window, str):
            time_window = pd.Timedelta(time_window)
        total_seconds = int(time_window.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        minute_prefix = 's' if minutes > 1 else ''
        hour_prefix = 's' if hours > 1 else ''
        formatted_hour_string = f"{hours} hour{hour_prefix}"
        formatted_minutes_string = f"{minutes} minute{minute_prefix}"

        if hours > 0:
            return formatted_hour_string if minutes == 0 else f"{formatted_hour_string} and {formatted_minutes_string}"
        return formatted_minutes_string

    @staticmethod
    def _convert_time_window_to_minutes(time_window):
        """
        Convert the time window string to minutes if it's in fractional hours.

        Parameters:
            time_window (str): The time window to convert.

        Returns:
            str: The converted time window in minutes.
        """
        if isinstance(time_window, str) and 'h' in time_window:
            hours_fraction = float(time_window.replace('h', ''))
            minutes = int(hours_fraction * 60)
            return f"{minutes}min"
        return time_window

    def _undo_redo_activity_detection(self):
        """
        Detects and generates alerts for high frequency of 'Undo' and 'Redo' actions within a time window.
        Updates the `alerts_df` attribute with detected alerts.
        """
        # Filter redo and undo actions
        redo_undo_df = self.loaded_df[self.loaded_df['Description'].str.contains('Undo|Redo', case=False)].copy()

        # Set a time window for detecting high frequency of actions
        configured_time_window = os.environ.get("ALERT_TIMEWINDOW", "60min")
        formatted_time_window = self._format_time_window(configured_time_window)
        redo_undo_df['TimeWindow'] = redo_undo_df['Time'].dt.floor(self._convert_time_window_to_minutes(configured_time_window))
        # redo_undo_df['TimeWindow'] = redo_undo_df['Time'].dt.floor(configured_time_window)
        grouped = redo_undo_df.groupby(['User', 'Document', 'TimeWindow']).size().reset_index(name='Count')

        # Filter the groups that exceed the threshold
        configured_threshold = int(os.environ.get("UNDO_REDO_THRESHOLD", 15))
        alerts = grouped[grouped['Count'] > configured_threshold].copy()

        # Prepare the alerts DataFrame
        if not alerts.empty:
            alerts['Time'] = alerts['TimeWindow'].dt.strftime('%H:%M:%S %d-%m-%Y')
            alerts['Description'] = (
                f'More than {configured_threshold} redos/undos detected '
                f'within {formatted_time_window}'
            )
            alerts['Indication'] = 'difficulty dealing with a certain challenge'
            alerts['Status'] = 'unread'
            self.alerts_df = alerts[['Time', 'User', 'Description', 'Document', 'Indication', 'Status']]
        else:
            self.alerts_df = pd.DataFrame(columns=['Time', 'User', 'Description', 'Document', 'Indication', 'Status'])

    def _context_switching_detection(self):
        """
        Detects and generates alerts for frequent context switching within a time window.
        Updates the `alerts_df` attribute with detected alerts.
        """
        # Set a time window and threshold for detecting frequent context switching
        time_window = pd.Timedelta(minutes=int(os.environ.get("CONTEXT_SWITCH_TIMEWINDOW", 30)))
        formatted_time_window = self._format_time_window(time_window)
        threshold = int(os.environ.get("CONTEXT_SWITCH_THRESHOLD", 5))

        # Initialize an empty list to store the context switching alerts
        context_switch_alerts = []

        # Iterate over each user
        for user in self.loaded_df['User'].unique():
            user_data = self.loaded_df[self.loaded_df['User'] == user].sort_values(by='Time')

            # Track the last document and tab to detect context switches
            last_document = None
            last_tab = None
            switch_count = 0
            switch_start_time = None

            for i, row in user_data.iterrows():
                current_document = row['Document']
                current_tab = row['Tab']
                current_time = row['Time']

                # Detect context switch
                if current_document != last_document or current_tab != last_tab:
                    if switch_start_time is None:
                        switch_start_time = current_time

                    switch_count += 1
                    last_document = current_document
                    last_tab = current_tab

                    # Check if the count exceeds the threshold within the time window
                    if switch_count >= threshold and (current_time - switch_start_time <= time_window):
                        context_switch_alerts.append({
                            'User': user,
                            'Start Time': switch_start_time,
                            'End Time': current_time,
                            'Switch Count': switch_count,
                            'Description': f'{threshold} context switches detected in {formatted_time_window}',
                            'Indication': 'multitasking or distraction',
                            'Status': 'unread'
                        })

                        # Reset the count and start time to prevent multiple alerts within the same window
                        switch_count = 0
                        switch_start_time = None
                        break  # Move to the next user or continue checking new data

                # Reset the tracking if the current time exceeds the time window
                if switch_start_time is not None and current_time - switch_start_time > time_window:
                    switch_count = 0
                    switch_start_time = None

        # Convert the alerts to a DataFrame
        if context_switch_alerts:
            context_switch_alerts_df = pd.DataFrame(context_switch_alerts)
            context_switch_alerts_df['Time'] = context_switch_alerts_df['Start Time'].dt.strftime('%H:%M:%S %d-%m-%Y')
            context_switch_alerts_df['Document'] = "N/A"
            context_switch_alerts_df = context_switch_alerts_df[['Time', 'User', 'Description', 'Document', 'Indication', 'Status']]
            self.alerts_df = pd.concat([self.alerts_df, context_switch_alerts_df], ignore_index=True)

    def _cancellation_detection(self):
        """
        Detects and generates alerts for high frequency of cancellations within a time window.
        Updates the `alerts_df` attribute with detected alerts.
        """
        # Set a time window and threshold for detecting high frequency of cancellations
        configured_time_window = os.environ.get("CANCELLATION_TIMEWINDOW", "30min")
        formatted_time_window = self._format_time_window(configured_time_window)
        threshold = int(os.environ.get("CANCELLATION_THRESHOLD", 3))

        # Filter for cancellation actions
        cancellation_df = self.loaded_df[self.loaded_df['Description'].str.contains('Cancel', case=False)].copy()

        # Set a time window for detecting high frequency of actions
        cancellation_df['TimeWindow'] = cancellation_df['Time'].dt.floor(self._convert_time_window_to_minutes(configured_time_window))
        # cancellation_df['TimeWindow'] = cancellation_df['Time'].dt.floor(configured_time_window)
        grouped = cancellation_df.groupby(['User', 'Document', 'TimeWindow']).size().reset_index(name='Count')

        # Filter the groups that exceed the threshold
        alerts = grouped[grouped['Count'] >= threshold].copy()

        # Prepare the alerts DataFrame
        if not alerts.empty:
            alerts['Time'] = alerts['TimeWindow'].dt.strftime('%H:%M:%S %d-%m-%Y')
            alerts['Description'] = (
                f'At least {threshold} cancellations detected within {formatted_time_window}'
            )
            alerts['Indication'] = 'indecisiveness or encountering problems while working'
            alerts['Status'] = 'unread'
            self.alerts_df = pd.concat([self.alerts_df, alerts[['Time', 'User', 'Description', 'Document', 'Indication', 'Status']]], ignore_index=True)

    def _generate_alerts_df(self):
        """
        Generates alerts DataFrame by detecting various alerts.
        Updates the `alerts_df` attribute with the generated alerts.
        """
        self._undo_redo_activity_detection()
        self._context_switching_detection()
        self._cancellation_detection()
