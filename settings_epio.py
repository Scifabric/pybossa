DEBUG = True

from bundle_config import config
SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (
    config['postgres']['username'],
    config['postgres']['password'],
    config['postgres']['host'],
    int(config['postgres']['port']),
    config['postgres']['database']
    )

TITLE = 'PyBossa Demo'
COPYRIGHT = 'Open Knowledge Foundation'
DESCRIPTION = "This is a demo of PyBossa, the open-source micro-tasking platform. Find out more at http://pybossa.readthedocs.com/"

## list of administrator emails to which error emails get sent
# ADMINS = ['me@sysadmin.org']

## logging config
## set path to enable
# LOG_FILE = '/path/to/log/file'
## Optional log level
# import logging
# LOG_LEVEL = logging.DEBUG

