from tweepy import Cursor

from api_interface import ShillAPI

"""
Middle API that works with the Search API.

"""


class ShillSearchAPI(ShillAPI):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, botometer_key):
        super().__init__(consumer_key, consumer_secret, access_token, access_token_secret, botometer_key)

    def tweets_by_hashtag_between(self, bigben_tweet_id_start, bigben_tweet_id_end, hashtags):
        tweet_iterator = Cursor(self._oauth_api.search, q=hashtags + "-filter:retweets AND -filter:replies", count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end).items()
        return list(tweet_iterator)

    def tweets_by_word(self, bigben_tweet_id_start, bigben_tweet_id_end, words):
        tweet_iterator = Cursor(self._oauth_api.search, q=words + "-filter:retweets AND -filter:replies", count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end,
                                tweet_mode="extended").items()
        return list(tweet_iterator)

    def tweets_by_hashtag_with_retweets(self, bigben_tweet_id_start, bigben_tweet_id_end, hashtags):
        tweet_iterator = Cursor(self._oauth_api.search, q=hashtags, count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end).items()
        return list(tweet_iterator)

    def tweets_by_word_with_retweets(self, bigben_tweet_id_start, bigben_tweet_id_end, words):
        tweet_iterator = Cursor(self._oauth_api.search, q=words, count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end,
                                tweet_mode="extended").items()
        return list(tweet_iterator)
