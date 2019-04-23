import psycopg2
import consts
from metrics.api_for_search import ShillSearchAPI


def create_db():
    """
    Creates the databases for user interactions

    :INTERACTIONS:
    :usr: The id of the user that performed the interaction
    :other_usr: The id of the user that was interacted with
    :interaction: The type of interaction (retweet, mention, reply)
    :topic: Name of the topic for which the interaction belongs to

    :TOPICS:
    :topic_code: The code for the topic
    :hashtag: A hashtag that belongs to the topic

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    create_table_1 = ''' CREATE TABLE interactions
                         (id SERIAL PRIMARY KEY,
                          usr VARCHAR(22),
                          other_usr VARCHAR(22),
                          interaction VARCHAR(22),
                          topic_code VARCHAR(22)); '''
    cursor.execute(create_table_1)
    create_table_2 = ''' CREATE TABLE topics
                         (id SERIAL PRIMARY KEY,
                          topic_code VARCHAR(22),
                          hashtag VARCHAR(200)); '''
    cursor.execute(create_table_2)
    connection.commit()


def add_interaction(usr, other_usr, interaction):
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    insert = ''' INSERT INTO interactions
                     (usr, other_usr, interaction, topic_code)
                     VALUES (%s, %s, %s, 'test'); '''
    cursor.execute(insert, [usr, other_usr, interaction])
    connection.commit()


api = ShillSearchAPI.create_API()


def add_lookup(cache, usr, screen_name, interaction):
    cache.append((usr, screen_name, interaction))
    if len(cache) == 100:
        screen_names = [i[1] for i in cache]
        ids = api.get_ids(screen_names)
        for i in range(len(ids)):
            if ids[i]:
                add_interaction(cache[i][0], ids[i], cache[i][2])
        cache.clear()
        print(completed)


completed = 0


def load_interactions(start):
    global completed
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    tweets_query = ''' SELECT * FROM tweets; '''
    cursor.execute(tweets_query)
    tweets = [None]
    previous = 0
    while len(tweets) > 0:
        tweets = cursor.fetchall()
        cache = []
        for i in range(start, len(tweets)):
            tweet = tweets[i]
            users = tweet[2].split(' ')
            if tweet[6]:
                usr = tweet[3]
                retweet_len = len(tweet[2].split(":")[0])
                users = tweet[2][retweet_len:].split(' ')
                other_usr = tweet[2].split(":")[0][4:]
                add_lookup(cache, usr, other_usr, "retweet")
            elif tweet[2][0] == '@':
                reply_count = 0  # The number of users the tweet is replying to
                for i in range(len(users)):
                    if len(users[i]) > 0 and users[i][0] != '@':
                        reply_count = i
                        break
                for other_usr in users[:reply_count]:
                    add_lookup(cache, tweet[3], other_usr[1:], "reply")
                users = users[reply_count:]
            for other_usr in users:
                if len(other_usr) > 0 and other_usr[0] == '@':
                    add_lookup(cache, tweet[3], other_usr[1:], "mention")
            completed = previous + i + 1
        previous += len(tweets)


def load_interactions_continue_on_error(start):
    while True:
        try:
            load_interactions(start)
        except:
            print("ERROR")


load_interactions_continue_on_error(0)
print("Checked: ", completed)
