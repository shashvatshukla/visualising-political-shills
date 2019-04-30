import tweepy
import consts
import psycopg2

from metrics.api_for_search import ShillSearchAPI
from metrics.api_for_db import ShillDBAPI
from metrics.BotDetection.helper_functions import add_to_db, does_user_exist, get_record_from_dict, fail_user

"""
Downloads the metadata of Twitter users, for training the logistic regression on.
"""

connection = psycopg2.connect(**consts.db_creds)


def create_db():
    """
    Creates the databases for storing user data.
    :return:

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    create_table_1 = ''' CREATE TABLE user_metadata
                         (usr_id VARCHAR(22) PRIMARY KEY,
                          screen_name VARCHAR(55),
                          no_statuses INTEGER,
                          no_followers INTEGER,
                          no_friends INTEGER,
                          no_favourites INTEGER,
                          no_listed INTEGER,
                          default_profile BOOLEAN,
                          geo_enabled BOOLEAN,
                          custom_bg_img BOOLEAN,
                          verified BOOLEAN,
                          protected BOOLEAN); '''
    cursor.execute(create_table_1)
    create_table_2 = ''' CREATE TABLE user_bot_status
                         (usr_id VARCHAR(22) PRIMARY KEY,
                         is_bot BOOLEAN); '''
    cursor.execute(create_table_2)
    create_table_3 = ''' CREATE TABLE failed_users
                         (usr_id VARCHAR(22) PRIMARY KEY,
                          error_msg VARCHAR(200)); '''
    cursor.execute(create_table_3)
    connection.commit()


def find_users(start, end, words, amount):
    """
    Searches the tweets database, then fetches the metadata and botometer result for the owners of the tweets, then
    adds them to the users database, or the failed_users database if an error is encountered.

    :param start: The start timestamp
    :param end: The end timestamp
    :param words: Keywords to filter Tweets
    :param amount: The maximum amount of users to download

    """
    search_api = ShillSearchAPI.create_API()
    db_api = ShillDBAPI.create_API()
    tweets = db_api.get_tweets(start, end, words)
    users = set()
    for tweet in tweets:
        users.add(tweet["usr"])
    print("Loaded users from DB")
    count = 0
    print(len(users))
    for user in list(users):
        if does_user_exist(user, is_bot=True, failed=True):
            continue
        data = None
        is_bot = None
        try:
            which = False
            is_bot = search_api.is_bot(user, False)
            which = True
            metadata_dict = search_api.get_metadata(user)
            data = get_record_from_dict(metadata_dict)
        except tweepy.error.TweepError as tweep:
            print('')
            error_msg = ("Botometer Failure: " if which else "Metadata Failure: ") + str(tweep)
            print(error_msg)
            fail_user(user, error_msg)
        except psycopg2.IntegrityError as sqlErr:
            print(sqlErr)
        else:
            print('', end='\n')
            print(count, end='')
            if count == amount:
                break
            count += 1
            add_to_db(user, metadata_dict["screen_name"], data, is_bot)


start = "2017-11-01 06:00:37"
end = "2017-12-31 07:02:14"

find_users(start, end, [], 10000)
