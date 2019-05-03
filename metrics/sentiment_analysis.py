from nltk import tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Sentiment Analysis Graphs

def sentiment_compound_score(tweet):
    """
        Returns the compound sentiment analysis score of a single tweet.

        :param tweet: a tweet represented as a dictionary.

        :return: a floating point number between -1 (most extreme negative) and 1 (most extreme positive).
        
    """

    #Separate the tweet into sentences and compute the score for each sentence, then the average.
    sentence_list = tokenize.sent_tokenize(tweet["text"])
    tweet_sentiments = 0.0
    analyzer = SentimentIntensityAnalyzer()
    for sentence in sentence_list:
        sentiment = analyzer.polarity_scores(sentence)
        tweet_sentiments += sentiment["compound"]

    if len(sentence_list) == 0:
        return 0
    else:
        return (tweet_sentiments/len(sentence_list))


def average_sentiment(tweets):
    """
        Returns the average sentiment score of a list of tweets.

        :param tweets: a list of tweets.

        :return: a floating point number between -1 (most extreme negative) and 1 (most extreme positive).
    """

    total_score = 0

    for tweet in tweets:
        score = sentiment_compound_score(tweet)
        total_score += score

    if len(tweets) == 0:
        return 0
    else:
        return total_score/len(tweets)


    

        
        
        
        

    
