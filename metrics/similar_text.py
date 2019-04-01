import nltk
import consts
from api_for_db import ShillDBAPI

"""
Module that deals with the text similarity metric. 

"""

api = ShillDBAPI(**consts.shill_api_creds)
_threshold_to_num = {
    "HI": 0.25,
    "MED": 0.45,
    "LOW": 0.75
}


def get_similar_tweets_to(text, all_tweets, threshold="HI"):
    """
    Function that returns all tweets similar to a given text.
    Uses Jaccard distance, ie it breaks the sentences in words and computes
    the "set distance" between the set of given words and each set of words
    produced from the provided tweets.

    :param text: given text
    :param all_tweets: the tweets we want to check for text similarity against
                       the given text
    :param threshold: 3 levels of similarity, LOW, MID, HI
    :return: all tweets with similar text

    """
    text_tokens = set(nltk.word_tokenize(text))

    res = []
    for tweet in all_tweets:
        tweet_tokens = set(nltk.word_tokenize(tweet['text']))
        jacc_dist = nltk.jaccard_distance(tweet_tokens, text_tokens)
        if jacc_dist < _threshold_to_num[threshold]:
            res.append(tweet)
    return res


def cluster_tweets_by_text(cluster_size):
    """

    :param cluster_size: Only messages that appear more than this parameter
                         Will be considered
    :return: list of dictionaries, each dictionary has 2 keys: 'text' and
             (number of) 'occurences'
    """
    res = api.get_similar(cluster_size)
    return res
