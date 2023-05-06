
import grpc
from grpc._server import _Server
import scrape_pb2 as scrape
import scrape_pb2_grpc
from keywords import *

import time
import os
import socket
import threading
from concurrent import futures
import requests
from urllib.parse import urljoin
import numpy as np
import pickle
import sys

import threading
import logging
from bs4 import BeautifulSoup
from queue import PriorityQueue
from datetime import datetime
from collections import Counter
import pandas as pd


class CrawlerServer(scrape_pb2_grpc.CrawlServicer):

    def setUpFromScratch(self):
        # initialize new variables
        # create a variable to store the total number of sites we have crawled
        self.number_of_sites_crawled = 0
        # a list to keep track of the urls that our crawler has visited
        self.visited_urls = []
        # a priority queue to hold the urls that our crawler needs to visit
        # the urls will be stored in the format `[(weight, url), (weight, url)]`
        self.urls_queue = PriorityQueue()
        # add the seed URL to our priority queue
        self.urls_queue.put((-100, 'https://www.wtatennis.com/'))

        # initialize Counter to have items for each player
        self.player_popularity = Counter(self.player_list)

        # log the server initialization
        self.log.info('Starting new web crawler server...')

    # initialize the server for our  distributed web crawler
    def __init__(self):
        # Mutex lock so only one thread can access each of these data structures at a given time
        # Need this to be a Recursive mutex as some subfunctions call on lock on
        # top of a locked function
        self.visited_urls_lock = threading.RLock()
        self.urls_queue_lock = threading.RLock()
        self.player_popularity_lock = threading.RLock()

        # Get the list of top 50 WTA players
        data = pd.read_csv('player_names.txt', delimiter="\t", header=0).values
        self.player_list = np.reshape(data, -1)

        # persistent output files for the visisted list and player populatiry dictionary
        self.restore_path = "restored.p"

        # create a logger file name and use that file to log crawling activities
        self.logname = "web_crawler_logs/WebCrawler" + \
            "_" + str(datetime.now()) + ".txt"
        logging.basicConfig(
            filename=self.logname,
            format='%(asctime)s,%(msecs)03d, %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO)

        self.log = logging.getLogger(__name__)

        # check if the pickle file to store the state as data exists,
        # if not then create the file
        if os.path.isfile(self.restore_path):
            # restore the queue, player_popularity, visited URLS
            # Load data (deserialize)
            try:
                # try to restore the server state from the pickle file
                with open(self.restore_path, 'rb') as handle:
                    # get the restored tuple with the server data structures from the pickle file
                    restored_tuple = pickle.load(handle)

                    # restore the visisted urls list
                    self.visited_urls = restored_tuple[0]

                    # restore the pending url queue
                    self.visited_urls.pop()
                    last_url = self.visited_urls.pop()
                    self.urls_queue = PriorityQueue()
                    self.urls_queue.put((-100, str(last_url)))
                    if RESTORE_URL in self.visited_urls:
                        self.visited_urls.remove(RESTORE_URL)
                    self.urls_queue.put((-100, RESTORE_URL))

                    # restore the player popularity Counter object
                    self.player_popularity = restored_tuple[1]

                    print("Restored this:", restored_tuple)

                    # create a variable to store the total number of sites we have crawled
                    self.number_of_sites_crawled = len(self.visited_urls)
                    print("Number of sites crawled:",
                          self.number_of_sites_crawled)

                    # log the server restoration
                    self.log.info('Restoring web crawler server...')
                    print("LOGGING")

            # if unsuccessful then set up the server from scratch
            except EOFError:
                print("Empty pickle file!")
                self.setUpFromScratch()

        # if not restoration pickle file exists, then set up the server from scratch
        else:
            self.setUpFromScratch()

    # function to create a prioqueue from an input dictionary
    def toPriorityQueue(self, dict):
        # create a new prioqueue
        new_pqueue = PriorityQueue()

        # get each item off the queue
        for weight, url in dict.items():
            new_pqueue.put((int(weight), url))

        # return the new prioqueue
        return new_pqueue

    # function to create a dictionary from an input prioqueue
    def toDict(self, pqueue):
        # create new dictionary
        new_dict = {}

        # get each item off the pqueue
        while not pqueue.empty():
            # get the url with the lowest weight and add that first
            url, weight = pqueue.get()
            new_dict[weight] = url

        # return the new constructed priorityQueue
        return new_dict

    # function to create persistent storage
    def save_to_pickle(self):
        # lock all the mutexes
        self.visited_urls_lock.acquire()
        self.urls_queue_lock.acquire()
        self.player_popularity_lock.acquire()

        # check if all data structures are populated so we can save them
        if self.visited_urls and self.urls_queue and self.player_popularity:
            # update the restore_tuple object so we can save it to our pickle file
            # restore_tuple = (self.visited_urls, self.urls_queue, self.player_popularity)
            restore_tuple = (self.visited_urls, self.player_popularity)

            # print("Saving this tuple: ", restore_tuple)
            # Store data (serialize)
            with open(self.restore_path, 'wb') as handle:
                pickle.dump(restore_tuple, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)

        # release the mutexes
        self.visited_urls_lock.release()
        self.urls_queue_lock.release()
        self.player_popularity_lock.release()

    # a function to add a new url to our url priorityQueue
    def add_url_to_prioqueue(self, weight, url):
        # logic will be that the weight for each child link will
        # be determined by the number of tennis players the parent
        # site mentions and the date the site was published if available
        # the weight will be calculated by the formula:
        # {~- number of names mentioned} + {2023 - latest year mentioned}
        # if the url has not ben visited before add it to the prioqueue
        # print("curr url queue", self.urls_queue.queue)
        # lock the visisted list mutex
        self.visited_urls_lock.acquire()

        # check if we have visisted this url before, if not then we can add it
        if url not in self.visited_urls:
            # lock the urls queue mutex
            self.urls_queue_lock.acquire()

            # add the URL to our priorityQueue
            self.urls_queue.put((weight, url))

            # save to our persistent storage
            self.save_to_pickle()

            # release mutex
            self.urls_queue_lock.release()

        # release mutex
        self.visited_urls_lock.release()

    # function to process the hyperlinks we receive from a client
    def process_hyperlinks(self, request, context):
        # create a variable for the next url to scrape
        next_url = PRIORITY_QUEUE_EMPTY

        # create variables for the values we receive from the client
        scraped_url_weight = request.weight

        # if this is not an intialization request on the client's
        # behalf, process the client data
        if scraped_url_weight != CLIENT_BYPASS:
            print("Processing URL data from client with weight", scraped_url_weight)
            # process the data from the client into a format we can use
            player_frequencies_on_url = self.convert_proto_to_dict(
                request.players_freq)
            new_urls = self.convert_proto_to_list(request.hyperlinks)

            # lock the player popularity mutex
            self.player_popularity_lock.acquire()
            # use the player frequency counts from the scraped URL to update our
            # player popularity Counter
            self.player_popularity.update(player_frequencies_on_url)
            # save to our persistent storage
            self.save_to_pickle()
            # release mutex
            self.player_popularity_lock.release()

            self.log.info('Finished crawling a site with %s distinct players mentioned and %s hyperlinks.', len(
                player_frequencies_on_url), len(new_urls))

            # check if the weight of the scraped URLs meets the threshold weight
            if scraped_url_weight < URL_WEIGHT_THRESHOLD:
                # add the new hyperlinks to the PriorityQueue according to the weight
                # lock the urls queue mutex
                self.urls_queue_lock.acquire()
                for url in new_urls:
                    self.add_url_to_prioqueue(scraped_url_weight, url)
                # save to our persistent storage
                self.save_to_pickle()
                # release mutex
                self.urls_queue_lock.release()

            # track how many sites have been visited
            self.visited_urls_lock.acquire()
            print("After visiting " + str(len(self.visited_urls)) +
                  " sites, we have the following statistics:")
            self.visited_urls_lock.release()

            # after processing this, print the player popularity stats
            self.find_most_popular_players()

        else:
            print("Client is querying for a new link... no client data to be processed.")

        # lock the urls queue mutex
        self.urls_queue_lock.acquire()
        if not self.urls_queue.empty():
            # get the next highest priority URL from the queue to be scraped
            # print('pre queue', self.urls_queue)
            next_url = self.urls_queue.get()[1]

            # add next url to visited ASAP so we do not visit sites multiple times
            # lock the visited urls mutex
            self.visited_urls_lock.acquire()

            # check that next_url isn't in visited
            while next_url in self.visited_urls:
                next_url = self.urls_queue.get()[1]

            # add the next url that will be scraped to the visited URLs list
            self.visited_urls.append(next_url)
            # save to our persistent storage
            self.save_to_pickle()
            # release mutex
            self.visited_urls_lock.release()

            # print('post getting', next_url)

            self.log.info('Crawling next site: %s', next_url)

        # release mutex
        self.urls_queue_lock.release()

        # return the next URL for the client to scrape
        return scrape.Message(message=next_url)

    # a function to determine the most popular players based on our player popularity Counter
    def find_most_popular_players(self):
        # returns 1) the total # player mentions and 2) a dict of 5 popular players:count
        # assuming player_popularity is a counter for this function

        # lock the player popularity mutex
        self.player_popularity_lock.acquire()

        # a variable to keep track of the
        total_mention_count = sum(self.player_popularity.values())
        max_player_count = 0
        max_player_name = ""

        # determine the players with the high mention counts
        for player, count in self.player_popularity.items():
            # check if the count of the current player is high than max player count
            # if so then update the max player count
            if count > max_player_count:
                max_player_count = count
                max_player_name = player

        print("Most Popular Player is", max_player_name)

        # get the five most popular players for our model
        five_most_common_players = self.player_popularity.most_common(5)
        for player, count in five_most_common_players:
            print(player + " was mentioned " + str(count) + " times. They comprise " +
                  str((count/total_mention_count)*100) + "% of total mentions.")

        # release the player popularity mutex
        self.player_popularity_lock.release()

        return max_player_name

    # function for converting our proto value to a player dicitonary
    def convert_proto_to_dict(self, proto):
        # create output dict
        output = {}

        # split the proto based on the dict pairs delimiter
        pairs = proto.split(PAIRDELIM)
        if pairs:
            for pair in pairs:
                if pair:
                    # split each pair based on the dict key delimiter
                    key, val = pair.split(KEYDELIM)
                    output[key] = int(val)

        return output

    # function for converting our proto value to a url list
    def convert_proto_to_list(self, proto):
        # create output list
        output = []

        # split the list items in the proto based on the list delimiter
        urls = proto.split(LISTDELIM)
        if urls:
            for url in urls:
                if url:
                    output.append(url)

        return output

# create a class for starting our Crawler server instance
class ServerRunner:
    # start an instance of a server
    def __init__(self):

        self.host = HOST
        self.port = PORT

    # a function to start the server
    def run(self):
        # add in timer function- run this for X minutes and then print stats @ the end.

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
    # restore = sys.argv[1].lower() == "true"
    server = ServerRunner()
    server.run()
