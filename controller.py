import datetime
import json
from itertools import chain


import plotly.graph_objs as go
import plotly.offline as py
from flask import *

import consts
import metrics.api_for_db as api
import metrics.coefficient_of_traffic_manipulation as coeff
import metrics.traffic_increase_pattern as traffic
import metrics.similar_text as simtex

app = Flask(__name__)


class Metrics:
    def __init__(self):
        self.traffic_increase_plot = None
        self.coeff_dictionary = None
        self.avg_tweets = None
        self.traffic_top_users = None
        self.retweets = None
        self.coefficient = None
        self.similar_text = None


metrics_data = Metrics()


@app.route('/')
def main():
    return redirect(url_for('index', code=302))


@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', title='Home')


@app.route('/dashboard', methods=['POST', 'GET'])
def second():
    if request.method == 'POST':
        # The things we get from POST
        hashtags = json.loads(request.form['hidden-tags'])
        start_date = request.form['start-date'] + " 00:00:00"
        end_date = request.form['end-date'] + " 23:59:59"
        start_date_timestamp = datetime.datetime.strptime(start_date,
                                                          "%Y-%m-%d %H:%M:%S")
        end_date_timestamp = datetime.datetime.strptime(end_date,
                                                        "%Y-%m-%d %H:%M:%S")

        shill_api = api.ShillDBAPI(**consts.shill_api_creds)
        tweets = shill_api.get_tweets(start_date_timestamp, end_date_timestamp,
                                     hashtags)
        metrics_data.traffic_increase_plot = traffic.graph_tweets_by_time(
            tweets, start_date, end_date, 60)
        metrics_data.similar_text = simtex.cluster_tweets_by_text(shill_api, 4)

        if len(tweets) == 0:
            metrics_data.coeff_dictionary = "No tweets found"
            metrics_data.avg_tweets = "No tweets found"
            metrics_data.traffic_top_users = "No tweets found"
            metrics_data.retweets = "No tweets found"
            metrics_data.coefficient = "No tweets found"
        else:
            metrics_data.coeff_dictionary = coeff.coefficient(tweets)
            metrics_data.coefficient = metrics_data.coeff_dictionary.get(
                "Coefficient of traffic manipulation")
            metrics_data.avg_tweets = metrics_data.coeff_dictionary.get(
                "Average number of tweets per user")
            metrics_data.traffic_top_users = metrics_data.coeff_dictionary.get(
                "Proportion of traffic from the top 50 users")
            metrics_data.retweets = metrics_data.coeff_dictionary.get(
                "Proportion of retweets")
        return render_template('dashboard.html',
                               div_traffic_increase=Markup(
                                   metrics_data.traffic_increase_plot),
                               coeff_text = metrics_data.coefficient)
    elif request.method == 'GET':
        return render_template('dashboard.html',
                               div_traffic_increase=Markup(
                                   metrics_data.traffic_increase_plot),
                               coeff_text = metrics_data.coefficient)


@app.route('/metric1', methods=['GET'])
def metric1():
    return render_template('metric1.html',
                           div_traffic_increase2=Markup(
                               metrics_data.traffic_increase_plot))


@app.route('/metric2', methods=['GET'])
def metric2():
    if metrics_data.coeff_dictionary == "No tweets found":
        rt_pie = "No tweets found"
        users_pie = "No tweets found"
    else:    
        colors = ['#1e88e5', '#7e57c2']
        rt_metrics_data = go.Pie(labels=['Original tweets', 'Retweets'],
                                 values=[100-metrics_data.retweets,
                                         metrics_data.retweets],
                                 hoverinfo='label', textinfo='percent',
                                 textfont=dict(size=20),
                                 marker=dict(colors=colors))
        users_metrics_data = go.Pie(labels=['Top 50 most active users',
                                            'The rest of the users'],
                                    values=[metrics_data.traffic_top_users,
                                            100-metrics_data.traffic_top_users],
                                    hoverinfo='label', textinfo='percent',
                                    textfont=dict(size=20),
                                    marker=dict(colors=colors))
        rt_pie = py.plot([rt_metrics_data], output_type = 'div')
        users_pie = py.plot([users_metrics_data], output_type = 'div')
    return render_template('metric2.html',
                           coeff_text=metrics_data.coefficient,
                           average_tweets=metrics_data.avg_tweets,
                           retweets_percent_pie = Markup(rt_pie),
                           most_tweets_pie = Markup(users_pie))


@app.route('/metric3', methods=['GET'])
def metric3():
    def flatten(l):
        return list(chain.from_iterable(l))

    def format_box(text):
        splitted = text.split(' ')
        formatted = '<br>'.join([' '.join(splitted[idx:idx + 10])
                                 for idx in range(0, len(splitted), 10)])
        return formatted

    clusters_len = len(metrics_data.similar_text)
    clusters_range = range(clusters_len)

    similar_text_data = [
    {
        'x': flatten([list(range(10)) for _ in clusters_range][:clusters_len]),
        'y': flatten([[idx * 10]*10 for idx in clusters_range][:clusters_len]),
        'mode': 'markers',
        'marker': {
            'color': [metrics_data.similar_text[idx]['occurrences']
                      for idx in clusters_range],
            'size': [metrics_data.similar_text[idx]['occurrences'] % 50 + 1
                     for idx in clusters_range],
            'showscale': True
        },
        'text': ['Text: ' +
                 format_box(str(metrics_data.similar_text[idx]['text'])) +
                 '<br>Occurences: ' +
                 str(metrics_data.similar_text[idx]['occurrences'])
                 for idx in clusters_range],
        'hoverinfo': 'text'
    }]
    similar_text_layout = go.Layout(
        title='Similar text clusters',
        hovermode='closest',
        xaxis=dict(autorange=True, showgrid=False, zeroline=False,
                   showline=False, ticks='', showticklabels=False),
        yaxis=dict(autorange=True, showgrid=False, zeroline=False,
                   showline=False, ticks='', showticklabels=False),
        showlegend=False
    )
    similar_text_fig = go.Figure(data=similar_text_data,
                                 layout=similar_text_layout)

    similar_text_bubble = py.plot(similar_text_fig,
                                  filename='scatter-colorscale',
                                  output_type='div')

    return render_template('metric3.html',
                           similar_text_bubble=Markup(similar_text_bubble))
