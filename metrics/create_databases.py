import psycopg2
import consts

connection = psycopg2.connect(**consts.db_creds)


def create_dbs():
    """
    Creates the databases for storing user data.
    :return:

    """
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
    create_table_2 = ''' CREATE TABLE user_bot_status
                         (usr_id VARCHAR(22) PRIMARY KEY,
                         is_bot BOOLEAN); '''
    create_table_3 = ''' CREATE TABLE failed_users
                         (usr_id VARCHAR(22) PRIMARY KEY,
                          error_msg VARCHAR(200)); '''
    create_table_4 = ''' CREATE TABLE interactions
                        (id SERIAL PRIMARY KEY,
                         usr VARCHAR(22),
                         other_usr VARCHAR(22),
                         interaction VARCHAR(22),
                         time TIMESTAMP NOT NULL,
                         topic_code VARCHAR(22)),
                         twid VARCHAR (255); '''
    create_table_5 = ''' CREATE TABLE topics
                         (id SERIAL PRIMARY KEY,
                          topic_code VARCHAR(22),
                          hashtag VARCHAR(200)); '''
    create_table_6 = ''' CREATE TABLE influences
                         (id SERIAL PRIMARY KEY,
                          usr VARCHAR(22),
                          other_usr VARCHAR(22),
                          UNIQUE (usr, other_usr)); '''
    try:
        cursor.execute(create_table_1)
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute("CREATE INDEX usr_id_index ON user_metadata (usr_id)")
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute("CREATE INDEX screen_name_index ON user_metadata (screen_name)")
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute("CREATE INDEX emp_up_name ON user_metadata (UPPER(screen_name))")
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute(create_table_2)
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute(create_table_3)
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute(create_table_4)
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute(create_table_5)
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    try:
        cursor.execute(create_table_6)
        connection.commit()
    except psycopg2.ProgrammingError:
        connection.rollback()
    connection.commit()
