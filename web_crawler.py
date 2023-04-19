import numpy as np
import logging
from urllib.parse import urljoin
import requests
import pandas as pd
from bs4 import BeautifulSoup
from queue import PriorityQueue
from datetime import datetime
import pandas as pd


# threshold for whether to add url to queue or not
threshold = 10

class WebCrawler:

    def __init__(self):
        # a list to keep track of the urls that our crawler has visited
        self.visited_urls = []
        # a priority queue to hold the urls that our crawler needs to visit
        # the urls will be stored in the format `[(weight, url), (weight, url)]`
        self.urls_queue = PriorityQueue()

        data = pd.read_csv('player_names.txt', delimiter="\t", header=0).values
        player_list = np.reshape(data, -1)

        player_popularity = {}

        # initialize the count vector to be 0 for each player
        for player in player_list:
            player_popularity[player] = 0

        # create a logger file name and use that file to log crawling activities
        self.logname = "web_crawler_logs/WebCrawler" + "_" + str(datetime.now()) + ".txt"
        logging.basicConfig(
            filename=self.logname,
            format='%(asctime)s,%(msecs)03d, %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO)

        self.log = logging.getLogger(__name__)

        self.log.info('Starting web crawler...')

    def get_hyperlinks(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            print("PATH", path)
            if path and path.startswith('/'):
                print("filtered path", path)
                path = urljoin(url, path)
            yield path

    def add_url_to_prioqueue(self, weight, url):
        # logic will be that the weight for each child link will
        # be determined by the number of tennis players the parent
        # site mentions and the date the site was published if available
        # the weight will be calculated by the formula:
        # {~- number of names mentioned} + {2023 - latest year mentioned}
        # if the url has not ben visited before add it to the prioqueue
        # print("curr url queue", self.urls_queue.queue)
        if url not in self.visited_urls:
            self.urls_queue.put((weight, url))
        # print("new curr url queue", self.urls_queue.queue)

    def get_player_info_and_date(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        html_text = soup.get_text()
        # TODO read the text file to find the latest year mentioned and the players
        latest_year = 2020
        player_count = 3
        return player_count, latest_year


    def crawl_url(self, url):
        # if we have not visited this url before, then we can crawl it for information
        if url not in self.visited_urls:
            # get the html of the url
            html = self.get_url_info(url)
            # get_player_info_and_date
            player_count, date = self.get_player_info_and_date(html)
            weight = self.compute_url_weight(player_count, date)
            if weight < threshold: 
                for url in self.get_hyperlinks(url, html):
                    if url is not None and not url.startswith('#'):
                        # print("weight, url", weight, url)
                        self.add_url_to_prioqueue(weight, url)
            self.visited_urls.append(url)


    def compute_url_weight(self, player_count, date=None):
        # TODO add logic for computing the url weight
        return 6

    def get_url_from_prioqueue(self):
        weight, url = self.urls_queue.get()
        # print("got weight, url?", weight, url)
        return url

    def get_url_info(self, url):
        # requests_text = requests.get(url).text
        # url_weight = self.compute_url_weight(requests_text)
        return requests.get(url).text

    def run_crawler(self):
        while not self.urls_queue.empty():
            url = self.get_url_from_prioqueue()
            self.log.info(f'Crawling: {url}')
            try:
                self.crawl_url(url)
                self.log.info(f'Finished crawling: {url}')
                print(self.visited_urls)
            except Exception:
                self.log.exception(f'Failed to crawl: {url}')


if __name__ == '__main__':
    # urls = ['https://www.wtatennis.com/', 'https://www.espn.com/tennis/']
    urls = ['https://www.wtatennis.com/']
    crawler = WebCrawler()
    for url in urls:
        crawler.add_url_to_prioqueue(9, url)
    crawler.run_crawler()
