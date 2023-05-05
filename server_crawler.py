
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

        # save to our persistent storage
        # self.save_to_pickle()

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

        # # persistent file for the URLs priorityQueue
        # self.restore_queue_path = "restore_queue.csv"


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
        # if os.path.isfile("fake.csv"):
        if os.path.isfile(self.restore_path):
            # restore the queue, player_popularity, visited URLS
            # Load data (deserialize)
            try: 
                with open(self.restore_path, 'rb') as handle:
                    restored_tuple = pickle.load(handle)
                    # restored_tuple = pickle.load(open(self.restore_path, "rb"))
                    self.visited_urls = restored_tuple[0]
                    self.visited_urls.pop()
                    # print('visited1', self.visited_urls)
                    last_url = self.visited_urls.pop()
                    self.urls_queue = PriorityQueue()
                    self.urls_queue.put((-100, str(last_url)))
                    self.urls_queue.put((-100, 'https://www.espn.com/tennis/'))
                    self.player_popularity = restored_tuple[1]

                    print("Restored this":, restored_tuple)
                    # print('visited_urls2', self.visited_urls)

                    # create a variable to store the total number of sites we have crawled
                    self.number_of_sites_crawled = len(self.visited_urls)
                    print("Number of sites crawled:", self.number_of_sites_crawled)

                    # log the server restoration 
                    self.log.info('Restoring web crawler server...')
                    print("LOGGING")

            except EOFError:
                print("Empty pickle file!")
                self.setUpFromScratch()
        else:
            self.setUpFromScratch()
    
    def toPriorityQueue(self, dict):
        new_pqueue = PriorityQueue()
        # get each item off the queue
        for weight, url in dict.items():
            new_pqueue.put((int(weight), url))
        return new_pqueue
    
    def toDict(self, pqueue):

        new_dict = {}
        # get each item off the queue

        while not pqueue.empty():
            
            url, weight = pqueue.get()
            print('url, weight', url, weight)
            new_dict[weight] = url
            # new_list.append(url, weight)
        
        print("New dict", new_dict)
        return new_dict

    # function to create persistent storage
    def save_to_pickle(self):
        # lock all the mutexes
        self.visited_urls_lock.acquire()
        self.urls_queue_lock.acquire()
        self.player_popularity_lock.acquire()

        if self.visited_urls and self.urls_queue and self.player_popularity:
            # update the restore_tuple object so we can save it to our pickle file
            # restore_tuple = (self.visited_urls, self.urls_queue, self.player_popularity)
            restore_tuple = (self.visited_urls, self.player_popularity)

            #print("Saving this tuple: ", restore_tuple)
            # Store data (serialize)
            with open(self.restore_path, 'wb') as handle:
                pickle.dump(restore_tuple, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # time.sleep(0.1)
        # # save the object to our pickle file
        # pickle.dump(restore_tuple, open(self.restore_path, "wb"))

        # release the mutexes
        self.visited_urls_lock.release()
        self.urls_queue_lock.release()
        self.player_popularity_lock.release()


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

    def process_hyperlinks(self, request, context):
        # create a variable for the next url to scrape
        next_url = PRIORITY_QUEUE_EMPTY

        # create variables for the values we receive from the client
        scraped_url_weight = request.weight

        
        # if this is not an intialization request on the client's
        # behalf, process the client data
        if scraped_url_weight != CLIENT_BYPASS:
            print("Processing URL data from client with weight", scraped_url_weight)

            player_frequencies_on_url = self.convert_proto_to_dict(request.players_freq)
            new_urls = self.convert_proto_to_list(request.hyperlinks)
            #print('Info from client', player_frequencies_on_url, new_urls)
            
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
            print("After visiting " + str(len(self.visited_urls)) + " sites, we have the following statistics:")
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

    def find_most_popular_players(self):
        # returns 1) the total # player mentions and 2) a dict of 5 popular players:count
        # assuming player_popularity is a counter for this function
        # total_counts = sum(self.player_popularity.values())
        # here you assume A is a dict, but we should convert it to be a counter anyways
        # return a dict of the 5 most popular players & a list of their counts
        # most_popular = dict(Counter(A).most_common(5))
        # return total_counts, most_popular
        
        # lock the player popularity mutex
        self.player_popularity_lock.acquire()

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
                  str((count/total_mention_count)*100) + "% of total mentions.")

        # release the player popularity mutex
        self.player_popularity_lock.release()
    
    # function for converting our proto value to a player dicitonary
    def convert_proto_to_dict(self, proto):
        output = {}
        pairs = proto.split(PAIRDELIM)
        if pairs:
            for pair in pairs:
                if pair:
                    key, val = pair.split(KEYDELIM)
                    output[key] = int(val)

        return output
    
    # function for converting our proto value to a url list
    def convert_proto_to_list(self, proto):
        output = []
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
