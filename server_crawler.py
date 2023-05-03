
import grpc
from grpc._server import _Server
import scrape_pb2 as scrape
import scrape_pb2_grpc
from keywords import *

import socket
import threading
from concurrent import futures
import requests
from urllib.parse import urljoin
import numpy as np

import threading
import logging
from bs4 import BeautifulSoup
from queue import PriorityQueue
from datetime import datetime
from collections import Counter
import pandas as pd


class CrawlerServer(scrape_pb2_grpc.CrawlServicer):
    # initialize the server for our  distributed web crawler
    def __init__(self):
        # Mutex lock so only one thread can access each of these data structures at a given time
        # Need this to be a Recursive mutex as some subfunctions call on lock on
        # top of a locked function
        self.visited_urls_lock = threading.RLock()
        self.urls_queue_lock = threading.RLock()
        self.player_popularity_lock = threading.RLock()

        # create a variable to store the total number of sites we have crawled
        self.number_of_sites_crawled = 0
        # a list to keep track of the urls that our crawler has visited
        self.visited_urls = []
        # a priority queue to hold the urls that our crawler needs to visit
        # the urls will be stored in the format `[(weight, url), (weight, url)]`
        self.urls_queue = PriorityQueue()
        # add the seed URL to our priority queue
        self.urls_queue.put((-100, 'https://www.wtatennis.com/'))

        # Get the list of top 50 WTA players
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

        self.log.info('Starting web crawler server...')

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

    def process_hyperlinks(self, request, context):
        # create a variable for the next url to scrape
        next_url = PRIORITY_QUEUE_EMPTY

        # create variables for the values we receive from the client
        scraped_url_weight = request.weight

        # lock the urls queue mutex
        self.urls_queue_lock.acquire()
        
        # if this is not an intialization request on the client's
        # behalf, process the client data
        if scraped_url_weight != CLIENT_BYPASS:
            player_frequencies_on_url = request.players_freq
            new_urls = request.hyperlinks

            # lock the player popularity mutex
            self.player_popularity_lock.acquire()
            # use the player frequency counts from the scraped URL to update our
            # player popularity Counter
            self.player_popularity.update(player_frequencies_on_url)
            # release mutex
            self.player_popularity_lock.release()

            self.log.info('Finished crawling a site with %s distinct players mentioned and %s hyperlinks.', len(
                player_frequencies_on_url), len(new_urls))

            # check if the weight of the scraped URLs meets the threshold weight
            if scraped_url_weight < 1000:
                # add the new hyperlinks to the PriorityQueue according to the weight
                for url in new_urls:
                    self.add_url_to_prioqueue(scraped_url_weight, url)

        if not self.urls_queue.empty():
            # get the next highest priority URL from the queue to be scraped
            next_url = self.urls_queue.get()

            self.log.info('Crawling next site: %s', next_url)

            # lock the visited urls mutex
            self.visited_urls_lock.release()
            # add the next url that will be scraped to the visited URLs list
            self.visited_urls.append(next_url)
            # release mutex
            self.visited_urls_lock.release()
        
        # release mutex
        self.urls_queue_lock.release()

        # return the next URL for the client to scrape
        return scrape.Message(message = next_url)

    def find_most_popular_players(self):
        # returns 1) the total # player mentions and 2) a dict of 5 popular players:count
        # assuming player_popularity is a counter for this function
        # total_counts = sum(self.player_popularity.values())
        # here you assume A is a dict, but we should convert it to be a counter anyways
        # return a dict of the 5 most popular players & a list of their counts
        # most_popular = dict(Counter(A).most_common(5))
        # return total_counts, most_popular
        total_mention_count = sum(self.player_popularity.values())
        max_player_count = 0
        max_player_name = ""
        for player, count in self.player_popularity.items():

            if count > max_player_count:
                max_player_count = count
                max_player_name = player

        print("Most Popular Player is", max_player_name)
        five_most_common_players = self.player_popularity.most_common(5)
        for player, count in five_most_common_players:
            print(player + " was mentioned " + str(count) + " times. They comprise " +
                  str(count/total_mention_count) + "% of total mentions.")


# create a class for starting our Crawler server instance
class ServerRunner:
    # start an instance of a server
    def __init__(self):

        self.host = HOST
        self.port = PORT

    # a function to start the server
    def run(self):
        self.server_crawler = CrawlerServer()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        scrape_pb2_grpc.add_CrawlServicer_to_server(
            self.server_crawler, self.server)
        self.server.add_insecure_port('[::]:' + str(self.port))
        self.server.start()
        print("Crawler server is running.")
        self.server.wait_for_termination()

    # a function to kill the server instance
    def kill(self):
        self.server_crawler.find_most_popular_players()
        self.server.stop(grace=None)
        # self.thread_pool.shutdown(wait=False)


if __name__ == '__main__':
    server = ServerRunner()
    server.run()
