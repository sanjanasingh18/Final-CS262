"""
INSTRUCTIONS 
From the `test_env` directory run  `python3 test_server.py`

"""

import os
import socket
import math
import time
import uuid
import unittest

import grpc
from grpc._server import _Server
import scrape_pb2 as scrape
import scrape_pb2_grpc
from concurrent import futures

from keywords import *
from crawler_client import CrawlerClient
from server_crawler import CrawlerServer, ServerRunner
from queue import PriorityQueue
from collections import Counter


class SimpleServerTestCase(unittest.TestCase):
    # create only one instance to avoid multiple instantiations
    def setUp(self):
        self. port = PORT
        self.host = HOST

        self.server_crawler = CrawlerServer()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        scrape_pb2_grpc.add_CrawlServicer_to_server(
            self.server_crawler, self.server)
        self.server.add_insecure_port('[::]:' + str(self.port))
        self.server.start()

        # set up host, port, create connection
        print('Server is active.')

    def tearDown(self):
        # conn.close()
        print('shut downwnn')

    def test_server_url_queue_persistence(self):
       # test the restore server persistence, this Server will automatically
       # restore from a previous pickle file, we will check that it was restored
       # correctly
        print("Testing the Server URL queue persistence")

        # check that the server URL queue is not empty after restoration
        self.assertEqual(URL_QUEUE_NONEMPTY,
                         self.server_crawler.urls_queue.empty())

    def test_server_player_counter_persistence(self):
       # test the restore server persistence, this Server will automatically
       # restore from a previous pickle file, we will check that it was restored
       # correctly
        print("Testing the Server URL player Counter persistence")

        # check that the server URL queue is not empty
        self.assertEqual(PLAYER_COUNTER_RESTORED, bool(
            self.server_crawler.player_popularity))

    def test_find_most_popular_player(self):
        # test the find most popular player function based on restored Counter object
        print("Testing the find_most_popular_player function")

        # create a variable to store the most popular player based on restore Counter
        expected_player = "swiatek"

        # get the output from the function
        output_player = self.server_crawler.find_most_popular_players()

        # check that the function returns the correct result
        self.assertEqual(expected_player, output_player)

    def test_add_url_to_prioqueue(self):
        # test the funciton that adds a URL to the priorityQueue
        print("Testing the add_url_to_prioqueue function")

        # create url to add to priority queue
        expected_url = "test_url.com"

        # add the test URL to the priorityQueue with the lowest weight possible
        self.server_crawler.add_url_to_prioqueue(-500, expected_url)

        # get the expected URL from the priorityQueue
        output_url = self.server_crawler.urls_queue.get()[1]

        # check that the function returns the correct result
        self.assertEqual(expected_url, output_url)

    def test_set_up_server_from_scratch(self):
        # testing the set up server from scratch function
        print("Testing the setUpFromScratch function")

        # create a variable for the expected output
        expected_output = 0

        # set up the test server from scratch
        result_output = self.server_crawler.setUpFromScratch()

        # check that the function returns the correct result
        self.assertEqual(expected_output, result_output)

    def test_to_priority_queue(self):
       # test the convert dictionary to priorityQueue function
        print("Testing the toPriorityQueue function")

        # create a variable to pass into the function
        dict = {"10": "url1", "8": "url2", "6": "url3", "4": "url4"}

        # create a variable for the output of the function
        test_pqueue = PriorityQueue()

        # convert the input dictionary to a pqueue
        for weight, url in dict.items():
            test_pqueue.put((int(weight), url))

        # get the first item off the priorityQueue
        expected_output = test_pqueue.get()

        # create a variable to store the test object we will compare
        test_output = self.server_crawler.toPriorityQueue(dict).get()

        # check if the function returns the correct result
        self.assertEqual(expected_output, test_output)

    def test_to_dict(self):
       # test the convert priorityQueue to dictionary function
        print("Testing the toDict function")

        # create a test prioqueue to pass into the function
        pqueue = PriorityQueue()
        pqueue.put((10, "url1"))
        pqueue.put((8, "url2"))
        pqueue.put((6, "url3"))
        pqueue.put((4, "url4"))

        # create a variable for the expected output of the function
        expected_dict = {'url1': 10, 'url2': 8, 'url3': 6, 'url4': 4}

        # get the output of the function
        output_dict = self.server_crawler.toDict(pqueue)

        # check if the function returns the correct result
        self.assertEqual(expected_dict, output_dict)

    def test_save_to_pickle(self):
        # test the save server state to pickle file function
        print("Testing the save_to_pickle function")

        # update test crawler server data structures to save to the pickle file
        self.server_crawler.visisted_urls = ["url1.com", "url2.com", "url3.com", "url4.com", "url5.com"]

        self.server_crawler.urls_queue = PriorityQueue()
        self.server_crawler.urls_queue.put((10, "url1"))
        self.server_crawler.urls_queue.put((8, "url2"))
        self.server_crawler.urls_queue.put((6, "url3"))
        self.server_crawler.urls_queue.put((4, "url4"))

        test_player_counter = Counter(TEST_PLAYER_DICT)

        # check if the function saved the server state successfully
        self.assertEqual(SUCCESS, self.server_crawler.save_to_pickle())

    def test_convert_proto_to_dict(self):
        # test the function that converts a proto dict format to a dictionary
        print("Testing the convert_proto_to_dict function")

        # create a variable for the expected list
        expected_dict = {'url1': 10, 'url2': 8, 'url3': 6, 'url4': 4}

        # get the output list from the function
        output_dict = self.server_crawler.convert_proto_to_dict(TEST_PROTO_DICT)

        # check if the function returns the correct output
        self.assertEqual(expected_dict, output_dict)

    def test_convert_proto_to_list(self):
        # test the function that converts a proto list format to a list
        print("Testing the convert_proto_to_list function")

        # create a variable for the expected list
        expected_list = ["url1.com", "url2.com", "url3.com", "url4.com", "url5.com"]

        # get the output list from the function
        output_list = self.server_crawler.convert_proto_to_list(TEST_PROTO_LIST)

        # check if the function returns the correct output
        self.assertEqual(expected_list, output_list)

if __name__ == '__main__':
    # start the unit tests for the crawler server
    unittest.main()
