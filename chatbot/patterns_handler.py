import re

from config.constants import DatabaseCollections


class PatternsHandler:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self._patterns = []
        self._load_shapeflow_patterns()

    def _load_shapeflow_patterns(self):
        patterns = self.db_handler.read_from_database(DatabaseCollections.BOT_PROMPTS.value)
        if patterns:
            for category, patterns in patterns.items():
                for pattern_data in patterns:
                    pattern = pattern_data['pattern']
                    responses = pattern_data['responses']
                    self._patterns.append((pattern, responses))

    def get_patterns(self):
        return self._patterns
