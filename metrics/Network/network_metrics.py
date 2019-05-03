import psycopg2
import consts
from metrics.Network.partition import partition_bots, partition_groups
from sentiment_analysis import sentiment_compound_score

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
    select_tweets = """SELECT interactions.usr, interactions.other_usr, tweets.text
                       FROM interactions
                       INNER JOIN tweets
                       ON tweets.twid = interactions.twid
                       WHERE tweets.text LIKE '%{}%' """ + "AND tweets.text LIKE '%{}%' " * (len(keywords) - 1)
    select_tweets = select_tweets.format(*keywords)
    cursor = connection.cursor()
    cursor.execute(select_tweets)
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
    total_sentiment = [[0 for _ in range(len(groups))] for _ in range(len(groups))]
    for tweet in tweets:
        if tweet[0] in groups_dict and tweet[1] in groups_dict:
            total_sentiment[groups_dict[tweet[0]]][groups_dict[tweet[1]]] += sentiment_compound_score(tweet[2])
    return total_sentiment


def sub_network(keywords):
    tweets = get_tweets(keywords)
    users = set()
    for i, j, _ in tweets:
        users.add(i)
        users.add(j)
    users = list(users)
    group1, group2 = partition_groups(users)
    partition = {}
    for i in group1:
        partition[i] = 0
    for i in group2:
        partition[i] = 1
    group1h, group1b = partition_bots(group1)
    group2h, group2b = partition_bots(group2)
    for i in tweets:
        if i[0] in group1h and i[1] in group2h:
            print(i[2])
            break
    sentiment = get_sentiment((group1h, group1b, group2h, group2b), tweets)
    return group1h, group1b, group2h, group2b, sentiment
