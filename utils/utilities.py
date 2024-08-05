### Utilities
import logging
from config.constants import PROJECT_NAME, RuntimeEnvironments, runtime_environment
from logger.database_logger import DatabaseLogger


class Utilities:
    def __init__(self, db_handler):
        self.logger = None
        self.db = db_handler
        self.setup_logger()

    def setup_logger(self):
        logging_level = logging.INFO
        if runtime_environment == RuntimeEnvironments.dev.value:
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

    def categorize_action(self, description):
        if 'undo' in description.lower():
            return 'Undo'
        elif 'redo' in description.lower():
            return 'Redo'
        elif 'insert' in description.lower():
            return 'Insert'
        elif 'export' in description.lower():
            return 'Export'
        elif 'edit' in description.lower():
            return 'Edit'
        elif 'commit' in description.lower():
            return 'Commit'
        elif 'add' in description.lower():
            return 'Add'
        elif 'close' in description.lower():
            return 'Close'
        elif 'move' in description.lower():
            return 'Move'
        elif 'open' in description.lower():
            return 'Open'
        else:
            return 'Other'
