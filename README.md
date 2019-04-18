# Running the app

Ensure you have everything in requirements.txt

    git clone https://github.com/shashvatshukla/visualising-political-shills.git

## On Windows

    start start.bat

## On Linux/Mac

    chmod +x start.sh
    ./start.sh

## Finally

Open localhost:5000 in a browser.

# Setting up a postgres server
## On Windows
1. Download postgresql from: https://www.postgresql.org/download/. 
During the installation you will be prompted to set up a password for the database.
2. Go to Task Manager > Services, find the service postgresql there
and make sure it is running.
3. Add a new environment variable pointing to 
C:\Program Files\PostgreSQL\11\bin. You can log in to the database by writing ```psql -U postgres``` and typing the 
password you chose.
4. The table that is created by the tool is ```tweets```. To see
the contents of the table run ```select * from tweets```.

## On Linux
See https://www.godaddy.com/garage/how-to-install-postgresql-on-ubuntu-14-04/ and
step 4 from the Windows setup.

# Using the Archive to DB tool

After making sure the postgres service is running, make 
sure that the database connection code in ```worker.py``` and ```multithread_controller.py``` 
contain the password you set when you installed postgresql. Then you can
run the tool from the terminal. The program you should run is ```multithread_controller.py``` and it accepts 2
command line args: (relative) path to archive and a list of words
to filter by. 

The file should be run from the main directory. Before running make sure to run 
```set PYTHONPATH=.```(Windows) or ```export PYTHONPATH=.```(Linux or Mac) so that the file ```consts.py``` is recognized.

Eg for the included test Archive in the dir testing/:
 
 ```python metrics/CreateDBFromArchive/multithread_controller.py -a metrics/CreateDBFromArchive/testing/Archive the are```
