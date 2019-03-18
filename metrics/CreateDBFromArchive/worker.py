import bz2
import os
import re

import json

import psycopg2

# -------------------------
abbr_to_number = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}
# -------------------------


def get_password():
    with open("../../keys.json") as keys:
        data = json.load(keys)
        return data["database_password"]


class Worker:
    def __init__(self, words):
        self._words = words
        self.cnt = 0
        self._db_creds = {
            "user": "postgres",
            "password": get_password(),
            "host": "127.0.0.1",
            "port": "5432",
            "database": "postgres"
        }

    def json_to_db(self, files):
        try:
            # Establish connection
            connection = psycopg2.connect(user="postgres",
                                          password=get_password(),
                                          host="127.0.0.1",
                                          port="5432",
                                          database="postgres")
            cursor = connection.cursor()

            self._deal_with_archives(files, cursor)
        except psycopg2.Error as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            # Batch commit all inserts
            connection.commit()

            # Close connection
            if connection:
                cursor.close()
                connection.close()

    def _deal_with_archives(self, files, db_cursor):
        for archive in files:
            decompressed_json = archive + '.json'
            with open(decompressed_json, 'wb') as new_file, open(archive, 'rb') as file:
                decompressor = bz2.BZ2Decompressor()
                for data in iter(lambda: file.read(100 * 1024), b''):
                    new_file.write(decompressor.decompress(data))

            self._upload_to_db(decompressed_json, db_cursor)
            os.remove(decompressed_json)

    def _upload_to_db(self, json_file, db_cursor):
        def escape_quote(to_escape):
            return "\'" + to_escape + "\'"

        tweet_pattern = "{\"created_at\":\"(?P<created_at>.*?)\"," \
                        "\"id\":(?P<twid>\d+).+" \
                        "\"text\":\"(?P<text>.*?)\".+" \
                        "\"user\":{\"id\":(?P<usr>\d+).+}.+" \
                        "\"lang\":\"(?P<lang>.*?)\",\"timestamp_ms\":.*}"

        with open(json_file) as file:
            text = file.read()
            for match in re.finditer(tweet_pattern, text):
                match_dict = match.groupdict()
                if match_dict['lang'] == "en" and re.search('|'.join(self._words), match_dict['text']):
                    splitted = match["created_at"].split(' ')
                    timestamp = splitted[5] + "-" + abbr_to_number[splitted[1]] + "-" + splitted[2] + " " + splitted[3]
                    add_tweet_query = "INSERT INTO tweets (created_at, text, usr, twid) " \
                                      "VALUES (TIMESTAMP " + \
                                               escape_quote(timestamp) + "," + \
                                               escape_quote(match_dict["text"].replace('\'', '\'\'')) + "," + \
                                               escape_quote(match_dict["usr"]) + "," + \
                                               escape_quote(match_dict["twid"]) + ")"
                    db_cursor.execute(add_tweet_query)
