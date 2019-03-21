import psycopg2

from api_interface import ShillAPI

"""
Middle API that works with the DB obtained from an archive.

"""


class ShillDBAPI(ShillAPI):
    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, botometer_key):
        super().__init__(consumer_key, consumer_secret, access_token,
                         access_token_secret, botometer_key)

        # Establish connection
        self.connection = psycopg2.connect(user="postgres",
                                           password="pass123",
                                           host="127.0.0.1",
                                           port="5432",
                                           database="postgres")
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
            print(res[len(res) - 1])

        return res
