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
            metrics_data.coefficient = metrics_data.coeff_dictionary.get(
                "Coefficient of traffic manipulation")
            metrics_data.avg_tweets = metrics_data.coeff_dictionary.get(
                "Average number of tweets per user")
            metrics_data.traffic_top_users = metrics_data.coeff_dictionary.get(
                "Proportion of traffic from the top 50 users")
            metrics_data.retweets = metrics_data.coeff_dictionary.get(
                "Proportion of retweets")
        if metrics_data.coefficient < 12:
                metrics_data.coeff_text = "Low"
                metrics_data.coeff_color = "green"
        else:
                if metrics_data.coefficient < 30:
                    metrics_data.coeff_text = "Medium"
                    metrics_data.coeff_color = "gold"
                else:
                    metrics_data.coeff_text = "High"
                    metrics_data.coeff_color = "red"
        return render_template('dashboard.html',
                               div_traffic_increase=Markup(
                                   metrics_data.traffic_increase_plot),
                               coeff_text = metrics_data.coeff_text,
                               coeff_color = metrics_data.coeff_color)
    elif request.method == 'GET':
        return render_template('dashboard.html',
                               div_traffic_increase=Markup(
                                   metrics_data.traffic_increase_plot),
                               coeff_text = metrics_data.coeff_text,
                               coeff_color = metrics_data.coeff_color)


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




@app.route('/metric4', methods=['GET'])
def metric4():
    def community_layout(g, partition):
        """
        Compute the layout for a modular graph.


        Arguments:
        ----------
        g -- networkx.Graph or networkx.DiGraph instance
            graph to plot

        partition -- dict mapping int node -> int community
            graph partitions


        Returns:
        --------
        pos -- dict mapping int node -> (float x, float y)
            node positions

        """

        pos_communities = _position_communities(g, partition, scale=3.)

        pos_nodes = _position_nodes(g, partition, scale=1.)

        # combine positions
        pos = dict()
        for node in g.nodes():
            pos[node] = pos_communities[node] + pos_nodes[node]

        return pos

    def _position_communities(g, partition, **kwargs):

        # create a weighted graph, in which each node corresponds to a community,
        # and each edge weight to the number of edges between communities
        between_community_edges = _find_between_community_edges(g, partition)

        communities = set(partition.values())
        hypergraph = nx.DiGraph()
        hypergraph.add_nodes_from(communities)
        for (ci, cj), edges in between_community_edges.items():
            hypergraph.add_edge(ci, cj, weight=len(edges))

        # find layout for communities
        pos_communities = nx.spring_layout(hypergraph, **kwargs)

        # set node positions to position of community
        pos = dict()
        for node, community in partition.items():
            pos[node] = pos_communities[community]

        return pos

    def _find_between_community_edges(g, partition):

        edges = dict()

        for (ni, nj) in g.edges():
            ci = partition[ni]
            cj = partition[nj]

            if ci != cj:
                try:
                    edges[(ci, cj)] += [(ni, nj)]
                except KeyError:
                    edges[(ci, cj)] = [(ni, nj)]

        return edges

    def _position_nodes(g, partition, **kwargs):
        """
        Positions nodes within communities.
        """

        communities = dict()
        for node, community in partition.items():
            try:
                communities[community] += [node]
            except KeyError:
                communities[community] = [node]

        pos = dict()
        for ci, nodes in communities.items():
            subgraph = g.subgraph(nodes)
            pos_subgraph = nx.spring_layout(subgraph, **kwargs)
            pos.update(pos_subgraph)

        return pos


    # G = nx.Graph()
    # G.add_nodes_from([1,2,3,4,5,6,7,8])
    # G.add_edges_from([(1,2),(2,3),(3,4),(1,4), (1,5), (1,6), (1,7), (2,8), (2,7)])
    # partition = {
    #     1: 0,
    #     2: 1,
    #     3: 1,
    #     4: 0,
    #     5: 0,
    #     6: 1,
    #     7: 0,
    #     8: 1
    # }
    G = nx.Graph()
    G.add_nodes_from(metrics_data.network[0])
    partition = metrics_data.network[1]
    G.add_edges_from(metrics_data.network[2])

    pos = community_layout(G, partition)

    # Actual Drawing
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])

    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))

    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Network Graph',
                        titlefont=dict(size=16),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False,
                                   showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False,
                                   showticklabels=False)))

    rendered = py.plot(fig, filename='networkx', output_type='div')
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
