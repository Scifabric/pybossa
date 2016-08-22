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
Original installation instructions can be found [here](http://docs.pybossa.com/en/latest/installing_pybossa.html). However, the Amnesty Decoders implementation requires some additional considerations. Specifically in regards to setting up MongoDB, a custom API for one of the projects, and setting up hosting with Apache httpd.

**IMPORTANT:** Please still read through the [original PyBossa installation instructions](http://docs.pybossa.com/en/latest/installing_pybossa.html) as it provides necessary context and explanation for all of the project's depenedencies.

## 3.1. Install MongoDB
Follow [these instructions](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/).

## 3.2. Install Apache Virtual Hosts 
```
sudo apt-get update
sudo apt-get install apache2
```

## 3.3. Checkout the Project
Be sure to use the --recursive flag to fetch submodules:
```
cd /var/www
git clone --recursive https://github.com/AltClick/pybossa-amnesty-microtasking.git
cd /var/www/pybossa-amnesty-microtasking
```

## 3.4. Install the Project
These instructions are beased on [the official PyBossa installation and configuration instructions](http://docs.pybossa.com/en/latest/install.html). They have been slightly modified for this specifcities related to this project.

#### 3.4.1. Install PostgreSQL Database
```
sudo apt-get install postgresql postgresql-server-dev-all libpq-dev python-psycopg2
```

#### 3.4.2. Install virtualenv
```
sudo apt-get install python-virtualenv
```

#### 3.4.3. Install the PyBossa Python requirements
```
sudo apt-get install python-dev build-essential libjpeg-dev libssl-dev swig libffi-dev dbus libdbus-1-dev libdbus-glib-1-dev
```

#### 3.4.4. Install the Project's Python libraries
The libraries are listed in /var/www/pybossa-amnesty-microtasking/requirements.txt
```
bash install.sh
```

### 3.5. Configuring PostgreSQL Database
#### 3.5.1. Create user for the app
```
sudo su postgres
createuser -d -P pybossa
```

Use password `tester` when prompted.

#### 3.5.2. Create the database
```
createdb pybossa -O pybossa
```

Exit the postgresql user:
```
exit
```

#### 3.5.3. Populate the database with its tables:
```
bash db_create.sh
```

### 3.6. Config Files
#### 3.6.1. Create a settings file and enter your SQLAlchemy DB URI (you can also override default settings as needed):
```
cp settings_local.py.tmpl settings_local.py
# now edit ...
nano settings_local.py
```

#### 3.6.1. Create the alembic config file and set the sqlalchemy.url to point to your database:
```
cp alembic.ini.template alembic.ini
# now set the sqlalchemy.url ...
nano alembic.ini
```

### 3.7. Install Redis

#### 3.7.1. Install
```
sudo apt-get install redis-server
```

#### 3.7.2. Run
In the contrib folder you will find a file named sentinel.conf that should be enough to run the sentinel node. Thus, for running it:
```
redis-server contrib/sentinel.conf --sentinel
```

#### 3.7.3. Run Scheduler and Jobs
```
bash run rqscheduler.sh &
bash run jobs.sh &
```

If somewher down the line you supect that the scheduler or the jobs are not running, you can check if they are still running like so:
```
ps ax | grep rqscheduler.sh
ps ax | grep jobs.sh
```

## 3.8. Hosting Project on Apache Virtual Host
## 3.8.1. Create the project's app.wsgi file:
```
sudo cp app.wsgi.tmpl app.wsgi
```

Open the new file in your editor with root privileges:
```
sudo nano app.wsgi
```

And configure the project's path:
```
app_dir_path = '/var/www/pybossa-amnesty-microtasking'
```

## 3.8.2. Install mod_wsgi
```
sudo apt-get install libapache2-mod-wsgi
```

## 3.8.3. Create virtual host config file
Copy default to create new file specific to the project:
```
sudo cp /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/decoders.amnesty.org.conf
```

Open the new file in your editor with root privileges:
```
sudo nano /etc/apache2/sites-available/decoders.amnesty.org.conf
```

And configure it to point to the project's app.wsgi file:
```
<VirtualHost *:80>
  ServerAdmin admin@localhost
  #ServerName decoders.amnesty.org
  
  WSGIScriptAlias / /var/www/pybossa-amnesty-microtasking/app.wsgi
  <Directory /var/www/pybossa-amnesty-microtasking>
    Order allow,deny
    Allow from all
  </Directory>
    
  ErrorLog ${APACHE_LOG_DIR}/error.log
  CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

## 3.8.4. Enably New Virtual Host File
First disable the defaul one:
```
sudo a2dissite 000-default.conf
```

Then enable the new one we just created:
```
sudo a2ensite decoders.amnesty.org.conf
```

Restart the server for these changes to take effect:
```
sudo service apache2 restart
```

## 3.9. Load the Project
Enter the IP adress of the server into the browser, the project should load splendidely.
Should errors be thrown, tail the apache error.log and access.log for clues on the root of the problem.

## 4. Deploy the Latest Codebase
To deploy the latest codebase, you need to do two git pulls from the project repo:
 - The first git pull is for the project.
 - The second git pull is for the project's submodules (e.g. themes).

These are the commands in question:
```
cd /var/www/pybossa-amnesty-microtasking
sudo git pull
sudo git submodule foreach git pull origin master
```

Restart the server for these changes to take effect:
```
sudo service apache2 restart
```



