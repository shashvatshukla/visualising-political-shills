from flask import *
import json
import sys
import metrics.traffic_increase_pattern as traffic
import metrics.coefficient_of_traffic_manipulation as coeff
import metrics.api_for_db as api
import consts
import datetime 
import plotly.offline as py
import plotly.graph_objs as go

app = Flask(__name__)

class Metrics():
    traffic_increase_plot = None
    coeff_dictionary = None
    avg_tweets = None
    traffic_top_users = None
    retweets = None
    coefficient = None

data = Metrics()

@app.route('/')
def main():
    return redirect(url_for('index', code=302))

@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', title='Home')

@app.route('/dashboard', methods=['POST', 'GET'])
def second():
    if request.method == 'POST':
        hashtags = json.loads(request.form['hidden-tags'])
        start_date = request.form['start-date'] + " 00:00:00"
        end_date = request.form['end-date'] + " 23:59:59"
        shillAPI = api.ShillDBAPI(**consts.shill_api_creds)
        start_date_timestamp = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end_date_timestamp = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        tweets = shillAPI.get_tweets(start_date_timestamp, end_date_timestamp, hashtags)
        data.traffic_increase_plot = traffic.graph_tweets_by_time(tweets, start_date, end_date, 60)
        if len(tweets) == 0:
            data.coeff_dictionary = "No tweets found"
            data.avg_tweets = "No tweets found"
            data.traffic_top_users = "No tweets found"
            data.retweets = "No tweets found"
            data.coefficient = "No tweets found"
        else:
            data.coeff_dictionary = coeff.coefficient(tweets)
            data.coefficient = data.coeff_dictionary.get("Coefficient of traffic manipulation")
            data.avg_tweets = data.coeff_dictionary.get("Average number of tweets per user")
            data.traffic_top_users = data.coeff_dictionary.get("Average number of tweets per user")
            data.retweets = data.coeff_dictionary.get("Proportion of retweets")
        return render_template('dashboard.html', div_traffic_increase=Markup(data.traffic_increase_plot), coeff_text = data.coefficient)
    elif request.method == 'GET':
        return render_template('dashboard.html', div_traffic_increase=Markup(data.traffic_increase_plot), coeff_text = data.coefficient)

@app.route('/metric1', methods=['GET'])
def metric1():
    return render_template('metric1.html', div_traffic_increase2=Markup(data.traffic_increase_plot))

@app.route('/metric2', methods=['GET'])
def metric2():
    if data.coeff_dictionary == "No tweets found":
        rt_pie = "No tweets found"
        users_pie = "No tweets found"
    else:    
        colors = ['#1e88e5', '#7e57c2']
        rt_data = go.Pie(labels=['Original tweets', 'Retweets'], values=[100-data.retweets, data.retweets],
                hoverinfo='label', textinfo='percent', 
                textfont=dict(size=20),
                marker=dict(colors=colors))
        users_data = go.Pie(labels=['Top 50 most active users', 'The rest of the users'], values=[data.traffic_top_users, 100-data.traffic_top_users],
                hoverinfo='label', textinfo='percent', 
                textfont=dict(size=20),
                marker=dict(colors=colors))
        rt_pie = py.plot([rt_data], output_type = 'div')
        users_pie = py.plot([users_data], output_type = 'div')
    return render_template('metric2.html', coeff_text=data.coefficient, average_tweets=data.avg_tweets, retweets_percent_pie = Markup(rt_pie), most_tweets_pie = Markup(users_pie))
