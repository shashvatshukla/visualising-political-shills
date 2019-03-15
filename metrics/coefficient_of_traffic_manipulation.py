import tweepy
import collections

"""
Returns percentage of retweets in a list of tweets.
Raises error if list is empty.

Args:
    tweets (list of Tweet objects) -- the list of tweets.

Returns:
    float -- the percentage of retweets in 'tweets', a floating-point number between 0 and 100.
"""
def _retweet_proportion(tweets):
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
        

"""
Return a Counter of all the distinct users in a given list of tweets,
together with the number of tweets from each user.

Args:
    tweets (list of Tweet objects) -- the list of tweets.

Returns:
    Counter -- a Counter of user IDs (str)
            consisting of the authors of the tweets in 'tweets'
            and the number of tweets in 'tweets' made by each of them.
"""

def _users_with_frequency(tweets):
    
    users = list(map(lambda tweet: tweet.user.id_str, tweets))
    users_with_freq = collections.Counter(users)
    
    return users_with_freq


"""
Return the average number of tweets per user from a list of tweets.

Args:
    tweets (list of Tweet objects) -- the list of tweets.
    users_with_freq (Counter of strings) -- a counter of usernames with the number of tweets in 'tweets' from each user.

Returns:
    float -- average number of tweets per user
"""

def _average_tweets_per_user(tweets, users_with_freq):
    
    tweets_number = len(tweets)
    users_number = len(users_with_freq)

    return tweets_number/users_number


"""
Return the percentage of the traffic that comes from the n most active accounts in a list of tweets.

Args:
    tweets (list of Tweet objects) -- the list of tweets.
    users_with_freq (Counter of strings) -- a counter of usernames with the number of tweets in 'tweets' from each user.
    n (int) -- number of most active users to be considered.

Returns:
    float -- percentage of the traffic that comes from the top n most active users in 'tweets',
            as a floating-point number between 0 and 100.

"""

def _proportion_of_traffic_from_top_users(tweets, users_with_freq, n):
    
    total_traffic = len(tweets)
    top_users = users_with_freq.most_common(n)
    
    traffic_from_top_users = 0
    
    for (user, freq) in top_users:
        traffic_from_top_users += freq
        
    return (traffic_from_top_users/total_traffic)*100


"""
Return the coefficient of traffic manipulation of a topic
as described in Ben Nimmo's "Measuring Traffic Manipulation on Twitter,
based on a list of tweets that mention that topic.

Args:
    tweets (iterable of Tweet objects) -- the list of tweets.

Returns:
    float -- the coefficient of traffic manipulation.
"""

def coefficient(tweets):
    
    tweets = list(tweets)
    
    users_with_freq = _users_with_frequency(tweets)

    r = _retweet_proportion(tweets)
    f = _proportion_of_traffic_from_top_users(tweets, users_with_freq, 50)
    u = _average_tweets_per_user(tweets, users_with_freq)
    
    return (r/10 + f + u)
