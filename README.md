# 1. Technical Background

- The [Amnesty Decoders project](https://decoders.amnesty.org/) is a customized implementation of [PyBossa](http://pybossa.com/).
- The platform is a fork of [PyBossa v1.6.1](https://github.com/PyBossa/pybossa/releases/tag/v1.6.1).
- The original README of the forked project can be found [here](https://github.com/PyBossa/pybossa/blob/1155b6f57fc7a152916ccc003e40df7f763aa60f/README.md).

# 2. Environment
- [Ubuntu 14.04.5 LTS (Trusty Tahr)](http://releases.ubuntu.com/14.04/)
- Git
- MongoDB 3.2.x
- Python >= 2.7.6, <3.0
- PostgreSQL >= 9.3
- Redis >= 2.6
- pip >= 6.1
- Apache Virtual Hosts (httpd)

# 3. Installation
Original installation instructions can be found [here](http://docs.pybossa.com/en/latest/installing_pybossa.html). However, the Amnesty Decoders implementation requires some additional considerations. Specifically in regards to setting up MongoDB, a custom API for one of the projects, and setting up hosting with Apache http..

## 3.1 MongoDB
Follow [these instructions](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/)

## 3.2 Apache Virtual Hosts 
```
sudo apt-get update
sudo apt-get install apache2
```

## 3.3 Checkout Project
Be sure to use the --recursive flag to fetch submodules:
```
cd /var/www
git clone --recursive https://github.com/AltClick/pybossa-amnesty-microtasking.git
cd /var/www/pybossa-amnesty-microtasking
```

## 3.4 Installing the Project
These instructions are beased on [the official PyBossa installation and configuration instructions](http://docs.pybossa.com/en/latest/install.html). They have been slightly modified for this specifcities related to this project.

#### 3.4.1 Installing the PostgreSQL database
```
sudo apt-get install postgresql postgresql-server-dev-all libpq-dev python-psycopg2
```

#### 3.4.2 Installing virtualenv
```
sudo apt-get install python-virtualenv
```

#### 3.4.3 Installing the PyBossa Python requirements
```
sudo apt-get install python-dev build-essential libjpeg-dev libssl-dev swig libffi-dev dbus libdbus-1-dev libdbus-glib-1-dev
```

#### 3.4.4 Install Python libraries required to run the Project.
The libraries are listed in /var/www/pybossa-amnesty-microtasking/requirements.txt
```
bash install.sh
```

### 3.5 Configuring PostgreSQL Database
#### 3.5.1 Create user for the app
```
sudo su postgres
createuser -d -P pybossa
```

Use password `tester` when prompted.

#### 3.5.2 Create the database
```
createdb pybossa -O pybossa
```

Exit the postgresql user:
```
exit
```

#### 3.5.3 Populate the database with its tables:
```
bash db_create.sh
```


### 3.6 Config Files
#### 3.6.1 Create a settings file and enter your SQLAlchemy DB URI (you can also override default settings as needed):
```
cp settings_local.py.tmpl settings_local.py
# now edit ...
nano settings_local.py
```

#### 3.6.1 Create the alembic config file and set the sqlalchemy.url to point to your database:
```
cp alembic.ini.template alembic.ini
# now set the sqlalchemy.url ...
nano alembic.ini
```

### 3.7 Installing Redis

#### 3.7.1 Install
```
sudo apt-get install redis-server
```

#### 3.7.2 Run
In the contrib folder you will find a file named sentinel.conf that should be enough to run the sentinel node. Thus, for running it:
```
redis-server contrib/sentinel.conf --sentinel
```

#### 3.7.3 Run Scheduler and Jobs
```
bash run rqscheduler.sh &
bash run jobs.sh &
```

To check if they are running:
```
ps ax | grep rqscheduler.sh
ps ax | grep job.sh
```

