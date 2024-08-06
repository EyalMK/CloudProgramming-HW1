import requests

from bs4 import BeautifulSoup


class Scraper:
    """
    A simple web scraper class to fetch and parse HTML pages.

    Attributes:
    None

    Methods:
    fetch_page(url):
        Fetches a webpage and returns a BeautifulSoup object if successful, otherwise returns None.
    """

    def __init__(self):
        """
        Initializes the Scraper class.

        This constructor does not perform any actions or initialize any attributes.
        """
        pass

    @staticmethod
    def fetch_page(url):
        """
        Fetches the content of the webpage at the specified URL.

        Args:
            url (str): The URL of the webpage to fetch.

        Returns:
            BeautifulSoup|None: A BeautifulSoup object containing the parsed HTML content if the request was successful
                                 (HTTP status code 200), otherwise None.
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            else:
                return None
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return None
