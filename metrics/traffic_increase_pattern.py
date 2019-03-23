import datetime 
import plotly.offline as py
import plotly.graph_objs as go

#Traffic increase pattern

def _tweet_times (tweets):
    """
    Given a list of tweets, returns a list containing the time of each tweet, up to minutes.

    :param tweets: A list of tweets represented as dictionaries.
    
    :return: A list of datetime objects 
    """
    times = list(map(lambda tweet: tweet["created_at"], tweets))
    return times 

def graph_tweets_by_time(tweets, start_datetime, end_datetime, width):
    """
    Displays a histogram of the number of tweets created in each subinterval of 'width' minutes over the time interval input by the user.

    :param tweets: A list of tweets represented as dictionaries.
    :param start_datetime: A string of the form "YYYY-MM-DD hh:mm:ss" representing the start of the time interval
    :param end_datetime: A string representing the end of the time interval.
    :param width: An integer representing a time duration in minutes.
    """
    times = _tweet_times(tweets)
    endtime = datetime.datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    starttime = datetime.datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")

    data = [go.Histogram(
            x = times,
            xbins = dict(
                start = starttime,
                end = endtime,
                size = 60000*width
                ),
            autobinx = False
        )]

    py.plot(data, filename = "traffic_pattern.html")
