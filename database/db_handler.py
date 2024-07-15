# Database Handler
import logging
from firebase import firebase


class DatabaseHandler():
    def __init__(self):
        self.db = None
        self.logger = None

    def connect_to_firebase(self, db_url: str):
        try:
            self.db = firebase.FirebaseApplication(db_url, None)
            self.logger.info("Connected to Firebase successfully.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Firebase: {e}")
            raise Exception(f"Failed to connect to Firebase: {e}")

    def set_logger(self, logger: logging.Logger):
        self.logger = logger

    def read_from_database(self, collection_name: str) -> dict:
        try:
            data = self.db.get(collection_name, None)
            if data is None:
                self.logger.warning("No data found in the database.")
            return data
        except Exception as e:
            self.logger.error(f"Error reading from database: {e}")
            raise e

    def write_to_database(self, collection_name: str, data: dict):
        try:
            self.db.post(collection_name, data)
            self.logger.info(f"Data written to {collection_name} successfully.")
        except Exception as e:
            self.logger.error(f"Error writing to database: {e}")
            raise e