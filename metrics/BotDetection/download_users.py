import tweepy
import consts
import psycopg2

from metrics.api_for_search import ShillSearchAPI
from metrics.api_for_db import ShillDBAPI

"""
Downloads the metadata of Twitter users, for training the logistic regression on.
"""

def create_db():
    """
    Creates the databases for storing user data.
    :return:

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    create_table_1 = ''' CREATE TABLE users
                         (usr_id VARCHAR(22) PRIMARY KEY,
                          no_statuses INTEGER,
                          no_followers INTEGER,
                          no_friends INTEGER,
                          no_favourites INTEGER,
                          no_listed INTEGER,
                          default_profile BOOLEAN,
                          geo_enabled BOOLEAN,
                          custom_bg_img BOOLEAN,
                          verified BOOLEAN,
                          protected BOOLEAN,
                          is_bot BOOLEAN); '''
    cursor.execute(create_table_1)
    create_table_2 = ''' CREATE TABLE failed_users
                         (usr_id VARCHAR(22) PRIMARY KEY,
                          error_msg VARCHAR(200)); '''
    cursor.execute(create_table_2)
    connection.commit()


def add_to_db(usr_id, metadata, is_bot):
    """
    Adds the metadata of a user, along with the botometer result, to the database.

    :param usr_id: The Twitter user id
    :param metadata: The users metadata
    :param is_bot: The botometer result for the user

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    insert = ''' INSERT INTO users
                 (usr_id, no_statuses, no_followers, no_friends, no_favourites,
                  no_listed, default_profile, geo_enabled, custom_bg_img,
                  verified, protected, is_bot)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s); '''
    cursor.execute(insert, [str(usr_id)] + [str(value) for value in metadata] + [str(is_bot)])
    connection.commit()

def get_record_from_dict(metadata):
    """
    Converts a metadata dictionary to a list, in the correct order to be added to the database by add_to_db.

    :param metadata: The metadata dictionary
    :return: A metadata list

    """
    return [metadata["no_statuses"], metadata["no_followers"], metadata["no_friends"],
            metadata["no_favourites"], metadata["no_listed"], metadata["default_profile"],
            metadata["geo_enabled"], metadata["custom_bg_img"], metadata["verified"],
            metadata["protected"]]


# Test if the user with user id 'user' exists in the users table
# failed: True to check for the id in the failed_users table
def does_user_exist(user, failed=True):
    """
    Checks if a user currently exists with the databases users and failed_users.

    :param user: The twitter user id
    :param failed: Boolean, True to check both databases, False to check only users
    :return: Boolean, True if the user id is found

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    exists = ''' SELECT usr_id from users
                 WHERE usr_id = %s;'''
    cursor.execute(exists, [user])
    exists_in_users = len(cursor.fetchall()) > 0
    if failed:
        failed_exists = ''' SELECT usr_id from failed_users
                            WHERE usr_id = %s;'''
        cursor.execute(failed_exists, [user])
        exists_in_failed = len(cursor.fetchall()) > 0
        return exists_in_users or exists_in_failed
    else:
        return exists_in_users


def fail_user(user, error_msg):
    """
    Adds a user to the failed_users database.

    :param user: The twitter user id
    :param error_msg: An error message

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    insert = ''' INSERT INTO failed_users
                 (usr_id, error_msg)
                 VALUES (%s, %s); '''
    cursor.execute(insert, [user, str(error_msg)])
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
        if does_user_exist(user):
            continue
        data = None
        is_bot = None
        try:
            which = False
            is_bot = search_api.is_bot(user, False)
            which = True
            data = get_record_from_dict(search_api.get_metadata(user))
        except tweepy.error.TweepError as tweep:
            print('')
            error_msg = ("Botometer Failure: " if which else "Metadata Failure: ") + str(tweep)
            print(error_msg)
            fail_user(user, error_msg)
        except psycopg2.IntegrityError as sqlErr:
            print(sqlErr)
        else:
            print('', end='\r')
            print(count, end='')
            if count == amount:
                break
            count += 1
            add_to_db(user, data, is_bot)


start = "2017-11-01 06:00:37"
end = "2017-12-31 07:02:14"

find_users(start, end, [], 10000)
