import botometer
from tweepy import API
from tweepy import AppAuthHandler
from tweepy import OAuthHandler
from tweepy import Cursor

"""
A very basic (right now) API that we will use to interact with different tools 
and expose various functions that will help us with the metrics.

"""


class ShillAPI:
    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, botometer_key):
        # Init the keys and secrets
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret
        self._botometer_key = botometer_key

        # Set up OAuth API; slow but must be used for almost all kinds of
        # requests
        auth = OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_token, self._access_token_secret)
        self._oauth_api = API(auth)

        # Set up AppAuth API; faster and also allows for more requests, can
        # only be used for certain stuff
        auth = AppAuthHandler(self._consumer_key, self._consumer_secret)
        auth.secure = True
        self._appauth_api = API(auth, wait_on_rate_limit=True,
                                wait_on_rate_limit_notify=True)

        # Botometer object
        self._botometer = botometer.Botometer(
            wait_on_ratelimit=True,
            mashape_key=self._botometer_key,
            consumer_key=self._consumer_key,
            consumer_secret=self._consumer_secret,
            access_token=self._access_token,
            access_token_secret=self._access_token_secret
        )

        # Constants and filters
        self._mentions_threshold = 100
        self._bot_threshold = 0.6

    def get_metadata(self, account):
        """
        Return user metadata, could be used for bot detection or just metrics

        :parameter account: name of the account, ie. realDonaldTrump
        :return: dictionary containing user metadata values.

        """
        user = self._appauth_api.get_user(account)
        return dict({
            "usr_id": user.id_str,
            "screen_name": user.screen_name,
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

    def get_batch_metadata(self, screen_names):
        """
        Return a list of users given a list of screen names

        :parameter screen_names: names of the accounts, ie. [realDonaldTrump]
        :return: list containing the users.

        """
        users = self._appauth_api.lookup_users(screen_names=screen_names)
        user_data = []
        current_user = 0
        for i in range(len(screen_names)):
            if users[current_user].screen_name.lower() == screen_names[i].lower():
                user_data.append({
                                 "usr_id": users[current_user].id_str,
                                 "screen_name": users[current_user].screen_name,
                                 "no_statuses": users[current_user].statuses_count,
                                 "no_followers": users[current_user].followers_count,
                                 "no_friends": users[current_user].friends_count,
                                 "no_favourites": users[current_user].favourites_count,
                                 "no_listed": users[current_user].listed_count,
                                 "default_profile": users[current_user].default_profile,
                                 "geo_enabled": users[current_user].geo_enabled,
                                 "custom_bg_img": users[current_user].profile_use_background_image,
                                 "verified": users[current_user].verified,
                                 "protected": users[current_user].protected
                                 })
                current_user += 1
                if len(users) == current_user:
                    break
            else:
                user_data.append(None)
        return user_data

    def get_tweets(self, start, end, words, with_rt=True):
        """
        Return tweets that contain the specified words (at least one) between
        start and finish (those depend on the API implementation), with or
        without RTs.

        :parameter start: depends on the implementation;
                          For the SEARCH API, a BIG BEN tweet id is expected;
                          For the DB API, a timestamp is expected.
        :parameter end: as specified for start.
        :parameter words: list of words the tweets must contain.
        :parameter with_rt: include RTs or not
        :return: iterator containing the requested tweets

        """
        pass

    def is_influencer(self, bot):
        """
        Function that decides if a bot is an influencer based on the number of
        mentions

        :parameter bot: name of the bot, ie. realDonaldTrump
        :returns: true if the number of mentions is above a preset threshold

        """
        cnt = 0
        for _ in Cursor(self._oauth_api.search, q="@" + bot, count=100).items():
            cnt += 1
            if cnt >= self._mentions_threshold:
                return True
        return False

    def is_bot(self, account, name=True):
        """
        Function that decides if an account is a bot (uses Botometer)
        Right now uses the english score

        :parameter account: name of the account or user id, ie. realDonaldTrump
        :parameter name: True if account is an account name, False if an id
        :returns: true if the bot score is above a certain threshold

        """
        result = self._botometer.check_account(('@' if name else '') + account)
        if result['scores']['english'] > self._bot_threshold:
            return True
        return False
