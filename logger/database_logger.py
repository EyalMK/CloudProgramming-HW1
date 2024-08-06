from datetime import datetime
import logging

from database.db_handler import DatabaseHandler


class DatabaseLogger(logging.Handler):
    """
    A custom logging handler that sends log messages to a database.

    This handler formats log messages and posts them to a specified database using
    the provided database handler. The log entries include the message, log level,
    and the timestamp when the log entry was created.

    Attributes:
        db_handler (DatabaseHandler): An instance of the DatabaseHandler used to
            interact with the database.
    """

    def __init__(self, db_handler: 'DatabaseHandler'):
        """
        Initialize the DatabaseLogger with a database handler.

        Parameters:
            db_handler (DatabaseHandler): An instance of the DatabaseHandler to
                be used for posting log entries.
        """
        super().__init__()
        self.db_handler = db_handler

    def emit(self, record: logging.LogRecord):
        """
        Emit a log message to the database.

        Formats the log record and posts it to the database. The log entry includes
        the formatted message, log level, and the timestamp of when the log was created.

        Parameters:
            record (logging.LogRecord): The log record containing information about
                the log message, level, and other details.
        """
        log_entry = self.format(record)
        log_data = {
            'message': log_entry,
            'level': record.levelname,
            'created': datetime.now().isoformat()
        }
        self.db_handler.db.post('/system-logs', log_data)
