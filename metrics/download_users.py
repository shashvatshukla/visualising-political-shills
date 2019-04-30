from metrics.api_for_search import ShillSearchAPI
from BotDetection.helper_functions import add_to_db, get_record_from_dict, fail_user, does_user_exist
from Network.partition import get_users


def download_users(users):
    api = ShillSearchAPI.create_API()
    for i in range(len(users)//100+1):
        print(i)
        batch = users[i:i+100]
        data = api.get_batch_metadata(user_ids=batch)
        for z, record in enumerate(data):
            if record is not None:
                if not does_user_exist(record["usr_id"], metadata=True):
                    add_to_db(record["usr_id"], record["screen_name"], get_record_from_dict(record))
            else:
                if not does_user_exist(users[i*100+z], failed=True):
                    fail_user(users[i*100+z], "Metadata Failure: User no longer exists.")


download_users(get_users(["Trump"]))
