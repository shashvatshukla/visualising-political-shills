import statsmodels.api as sm
import consts
import psycopg2

"""
Functions from loading the data from the Fake Project csv files
"""


def validate(metadata, is_user_bot, model):
    """
    Prints out the accuracy of the model.

    :param metadata: The metadata for inputting to the model
    :param is_user_bot: The botometer results of the users
    :param model: The logistic regression model

    """
    not_bot = []
    is_bot = []
    for i in range(len(metadata)):
        if is_user_bot[i]:
            is_bot.append(metadata[i])
        else:
            not_bot.append(metadata[i])
    true_acc = 0
    false_acc = 0
    for i in not_bot:
        if model.predict(i)[0] < 0.5:
            false_acc += 1
    for i in is_bot:
        if model.predict(i)[0] > 0.5:
            true_acc += 1
    print("Not bots:", false_acc, "out of", len(not_bot), ",", round(100 * (false_acc / len(not_bot)), 2), "%")
    print("Bots:", true_acc, "out of", len(is_bot), ",", round(100 * (true_acc / len(is_bot)), 2), "%")


def balance(metadata, is_user_bot):
    """
    Equalises the number of bots and nonbots in the training data, to improve training.

    :param metadata: The user metadata
    :param is_user_bot: The botometer results
    :return: Balanced metadata and is_user_bot lists

    """
    no_of_bots = sum(is_user_bot)
    no_of_humans = len(is_user_bot) - sum(is_user_bot)
    total = min(no_of_bots, no_of_humans)
    count_not_bot = 0
    count_is_bot = 0
    metadata_out = []
    is_user_bot_out = []
    for i in range(len(metadata)):
        if is_user_bot[i]:
            if count_not_bot < total:
                metadata_out.append(metadata[i])
                is_user_bot_out.append(True)
                count_not_bot += 1
        else:
            if count_is_bot < total:
                metadata_out.append(metadata[i])
                is_user_bot_out.append(False)
                count_is_bot += 1
    return metadata_out, is_user_bot_out


def get_data():
    """
    :return: All of the the records from the users table.

    """
    connection = psycopg2.connect(**consts.db_creds)
    cursor = connection.cursor()
    metadata_query = ''' SELECT * FROM users; '''
    cursor.execute(metadata_query)
    metadata = cursor.fetchall()
    metadata = [[int(z) for z in i] for i in metadata]
    print(metadata[0])
    return metadata


data = get_data()
metadata = []
is_user_bot = []
for i in data:
    metadata.append(i[1:9])
    is_user_bot.append(i[11])

original_metadata = metadata
original_bot_data = is_user_bot
metadata, is_user_bot = balance(metadata, is_user_bot)

logit_model = sm.Logit(is_user_bot, metadata)
result = logit_model.fit()
print(result.summary2())
validate(original_metadata, original_bot_data, result)
