import requests
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self):
        pass

    def fetch_page(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        else:
            return None
