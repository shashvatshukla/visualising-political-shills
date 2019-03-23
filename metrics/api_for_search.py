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
        
        def tweet_to_dict(tweet):
            """
            Converts a Tweet object to a dictionary only containing the relevant metadata, to make it compatible with data stored in the database. 
            :param tweet: a Tweet object.
            :return: a dictionary containing the created_at, text, user id, tweet id, and retweet status of the tweet.
            """
            tweet_dict = {
                "created_at": str(tweet.created_at),
                "text": tweet.text,
                "usr": tweet.user.id_str,
                "twid": tweet.id,
                "rt_status": hasattr(tweet, "retweeted_status")
            }
            return tweet_dict
        
        return list(map(tweet_to_dict,tweet_iterator))
