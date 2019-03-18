import psycopg2

from api_interface import ShillAPI

"""
Middle API that works with the DB obtained from an archive.

"""


class ShillDBAPI(ShillAPI):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, botometer_key):
        super().__init__(consumer_key, consumer_secret, access_token, access_token_secret, botometer_key)

    def tweets_by_hashtag_between(self, bigben_tweet_id_start, bigben_tweet_id_end, hashtags):
        pass

    def tweets_by_word(self, bigben_tweet_id_start, bigben_tweet_id_end, words):
        pass

    def tweets_by_hashtag_with_retweets(self, bigben_tweet_id_start, bigben_tweet_id_end, hashtags):
        pass

    def tweets_by_word_with_retweets(self, bigben_tweet_id_start, bigben_tweet_id_end, words):
        pass
