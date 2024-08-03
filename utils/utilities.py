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
