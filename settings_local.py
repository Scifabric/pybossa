import os

# DEBUG = False

## webserver host and port
# HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 5000))

SECRET = 'foobar'
SECRET_KEY = 'my-session-secret'

SQLALCHEMY_DATABASE_URI = os.environ.get('SHARED_DATABASE_URL', "default_db_url")

## project configuration
BRAND = 'PyBossa'
TITLE = 'PyBossa'
COPYRIGHT = 'Set Your Institution'
DESCRIPTION = 'Set the description in your config'

## External Auth providers
#TWITTER_CONSUMER_KEY = ''
#TWITTER_CONSUMER_SECRET = ''


## list of administrator emails to which error emails get sent
# ADMINS = ['me@sysadmin.org']

## logging config
## set path to enable
# LOG_FILE = '/path/to/log/file'
## Optional log level
# import logging
# LOG_LEVEL = logging.DEBUG

