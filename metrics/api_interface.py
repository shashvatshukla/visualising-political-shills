import botometer
import psycopg2
import consts
from tweepy import API
from tweepy import AppAuthHandler
from tweepy import OAuthHandler
from tweepy import Cursor
import tweepy

from metrics.BotDetection.helper_functions import add_to_db, get_record_from_dict

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

        # Establish connection to db
        self.connection = psycopg2.connect(**consts.db_creds)
        self.cursor = self.connection.cursor()

    def get_metadata(self, account, check_cache=False, cache_result=False):
        """
        Return user metadata, could be used for bot detection or just metrics

        :parameter account: name of the account, ie. realDonaldTrump
        :parameter check_cache: If True, search for the user in thr db before checking Twitter
        :parameter cache_result: If True, store the result in the db
        :return: dictionary containing user metadata values.

        """
        if check_cache:
            select_user = """SELECT *
                             FROM user_metadata
                             WHERE usr_id = %s OR screen_name = %s"""
            self.cursor.execute(select_user, [account, account])
            result = self.cursor.fetchall()
            if len(result) > 0:
                return {
                    "usr_id": result[0][0],
                    "screen_name": result[0][1],
                    "no_statuses": result[0][2],
                    "no_followers": result[0][3],
                    "no_friends": result[0][4],
                    "no_favourites": result[0][5],
                    "no_listed": result[0][6],
                    "default_profile": result[0][7],
                    "geo_enabled": result[0][8],
                    "custom_bg_img": result[0][9],
                    "verified": result[0][10],
                    "protected": result[0][11]
                }
        user = self._appauth_api.get_user(account)
        return_dict = {
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
        }
        if cache_result:
            add_to_db(user.id_str, user.screen_name, get_record_from_dict(return_dict))
        return return_dict

    def get_batch_metadata(self, screen_names=None, user_ids=None):
        """
        Return a list of users given a list of screen names

        :parameter screen_names: names of the accounts, ie. [realDonaldTrump]
        :parameter user_ids: user ids of the accounts
        :return: list containing the users.

        """
        try:
            if screen_names is not None:
                input_size = len(screen_names)
                users = self._appauth_api.lookup_users(screen_names=screen_names)
            elif user_ids is not None:
                input_size = len(user_ids)
                users = self._appauth_api.lookup_users(user_ids=user_ids)
            else:
                raise ValueError("At least one of screen_names or user_ids must be given")
        except tweepy.error.TweepError as tweep:
            print(screen_names, user_ids, tweep.response.text)
            if str(tweep) != "[{'code': 17, 'message': 'No user matches for specified terms.'}]":
                raise
            return []
        user_data = []
        current_user = 0
        if users is None:
            print("users is none")
        for i in range(input_size):
            if (screen_names is not None and users[current_user].screen_name.lower() == screen_names[i].lower()) or\
                   (user_ids is not None and users[current_user].id_str == user_ids[i]):
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
