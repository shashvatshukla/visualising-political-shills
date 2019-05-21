# Visualising Political Shills

Done by Alexandra Timoce, Andrei Cristian Diaconu, Daniel David O’Connor, Ioana-Victoria Iaru, Lu Yuchen, Shashvat Shukla as part of the 2nd Year Group Design Practical done by all undergraduates studying for Computer Science and joint schools at the University of Oxford.

## Problem Identified

We were tasked to identify and solve a problem in the theme of shill accounts on Twitter.

Shill accounts have been used covertly by political actors in recent years to influence public opinion.

We decided to make something to help Election Commissions investigate whether traffic on Twitter about a certain topic had been manipulated. 

As we did not work with a real client, we had to make assumptions about what an Election Commission would want from our app.

The overall goal of Election Commissions is to conduct elections and ensure their fairness. In relation to shill accounts, one can imagine they will have subgoals such as: 
* Identifying shill accounts that are aligned in their goals. 
* Determining which political actors are behind a particular set of related shill accounts.
* Measure and Report the impact of these particular shill accounts
* Inform the public about specific classes of shill accounts
* Understand shill account activity so as to inform future collaborations with and regulations on social media platforms

We designed our solution to help an Election Commission achieve the objectives outlined above.

## What this app can do

First an Election Commission official enters a list of hashtags they would like to investigate and a time period:

![landing page](https://github.com/shashvatshukla/visualising-political-shills/blob/master/screenshots/landingpage.png)

The app will then call twitter APIs for relevant data and perform all our analysis on the data. 

![loading screen](https://github.com/shashvatshukla/visualising-political-shills/blob/master/screenshots/loadingpage.png)

This analysis will be presented on a dashboard...

![dashboard](https://github.com/shashvatshukla/visualising-political-shills/blob/master/screenshots/dashboard.png)

The user may click through to get more details:

![network partitioning page](https://github.com/shashvatshukla/visualising-political-shills/blob/master/screenshots/networkpartition.png)

![repeated tweets page](https://github.com/shashvatshukla/visualising-political-shills/blob/master/screenshots/textcluster.png)

Our analysis metrics include:
* Traffic and Sentiment over Time and Spike detection
* Copied and similar Tweet detection
* Coefficient of Traffic Manipulation ([Ben Nimmo's work](https://comprop.oii.ox.ac.uk/wp-content/uploads/sites/93/2019/01/Manipulating-Twitter-Traffic.pdf))
* Partition of the network based on political affiliation (Inspired by [this paper](https://www.pnas.org/content/pnas/115/49/12435.full.pdf))


Note that since we did not have a paid subscription to the Twitter API, we used a downloaded archive for testing and demonstration - however the code can be adapted to use the Twitter API

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
