import csv

from metrics.BotDetection.helper_functions import add_to_db, does_user_exist

"""
Downloads the metadata of Twitter users, for training the logistic regression on.
"""


def get_record_from_csv_row(keys, row):
    """
    Converts a row from the csv file to a metadata list, in the correct order to be added to the database by add_to_db.

    :param keys: The column titles
    :param row: The users metadata, from a csv row
    :return: A metadata list

    """
    metadata = {}
    for i in range(len(keys)):
        if row[i] == "":
            metadata[keys[i]] = "0"
        else:
            metadata[keys[i]] = row[i]
    
    return [metadata["statuses_count"], metadata["followers_count"], metadata["friends_count"],
            metadata["favourites_count"], metadata["listed_count"], metadata.get("default_profile", False),
            metadata.get("geo_enabled", False), metadata.get("profile_use_background_image", False), metadata.get("verified", False),
            metadata.get("protected", False)]


def load_table(file_name, are_bots):
    file = open(file_name, encoding="utf-8")
    csv_reader = csv.reader(file, delimiter=',')
    keys = next(csv_reader)
    for row in csv_reader:
        if does_user_exist(row[0]):
            continue
        metadata = get_record_from_csv_row(keys, row)
        add_to_db(row[0], row[2], metadata, are_bots)


load_table("users.csv", True)
