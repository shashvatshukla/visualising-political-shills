import ArchiveToDBController as ATDBC
import json

keys = open("../../keys.json")
data = json.load(keys)

absolute_path_to_archive = data["archive_path"]
runner = ATDBC.ArchiveToDBController(absolute_path_to_archive)
runner.create_db()
