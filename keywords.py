# Set our PORT variable
PORT = 8888

# change the HOST variable according to the hostname of your computer
HOST = "dhcp-10-250-239-247.harvard.edu" # sanj
#HOST = "dhcp-10-250-168-147.harvard.edu" # soph
ADDRESS = (HOST, PORT)

# constant weight variable for client initialization
CLIENT_BYPASS = 309514

# constant variable for error getting URL from priority queue
PRIORITY_QUEUE_EMPTY = "PRIORITY_QUEUE_EMPTY"

# variable for our key delimiter
KEYDELIM = "we_love_cs262"

# variable for our pair delimiter
PAIRDELIM = "we_really_love_cs262"

# variable for our list delimiter
LISTDELIM = "we_will_miss_cs262"

# threshold for sites to add to queue
URL_WEIGHT_THRESHOLD = 15

# list of bad url paths
BAD_URL_PATHS = ["apps", "./"]
