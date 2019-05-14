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


def get_tweets(keywords, start_time, end_time):
    select_tweets = """SELECT interactions.usr, interactions.other_usr, tweets.text, user_1.*, user_2.*, tweets.retweet_text
                       FROM interactions
                       INNER JOIN tweets
                       ON tweets.twid = interactions.twid
                       INNER JOIN user_metadata as user_1
                       ON user_1.usr_id = interactions.usr
                       INNER JOIN user_metadata as user_2
                       ON user_2.usr_id = interactions.other_usr
                       WHERE %s < interactions.time AND interactions.time < %s AND
                       tweets.text LIKE %s """ + "OR tweets.text LIKE %s " * (len(keywords) - 1)
    cursor = connection.cursor()
    cursor.execute(select_tweets, [start_time, end_time] + ['%'+i+'%' for i in keywords])
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
            text = tweet[2]
            if tweet[27] is not None:
                start_length = len(text.split(":")[0]) + 2
                text = text[start_length + len(tweet[27]):]
                if len(text) == 0:
                    continue
            total_sentiment[groups_dict[tweet[0]]][groups_dict[tweet[1]]] += sentiment_compound_score({"text": text})
            total_tweets[groups_dict[tweet[0]]][groups_dict[tweet[1]]] += 1
    return total_tweets, total_sentiment


def get_interaction_tweets(groups, tweets):
    interaction_tweets = [[[] for _ in range(len(groups))] for _ in range(len(groups))]
    reply_count = [[0 for _ in range(len(groups))] for _ in range(len(groups))]
    for tweet in tweets:
        done = False
        for i in range(len(groups)):
            for j in range(len(groups)):
                if len(interaction_tweets[i][j])-reply_count[i][j] < 10 and reply_count[i][j]<10 and tweet[0] in groups[i] and tweet[1] in groups[j]:
                    if (tweet[2][0:2] == "RT" and len(interaction_tweets[i][j])-reply_count[i][j] < 10) or (tweet[2][0:2] != "RT" and reply_count[i][j] < 10):
                        if tweet[2][0:2] == "RT":
                            reply_count[i][j] += 1
                        if tweet[2][-1] == '\u2026' or tweet[2][-2] == '\u2026':
                            interaction_tweets[i][j].append(tweet[2].split(":")[0]+": "+tweet[27])
                        else:
                            interaction_tweets[i][j].append(tweet[2])
                    done = True
                    break
            if done:
                break
        done = True
        for i in range(len(groups)):
            for j in range(len(groups)):
                if len(interaction_tweets[i][j]) < 5:
                    done = False
        if done:
            break
    return interaction_tweets


def sub_network(keywords, start_time, end_time):
    tweets = get_tweets(keywords, start_time, end_time)
    users = set()
    for i, data in enumerate(tweets):
        users.add((data[0],) + data[5:13])
        users.add((data[1],) + data[17:25])
    users = np.array(list(users))
    group1, group2 = partition_groups(users)
    group1h, group1b = partition_bots(group1)
    group2h, group2b = partition_bots(group2)
    total_tweets, total_sentiment = get_sentiment((group1h, group2h, group1b, group2b), tweets)
    average_sentiment = [[0 for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            if total_tweets[i][j] > 0:
                average_sentiment[i][j] = total_sentiment[i][j] / total_tweets[i][j]
    interaction_tweets = get_interaction_tweets([group1h, group2h, group1b, group2b], tweets)

    return total_tweets, average_sentiment, interaction_tweets
