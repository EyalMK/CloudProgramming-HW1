from nltk.stem import PorterStemmer
import re

from config.constants import DatabaseCollections, ONSHAPE_GLOSSARY_URL
from search_engine.scraper import Scraper


class SearchEngine:
    def __init__(self, db_handler, utils):
        self.indices = {}
        self.stemmed_indices = None
        self.glossary_soap = None
        self.utils = utils
        self.db_handler = db_handler
        self.chosen_words = []
        self.stemmer = PorterStemmer()
        self._initialize_base_words()
        self.scraper = Scraper()
        self._search_engine()

    def perform_search(self, query):
        # Cache search results to avoid re-indexing the query
        # Todo: For HW3, store results in database instead
        if query in self.indices:
            return self.indices[query]

        words = query.split()
        combined_results = {}

        # Search for each word
        for word in words:
            results = self._search_indices(word, self.stemmed_indices)
            self.utils.logger.debug(f"Word: {word}, results: {results}")
            # Aggregation
            for key, val in results.items():
                if key in combined_results:
                    combined_results[key] += val
                else:
                    combined_results[key] = val
        return combined_results

    def _initialize_base_words(self):
        try:
            self.chosen_words = self.db_handler.read_from_database(DatabaseCollections.glossary_words.value)
        except Exception as e:
            self.utils.logger.error(f"Error initializing base words: {str(e)}")

    def _search_indices(self, query, indices):
        query_words = re.findall(r'\w+', query.lower())
        results = {}
        for word in query_words:
            word = self.stemmer.stem(word)
            if word in indices:
                results[word] = indices[word]
        self.indices[query] = results
        return results

    def _apply_stemming(self):
        stemmed_index = {}
        for word, count in self.indices.items():
            stemmed_word = self.stemmer.stem(word)
            if stemmed_word in stemmed_index:
                stemmed_index[stemmed_word] += count
            else:
                stemmed_index[stemmed_word] = count
        return stemmed_index

    def _index_words(self, soup):
        words = re.findall(r'\w+', soup.get_text())
        for word in words:
            word = word.lower()
            if word in self.indices:
                self.indices[word] += 1
            else:
                self.indices[word] = 1
        return self.indices

    def _remove_stop_words(self):
        stop_words = {'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at'}
        for stop_word in stop_words:
            if stop_word in self.indices:
                del self.indices[stop_word]

    def _search_engine(self):
        self.glossary_soap = self.scraper.fetch_page(ONSHAPE_GLOSSARY_URL)
        if self.glossary_soap is None:
            return
        self._index_words(self.glossary_soap)
        self._remove_stop_words()
        self.stemmed_indices = self._apply_stemming()
