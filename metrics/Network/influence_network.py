import psycopg2
import consts


connection = psycopg2.connect(**consts.db_creds)


def create_table():
    cursor = connection.cursor()
    create_table_1 = ''' CREATE TABLE influences
                         (id SERIAL PRIMARY KEY,
                          usr VARCHAR(22),
                          other_usr VARCHAR(22),
                          UNIQUE (usr, other_usr)); '''
    cursor.execute(create_table_1)
    connection.commit()


def get_retweets(usr):
    cursor = connection.cursor()
    select_retweets = """ SELECT *
                          FROM interactions
                          WHERE usr = %s AND interaction = 'retweet' """
    cursor.execute(select_retweets, [usr])
    interactions = []
    fetched = [None]
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        interactions.extend(fetched)
    return interactions


def is_strong(usr, other_usr, retweet_time, time_limit=None):
    cursor = connection.cursor()
    if time_limit:
        select_interactions = """ SELECT *
                                  FROM interactions
                                  WHERE usr = %s AND other_usr = %s AND
                                        ((%s BETWEEN time - INTERVAL %s AND time - INTERVAL '1 minute') OR
                                         (%s BETWEEN time + INTERVAL '1 minute' AND time + INTERVAL %s)); """
        cursor.execute(select_interactions, [usr, other_usr, retweet_time, time_limit, retweet_time, time_limit])
    else:
        select_interactions = """ SELECT *
                                  FROM interactions
                                  WHERE usr = %s AND other_usr = %s; """
        cursor.execute(select_interactions, [usr, other_usr])
    return len(cursor.fetchall()) > 0


def add_link(usr, other_usr):
    cursor = connection.cursor()
    # Check for existing link
    select_link = ''' SELECT * 
                      FROM influences
                      WHERE usr = %s AND other_usr = %s;'''
    cursor.execute(select_link, [usr, other_usr])
    if len(cursor.fetchall()) == 0:
        # Add new link
        insert_link = ''' INSERT INTO influences (usr, other_usr)
                          VALUES (%s, %s);'''
        cursor.execute(insert_link, [usr, other_usr])
        connection.commit()


def get_users_from_interactions():
    cursor = connection.cursor()
    select_users = """ SELECT DISTINCT usr
                       FROM interactions """
    cursor.execute(select_users)
    users = []
    fetched = [None]
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        users.extend(fetched)
    return users


def build_network():
    users = get_users_from_interactions()
    print(len(users))
    for i, user in enumerate(users):
        if i % 10000 == 0:
            print(i)
        retweets = get_retweets(user)
        for retweet in retweets:
            if is_strong(retweet[1], retweet[2], retweet[4]):
                add_link(retweet[1], retweet[2])


def get_edges(users):
    cursor = connection.cursor()
    select_connections = """ SELECT usr, other_usr
                             FROM interactions"""
    cursor.execute(select_connections)
    edges = []
    fetched = [None]
    while len(fetched) > 0:
        for record in fetched:
            if record[0] in users or record[1] in users:
                edges.append(record)
    return edges


build_network()
