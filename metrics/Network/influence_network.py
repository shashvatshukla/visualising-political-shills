import psycopg2
import consts
from metrics.Network.partition import *

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


def build_network():
    build_network_sql = """INSERT INTO influences (usr, other_usr)
                           (SELECT usr, other_usr
                            FROM interactions
                            GROUP BY usr, other_usr
                            HAVING COUNT(id)>=1)
                           INTERSECT
                           (SELECT usr, other_usr
                            FROM interactions
                            WHERE interactions.interaction = 'retweet'
                            GROUP BY usr, other_usr
                            HAVING COUNT(id)>=1)"""

    build_network_sql_1 = """INSERT INTO influences (usr, other_usr)
                             SELECT usr, other_usr
                             FROM interactions as inter1
                             INNER JOIN interactions as inter2
                             ON ((%s BETWEEN time - INTERVAL %s AND time - INTERVAL '1 minute') OR
                                (%s BETWEEN time + INTERVAL '1 minute' AND time + INTERVAL %s)) AND
                                inter1.usr = inter2.usr AND inter1.other_usr = inter2.other_usr
                             GROUP BY usr, other_usr"""

    cursor = connection.cursor()
    cursor.execute(build_network_sql)
    connection.commit()


def get_edges(users):
    user_dict = {}
    for i in users:
        user_dict[i] = 1
    cursor = connection.cursor()
    drop_old = "DELETE FROM temp"
    connection.commit()
    try:
        cursor.execute(drop_old)
    except psycopg2.ProgrammingError:
        pass
    insert = """INSERT INTO temp (usr)
                 VALUES (%s);"""
    for user in user_dict:
        cursor.execute(insert, [user])
    connection.commit()
    select = """ SELECT influences.usr, influences.other_usr
                 FROM influences
                 INNER JOIN temp as t1
                 ON t1.usr = influences.usr AND influences.usr != influences.other_usr
                 INNER JOIN temp as t2
                 ON t2.usr = influences.other_usr"""
    cursor.execute(select)
    edges = []
    fetched = [None]
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        edges.extend(fetched)
    cursor.execute(drop_old)
    connection.commit()
    return edges


def sub_network(keywords):
    users = get_users(keywords)
    edges = get_edges(users)
    group1, group2 = partition_groups(users)
    partition = {}
    for i in group1:
        partition[i] = 0
    for i in group2:
        partition[i] = 1
    return users, partition, edges

