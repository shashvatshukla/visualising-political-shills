import consts
import psycopg2


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
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    insert_metadata = ''' INSERT INTO user_metadata
                          (usr_id, screen_name, no_statuses, no_followers, no_friends, no_favourites,
                           no_listed, default_profile, geo_enabled, custom_bg_img,
                           verified, protected)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s); '''
    cursor.execute(insert_metadata, [str(usr_id), str(screen_name)] + [str(value) for value in metadata])
    if is_bot is not None:
        insert_bot_status = '''INSERT INTO user_bot_status (usr_id, is_bot)
                               VALUES (%s, %s)'''
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
