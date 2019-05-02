import datetime
import json
import zipfile
import os
import io
import networkx as nx
import metrics.Network.influence_network as infnet


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
        self.tweets = None
        self.traffic_increase_plot = None
        self.coeff_dictionary = None
        self.avg_tweets = None
        self.traffic_top_users = None
        self.retweets = None
        self.coefficient = None
        self.similar_text = None
        self.coeff_text = None
        self.coeff_color = "grey"
        self.network = None
        self.coeff_explanation = None


metrics_data = Metrics()
shill_api = api.ShillDBAPI(**consts.shill_api_creds)

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


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

        metrics_data.tweets = shill_api.get_tweets(start_date_timestamp,
                                                   end_date_timestamp,
                                                   hashtags)
        metrics_data.traffic_increase_plot = traffic.graph_traffic_and_spikes(
            metrics_data.tweets, start_date, end_date, 60)

        metrics_data.similar_text = simtex.cluster_tweets_by_text(shill_api, 4)

        # Networking
        metrics_data.network = infnet.sub_network(hashtags)

        if len(metrics_data.tweets) == 0:
            metrics_data.coeff_dictionary = "No tweets found"
            metrics_data.avg_tweets = "No tweets found"
            metrics_data.traffic_top_users = "No tweets found"
            metrics_data.retweets = "No tweets found"
            metrics_data.coefficient = "No tweets found"
        else:
            metrics_data.coeff_dictionary = coeff.coefficient(metrics_data.tweets)
            metrics_data.coefficient = truncate(metrics_data.coeff_dictionary.get(
                "Coefficient of traffic manipulation"), 2)
            metrics_data.avg_tweets = truncate(metrics_data.coeff_dictionary.get(
                "Average number of tweets per user"), 2)
            metrics_data.traffic_top_users = truncate(metrics_data.coeff_dictionary.get(
                "Proportion of traffic from the top 50 users"), 2)
            metrics_data.retweets = truncate(metrics_data.coeff_dictionary.get(
                "Proportion of retweets"), 2)
            if metrics_data.coefficient < 12:
                    metrics_data.coeff_text = "Low"
                    metrics_data.coeff_color = "green"
                    metrics_data.coeff_explanation = "Traffic was barely manipulated."
            else:
                    if metrics_data.coefficient < 20:
                        metrics_data.coeff_text = "Medium"
                        metrics_data.coeff_color = "gold"
                        metrics_data.coeff_explanation = "Traffic was slightly manipulated."
                    else:
                        if metrics_data.coefficient < 30:
                            metrics_data.coeff_text = "High"
                            metrics_data.coeff_color = "OrangeRed"
                            metrics_data.coeff_explanation = "Traffic was very manipulated."
                        else:
                            metrics_data.coeff_text = "Very high"
                            metrics_data.coeff_color = "red"
                            metrics_data.coeff_explanation = "Traffic was extremely manipulated."
        return render_template('dashboard.html',
                               div_traffic_increase=Markup(
                                   metrics_data.traffic_increase_plot),
                               coeff_text = metrics_data.coeff_text,
                               coeff_color = metrics_data.coeff_color,
                               coeff_explanation = metrics_data.coeff_explanation)
    elif request.method == 'GET':
        return render_template('dashboard.html',
                               div_traffic_increase=Markup(
                                   metrics_data.traffic_increase_plot),
                               coeff_text = metrics_data.coeff_text,
                               coeff_color = metrics_data.coeff_color,
                               coeff_explanation = metrics_data.coeff_explanation)

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
                           coeff=metrics_data.coefficient,
                           rt = metrics_data.retweets,
                           fifty = metrics_data.traffic_top_users,
                           average_tweets=metrics_data.avg_tweets,
                           coeff_color= metrics_data.coeff_color,
                           retweets_percent_pie = Markup(rt_pie),
                           most_tweets_pie = Markup(users_pie))


@app.route('/metric3', methods=['GET'])
def metric3():
    def priority(occ):
        if occ <= 5:
            return "green"
        elif occ <= 10:
            return "yellow"
        else:
            return "red"

    html = """<ul class="collapsible">"""
    exist = False
    for cluster in sorted(metrics_data.similar_text,
                          key=lambda cluster: cluster['occurrences'],
                          reverse=True):
        # similar_or_exact = simtex.get_similar_tweets_to(cluster['text'],
        #                                                 metrics_data.tweets)
        # if similar_or_exact == []:
        #     continue

        exist = True
        # suspicious = [s['usr'] for s in similar_or_exact]
        suspicious = shill_api.get_users_who_tweeted(cluster['text'])

        html += """<li>
                        <div class="collapsible-header">
                        <i class="material-icons %s-text">priority_high</i>
                        Text: %s <br>
                        Occurrences: %s
                        </div>
                        
                        <div class="collapsible-body">
                        <span>
                            Accounts that sent this message or variants:<br>
                            %s
                        </span>
                        </div>
                </li>""" % (priority(cluster['occurrences']),
                            cluster['text'], cluster['occurrences'],
                            suspicious)
    html += """</ul>"""

    if not exist:
        html = "No clusters detected!"

    return render_template('metric3.html',
                           similar_text_bubble=Markup(html))


@app.route('/metric4', methods=['GET'])
def metric4():

    trace = go.Scatter(
        x=[],
        y=[],
    )
    
    fig = go.Figure(
        data=[trace],
        layout=go.Layout(
            hovermode='closest',
            xaxis=dict(
                range=[-10, 10],
                autorange=True,
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='',
                showticklabels=False
            ),
            yaxis=dict(
                scaleanchor="x",
                scaleratio=1,
                range=[-10, 10],
                autorange=True,
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='',
                showticklabels=False
            ),
            shapes=[
            {
                'type': 'circle',
                'xref': 'x',
                'yref': 'y',
                'fillcolor': '#1565c0',
                'x0': -7.5,
                'y0': 2.5,
                'x1': -2.5,
                'y1': 7.5,
            },
            {
                'type': 'circle',
                'xref': 'x',
                'yref': 'y',
                'fillcolor': '#1565c0',
                'x0': 2.5,
                'y0': 2.5,
                'x1': 7.5,
                'y1': 7.5,
            },
            {
                'type': 'circle',
                'xref': 'x',
                'yref': 'y',
                'fillcolor': '#dd2c00',
                'x0': 2.5,
                'y0': -2.5,
                'x1': 7.5,
                'y1': -7.5,
            },
            {
                'type': 'circle',
                'xref': 'x',
                'yref': 'y',
                'fillcolor': '#dd2c00',
                'x0': -2.5,
                'y0': -2.5,
                'x1': -7.5,
                'y1': -7.5,
            },
            {
                'type': 'line',
                'x0': -2.5,
                'y0': 5.5,
                'x1': 2.5,
                'y1': 5.5,
                'line': {
                    'color': 'black',
                    'width': 3,
                },
            },
            {
                'type': 'line',
                'x0': -2.5,
                'y0': 4.5,
                'x1': 2.5,
                'y1': 4.5,
                'line': {
                    'color': 'black',
                    'width': 9,
                },
            },
            {
                'type': 'line',
                'x0': 5.5,
                'y0': 2.5,
                'x1': 5.5,
                'y1': -2.5,
                'line': {
                    'color': 'black',
                    'width': 9,
                },
            },
            {
                'type': 'line',
                'x0': 4.5,
                'y0': 2.5,
                'x1': 4.5,
                'y1': -2.5,
                'line': {
                    'color': 'black',
                    'width': 9,
                },
            },
            {
                'type': 'line',
                'x0': -5.5,
                'y0': 2.5,
                'x1': -5.5,
                'y1': -2.5,
                'line': {
                    'color': 'black',
                    'width': 9,
                },
            },
            {
                'type': 'line',
                'x0': -4.5,
                'y0': 2.5,
                'x1': -4.5,
                'y1': -2.5,
                'line': {
                    'color': 'black',
                    'width': 9,
                },
            }
            ]
        )
    )
    rendered = py.plot(fig, output_type='div')

    return render_template('metric4.html',
                           network=Markup(rendered))


@app.route('/download')
def download():
    try:
        files_list = []
        for root, dirs, files in os.walk("cache/"):
            for file in files:
                files_list.append(os.path.join(root, file))

        # Construct the zip file
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for f in files_list:
                zf.write(f)
        memory_file.seek(0)

        return send_file(memory_file, attachment_filename='static_cache.zip',
                         as_attachment=True)
    except:
        return "Something went wrong"
