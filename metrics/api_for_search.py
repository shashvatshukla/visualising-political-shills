from tweepy import Cursor

from api_interface import ShillAPI

"""
Middle API that works with the Search API.

"""


class ShillSearchAPI(ShillAPI):
    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, botometer_key):
        super().__init__(consumer_key, consumer_secret, access_token,
                         access_token_secret, botometer_key)

    def get_tweets(self, bigben_tweet_id_start, bigben_tweet_id_end,
                   words, with_rt=True):
        if not with_rt:
            query = ' '.join(words) + " -filter:retweets"
        else:
            query = ' '.join(words)
        print(query)
        tweet_iterator = Cursor(self._oauth_api.search, q=query,
                                count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end).items()
        return list(tweet_iterator)
