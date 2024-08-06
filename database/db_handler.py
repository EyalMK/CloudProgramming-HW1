# Database Handler
import logging
from typing import Any

from firebase import firebase

from config.constants import DatabaseCollections


class DatabaseHandler:
    """
    A class to handle database operations with Firebase.

    Attributes:
        db (firebase.FirebaseApplication): The Firebase application instance.
        logger (logging.Logger): Logger instance for logging information and errors.
    """
    def __init__(self):
        """Initialize the DatabaseHandler with no database connection and logger."""
        self.db = None
        self.logger = None

    def connect_to_firebase(self, db_url: str):
        """
        Connect to Firebase using the provided database URL.

        Args:
            db_url (str): The URL of the Firebase database.

        Raises:
            Exception: If connection to Firebase fails.
        """
        try:
            self.db = firebase.FirebaseApplication(db_url, None)
            self.logger.info("Connected to Firebase successfully.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Firebase: {e}")
            raise Exception(f"Failed to connect to Firebase: {e}")

    def set_logger(self, logger: logging.Logger):
        """
        Set the logger for the DatabaseHandler.

        Args:
            logger (logging.Logger): Logger instance to be used for logging.
        """
        self.logger = logger

    def read_from_database(self, collection_name: str) -> Any | None:
        """
        Read data from a specified collection in the database.

        Args:
            collection_name (str): The name of the collection to read from.

        Returns:
            Any | None: The data read from the database, or None if no data is found.

        Raises:
            Exception: If reading from the database fails.
        """
        try:
            data = self.db.get(collection_name, None)
            if data is None:
                self.logger.warning(f"No data found in the collection {collection_name}.")
                return data
            return data
        except Exception as e:
            self.logger.error(f"Error reading from database: {e}")
            raise e

    def write_to_database(self, collection_name: str, data: dict):
        """
        Write data to a specified collection in the database.

        Args:
            collection_name (str): The name of the collection to write to.
            data (dict): The data to write to the database.

        Raises:
            Exception: If writing to the database fails.
        """
        try:
            # Clear the collection if it's the default collection
            # This is to prevent the database from storing duplicate defaults
            if collection_name == DatabaseCollections.ONSHAPE_LOGS.value:
                self.db.delete(collection_name, None)
                self.logger.info(f"{collection_name} cleared successfully. Setting new default log...")

            self.db.post(collection_name, data)
            self.logger.info(f"Data written to {collection_name} successfully.")
        except Exception as e:
            self.logger.error(f"Error writing to database: {e}")
            raise e
