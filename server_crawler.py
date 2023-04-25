
import grpc
from grpc._server import _Server
import scrape_pb2
import scrape_pb2_grpc
from keywords import *

import socket
import threading
from concurrent import futures
import re

import threading

mutex_unsent_messages = threading.Lock()
mutex_accounts = threading.Lock()
mutex_active_accounts = threading.Lock()


class CrawlerServer(scrape_pb2_grpc.CrawlServicer):
    # initialize the server for our  distributed web crawler
    def __init__(self):
        # create a variable to store the total number of sites we have crawled
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

    def process_hyperlinks(self, request, context):

        
# create a class for starting our Crawler server instance
class ServerRunner:
    # start an instance of a server
    def __init__(self):

        self.host = HOST
        self.port = PORT

        # TODO change this code from here through the kill function

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.chat_servicer = ChatServicer()

    # a function to start the server
    def start(self):
        new_route_guide_pb2_grpc.add_ChatServicer_to_server(
            self.chat_servicer, self.server)
        self.server.add_insecure_port(f"[::]:{self.port}")
        self.server.start()
        self.server.wait_for_termination()

    # a function to kill the server instance
    def kill(self):
        self.server.stop(grace=None)
        self.thread_pool.shutdown(wait=False)

if __name__ == '__main__':
    server = ServerRunner()
    server.start()