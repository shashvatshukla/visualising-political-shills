import tweepy

def tweet_to_dict(tweet):
    """
    Converts a Tweet object to a dictionary containing the relevant tweet metadata. 

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
