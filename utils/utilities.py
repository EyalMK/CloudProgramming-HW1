# Utilities
import logging
from config.constants import PROJECT_NAME, RuntimeEnvironments, runtime_environment
from logger.database_logger import DatabaseLogger
from config.constants import ACTION_MAP


class Utilities:
    def __init__(self, db_handler):
        """
        Initialize the Utilities class with a database handler.
    
        This constructor sets up a logger for the Utilities class, which logs to both the console and a database.
        It also initializes the database handler and calls the setup_logger method to configure the logger.
    
        Parameters:
        db_handler (DatabaseHandler): An instance of a database handler to be used for logging.
    
        Returns:
        None
        """
        self.logger = None
        self.db = db_handler
        self.setup_logger()

    def setup_logger(self):
        """
        Set up the logger for the Utilities class.

        This method configures the logger to log to both the console and a database.
        It sets the logging level based on the runtime environment.

        Parameters:
        self (Utilities): The instance of the Utilities class.

        Returns:
        None
        """
        logging_level = logging.INFO
        if runtime_environment == RuntimeEnvironments.DEV.value:
            logging_level = logging.DEBUG

        self.logger = logging.getLogger(PROJECT_NAME)
        self.logger.setLevel(logging_level)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # DB Log Handler
        firebase_handler = DatabaseLogger(db_handler=self.db)
        firebase_handler.setFormatter(console_formatter)
        self.logger.addHandler(firebase_handler)

        # Console Log Handler
        console_logger = logging.StreamHandler()
        console_logger.setFormatter(console_formatter)
        self.logger.addHandler(console_logger)

    @staticmethod
    def categorize_action(description):
        """
        Categorizes an action based on the given description.

        Args:
            description (str): The description of the action to be categorized.

        Returns:
            str: The category of the action. Possible values are 'Undo', 'Redo',
                 'Insert', 'Export', 'Edit', 'Commit', 'Add', 'Close', 'Move',
                 'Open', or 'Other' if no keywords are matched.
        """
        # Convert description to lowercase once
        description = description.lower()

        # Find the category based on the keywords
        for keyword, category in ACTION_MAP.items():
            if keyword in description:
                return category

        return 'Other'
