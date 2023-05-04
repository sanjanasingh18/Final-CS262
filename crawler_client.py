import grpc
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
from bs4 import BeautifulSoup
from queue import PriorityQueue
from datetime import datetime
from collections import Counter
import pandas as pd


screening_years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018',
                   '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030']


class CrawlerClient:
    def __init__(self):

        self.connection = None
        try:
            self.connection = scrape_pb2_grpc.CrawlStub(
                grpc.insecure_channel(f"{HOST}:{PORT}"))
        except Exception as e:
            print(e)
            print("Could not connect to crawler server.")
            return

        # Get the list of top 50 WTA players
        data = pd.read_csv('player_names.txt', delimiter="\t", header=0).values
        self.player_list = np.reshape(data, -1)

    def get_hyperlinks(self, url, html):
        list_of_hyperlinks = []
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            # print("PATH", path)
            if path and path.startswith('/'):
                # print("filtered path", path)
                path = urljoin(url, path)
            if path and not path.startswith('#') and not path.startswith("./") and path not in BAD_URL_PATHS:
                list_of_hyperlinks.append(path)
        return list_of_hyperlinks

    def get_player_info_and_date(self, html):
        # print("getplaya", html)
        soup = BeautifulSoup(html, 'html.parser')
        html_text = soup.get_text().lower()
        # print('orig', html_text)
        # compute the counts of each of the years
        year_counts = []
        for year in screening_years:
            year_counts.append(html_text.count(year))
        non_zero_arr = np.nonzero(year_counts)[0]

        # if there is a year mentioned, compute the max year
        if non_zero_arr.size > 0:
            # find the latest year where the count isn't 0
            max_year = screening_years[max(non_zero_arr)]
        else:
            max_year = 2010
        # print('YEARCOUNTS', year_counts, max_year)

        # make the player count dictionary for each player mentioned and set that dic to be the dic in our data object
        # for each of the top 50 players that we want to search for
        # read the text file to find the latest year mentioned and the players

        player_count_on_site = {}
        player_count = 0
        for player in self.player_list:
            count_from_cur_site = html_text.count(player)
            if count_from_cur_site > 0:
                # add the count to the dict
                # at the end, update the count
                player_count_on_site[player] = count_from_cur_site
                player_count += 1

            # cur_count = self.player_popularity[player]
            # self.player_popularity[player] = count_from_cur_site + cur_count
            # if count_from_cur_site > 0:
            #     player_count += 1
        # self.player_popularity.update(player_count_on_site)

        # return the count of the players mentioned and the maximum year mentioned
        # print('PLAYERCOUNT', player_count)
        # print('popularity dict', self.player_popularity)
        return player_count_on_site, player_count, int(max_year)

    def compute_url_weight(self, player_count, date):
        # the logic for computing the url weight
        if int(date) < 2018 or player_count == 0:
            # if the URL is outdated, return threshold so it is never
            # added to the queue as this will be filtered later
            return URL_WEIGHT_THRESHOLD 
        url_weight = - player_count + (2023 - date)
        print("URL weight computation", player_count, date, url_weight)
        return url_weight

    def get_url_info(self, url):
        # requests_text = requests.get(url).text
        # url_weight = self.compute_url_weight(requests_text)
        return requests.get(url).text
    
    # function for converting our player dicitonary to a proto value
    def convert_dict_to_proto(self, dict):
        output = str(PAIRDELIM)
        for key, val in dict.items():
            output += str(key) + str(KEYDELIM)+ str(val) + str(PAIRDELIM)

        return output
    
        
    # function for converting our url list to a proto value
    def convert_list_to_proto(self, list):
        # convert list to a set to get rid of duplicate hyperlinks
        set_list = set(list)

        output = str(LISTDELIM)
        for url in set_list:
            output += str(url) + str(LISTDELIM)

        return output

    def run_client(self):
        # want to send to server that you have joined so you receive
        # a URL to scrape
        # populate request data object
        # players_freq_var = scrape.Dictionary()
        # entry = scrape.Pair()
        # entry.key = "1"
        # entry.value = "one"
        # players_freq_var.extend(entry)

        # hyperlinks_var = scrape.List()
        request = scrape.Data()
        request.weight = CLIENT_BYPASS
        # request.players_freq.CopyFrom(players_freq_var)
        # request.hyperlinks.CopyFrom(hyperlinks_var)

        next_url = self.connection.process_hyperlinks(request).message


        while True:
            while next_url == PRIORITY_QUEUE_EMPTY:
                # populate request data object
                request = scrape.Data(weight=CLIENT_BYPASS)
                next_url = self.connection.process_hyperlinks(request).message

            print("Next URL to scrape:", next_url)
            next_html = self.get_url_info(next_url)
            player_count_on_site, player_count, max_year = self.get_player_info_and_date(
                next_html)

            weight = self.compute_url_weight(player_count, max_year)

            new_hyperlinks = self.get_hyperlinks(next_url, next_html)


            print("Stats from this site:", player_count, max_year, weight, player_count_on_site)
            players_freq = self.convert_dict_to_proto(player_count_on_site)
            hyperlinks = self.convert_list_to_proto(new_hyperlinks)

            request = scrape.Data(
                weight=int(weight), 
                players_freq=players_freq, 
                hyperlinks=hyperlinks)
            
            next_url = self.connection.process_hyperlinks(request).message


if __name__ == '__main__':
    client = CrawlerClient()
    client.run_client()
