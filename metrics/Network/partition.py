import psycopg2
import consts
import numpy as np
import tweepy
from metrics.api_for_search import ShillSearchAPI
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigs
from metrics.BotDetection.logistic_regression import classify
from metrics.BotDetection.helper_functions import get_record_from_dict, does_user_exist

connection = psycopg2.connect(**consts.db_creds)


def get_users(keywords=None):
    cursor = connection.cursor()
    select_users = ''' SELECT usr, other_usr
                       FROM interactions'''
    cursor.execute(select_users)
    users = set()
    fetched = [None]
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        for record in fetched:
            users.add(record[0])
            users.add(record[1])
    if keywords is not None:
        cursor = connection.cursor()
        select_tweets = ''' SELECT usr, text
                            FROM tweets'''
        cursor.execute(select_tweets)
        users_keywords = set()
        fetched = [None]
        while len(fetched) > 0:
            fetched = cursor.fetchall()
            for record in fetched:
                user = record[0]
                tweet = record[1]
                if user in users and min([(word in tweet) for word in keywords]):
                    users_keywords.add(user)
        return list(users_keywords)
    else:
        return list(users)


def get_incidence_matrix(users_list, start, end, keywords):
    users_dict = {}
    for i, user in enumerate(users_list):
        users_dict[user] = i
    cursor = connection.cursor()
    get_size = ''' SELECT COUNT(*)
                   FROM interactions
                   INNER JOIN tweets
                   ON tweets.twid = interactions.twid
                   WHERE %s < interactions.time AND interactions.time < %s AND
                   tweets.text LIKE %s ''' + "OR tweets.text LIKE %s " * (len(keywords) - 1)
    cursor.execute(get_size, [start, end] + ['%'+i+'%' for i in keywords])
    num_edges = cursor.fetchall()[0]
    select_influence = ''' SELECT interactions.usr, interactions.other_usr
                           FROM interactions
                           INNER JOIN tweets
                           ON tweets.twid = interactions.twid
                           WHERE %s < interactions.time AND interactions.time < %s AND
                           tweets.text LIKE %s ''' + "OR tweets.text LIKE %s " * (len(keywords) - 1)
    cursor.execute(select_influence, [start, end] + ['%'+i+'%' for i in keywords])
    data = []
    i = []
    j = []
    fetched = [None]
    count = 0
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        for edge in fetched:
            if edge[0] in users_dict and edge[1] in users_dict:
                vertices = (users_dict[edge[0]], users_dict[edge[1]])
                if vertices[0] == vertices[1]:
                    continue
                data.extend([-1., 1.])
                i.extend([count, count])
                j.extend([min(*vertices), max(*vertices)])
                count += 1
    return coo_matrix((data, (i, j)), shape=(int(num_edges[0]), len(users_list)))


def partition_groups(users_list, start, end, keywords):
    incidence = get_incidence_matrix(users_list[:, 0], start, end, keywords)
    laplacian = incidence.transpose()*incidence
    w, v = eigs(laplacian)
    inds = np.argsort(np.real(w))
    group1 = []
    group2 = []
    for i, value in enumerate(v[:, inds[1]]):
        if value > 0:
            group1.append(users_list[i])
        else:
            group2.append(users_list[i])
    return group1, group2


def partition_bots(users_list):
    api = ShillSearchAPI.create_API()
    humans = []
    bots = []
    for i, user in enumerate(users_list):
        if user[1] is not None:
            if classify(user[1:9]):
                bots.append(user[0])
            else:
                humans.append(user[0])
        else:
            if does_user_exist(user, failed=True):
                continue
            try:
                metadata = api.get_metadata(user, True, True)
                if classify(get_record_from_dict(metadata)[0:8]):
                    bots.append(user[0])
                else:
                    humans.append(user[0])
            except tweepy.error.TweepError as tweep:
                pass
    return humans, bots

