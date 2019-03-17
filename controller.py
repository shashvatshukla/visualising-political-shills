from flask import *
import json
import sys
app = Flask(__name__)

@app.route('/')
def main():
    return redirect(url_for('index', code=302))

@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', title='Home')

@app.route('/page2', methods=['POST', 'GET'])
def second():
    if request.method == 'POST':
        hashtags = json.loads(request.form['hidden-tags'])
        start_date = request.form['start-date']
        end_date = request.form['end-date']
        text = "Gathered tweets from " + start_date + " to " + end_date + " for " + ", ".join(hashtags)
        return render_template('page2.html', title="Analysis", return_text=text)
    elif request.method == 'GET':
        return redirect(url_for('index', code=302))
