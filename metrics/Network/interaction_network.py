import psycopg2
import consts
import re

from metrics.api_for_search import ShillSearchAPI
from metrics.BotDetection.helper_functions import get_record_from_dict, add_to_db

connection = psycopg2.connect(**consts.db_creds)


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
    cursor = connection.cursor()
    create_table_1 = ''' CREATE TABLE interactions
                         (id SERIAL PRIMARY KEY,
                          usr VARCHAR(22),
                          other_usr VARCHAR(22),
                          interaction VARCHAR(22),
                          time TIMESTAMP NOT NULL,
                          topic_code VARCHAR(22)),
                          twid VARCHAR (255); '''
    cursor.execute(create_table_1)
    create_table_2 = ''' CREATE TABLE topics
                         (id SERIAL PRIMARY KEY,
                          topic_code VARCHAR(22),
                          hashtag VARCHAR(200)); '''
    cursor.execute(create_table_2)
    connection.commit()


def add_interaction(usr, other_usr, interaction, time, twid):
    cursor = connection.cursor()
    insert = ''' INSERT INTO interactions
                     (usr, other_usr, interaction, time, topic_code, twid)
                     VALUES (%s, %s, %s, %s, 'test'); '''
    cursor.execute(insert, [usr, other_usr, interaction, time, twid])
    connection.commit()


api = ShillSearchAPI.create_API()


def add_lookup(cache, usr, screen_name, interaction, time, twid):
    cursor = connection.cursor()
    find_user = ''' SELECT * 
                    FROM user_metadata
                    WHERE UPPER(screen_name) = %s '''
    cursor.execute(find_user, [screen_name.upper()])
    connection.commit()

    user_data = cursor.fetchall()
    if len(user_data) > 0:
        add_interaction(usr, user_data[0][0], interaction, time, twid)
    else:
        cache.append((usr, screen_name, interaction, time, twid))
        if len(cache) == 100:
            screen_names = [i[1] for i in cache]
            user_data = api.get_batch_metadata(screen_names)
            for i, user in enumerate(user_data):
                if user:
                    add_interaction(cache[i][0], user["usr_id"], cache[i][2], cache[i][3], cache[i][4])
                    add_to_db(user["usr_id"], user["screen_name"], get_record_from_dict(user))
            cache.clear()
            print(completed)


completed = 0


def load_interactions(start):
    global completed
    cursor = connection.cursor()
    tweets_query = ''' SELECT * FROM tweets; '''
    cursor.execute(tweets_query)
    tweets = [None]
    previous = 0
    while len(tweets) > 0:
        tweets = cursor.fetchall()
        cache = []
        if previous + len(tweets) < start:
            previous += len(tweets)
            continue
        for i in range(start, len(tweets)):
            if previous + i < start:
                continue
            tweet = list(tweets[i])
            tweet[2] = re.sub('[^0-9a-zA-Z_:@]+', ' ', tweet[2])
            users = re.split(' :', tweet[2])
            if tweet[6]:
                usr = tweet[3]
                retweet_len = len(tweet[2].split(":")[0])
                users = re.split(' :', tweet[2][retweet_len:])
                other_usr = tweet[2].split(":")[0][4:]
                add_lookup(cache, usr, other_usr, "retweet", tweet[1], tweet[4])
            elif tweet[2][0] == '@':
                reply_count = 0  # The number of users the tweet is replying to
                for z in range(len(users)):
                    if len(users[z]) > 0 and users[z][0] != '@':
                        reply_count = z
                        break
                for other_usr in users[:reply_count]:
                    add_lookup(cache, tweet[3], other_usr[1:], "reply", tweet[1], tweet[4])
                users = users[reply_count:]
            for other_usr in users:
                if len(other_usr) > 0 and other_usr[0] == '@':
                    add_lookup(cache, tweet[3], other_usr[1:], "mention", tweet[1], tweet[4])
            completed = previous + i + 1
        previous += len(tweets)


def load_interactions_continue_on_error(start):
    global completed
    completed = start
    while True:
        try:
            load_interactions(completed)
        except Exception as e:
            print(e)


load_interactions_continue_on_error(1117383)
