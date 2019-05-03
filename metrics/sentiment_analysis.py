from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyser = SentimentIntensityAnalyzer()


def tweet_sentiment(text):
    return analyser.polarity_scores(text)['compound']

