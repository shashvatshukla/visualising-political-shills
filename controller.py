import datetime
import json
import zipfile
import os
import io
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
        self.tweets = None
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
        metrics_data.tweets = shill_api.get_tweets(start_date_timestamp,
                                                   end_date_timestamp,
                                                   hashtags)
        metrics_data.traffic_increase_plot = traffic.graph_traffic_and_spikes(
            metrics_data.tweets, start_date, end_date, 20)
        metrics_data.similar_text = simtex.cluster_tweets_by_text(shill_api, 4)

        if len(metrics_data.tweets) == 0:
            metrics_data.coeff_dictionary = "No tweets found"
            metrics_data.avg_tweets = "No tweets found"
            metrics_data.traffic_top_users = "No tweets found"
            metrics_data.retweets = "No tweets found"
            metrics_data.coefficient = "No tweets found"
        else:
            metrics_data.coeff_dictionary = coeff.coefficient(metrics_data.tweets)
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
        similar_or_exact = simtex.get_similar_tweets_to(cluster['text'],
                                                        metrics_data.tweets)
        if similar_or_exact == []:
            continue

        exist = True
        suspicious = [s['usr'] for s in similar_or_exact]

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
