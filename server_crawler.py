
import grpc
from grpc._server import _Server
import scrape_pb2
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
        # create variables for the values we receive from the client
        scraped_url_weight = request.weight
        player_frequencies_on_url = request.players_freq
        new_urls = request.hyperlinks

        self.log.info('Finished crawling a site with %s distinct players mentioned and %s hyperlinks.', len(
            player_frequencies_on_url), len(new_urls))

        # lock the urls queue mutex
        self.urls_queue_lock.acquire()
        # check if the weight of the scraped URLs meets the threshold weight
        if scraped_url_weight < 1000:
            # add the new hyperlinks to the PriorityQueue according to the weight
            for url in new_urls:
                self.add_url_to_prioqueue(scraped_url_weight, url)

        # get the next highest priority URL from the queue to be scraped
        next_url = self.urls_queue.get()
        # release mutex
        self.urls_queue_lock.release()

        self.log.info('Crawling next site: %s', next_url)

        # lock the visited urls mutex
        self.visited_urls_lock.release()
        # add the next url that will be scraped to the visited URLs list
        self.visited_urls.append(next_url)
        # release mutex
        self.visited_urls_lock.release()

        # lock the player popularity mutex
        self.player_popularity_lock.acquire()
        # use the player frequency counts from the scraped URL to update our
        # player popularity Counter
        self.player_popularity.update(player_frequencies_on_url)
        # release mutex
        self.player_popularity_lock.release()

        # return the next URL for the client to scrape
        return next_url


# create a class for starting our Crawler server instance
class ServerRunner:
    # start an instance of a server
    def __init__(self):

        self.host = HOST
        self.port = PORT

    # a function to start the server
    def run(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        scrape_pb2_grpc.add_CrawlServicer_to_server(
            CrawlerServer(), self.server)
        self.server.add_insecure_port('[::]:' + self.port)
        self.server.start()
        self.server.wait_for_termination()

    # a function to kill the server instance
    def kill(self):
        self.server.stop(grace=None)
        # self.thread_pool.shutdown(wait=False)


if __name__ == '__main__':
    server = ServerRunner()
    server.run()
