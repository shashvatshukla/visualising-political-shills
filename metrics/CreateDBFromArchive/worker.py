import bz2
import os
import re
import hashlib

import psycopg2
from psycopg2 import sql
import json

import consts

class Worker:
    def __init__(self, words, lock):
        self._words = words
        self.lock = lock
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
            self.lock.acquire()
            # Batch commit all inserts
            connection.commit()

            # Close connection
            if connection:
                cursor.close()
                connection.close()
            self.lock.release()

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

                    text_hash = str(hashlib.md5(tweet["text"].encode('utf-8')).
                                    hexdigest())

                    retweet_text = None
                    if "retweeted_status" in tweet:
                        rt_status = "TRUE"
                        if tweet["retweeted_status"]["truncated"]:
                            retweet_text = tweet["retweeted_status"]["extended_tweet"]["full_text"]
                        else:
                            retweet_text = tweet["retweeted_status"]["text"]
                    else:
                        rt_status = "FALSE"

                    if tweet["truncated"]:
                        text = tweet["extended_tweet"]["full_text"]
                    else:
                        text = tweet["text"]

                    add_tweet_query = sql.SQL("""INSERT INTO tweets
                                                 (created_at, text, usr, twid, md5_hash, rt_status, screen_name, retweet_text) 
                                                 VALUES (TIMESTAMP %s, %s, %s, %s, %s, %s, %s, %s)""")
                    db_cursor.execute(add_tweet_query, (timestamp,
                                                        tweet["text"],
                                                        str(tweet["user"]["id"]),
                                                        str(tweet["id"]),
                                                        text_hash,
                                                        rt_status,
                                                        tweet["user"]["screen_name"],
                                                        retweet_text))

                    add_user_metadata = """ INSERT INTO user_metadata
                                            (usr_id, screen_name, no_statuses, no_followers, no_friends, no_favourites,
                                             no_listed, default_profile, geo_enabled, custom_bg_img,
                                             verified, protected)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                            ON CONFLICT (usr_id) DO NOTHING; """
                    users = [tweet["user"]]
                    if rt_status == "TRUE":
                        users.append(tweet["retweeted_status"]["user"])
                    for user in users:
                        db_cursor.execute(add_user_metadata, (user["id_str"], user["screen_name"],
                                                              user["statuses_count"], user["followers_count"],
                                                              user["friends_count"], user["favourites_count"],
                                                              user["listed_count"], user["default_profile"],
                                                              user["geo_enabled"],  user["profile_use_background_image"],
                                                              user["verified"], user["protected"]))