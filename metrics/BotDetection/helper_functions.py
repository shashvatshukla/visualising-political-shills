import tweepy
import consts
import psycopg2

from metrics.api_for_search import ShillSearchAPI
from metrics.api_for_db import ShillDBAPI

def add_to_db(usr_id, screen_name, metadata, is_bot):
    """
    Adds the metadata of a user, along with the botometer result, to the database.

    :param usr_id: The Twitter user id
    :param metadata: The users metadata
    :param is_bot: The botometer result for the user

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    insert_metadata = ''' INSERT INTO user_metadata
                          (usr_id, screen_name, no_statuses, no_followers, no_friends, no_favourites,
                           no_listed, default_profile, geo_enabled, custom_bg_img,
                           verified, protected)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s); '''
    insert_bot_status = '''INSERT INTO user_bot_status (usr_id, is_bot)
                           VALUES (%s, %s)'''
    cursor.execute(insert_metadata, [str(usr_id), str(screen_name)] + [str(value) for value in metadata])
    cursor.execute(insert_bot_status, [str(usr_id), str(is_bot)])
    connection.commit()

    
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
