import CreateDBFromArchive.ArchiveToDBController as ATDBC

absolute_path_to_archive = "C:\\Users\\Blade\\Desktop\\Archive"
runner = ATDBC.ArchiveToDBController(absolute_path_to_archive)
runner.create_db()
