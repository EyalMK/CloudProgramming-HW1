from nltk.stem import PorterStemmer
import re
from search_engine.scraper import Scraper


class SearchEngine:
    def __init__(self, utils, chosen_words, url, query):
        self.indices = {}
        self.utils = utils
        self.chosen_words = chosen_words
        self.url = url
        self.query = query
        self.scraper = Scraper()

    def search(self, query, indices):
        stemmer = PorterStemmer()
        query_words = re.findall(r'\w+', query.lower())
        results = {}
        for word in query_words:
            word = stemmer.stem(word)
            if word in indices:
                results[word] = indices[word]
        self.indices = results
        return results

    def apply_stemming(self):
        stemmer = PorterStemmer()
        stemmed_index = {}
        for word, count in self.indices.items():
            stemmed_word = stemmer.stem(word)
            if stemmed_word in stemmed_index:
                stemmed_index[stemmed_word] += count
            else:
                stemmed_index[stemmed_word] = count
        return stemmed_index

    def index_words(self, soup):
        words = re.findall(r'\w+', soup.get_text())
        for word in words:
            word = word.lower()
            if word in self.indices:
                self.indices[word] += 1
            else:
                self.indices[word] = 1
        return self.indices

    def remove_stop_words(self):
        stop_words = {'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at'}
        for stop_word in stop_words:
            if stop_word in self.indices:
                del self.indices[stop_word]

    def search_engine(self):
        soup = self.scraper.fetch_page(self.url)
        if soup is None:
            return None
        self.index_words(soup)
        self.remove_stop_words()
        stemmed_indices = self.apply_stemming()
        results = self.search(self.query, stemmed_indices)
        return results