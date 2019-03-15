import os
import shutil
import bz2
import re
import psycopg2


# -------------------------
abbr_to_number = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}
# -------------------------


class ArchiveToDBController:
    def __init__(self, archive_path):
        self.archive_path = archive_path
        self._db_creds = {
            "user": "postgres",
            "password": "toporasi31",
            "host": "127.0.0.1",
            "port": "5432",
            "database": "postgres"
        }

    def create_db(self):
        try:
            # Establish connection
            connection = psycopg2.connect(user="postgres",
                                          password="your_pass_here(obtained during installation)",
                                          host="127.0.0.1",
                                          port="5432",
                                          database="postgres")

            # Create tweets table
            drop_first = '''DROP TABLE IF EXISTS tweets'''
            cursor = connection.cursor()
            cursor.execute(drop_first)

            create_table_query = ''' CREATE TABLE tweets
                                     (ID SERIAL PRIMARY KEY,
                                      created_at TIMESTAMP NOT NULL,
                                      text TEXT NOT NULL,
                                      usr VARCHAR (255) NOT NULL,
                                      twid VARCHAR (255) NOT NULL);
                                 '''
            cursor.execute(create_table_query)
            connection.commit()
            print("Tweets table created successfully!")

            # Now run everything else
            self._deal_with_archives(cursor)
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            # Batch commit all changes
            connection.commit()

            # Close connection
            if connection:
                cursor.close()
                connection.close()

    def _deal_with_archives(self, db_cursor):
        for root, dirs, files in os.walk(self.archive_path):
            for name in files:
                subject = root + "\\" + name
                temp_json_file = root + "\\" + "tmp" + name
                shutil.copy(subject, temp_json_file)

                self._deal_with_json(root, temp_json_file, db_cursor)

    def _deal_with_json(self, root, temp_file, db_cursor):
        decompressed_json = os.path.join(root, temp_file + '.json')
        with open(decompressed_json, 'wb') as new_file, open(temp_file, 'rb') as file:
            decompressor = bz2.BZ2Decompressor()
            for data in iter(lambda: file.read(100 * 1024), b''):
                new_file.write(decompressor.decompress(data))

        self._upload_to_db(decompressed_json, db_cursor)
        os.remove(decompressed_json)
        os.remove(temp_file)

    @staticmethod
    def _upload_to_db(json_file, db_cursor):
        def escape_quote(to_escape):
            return "\'" + to_escape + "\'"

        tweet_pattern = "{\"created_at\":\"(?P<created_at>.*?)\"," \
                        "\"id\":(?P<twid>\d+).+" \
                        "\"text\":\"(?P<text>.*?)\".+" \
                        "\"user\":{\"id\":(?P<usr>\d+).+}.+" \
                        "\"lang\":\"(?P<lang>.*?)\",\"timestamp_ms\":.*}"

        with open(json_file) as file:
            text = file.read()
            for match in re.finditer(tweet_pattern, text):
                match_dict = match.groupdict()
                if match_dict['lang'] == "en":
                    splitted = match["created_at"].split(' ')
                    timestamp = splitted[5] + "-" + abbr_to_number[splitted[1]] + "-" + splitted[2] + " " + splitted[3]
                    add_tweet_query = "INSERT INTO tweets (created_at, text, usr, twid) " \
                                      "VALUES (TIMESTAMP " + \
                                               escape_quote(timestamp) + "," + \
                                               escape_quote(match_dict["text"].replace('\'', '\'\'')) + "," + \
                                               escape_quote(match_dict["usr"]) + "," + \
                                               escape_quote(match_dict["twid"]) + ")"
                    db_cursor.execute(add_tweet_query)
