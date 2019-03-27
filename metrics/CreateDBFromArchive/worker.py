import bz2
import os
import re

import psycopg2
from psycopg2 import sql
import json

import consts

class Worker:
    def __init__(self, words):
        self._words = words
        self.cnt = 0

    def json_to_db(self, files):
        try:
            # Establish connection
            connection = psycopg2.connect(**consts.db_creds)
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
            with open(decompressed_json, 'wb') as new_file, \
                 open(archive, 'rb') as file:
                decompressor = bz2.BZ2Decompressor()
                for data in iter(lambda: file.read(100 * 1024), b''):
                    new_file.write(decompressor.decompress(data))
            
            self._upload_to_db(decompressed_json, db_cursor)
            os.remove(decompressed_json)

    def _upload_to_db(self, json_file, db_cursor):
        with open(json_file) as file:
            text = file.read()
            for json_object in text.split('\n')[:-1]:
                tweet = json.loads(json_object)
                
                # Check if the object is really a Tweet
                if tweet.get('lang') == None or tweet.get("text") == None or tweet.get("user") == None:
                    continue

                if tweet['lang'] == "en" and \
                   (len(self._words) == 0 or re.search('|'.join(self._words), tweet['text'])):
                    splitted = tweet["created_at"].split(' ')
                    timestamp = splitted[5] + "-" + \
                                consts.abbr_to_number[splitted[1]] + "-" + \
                                splitted[2] + " " + \
                                splitted[3]

                    if tweet["text"][0:2] == 'RT':
                        rt_status = "TRUE"
                    else:
                        rt_status = "FALSE"

                    add_tweet_query = sql.SQL("INSERT INTO tweets" \
                                      "(created_at, text, usr, twid, rt_status)" \
                                      "VALUES (TIMESTAMP %s, %s, %s, %s, %s)")
                    db_cursor.execute(add_tweet_query, (timestamp, tweet["text"], str(tweet["user"]["id"]), str(tweet["id"]), rt_status))
