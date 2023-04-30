import numpy as np
import logging
from urllib.parse import urljoin
import requests
import pandas as pd
from bs4 import BeautifulSoup
from queue import PriorityQueue
from datetime import datetime
from collections import Counter
import time

# TODO make self.player_popularity into a counter object not a dictionary

# threshold for whether to add url to queue or not
threshold = 10
screening_years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018',
                    '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030']


class WebCrawler:

    def __init__(self):
        self.number_of_sites_crawled = 0
        # a list to keep track of the urls that our crawler has visited
        self.visited_urls = []
        # a priority queue to hold the urls that our crawler needs to visit
        # the urls will be stored in the format `[(weight, url), (weight, url)]`
        self.urls_queue = PriorityQueue()

        data = pd.read_csv('player_names.txt', delimiter="\t", header=0).values
        self.player_list = np.reshape(data, -1)

        # initialize Counter to have items for each player
        self.player_popularity = Counter(self.player_list)
        # self.player_popularity = {}

        # # initialize the count vector to be 0 for each player
        # for player in self.player_list:
        #     self.player_popularity[player] = 0

        # create a logger file name and use that file to log crawling activities
        self.logname = "web_crawler_logs/WebCrawler" + \
            "_" + str(datetime.now()) + ".txt"
        logging.basicConfig(
            filename=self.logname,
            format='%(asctime)s,%(msecs)03d, %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO)

        self.log = logging.getLogger(__name__)

        self.log.info('Starting web crawler...')

    # def get_hyperlinks(self, url, html):
    #     soup = BeautifulSoup(html, 'html.parser')
    #     for link in soup.find_all('a'):
    #         path = link.get('href')
    #         # print("PATH", path)
    #         if path and path.startswith('/'):
    #             # print("filtered path", path)
    #             path = urljoin(url, path)
    #         yield path

    # def add_url_to_prioqueue(self, weight, url):
    #     # logic will be that the weight for each child link will
    #     # be determined by the number of tennis players the parent
    #     # site mentions and the date the site was published if available
    #     # the weight will be calculated by the formula:
    #     # {~- number of names mentioned} + {2023 - latest year mentioned}
    #     # if the url has not ben visited before add it to the prioqueue
    #     # print("curr url queue", self.urls_queue.queue)
    #     if url not in self.visited_urls:
    #         self.urls_queue.put((weight, url))
    #     # print("new curr url queue", self.urls_queue.queue)

    # def get_player_info_and_date(self, html):
    #     soup = BeautifulSoup(html, 'html.parser')
    #     html_text = soup.get_text().lower()
    #     #print('orig', html_text)
    #     # compute the counts of each of the years
    #     year_counts = []
    #     for year in screening_years:
    #         year_counts.append(html_text.count(year))
    #     non_zero_arr = np.nonzero(year_counts)[0]
        
    #     # if there is a year mentioned, compute the max year
    #     if non_zero_arr.size > 0:
    #         # find the latest year where the count isn't 0
    #         max_year = screening_years[max(non_zero_arr)]
    #     else:
    #         max_year = 2010
    #     #print('YEARCOUNTS', year_counts, max_year)
    #     # TODO add mutexes

    #     player_count = 0
        
    #     # for each of the top 50 players that we want to search for
    #     # read the text file to find the latest year mentioned and the players
    #     player_count_on_site = {}
    #     for player in self.player_list:
    #         count_from_cur_site = html_text.count(player)
    #         if count_from_cur_site > 0:
    #             # add the count to the dict
    #             # at the end, update the count
    #             player_count_on_site[player] = count_from_cur_site
    #             player_count += 1
    #         # cur_count = self.player_popularity[player]
    #         # self.player_popularity[player] = count_from_cur_site + cur_count
    #         # if count_from_cur_site > 0:
    #         #     player_count += 1
    #     self.player_popularity.update(player_count_on_site)

    #     # return the count of the players mentioned and the maximum year mentioned
    #     # print('PLAYERCOUNT', player_count)
    #     # print('popularity dict', self.player_popularity)
    #     return player_count, int(max_year)

    def find_most_popular_players(self):
        # returns 1) the total # player mentions and 2) a dict of 5 popular players:counts
        # TODO make this a counter to run this code
        # assuming player_popularity is a counter for this function
        # total_counts = sum(self.player_popularity.values())        
        # here you assume A is a dict, but we should convert it to be a counter anyways
        # return a dict of the 5 most popular players & a list of their counts 
        # most_popular = dict(Counter(A).most_common(5))
        # return total_counts, most_popular
        max_player_count = 0
        max_player_name = ""
        for player, count in self.player_popularity.items():
            if count > max_player_count:
                max_player_count = count
                max_player_name = player

        print("Most Popular Player is", max_player_name)

    def crawl_url(self, url):
        # if we have not visited this url before, then we can crawl it for information
        if url not in self.visited_urls:
            self.number_of_sites_crawled += 1
            print("Number of Sites Crawled:", self.number_of_sites_crawled)
            self.visited_urls.append(url)
            html = self.get_url_info(url)
            # get_player_info_and_date
            player_count, date = self.get_player_info_and_date(html)
            print("player_count, date", player_count, date)
            weight = self.compute_url_weight(player_count, date)
            self.find_most_popular_players()
            if weight < threshold:
                for link in self.get_hyperlinks(url, html):
                    if link is not None and not link.startswith('#'):
                        # print("weight, url", weight, url)
                        self.add_url_to_prioqueue(weight, link)

    def compute_url_weight(self, player_count, date):
        # the logic for computing the url weight
        if int(date) < 2018 or player_count == 0:
            # if the URL is outdated, return 10000 so it is never 
            # added to the queue as this will be filtered later
            return 10000
        url_weight = -player_count + (2023 - date)
        return url_weight

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
            # print(f'Crawling: {url}')
            # print("Pre crawling link, this is our visited", self.visited_urls)
            try:
                self.crawl_url(url)
                self.log.info(f'Finished crawling: {url}')
                # print(f'Finished crawling: {url}')
                # print('visited', self.visited_urls)
            except Exception:
                self.log.exception(f'Failed to crawl: {url}')


if __name__ == '__main__':
    # urls = ['https://www.wtatennis.com/', 'https://www.espn.com/tennis/']
    urls = ['https://www.wtatennis.com/']
    crawler = WebCrawler()
    for url in urls:
        crawler.add_url_to_prioqueue(9, url)
    crawler.run_crawler()
