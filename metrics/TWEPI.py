from tweepy import OAuthHandler
from tweepy import API
from tweepy import AppAuthHandler
from tweepy import Cursor
import botometer

"""
A very basic (right now) API that we will use to interact with different tools and expose various functions
that will help us with the metrics

"""


class TwePI:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, botometer_key):
        # Init the keys and secrets
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret
        self._botometer_key = botometer_key

        # Set up OAuth API; slow but must be used for almost all kinds of requests
        auth = OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_token, self._access_token_secret)
        self._oauth_api = API(auth)

        # Set up AppAuth API; faster and also allows for more requests, can only be used for certain stuff
        auth = AppAuthHandler(self._consumer_key, self._consumer_secret)
        auth.secure = True
        self._appauth_api = API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        # Botometer object
        self._botometer = botometer.Botometer(wait_on_ratelimit=True,
                                              mashape_key=self._botometer_key,
                                              consumer_key=self._consumer_key,
                                              consumer_secret=self._consumer_secret,
                                              access_token=self._access_token,
                                              access_token_secret=self._access_token_secret)

        # Constants and filters
        self._mentions_threshold = 100
        self._bot_threshold = 0.6

    """
    Return user metadata, could be used for bot detection or just metrics

    :parameter account: name of the account, ie. realDonaldTrump
    :return: dictionary containing user metadata values.
    
    """
    def get_metadata(self, account):
        user = self._appauth_api.get_user(account)
        return dict({
            "no_statuses": user.statuses_count,
            "no_followers": user.followers_count,
            "no_friends": user.friends_count,
            "no_favourites": user.favourites_count,
            "no_listed": user.listed_count,
            "default_profile": user.default_profile,
            "geo_enabled": user.geo_enabled,
            "custom_bg_img": user.profile_use_background_image,
            "verified": user.verified,
            "protected": user.protected
        })

    """
    Return tweets that contain the specified hashtags and that were posted between 2 specified big ben tweets, excluding retweets and replies

    :parameter bigben_tweet_id_start: the id of the big ben tweet, represents the start hour and day
    :parameter bigben_tweet_id_end: the id of the big ben tweet, represents the start hour and day
    :parameter hashtags: list of words that are used 
    :return: iterator containing the requested tweets
    
    """
    def tweets_by_hashtag_between(self, bigben_tweet_id_start, bigben_tweet_id_end, hashtags):
        tweet_iterator = Cursor(self._oauth_api.search, q=hashtags + "-filter:retweets AND -filter:replies", count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end).items()
        return tweet_iterator

    """
    Return tweets that contain the specified words and that were posted between 2 specified big ben tweets, excluding retweets and replies
    
    :parameter bigben_tweet_id_start: the id of the big ben tweet, represents the start hour and day
    :parameter bigben_tweet_id_end: the id of the big ben tweet, represents the start hour and day
    :parameter words: list of words that are used 
    :return: iterator containing the requested tweets
    
    """
    def tweets_by_word(self, bigben_tweet_id_start, bigben_tweet_id_end, words):
        tweet_iterator = Cursor(self._oauth_api.search, q=words + "-filter:retweets AND -filter:replies", count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end,
                                tweet_mode="extended").items()
        return tweet_iterator

    """
    Return tweets that contain the specified hashtags and that were posted between 2 specified big ben tweets, INCLUDING RETWEETS AND REPLIES

    :parameter bigben_tweet_id_start: the id of the big ben tweet, represents the start hour and day
    :parameter bigben_tweet_id_end: the id of the big ben tweet, represents the start hour and day
    :parameter hashtags: list of words that are used 
    :return: iterator containing the requested tweets
    
    """
    def tweets_by_hashtag_with_retweets(self, bigben_tweet_id_start, bigben_tweet_id_end, hashtags):
        tweet_iterator = Cursor(self._oauth_api.search, q=hashtags, count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end).items()
        return tweet_iterator

    """
    Return tweets that contain the specified words and that were posted between 2 specified big ben tweets, INCLUDING RETWEETS AND REPLIES
    
    :parameter bigben_tweet_id_start: the id of the big ben tweet, represents the start hour and day
    :parameter bigben_tweet_id_end: the id of the big ben tweet, represents the start hour and day
    :parameter words: list of words that are used 
    :return: iterator containing the requested tweets
    
    """
    def tweets_by_word_with_retweets(self, bigben_tweet_id_start, bigben_tweet_id_end, words):
        tweet_iterator = Cursor(self._oauth_api.search, q=words, count=15,
                                since_id=bigben_tweet_id_start,
                                max_id=bigben_tweet_id_end,
                                tweet_mode="extended").items()
        return tweet_iterator

    """
    Function that decides if a bot is an influencer based on the number of mentions
    
    :parameter bot: name of the bot, ie. realDonaldTrump
    :returns: true if the number of mentions is above a preset threshold
    
    """
    def is_influencer(self, bot):
        cnt = 0
        for _ in Cursor(self._oauth_api.search, q="@" + bot, count=100).items():
            cnt += 1
            if cnt >= self._mentions_threshold:
                return True
        return False

    """
    Function that decides if an account is a bot (uses Botometer)
    Right now uses the english score

    :parameter bot: name of the account, ie. realDonaldTrump
    :returns: true if the bot score is above a certain threshold
    
    """
    def is_bot(self, account):
        result = self._botometer.check_account('@' + account)
        if result['scores']['english'] > self._bot_threshold:
            return True
        return False
