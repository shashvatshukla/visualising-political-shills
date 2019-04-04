import psycopg2

import consts
from metrics.api_interface import ShillAPI

"""
Middle API that works with the DB obtained from an archive.

"""


class ShillDBAPI(ShillAPI):
    @staticmethod
    def create_API():
        api_creds = consts.shill_api_creds
        return ShillDBAPI(api_creds["consumer_key"], api_creds["consumer_secret"],
                        api_creds["access_token"], api_creds["access_token_secret"],
                        api_creds["botometer_key"])
    
    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, botometer_key):
        super().__init__(consumer_key, consumer_secret, access_token,
                         access_token_secret, botometer_key)

        # Establish connection
        self.connection = psycopg2.connect(**consts.db_creds)
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()
        self.cursor.close()

    def get_tweets(self, start, end, words, with_rt=True):
        patterns = "|".join(words)
        query = f'''
                SELECT * FROM tweets
                WHERE text SIMILAR TO '%({patterns})%' AND
                      created_at BETWEEN '{start}'::timestamp AND 
                                         '{end}'::timestamp
                '''
        if not with_rt:
            query += " AND NOT rt_status = TRUE"

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        res = []
        for row in rows:
            res.append({
                'created_at': str(row[1]),
                'text': row[2],
                'usr': row[3],
                'twid': row[4],
                'rt_status': row[5]
            })

        return res

    def get_similar(self, cluster_size):
        query = f'''
                SELECT text, count(*) FROM tweets WHERE rt_status = FALSE 
                GROUP BY text HAVING count(*) > { cluster_size }
                '''

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        res = []
        for row in rows:
            res.append({
                'text': str(row[0]),
                'occurences': row[1],
            })

        return res
