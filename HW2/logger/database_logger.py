from datetime import datetime
import logging

# Firebase Logger Handler
class DatabaseLogger(logging.Handler):
  def __init__(self, db_handler: 'DatabaseHandler'):
    super().__init__()
    self.db_handler = db_handler

  def emit(self, record: logging.LogRecord):
      log_entry = self.format(record)
      log_data = {
                'message': log_entry,
                'level': record.levelname,
                'created': datetime.now().isoformat()
            }
      self.db_handler.db.post('/system-logs', log_data)