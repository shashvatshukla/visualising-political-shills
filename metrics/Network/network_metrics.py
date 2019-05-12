import psycopg2
import consts
from metrics.Network.partition import partition_bots, partition_groups
from metrics.sentiment_analysis import sentiment_compound_score
import numpy as np

connection = psycopg2.connect(**consts.db_creds)


def get_edges(users):
    user_dict = {}
    for i in users:
        user_dict[i] = 1
    cursor = connection.cursor()
    drop_old = "DELETE FROM temp"
    connection.commit()
    try:
        cursor.execute(drop_old)
    except psycopg2.ProgrammingError:
        pass
    insert = """INSERT INTO temp (usr)
                 VALUES (%s);"""
    for user in user_dict:
        cursor.execute(insert, [user])
    connection.commit()
    select = """ SELECT influences.usr, influences.other_usr
                 FROM influences
                 INNER JOIN temp as t1
                 ON t1.usr = influences.usr AND influences.usr != influences.other_usr
                 INNER JOIN temp as t2
                 ON t2.usr = influences.other_usr"""
    cursor.execute(select)
    edges = []
    fetched = [None]
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        edges.extend(fetched)
    cursor.execute(drop_old)
    connection.commit()
    return edges


def get_tweets(keywords):
    select_tweets = """SELECT interactions.usr, interactions.other_usr, user_1.*, user_2.*
                       FROM interactions
                       INNER JOIN tweets
                       ON tweets.twid = interactions.twid
                       INNER JOIN user_metadata as user_1
                       ON user_1.usr_id = interactions.usr
                       INNER JOIN user_metadata as user_2
                       ON user_2.usr_id = interactions.other_usr
                       WHERE tweets.text LIKE %s """ + "OR tweets.text LIKE %s " * (len(keywords) - 1)
    cursor = connection.cursor()
    cursor.execute(select_tweets, ['%'+i+'%' for i in keywords])
    fetched = [None]
    output = []
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        output.extend(fetched)
    return output


def get_sentiment(groups, tweets):
    groups_dict = {}
    for i, group in enumerate(groups):
        for user in group:
            groups_dict[user] = i
    total_tweets = [[0 for _ in range(len(groups))] for _ in range(len(groups))]
    total_sentiment = [[0 for _ in range(len(groups))] for _ in range(len(groups))]
    for tweet in tweets:
        if tweet[0] in groups_dict and tweet[1] in groups_dict:
            total_sentiment[groups_dict[tweet[0]]][groups_dict[tweet[1]]] += sentiment_compound_score({"text": tweet[2]})
            total_tweets[groups_dict[tweet[0]]][groups_dict[tweet[1]]] += 1
    return total_tweets, total_sentiment


def get_interaction_tweets(groups, tweets):
    interaction_tweets = [[0 for _ in range(len(groups))] for _ in range(len(groups))]
    for i in range(len(groups)):
        for j in range(len(groups)):
            output = []
            for z in tweets:
                if z[0] in groups[i] and z[1] in groups[j]:
                    output.append(z[2])
                    if len(output) == 20:
                        break
            interaction_tweets[i][j] = output
    return interaction_tweets


def sub_network(keywords):
    tweets = get_tweets(keywords)
    users = set()
    for i, data in enumerate(tweets):
        users.add((data[0],) + data[4:12])
        users.add((data[1],) + data[16:24])
    users = np.array(list(users))
    group1, group2 = partition_groups(users)
    group1h, group1b = partition_bots(group1)
    group2h, group2b = partition_bots(group2)
    for i in tweets:
        if i[0] in group1h and i[1] in group2h:
            print(i[2])
            break
    total_tweets, total_sentiment = get_sentiment((group1h, group2h, group1b, group2b), tweets)
    average_sentiment = [[0 for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            if total_tweets[i][j] > 0:
                average_sentiment[i][j] = total_sentiment[i][j] / total_tweets[i][j]
    interaction_tweets = get_interaction_tweets([group1h, group2h, group1b, group2b], tweets)

    return total_tweets, average_sentiment, interaction_tweets
