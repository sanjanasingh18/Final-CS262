"""
Configuration (BEFORE RUNNING `python3 test_client.py`)
In a separate terminal run `python3 server_crawler.py` and wait for the 'Crawler server is running.' message.

Then, run `python3 test_client.py` in another terminal. 

"""

import os
import socket
import math
import time
import uuid
import uuid
import unittest
from keywords import *
from bs4 import BeautifulSoup
from crawler_client import CrawlerClient
from server_crawler import CrawlerServer, ServerRunner

class TestClientMethods(unittest.TestCase):
    def setUp(self):
        self.client_crawler = CrawlerClient()
        # self.client_crawler.run_client()

    # def tearDown(self):
    #     self.client_crawler.client.close()

    def test_get_url_info(self):
        # test the function that gets the HTML link from a URL that is used to parse a url
        print("Testing the get_url_info function")

        # get the output from the function
        output_html = self.client_crawler.get_url_info(TEST_URL)
        output_html_test = BeautifulSoup(output_html, 'html.parser')

        # check that the function returns the correct output
        self.assertEqual(HTML_INFO_SUCCESS, output_html_test == "")

    def test_convert_dict_to_proto(self):
        # test the function that converts a dictionary to a proto dict format
        print("Testing the convert_dict_to_proto function")

        # create a variable for the expected list
        input_dict = {'url1': 10, 'url2': 8, 'url3': 6, 'url4': 4}

        # get the output list from the function
        output_proto = self.client_crawler.convert_dict_to_proto(input_dict)
        print("HELPP 11111", output_proto)

        # check if the function returns the correct output
        self.assertEqual(TEST_PROTO_DICT, output_proto)

    def test_convert_list_to_proto(self):
        # test the function that converts a list to a proto list format
        print("Testing the convert_list_to_proto function")

        # create a variable for the expected list
        input_list = ["url1.com", "url2.com", "url3.com", "url4.com", "url5.com"]

        # get the output list from the function
        output_proto = self.client_crawler.convert_list_to_proto(input_list)
        print("HELPP", output_proto)

        # check if the function returns the correct output
        self.assertEqual(TEST_PROTO_LIST, output_proto)

    def test_compute_url_weight(self):
        # test the function that computes the weight of a url
        print("Testing the compute_url_weight function")

        # create test input variables
        test_player_count = 28
        test_url_date = 2023

        # get the weight from the client function
        output_weight = self.client_crawler.compute_url_weight(test_player_count, test_url_date)

        # check if the function returns the correct output
        self.assertEqual(TEST_URL_WEIGHT, output_weight)

    def test_compute_url_weight_no_players(self):
        # test the compute url weight on a url that has no player mentions
        print("Testing the compute_url_weight function with no player mentions")

        # create test input variables
        test_player_count = 0
        test_url_date = 2023

        # get the weight with a site that has no player mentions
        output_weight = self.client_crawler.compute_url_weight(test_player_count, test_url_date)

        # check if the function returns the correct output
        self.assertEqual(URL_WEIGHT_THRESHOLD, output_weight)

    def test_compute_url_weight_outdated(self):
        # test the compute url weight on a url that doesn't meet our date threshold
        print("Testing the compute_url_weight function with an outdated url")

        # create test input variables
        test_player_count = 28
        test_url_date = 2015

        # get the weight with a site that has no player mentions
        output_weight = self.client_crawler.compute_url_weight(test_player_count, test_url_date)

        # check if the function returns the correct output
        self.assertEqual(URL_WEIGHT_THRESHOLD, output_weight)

    def test_get_player_info_and_date(self):
        # test the function that scrapes an HTML input for player info and url date
        print("Testing the get_player_info_and_date function")

        # get the HTML from our test url
        test_html = self.client_crawler.get_url_info(TEST_URL)

        # call the function on the test HTML parse
        output_player_count_on_site, output_player_count, output_year = self.client_crawler.get_player_info_and_date(test_html)

        # check if the function returns the correct output
        self.assertEqual(TEST_PLAYER_COUNT_ON_SITE, bool(output_player_count_on_site))
        self.assertEqual(False, output_player_count == 0)
        self.assertEqual(True, output_year > 2022)

    def test_get_hyperlinks(self):
        # test the function that gets all the hyperlinks from a url and html
        print("Testing the get_hyperlinks function")

        # get the HTML from our test url
        test_html = self.client_crawler.get_url_info(TEST_URL)

        # call the function on the test url and test html
        output_hyperlinks = self.client_crawler.get_hyperlinks(TEST_URL, test_html)

        # check if the function returns the correct output
        self.assertEqual(True, bool(output_hyperlinks))

if __name__ == '__main__':
    # start the unit tests for the crawler client
    unittest.main()