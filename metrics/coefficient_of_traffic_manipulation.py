import tweepy
import collections


def retweet_proportion(tweets):
    
    """
    Returns percentage of retweets in a list of tweets.
    Raises error if list is empty.

    :param tweets: the list of tweets.
    :return: float. the percentage of retweets in 'tweets', a number between 0 and 100.
    """

    retweets = 0
    original = 0

    for tweet in tweets:
        if(hasattr(tweet, "retweeted_status")):
            retweets += 1
        else:
            original += 1

    try:
        proportion = retweets/(retweets+original)
        return proportion*100

    except ZeroDivisionError:
        print("No tweets found.")

def users_with_frequency(tweets):
    
    """
    Return a Counter of all the distinct users in a given list of tweets,
    together with the number of tweets from each user.

    :param tweets: the list of tweets.
    :return: a Counter of user IDs consisting of the authors of the tweets and the number of tweets in 'tweets' made by each of them.
    """

    users = list(map(lambda tweet: tweet.user.id_str, tweets))
    users_with_freq = collections.Counter(users)

    return users_with_freq


def average_tweets_per_user(tweets, users_with_freq):
    
    """
    Return the average number of tweets per user from a list of tweets.

    :param tweets: the list of tweets.
    :param users_with_freq: a Counter of usernames with the number of tweets in 'tweets' from each user.

    :return: float. average number of tweets per user
    """

    tweets_number = len(tweets)
    users_number = len(users_with_freq)

    return tweets_number/users_number


def proportion_of_traffic_from_top_users(tweets, users_with_freq, n):
    
    """
    Return the percentage of the traffic that comes from the n most active accounts in a list of tweets.

    :param tweets: the list of tweets.
    :param users_with_freq: a Counter of usernames with the number of tweets in 'tweets' from each user.
    :param n: number of most active users to be considered.

    :return: float. percentage of the traffic that comes from the top n most active users in 'tweets'
    """

    total_traffic = len(tweets)
    top_users = users_with_freq.most_common(n)

    traffic_from_top_users = 0

    for (user, freq) in top_users:
        traffic_from_top_users += freq

    return (traffic_from_top_users/total_traffic)*100


def coefficient(tweets):

    """
    Return the coefficient of traffic manipulation of a topic as described in Ben Nimmo's "Measuring Traffic Manipulation on Twitter, based on a list of tweets that mention that topic.

    :param tweets: the list of tweets.

    :return: float. the coefficient of traffic manipulation.
    """

   # tweets = list(tweets)

    users_with_freq = users_with_frequency(tweets)

    r = retweet_proportion(tweets)
    f = proportion_of_traffic_from_top_users(tweets, users_with_freq, 50)
    u = average_tweets_per_user(tweets, users_with_freq)

    return (r/10 + f + u)
