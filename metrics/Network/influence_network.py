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


