import statsmodels.api as sm
import consts
import psycopg2
import random
import pickle

"""
Functions from loading the data from the Fake Project csv files
"""

logit_model = None


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
    for i in range(len(metadata)):
        metadata[i].append(is_user_bot[i])
    random.shuffle(metadata)
    for i in range(len(metadata)):
        is_user_bot[i] = metadata[i][-1]
        del metadata[i][-1]
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
    metadata_query = ''' SELECT * FROM user_metadata; '''
    cursor.execute(metadata_query)
    metadata = cursor.fetchall()
    is_bot_query = ''' SELECT usr_id, is_bot
                       FROM   user_bot_status
                       WHERE  usr_id = %s;'''
    is_user_bot = []
    missing_status = []
    for i, row in enumerate(metadata):
        cursor.execute(is_bot_query, [str(row[0])])
        result = cursor.fetchall()
        if len(result) > 0:
            is_user_bot.append(result[0][1])
        else:
            missing_status.insert(0, i)
    for i in missing_status:
        del metadata[i]
    metadata = [[int(z) for z in i[2:10]] for i in metadata]
    return metadata, is_user_bot


def train_model():
    metadata, is_user_bot = get_data()

    print(len(metadata), len(is_user_bot))

    original_metadata = metadata
    original_bot_data = is_user_bot
    metadata, is_user_bot = balance(metadata, is_user_bot)

    logit_model = sm.Logit(is_user_bot, metadata)
    result = logit_model.fit()
    print(result.summary2())
    validate(original_metadata, original_bot_data, result)
    return result


def save_model():
    logit_model = train_model()
    f = open("logit_model.sm", "wb")
    pickle.dump(logit_model, f)


def load_model():
    global logit_model
    f = open(consts.logit_model_file, "rb")
    logit_model = pickle.load(f)


def classify(metadata):
    if logit_model is None:
        load_model()
    return logit_model.predict([int(i) for i in metadata[0:5]]+[i[0] == 'T' for i in metadata[5:8]])[0] > 0.5
