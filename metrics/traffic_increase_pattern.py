import datetime 
import plotly.offline as py
import plotly.graph_objs as go
import numpy
import collections
from metrics.sentiment_analysis import *


#Traffic increase pattern

def _tweet_times (tweets):
    """
    Given a list of tweets, returns a list containing the time of each tweet, up to minutes.

    :param tweets: A list of tweets represented as dictionaries.
    
    :return: A list of datetime objects 
    """
    times_as_strings = list(map(lambda tweet: tweet["created_at"], tweets))
    times = list(map(lambda time: datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S"), times_as_strings))
    return times


def pct_change(before, after):
    """
    Computes the increase from 'after' to 'before' as a percentage of 'before'.
    """
    pct = ((after - before)/before)*100
    return pct

    
def _spikes_in_traffic(times, bins, tweet_bins_ind, pct_change_threshold):
    """
    Given a list of tweet times and the bins (time intervals) they will be divided into in the histogram, return a list of traffic spike points 
    (i.e. time intervals where the increase in traffic compared to the previous interval goes over a given threshold).
    
    :param times: A list of tweet times represented as datetime objects.
    :param bins: A list containing the start points of each histogram bin.
    :param tweet_bins_ind: A list containing the index corresponding to the bin of each tweet.
    :param pct_change_threshold: The threshold for what we consider a spike in traffic, as a percentage increase between the previous period and the current one.
    
    :return: A list of (datetime, int) pairs representing the time periods when there were spikes in traffic, together with the number of tweets over that period.
    """

     # sorted list of (bin, number of tweets in bin) pairs (basically a representation of the histogram as pairs)
    tweet_bin_counts = sorted(collections.Counter(tweet_bins_ind).items())
    
    bins_number = len(tweet_bin_counts)

    # list of traffic spike points
    spikes_bins = []
    spikes_counts = []

    # lower bound for the size of potential spikes
    min_spike_size = 20
    
    for i in range(0, bins_number-1):
        curr_pct_change = pct_change(tweet_bin_counts[i][1], tweet_bin_counts[i+1][1])
        if curr_pct_change > pct_change_threshold and tweet_bin_counts[i+1][1] >= min_spike_size :
            curr_bin = bins[tweet_bin_counts[i][0]]
            spikes_bins.append(curr_bin)
            spikes_counts.append(tweet_bin_counts[i+1][1])
    
            
    return (spikes_bins, spikes_counts)

def _sentiment_over_time(tweets, bins, tweet_bins_ind):
    """
    Compute the average sentiment score of the tweets in each time interval.
    
    :param tweets: A list of tweets.
    :param bins: A list containing the start points of each histogram bin.
    :param tweet_bins_ind: A list containing the index corresponding to the bin of each tweet.

    :return: A list containing the average sentiment score of the tweets in each bin.
    """
    sent_by_bin = []
    count_by_bin = []
    
    max_bin_ind = len(bins)
    for i in range(0, max_bin_ind + 1):
        sent_by_bin.append(0)
        count_by_bin.append(0)

    for i in range(0, len(tweet_bins_ind)):
        curr_bin = tweet_bins_ind[i]
        tweet_sentiment = sentiment_compound_score(tweets[i])
        sent_by_bin[curr_bin] += tweet_sentiment
        count_by_bin[curr_bin] += 1

    for i in range(0, max_bin_ind):
        if count_by_bin[i] != 0:
            sent_by_bin[i] = sent_by_bin[i]/count_by_bin[i]

    return sent_by_bin


def graph_traffic_and_spikes(tweets, start_datetime, end_datetime, width, pct_change_threshold = 400):
    """
     Displays a histogram of the number of tweets created in each subinterval of 'width' minutes over the time interval input by the user, as well as the spikes in traffic.
     
    :param tweets: A list of tweets represented as dictionaries.
    :param start_datetime: A string of the form "YYYY-MM-DD hh:mm:ss" representing the start of the time interval
    :param end_datetime: A string representing the end of the time interval.
    :param width: An integer representing a time duration in minutes.
    :param pct_change_threshold: The threshold for what we consider a spike in traffic, as a percentage increase between the previous period and the current one.
    
    :return: A call to plotly.offline.plot that will graph the traffic over time, with the spike points highlighted. 
    """
    times = _tweet_times(tweets)
    times = sorted(times)
    endtime = datetime.datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    starttime = datetime.datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")

    bin_size = 60000*width

    traffic_hist = go.Histogram(
            x = times,
            xbins = dict(
                start = starttime,
                end = endtime,
                size = bin_size
                ),
            marker = dict(
                color = '#0d47a1'
                ),
            name = "Traffic",
            autobinx = False,
            opacity = 0.7,
            xaxis = "x1",
            yaxis = "y1"
        )
    
    bins = numpy.arange(starttime, endtime, bin_size*1000)
    bins = list(map(lambda b: b.astype(datetime.datetime), bins))

    tweet_timestamps = list(map(datetime.datetime.timestamp, times))
    bins_as_timestamps = list(map(datetime.datetime.timestamp, bins))

    # list of indices of bins each tweet would be in in the histogram
    tweet_bins_ind = numpy.digitize(tweet_timestamps, bins_as_timestamps)
    
    (spikes_bins, spikes_counts) = _spikes_in_traffic(times, bins, tweet_bins_ind, pct_change_threshold)
    spikes_bins = list(map(lambda b: b + datetime.timedelta(minutes = width/2),spikes_bins))
    traffic_spikes_scatter = go.Scatter(
        x = spikes_bins,
        y = list(map(lambda b: b + 1, spikes_counts)),
        hoverinfo = "text",
        hovertext = list(map(str, spikes_counts)),
        marker = dict(color = '#BE5057', symbol='triangle-down'),
        mode = 'markers',
        name = "Spikes",
        xaxis = "x1",
        yaxis = "y1"
        )

    sentiment_scatter = go.Scatter(
            x = list(map(lambda b: b + datetime.timedelta(minutes = width/2), bins)),
            y = _sentiment_over_time(tweets, bins, tweet_bins_ind),
            marker = dict(line = dict(width = 1.4)),
            name = "Sentiment",
            xaxis = "x1",
            yaxis = "y2"
        )
    
    data = [traffic_hist, traffic_spikes_scatter, sentiment_scatter]
    layout = go.Layout(barmode = 'overlay',
                       xaxis = dict(
                           title = 'Time',
                           ),
                       yaxis = dict(
                           title = 'Number of tweets',
                           ),
                       yaxis2 = dict(
                           overlaying = 'y',
                           range = [-1,1],
                           side = 'right',
                           title = 'Sentiment score',
                           zeroline = False
                           ),
                       bargap = 0.2,
                       plot_bgcolor = "#f1f1f1"
                        )
    
    fig = go.Figure(data=data, layout=layout)

    return(py.plot(fig, output_type = 'div'))
