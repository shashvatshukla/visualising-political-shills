import consts
import psycopg2

connection = psycopg2.connect(**consts.db_creds)


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


def add_to_db(usr_id, screen_name, metadata, is_bot=None):
    """
    Adds the metadata of a user, along with the botometer result, to the database.

    :param usr_id: The Twitter user id
    :param screen_name: The Twitter user screen name
    :param metadata: The users metadata
    :param is_bot: The botometer result for the user, leave as None is the result is unknown

    """
    cursor = connection.cursor()
    if not does_user_exist(usr_id, metadata=True):
        insert_metadata = ''' INSERT INTO user_metadata
                              (usr_id, screen_name, no_statuses, no_followers, no_friends, no_favourites,
                               no_listed, default_profile, geo_enabled, custom_bg_img,
                               verified, protected)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s); '''
        cursor.execute(insert_metadata, [str(usr_id), str(screen_name)] + [str(value) for value in metadata])
    if is_bot is not None:
        if not does_user_exist(usr_id, is_bot=True):
            insert_bot_status = '''INSERT INTO user_bot_status (usr_id, is_bot)
                               VALUES (%s, %s)'''
            cursor.execute(insert_bot_status, [str(usr_id), str(is_bot)])
    connection.commit()

    
# Test if the user with user id 'user' exists in certain tables
def does_user_exist(user, metadata=False, is_bot=False, failed=False):
    """
    Checks if a user currently exists with the databases users and failed_users.

    :param user: The twitter user id
    :param metadata: Boolean, True to check if the user metadata is known
    :param is_bot: Boolean, True to check if bot status for user is known
    :param failed: Boolean, True to check if user has failed before
    :return: Boolean, True if the user id is found

    """
    cursor = connection.cursor()
    if metadata:
        exists = ''' SELECT usr_id from user_metadata
                   WHERE usr_id = %s;'''
        cursor.execute(exists, [user])
        if len(cursor.fetchall()) > 0:
            return True
    if failed:
        failed_exists = ''' SELECT usr_id from failed_users
                            WHERE usr_id = %s;'''
        cursor.execute(failed_exists, [user])
        if len(cursor.fetchall()) > 0:
            return True
    if is_bot:
        exists = ''' SELECT usr_id from user_bot_status
                           WHERE usr_id = %s;'''
        cursor.execute(exists, [user])
        if len(cursor.fetchall()) > 0:
            return True


def fail_user(user, error_msg):
    """
    Adds a user to the failed_users database.

    :param user: The twitter user id
    :param error_msg: An error message

    """
    cursor = connection.cursor()
    insert = ''' INSERT INTO failed_users
                 (usr_id, error_msg)
                 VALUES (%s, %s); '''
    cursor.execute(insert, [user, str(error_msg)])
    connection.commit()
