import nltk
import consts
from api_for_db import ShillDBAPI

"""
Module that deals with the text similarity metric. 

"""

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


def cluster_tweets_by_text(all_tweets):
    """
    TODO: find an efficient way to cluster the tweets based on their similarity

    :param all_tweets:
    :return:
    """
    pass


if __name__ == "__main__":
    api = ShillDBAPI(**consts.shill_api_creds)
    tweets = api.get_tweets("2017-11-01 06:00:00", "2017-11-01 08:00:00", [])
    text = "All of the ones I checked resolve to, you guessed it, "\
    "Russia. Now, think the malware actually originates with " \
    "Trump"
    print(get_similar_tweets_to(text, tweets, "HI"))



