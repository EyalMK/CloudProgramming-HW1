from config.constants import DatabaseCollections


class PatternsHandler:
    """
    Handles the retrieval and storage of chatbot patterns from the database.

    Attributes:
        db_handler (DatabaseHandler): The database handler used for reading data.
        _patterns (list): A list of tuples where each tuple contains a pattern and its associated responses.
    """
    def __init__(self, db_handler):
        """
        Initializes the PatternsHandler with a database handler and loads the chatbot patterns.

        Parameters:
            db_handler (DatabaseHandler): An instance of the database handler to read patterns from the database.
        """
        self.db_handler = db_handler
        self._patterns = []
        self._load_shapeflow_patterns()

    def _load_shapeflow_patterns(self):
        """
        Loads chatbot patterns from the database and stores them in the _patterns attribute.

        The method retrieves patterns from the BOT_PROMPTS collection in the database.
        It processes the data into a list of tuples, where each tuple contains a pattern and its responses.
        """
        patterns = self.db_handler.read_from_database(DatabaseCollections.BOT_PROMPTS.value)
        if patterns:
            for category, pattern_list in patterns.items():
                for pattern_data in pattern_list:
                    pattern = pattern_data['pattern']
                    responses = pattern_data['responses']
                    self._patterns.append((pattern, responses))

    def get_patterns(self):
        """
        Retrieves the list of loaded patterns.

        Returns:
            list: A list of tuples, where each tuple contains a pattern and its associated responses.
        """
        return self._patterns
