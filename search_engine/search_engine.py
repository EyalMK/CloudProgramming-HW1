import re
from nltk.stem import PorterStemmer

from config.constants import DatabaseCollections, ONSHAPE_GLOSSARY_URL
from search_engine.scraper import Scraper


class SearchEngine:
    """
    A class that implements a search engine for indexing and querying words from a glossary.

    Attributes:
        db_handler: An instance of a database handler for reading and writing data.
        utils: An instance of utility functions, including a logger.
        indices: A dictionary storing indexed words and their counts.
        indices_by_words: A helper dictionary for storing counts by individual words.
        stemmed_indices: A dictionary for storing stemmed words and their counts.
        glossary_soap: A BeautifulSoup object containing the parsed HTML content of the glossary.
        chosen_words: A list of words chosen for the search engine.
        stemmer: An instance of PorterStemmer for word stemming.
        scraper: An instance of Scraper for fetching web pages.
    """
    def __init__(self, db_handler, utils):
        """
        Initializes the SearchEngine class with a database handler and utility functions.

        Parameters:
            db_handler (DatabaseHandler): An instance of the database handler.
            utils (Utilities): An instance of utility functions, including a logger.
        """
        self.initialized = True
        self.indices = {}
        self.indices_by_words = {}  # Helper indices dictionary for each word in chosen words.
        self.stemmed_indices = None
        self.glossary_soap = None
        self.utils = utils
        self.db_handler = db_handler
        self.chosen_words = []
        self.stemmer = PorterStemmer()
        self.scraper = Scraper()
        self._initialize_base_words()
        self._search_engine()

    def perform_search(self, query):
        """
        Performs a search using the given query.

        Parameters:
            query (str): The search query.

        Returns:
            dict: A dictionary with stemmed words as keys and their counts as values.
        """
        return self._search_indices(query)

    def _initialize_base_words(self):
        """
        Initializes the list of chosen words from the database.

        Reads the glossary words from the database and sets them as the chosen words.
        Logs an error if the initialization fails.
        """
        try:
            data = self.db_handler.read_from_database(DatabaseCollections.GLOSSARY_WORDS.value)
            if data:
                self.chosen_words = data
        except Exception as e:
            self.utils.logger.error(f"Error initializing base words: {str(e)}")

    def _search_indices(self, query):
        """
        Searches the indexed words for the given query.

        Parameters:
            query (str): The search query.

        Returns:
            dict: A dictionary with stemmed words as keys and their counts as values.
        """
        if query in self.indices:
            return self.indices[query]

        query_words = re.findall(r'\w+', query.lower())
        results = {}
        for word in query_words:
            word = self.stemmer.stem(word)
            if word in self.stemmed_indices:
                results[word] = self.stemmed_indices[word]
            else:
                results[word] = 0

        # Cache query search results (users tend to search the same terms multiple times)
        self.indices[query] = results
        return results

    def _apply_stemming(self):
        """
        Applies stemming to the indexed words.

        Returns:
            dict: A dictionary with stemmed words as keys and their counts as values.
        """
        stemmed_index = {}
        for word, count in self.indices.items():
            stemmed_word = self.stemmer.stem(word)
            if stemmed_word in stemmed_index:
                stemmed_index[stemmed_word] += count
            else:
                stemmed_index[stemmed_word] = count
        return stemmed_index

    @staticmethod
    def _index_words(soup):
        """
        Indexes words from the parsed HTML content.

        Parameters:
            soup (BeautifulSoup): The parsed HTML content.

        Returns:
            dict: A dictionary with words as keys and their counts as values.
        """
        index = {}
        words = re.findall(r'\w+', soup.get_text())
        for word in words:
            word = word.lower()
            if word in index:
                index[word] += 1
            else:
                index[word] = 1
        return index

    def _remove_stop_words(self):
        """
        Removes common stop words from the indexed words.

        Stop words are removed from the indices to focus on more meaningful words.
        """
        stop_words = {'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at'}
        for stop_word in stop_words:
            if stop_word in self.indices:
                del self.indices[stop_word]

    def _search_engine(self):
        """
        Initializes and updates the search engine indices.

        Fetches the glossary page, reads existing indices from the database, or creates new ones.
        Writes the indices to the database and applies stemming to the indexed words.
        """
        self.glossary_soap = self.scraper.fetch_page(ONSHAPE_GLOSSARY_URL)
        if self.glossary_soap is None:
            return

        indices = self.db_handler.read_from_database(DatabaseCollections.INDICES_WORDS.value)
        if indices:
            for key in indices:
                self.indices = indices[key]
                break
        else:
            self.indices = self._index_words(self.glossary_soap)
            self._remove_stop_words()
            self.db_handler.write_to_database(DatabaseCollections.INDICES_WORDS.value, self.indices)

        self.stemmed_indices = self._apply_stemming()
