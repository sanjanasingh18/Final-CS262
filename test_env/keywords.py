# set our PORT variable
PORT = 8889

# change the HOST variable according to the hostname of your computer
HOST = "0.0.0.0"  # "dhcp-10-250-239-247.harvard.edu" # sanj
# HOST = "dhcp-10-250-168-147.harvard.edu" # soph
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

# variable for a restore URL value
RESTORE_URL = "https://www.espn.com/tennis/dailyResults"

# variable for test success
SUCCESS = True

# variable for player counter restored
PLAYER_COUNTER_RESTORED = True

# variable for URL queue non empty
URL_QUEUE_NONEMPTY = False

# variable for if HTML is non empty
HTML_INFO_SUCCESS = False

# variable for a test player dictionary
TEST_PLAYER_DICT = {'swiatek': 63, 'sabalenka': 52, 'pera': 39, 'kvitova': 35,
                    'halep': 31, 'pegula': 21, 'garcia': 17, 'rybakina': 17,
                    'pliskova': 17, 'keys': 17, 'stephens': 12, 'sakkari': 11,
                    'kudermetova': 11, 'zhang': 10, 'jabeur': 9, 'gauff': 9,
                    'bencic': 9, 'krejcikova': 9, 'cirstea': 9,
                    'samsonova': 8, 'andreescu': 8, 'siniakova': 8,
                    'kasatkina': 7, 'azarenka': 6, 'ostapenko': 5, 'mertens': 5,
                    'badosa': 4, 'alexandrova': 3, 'teichmann': 3, 'rogers': 3,
                    'zhu': 3, 'begu': 2, 'collins': 2, 'vekic': 1, 'potapova': 1,
                    'kalinina': 1, 'anisimova': 1, 'sasnovich': 1, 'fernandez': 1}

# variable for a test proto dict value
TEST_PROTO_DICT = PAIRDELIM + "url1" + KEYDELIM + "10" + PAIRDELIM + "url2" + KEYDELIM + "8" + PAIRDELIM + "url3" + KEYDELIM + "6" + PAIRDELIM + "url4" + KEYDELIM + "4" + PAIRDELIM

# variable for a test proto list value
TEST_PROTO_LIST = LISTDELIM + "url1.com" + LISTDELIM + "url2.com" + LISTDELIM + "url3.com" + LISTDELIM + "url4.com" + LISTDELIM + "url5.com" + LISTDELIM

# variable for testing the compute URL weight function
TEST_URL_WEIGHT = -28

# variable for a test URL
TEST_URL = "https://www.wtatennis.com/"

# variable for player count on test url
TEST_PLAYER_COUNT_ON_SITE = True
