import datetime 
import plotly.offline as py
import plotly.graph_objs as go

#Traffic increase pattern


def _date_up_to_minutes (datetime_string):
    """
    Turns the timestamp of a tweet represented as a string into a datetime object corresponding to the date and time up to the minutes.

    :param datetime_string: A string of the form "YYYY-MM-DD hh:mm:ss" representing the date and time a tweet was posted.

    :return: A datetime object corresponding to the same date and time, up to the minutes.

    >>> traffic_increase_pattern._date_up_to_minutes("2017-11-16 03:17:28")
    2017-11-16 03:17:00
    
    """
    datetime_string = datetime_string[:-3]+":00" #remove the last 3 characters (:ss) from the string.
    return datetime_string


def _tweet_times (tweets):
    """
    Given a list of tweets, returns a list containing the time of each tweet, up to minutes.

    :param tweets: A list of tweets represented as dictionaries.
    
    :return: A list of datetime objects 
    """
    times = list(map(lambda tweet: _date_up_to_minutes(tweet["created_at"]), tweets))
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
