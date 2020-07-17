# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.
from datetime import timedelta
from os import environ
from collections import OrderedDict

DEBUG = True
FORCE_HTTPS = False

## webserver host and port
HOST = '0.0.0.0'
PORT = 5000

SECRET = 'foobar'
SECRET_KEY = 'my-session-secret'

# SQLALCHEMY_DATABASE_URI = 'postgresql://pybossa:tester@gig_postgres/pybossa'
SQLALCHEMY_DATABASE_URI = 'postgresql://gigwork:GIgW0rk12$@pg_pgdev_dev.bdns.bloomberg.com:4338/appsdb?options=--search_path=gigwork'
##Slave configuration for DB
SQLALCHEMY_BINDS = {
#    'slave': 'postgresql://user:password@server/db'
    'bulkdel': SQLALCHEMY_DATABASE_URI
}

_bcos = {
    'host': 'bcos.dev.blpprofessional.com',
    'port': 8443,
    'host_suffix': '/v1',
    'auth_headers': [('x-bbg-bcos-account', 'access_key'), ('x-bbg-bcos-secret-key', 'secret_key')],
    'aws_access_key_id': 'gigwork_bcos',
    'aws_secret_access_key': '43b065cacded19b383a7099d225fe40a42151b57fbe14ef38ae74d0b475b0295'
}

ITSDANGEROUSKEY = 'its-dangerous-key'

## project configuration
BRAND = 'PyBossa'
TITLE = 'PyBossa'
LOGO = 'default_logo.svg'
COPYRIGHT = 'Set Your Institution'
DESCRIPTION = 'Set the description in your config'
TERMSOFUSE = 'http://okfn.org/terms-of-use/'
DATAUSE = 'http://opendatacommons.org/licenses/by/'
CONTACT_EMAIL = 'info@pybossa.com'
CONTACT_TWITTER = 'PyBossa'

S3_BUCKET = 'gigwork-sandbox'
S3_REQUEST_BUCKET = 'gigwork-sandbox'
S3_UPLOAD_DIRECTORY = 'gig-results'
#S3_IMPORT_BUCKET=S3_REQUEST_BUCKET
# S3_CONN_TYPE = 'bcos-dev'

## Default number of projects per page
## APPS_PER_PAGE = 20

## External Auth providers
# TWITTER_CONSUMER_KEY=''
# TWITTER_CONSUMER_SECRET=''
# FACEBOOK_APP_ID=''
# FACEBOOK_APP_SECRET=''
# GOOGLE_CLIENT_ID=''
# GOOGLE_CLIENT_SECRET=''

## Supported Languages
## NOTE: You need to create a symbolic link to the translations folder, otherwise
## this wont work.
## ln -s pybossa/themes/your-theme/translations pybossa/translations
#DEFAULT_LOCALE = 'en'
#LOCALES = [('en', 'English'), ('es', u'Español'),
#           ('it', 'Italiano'), ('fr', u'Français'),
#           ('ja', u'日本語'),('pt_BR','Brazilian Portuguese')]


## list of administrator emails to which error emails get sent
# ADMINS = ['me@sysadmin.org']

## CKAN URL for API calls
#CKAN_NAME = "Demo CKAN server"
#CKAN_URL = "http://demo.ckan.org"


## logging config
# Sentry configuration
# SENTRY_DSN=''
LOG_DICT_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(name)s:%(levelname)s:[%(asctime)s] %(message)s [in %(pathname)s:%(lineno)d]',
        }
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'level': 'DEBUG',
            'formatter': 'default'
        }
    },
    'loggers': {
        'pybossa': {
            'level': 'DEBUG',
            'handlers': ['stdout'],
            'formatter': 'default'
        }
    }
}



S3_UPLOAD = _bcos
S3_TASK_REQUEST = _bcos
S3_TASKRUN = _bcos
S3_IMPORT = _bcos
##S3_PRES_CONN = _bcos


# PRESENTERS = ["basic", "annex", "helper-components"]
# S3_PRESENTER_BUCKET = "gigwork-task-presenter-templates"
# S3_PRESENTERS = {"annex": "annex_presenter.html", "helper-components": "helper_components_presenter.html"}

S3_PRES_CONN = _bcos
S3_CONN_TYPE = 'bcos-dev'
S3_PRESENTER_BUCKET = "gigwork-task-presenter-templates"
PRESENTERS = ["basic", "annex", "helper-components", "entity-tagging", "pointshoot-base", "relevancy"]
S3_PRESENTERS = {
    "annex": "annex_presenter.html",
    "helper-components": "helper_components_presenter.html",
    "entity-tagging": "entity_tagging_presenter.html",
    "pointshoot-base": "pointshoot-base.html",
    "relevancy": "relevancy.html"
}

## Mail setup
MAIL_SERVER = 'relay.bloomberg.com'
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_PORT = 25
MAIL_FAIL_SILENTLY = False
MAIL_DEFAULT_SENDER = 'PyBossa Support <info@pybossa.com>'

## Announcement messages
## Use any combination of the next type of messages: root, user, and app owners
## ANNOUNCEMENT = {'admin': 'Root Message', 'user': 'User Message', 'owner': 'Owner Message'}

## Enforce Privacy Mode, by default is disabled
## This config variable will disable all related user pages except for admins
## Stats, top users, leaderboard, etc
ENFORCE_PRIVACY = False


## Cache setup. By default it is enabled
## Redis Sentinel
# List of Sentinel servers (IP, port)
# REDIS_MASTER_DNS = 'redis_master'
# REDIS_SLAVE_DNS = 'redis_master'
# REDIS_PORT = 6379
REDIS_SENTINEL = [(u'10.34.160.157', 16430), (u'10.122.104.85', 16430), (u'10.122.104.78', 16430), (u'10.34.160.113', 16430)]
REDIS_SENTINELS = ','.join(':'.join(str(x) for x in s) for s in REDIS_SENTINEL)
RQ_POLL_INTERVAL = 2500

REDIS_MASTER = 'gigwork_prv_qa'
REDIS_MASTER_NAME = REDIS_MASTER
REDIS_DB = 0
# REDIS_PWD =
REDIS_KEYPREFIX = 'pybossa_cache'
REDIS_SOCKET_TIMEOUT = 500

## Allowed upload extensions
ALLOWED_EXTENSIONS = ['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'zip']

## If you want to use the local uploader configure which folder
UPLOAD_METHOD = 'local'
UPLOAD_FOLDER = 'uploads'

## If you want to use Rackspace for uploads, configure it here
# RACKSPACE_USERNAME = 'username'
# RACKSPACE_API_KEY = 'apikey'
# RACKSPACE_REGION = 'ORD'

## Default number of users shown in the leaderboard
# LEADERBOARD = 20
## Default shown presenters
# PRESENTERS = ["basic", "image", "sound", "video", "map", "pdf"]
# S3_PRESENTER_BUCKET = "presenter-bucket"
# S3_PRESENTERS = {"presenter_name": "path/to/presenter.html"}

# Default Google Docs spreadsheet template tasks URLs
TEMPLATE_TASKS = {}

# Expiration time for password protected project cookies
PASSWD_COOKIE_TIMEOUT = 60 * 30

# Login settings
REMEMBER_COOKIE_NAME = 'gw_remember_token'
PERMANENT_SESSION_LIFETIME = timedelta(hours=100)

# Expiration time for account confirmation / password recovery links
ACCOUNT_LINK_EXPIRATION = 5 * 60 * 60

## Ratelimit configuration
# LIMIT = 300
# PER = 15 * 60

# Disable new account confirmation (via email)
ACCOUNT_CONFIRMATION_DISABLED = True

# Mailchimp API key
# MAILCHIMP_API_KEY = "your-key"
# MAILCHIMP_LIST_ID = "your-list-ID"

# Flickr API key and secret
# FLICKR_API_KEY = 'your-key'
# FLICKR_SHARED_SECRET = 'your-secret'

# Dropbox app key
# DROPBOX_APP_KEY = 'your-key'

# Send emails weekly update every
# WEEKLY_UPDATE_STATS = 'Sunday'

# Youtube API server key
# YOUTUBE_API_SERVER_KEY = 'your-key'

# Enable Server Sent Events
# WARNING: this will require to run PyBossa in async mode. Check the docs.
# WARNING: if you don't enable async when serving PyBossa, the server will lock
# WARNING: and it will not work. For this reason, it's disabled by default.
# SSE = False

# Add here any other ATOM feed that you want to get notified.
NEWS_URL = ['https://github.com/pybossa/enki/releases.atom',
            'https://github.com/pybossa/pybossa-client/releases.atom',
            'https://github.com/pybossa/pbs/releases.atom']

# Pro user features. False will make the feature available to all regular users,
# while True will make it available only to pro users
PRO_FEATURES = {
    'auditlog':              True,
    'webhooks':              True,
    'updated_exports':       True,
    'notify_blog_updates':   True,
    'project_weekly_report': True,
    'autoimporter':          True,
    'better_stats':          True
}

# Libsass style. You can use nested, expanded, compact and compressed
LIBSASS_STYLE = 'compressed'

# CORS resources configuration.
# WARNING: Only modify this if you know what you are doing. The below config
# are the defaults, allowing PYBOSSA to have full CORS api.
# For more options, check the Flask-Cors documentation: https://flask-cors.readthedocs.io/en/latest/
# CORS_RESOURCES = {r"/api/*": {"origins": "*",
#                               "allow_headers": ['Content-Type',
#                                                 'Authorization'],
#                               "methods": "*"
#                               }}

# Email notifications for background jobs.
# FAILED_JOBS_MAILS = 7
# FAILED_JOBS_RETRIES = 3

# Language to use stems, full text search, etc. from postgresql.
# FULLTEXTSEARCH_LANGUAGE = 'english'


# Use strict slashes at endpoints, by default True
# This will return a 404 if and endpoint does not have the api/endpoint/
# while if you configured as False, it will return the resource with and without the trailing /
# STRICT_SLASHES = True

# Use SSO on Disqus.com
# DISQUS_SECRET_KEY = 'secret-key'
# DISQUS_PUBLIC_KEY = 'public-key'

# Use Web Push Notifications
# ONESIGNAL_APP_ID = 'Your-app-id'
# ONESIGNAL_API_KEY = 'your-app-key'

# Enable two factor authentication
# ENABLE_TWO_FACTOR_AUTH = True

# Strong password policy for user accounts
# ENABLE_STRONG_PASSWORD = True

# Create new leaderboards based on info field keys from user
# LEADERBOARDS = ['foo', 'bar']

# AVAILABLE_IMPORTERS = ['localCSV']

# Unpublish inactive projects
# UNPUBLISH_PROJECTS = True

# Use this config variable to create valid URLs for your SPA
# SPA_SERVER_NAME = 'https://yourserver.com'

# LDAP
# LDAP_HOST = '127.0.0.1'
# LDAP_BASE_DN = 'ou=users,dc=scifabric,dc=com'
# LDAP_USERNAME = 'cn=yourusername,dc=scifabric,dc=com'
# LDAP_PASSWORD = 'yourpassword'
# LDAP_OBJECTS_DN = 'dn'
# LDAP_OPENLDAP = True
# Adapt it to your specific needs in your LDAP org
# LDAP_USER_OBJECT_FILTER = '(&(objectclass=inetOrgPerson)(cn=%s))'
# LDAP_USER_FILTER_FIELD = 'cn'
# LDAP_PYBOSSA_FIELDS = {'fullname': 'givenName',
#                        'name': 'uid',
#                        'email_addr': 'cn'}

# Flask profiler
# FLASK_PROFILER = {
#     "enabled": True,
#     "storage": {
#         "engine": "sqlite"
#     },
#     "basicAuth":{
#         "enabled": True,
#         "username": "admin",
#         "password": "admin"
#     },
#     "ignore": [
#       "^/static/.*"
#   ]
# }

# disallow api access without login using api key that can bypass two factor authentication
# SECURE_APP_ACCESS = True

# allow admin access to particular email addresses or to specific email accounts
# SUPERUSER_WHITELIST_EMAILS = ['@mycompany.com$', '^admin@mycompany.com$', '^subadmin@mycompany.com$']
SQLALCHEMY_TRACK_MODIFICATIONS = False
AVAILABLE_IMPORTERS = ['localCSV']



# # Access control configurations
# ENABLE_ACCESS_CONTROL = True

# VALID_ACCESS_LEVELS  = [("L1", "L1"), ("L2", "L2"),
#         ("L3", "L3"), ("L4", "L4")]

# # Given project/task level, return valid user levels
# # Project/task with L1, users only with level L1 permitted
# # Project/task with L2, users with levels L1, L2 permitted ...
# # Key: project/task level, Value: implicit valid user levels
# VALID_USER_LEVELS_FOR_PROJECT_TASK_LEVEL = dict(L1=[],
#     L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"])

# # Given a user level, return valid project/task levels
# # Users with L1 can work on project/tasks with level L2, L3, L4
# # Key: user level, Value: implicit valid levels for project/task
# VALID_TASK_LEVELS_FOR_USER_LEVEL = dict(L1=["L2", "L3", "L4"],
#     L2=["L3", "L4"], L3=["L4"], L4=[])

# # Given the access control level for a task (key), a project must have one of
# # the access control levels in the value list in order for the task to be
# # assignable to the project.
# VALID_PROJECT_LEVELS_FOR_TASK_LEVEL = dict(
#     L1=["L1"], L2=["L1", "L2"], L3=["L1", "L2", "L3"], L4=["L1", "L2", "L3", "L4"])

# # Given the access control level of a project (key), a task must be one of
# # the access control levels in the value list in order for the task to be
# # assignable to the project.
# VALID_TASK_LEVELS_FOR_PROJECT_LEVEL = dict(
#     L1=["L1", "L2", "L3", "L4"], L2=["L2", "L3", "L4"], L3=["L3", "L4"], L4=["L4"])

# # Defined data access levels based on user type
# VALID_ACCESS_LEVELS_FOR_USER_TYPES = {
#     'Full-time Employee': ["L1", "L2", "L3", "L4"],
#     'Intern': ["L1", "L2", "L3", "L4"],
#     'Part-time Employee': ["L1", "L2", "L3", "L4"],
#     'Temporary Employee': ["L1", "L2", "L3", "L4"],
#     'Formax Vendor': ["L2", "L3", "L4"],
#     'Infosys Vendor': ["L2", "L3", "L4"],
#     'Innodata Vendor': ["L2", "L3", "L4"],
#     'Liberty Vendor': ["L2", "L3", "L4"],
#     'Mindcrest Vendor': ["L2", "L3", "L4"],
#     'Tata Vendor': ["L2", "L3", "L4"],
#     'Wipro Vendor': ["L2", "L3", "L4"],
#     'iMerit Vendor': ["L2", "L3", "L4"]
# }

# ENABLE_ENCRYPTION = True
# FILE_ENCRYPTION_KEY = 'aloooo'
# from collections import OrderedDict
# EXTERNAL_CONFIGURATIONS = OrderedDict([
#     ('gigwork_poller', {
#         'display': 'BBDS poller',
#         'fields': {
#             'service': ('HiddenField', 'Service', None, {
#                 'default': 'bcos-dev'
#             }),
#             'target_bucket': ('TextField', 'BCOS bucket', None)
#         }
#     }),
#     ('data_access', {
#         'display': 'Data Access',
#         'fields': {
#             'tracking_id': ('TextField', 'SDSK Number', None)
#         }
#     }),
#     ('encryption', {
#         'display': 'Encryption for request/response files',
#         'fields': {
#             'bpv_key_id': ('TextField', 'BPV ID for Private Key', None)
#         }
#     }),
#     ('hdfs', {
#         'display': 'HDFS Config',
#         'fields': {
#             'cluster': ('SelectField', 'Cluster', None, {
#                 'choices': [('dnj2-gen', 'DNJ2-GEN'), ('dob2-gen', 'DOB2-GEN')]
#             }),
#             'path': ('TextField', 'Path for responses', None)
#         }
#     })
# ])

WIZARD_STEPS = OrderedDict([
    ('new_project', {
        'title': 'Project Creation',
        'icon': 'fa fa-pencil',
        'href': {'url_for': 'project.new',
                 'args': ['']},
        'done_checks': {'always': False},
        'enable_checks': {'always': True},
        'visible_checks': {'and': ['not_project_exist'], 'or': []},
    }),
    ('project_details', {
        'title': 'Project Details',
        'icon': 'fa fa-pencil',
        'href': {'url_for': 'project.update',
                 'args': ['short_name']},
        'done_checks': {'always': True},
        'enable_checks': {'always': True},
        'visible_checks': {'and': ['project_exist'], 'or': []}
    }),
    ('task_imports', {
        'title': 'Task Imports',
        'icon': 'fa fa-file',
        'href': {'url_for': 'project.import_task',
                 'args': ['short_name']},
        'done_checks': {'and': ['tasks_amount'], 'or': []},
        'enable_checks': {'and': ['project_exist'], 'or': []},
        'visible_checks': {'always': True}
    }),
    ('task_presenter', {
        'title': 'Task Presenter',
        'icon': 'fa fa-pencil',
        'href': {'url_for': 'project.task_presenter_editor',
                 'args': ['short_name']},
        'done_checks': {'and': ['task_presenter'], 'or': []},
        'enable_checks': {'and': ['tasks_amount'], 'or': ['task_presenter', 'project_publish']},
        'visible_checks': {'always': True}
    }),
    ('task_settings', {
        'title': 'Task Settings',
        'icon': 'fa fa-cogs',
        'href': {'url_for': 'project.task_settings',
                 'args': ['short_name']},
        'done_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'enable_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'visible_checks': {'always': True}
    }),
    ('publish', {
        'title': 'Publish',
        'icon': 'fa fa-check',
        'href': {'url_for': 'project.publish',
                 'args': ['short_name', 'published']},
        'done_checks': {'always': False},
        'enable_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'visible_checks': {'and': ['not_project_publish'], 'or': ['not_project_exist']},
    }),
    ('published', {
        'title': 'Published',
        'icon': 'fa fa-check',
        'href': {'url_for': 'project.details',
                 'args': ['short_name']},
        'done_checks': {'always': True},
        'enable_checks': {'always': True},
        'visible_checks': {'and': ['project_publish'], 'or': []},
    })]
)

DATA_CLASSIFICATION = [
    ('', True),
    ('L1 - Restricted Client Data', False),
    ('L1 - Limited Access Client Data', False),
    ('L2 - Community-Wide Client Data', False),
    ('L2 - Restricted Internal Data', False),
    ('L2 - Limited Access internal Data', False),
    ('L2 - Restricted Third-Party Data', False),
    ('L2 - Limited Access Third-Party Data', False),
    ('L3 - Community-Wide Internal Data', False),
    ('L4 - Public Internal Data', True),
    ('L4 - Public Third-Party Data', True)
]
VALID_DATA_CLASSES = [data_class for data_class, enabled in DATA_CLASSIFICATION if enabled and data_class]
VALID_ACCESS_LEVELS = sorted(set(data_class.split('-')[0].strip() for data_class in VALID_DATA_CLASSES))

SERVER_TYPE = ""

BSSO_SETTINGS = {
    "strict": False,
    "debug": True,
    "sp": {
        "entityId": "WebChampBSSOSample",
        "assertionConsumerService": {
            "url": "http://localhost:5000/bloomberg/login",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTPS-POST",
        },
        "singleLogoutService": {
            "url": "http://localhost:5000/bloomberg/logout/",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:transient",
        "x509cert": "MIIEowIBAAKCAQEAw3UyNn0OWwRZiOVeOEAlxpfKdTl1ezx8rCUBpGHw5UtKomCvNUcc9Bv7hzUsBLCq/GgwZFvOvMmB/K1KyKujr8mGVH/fCTsGFyZxCusAEgGgDC0Z/tLqxsQBAS0PxNbAJVlQghJfgbixCiMBenpPhu/xy5CdFxhOoJBkLm6ec5hs72vO9ek8xoY9nfnxoS6cX1uJ6Xj6wjHgxF1VJ/0ZUA7lGM9t4dsKrbLkHO49s8O74d+TaQUZEiPyifA3prz2ucQOvPKeHCqchFUIthVWK1v6YpvVBGjR1op4xRbLmpnPIqQPyLXUwb5KWt/2YWfH7mvsqSAzy/w2i9EQFvXsuQIDAQABAoIBAQDA/oyJHuw41M+vi4OAGV7ze9fN7eFhwPT9aUD41jhtv+0+7iayfbhKFQNEmy0OqH784ce+oKQ+5t2x6E5qXIgwv9UixGwvChfWbf+6nxYfsXkd7L65TfvCLbEsPxlN7BooBsum04t4ZCxzbOM9012JSI1AyldCgZ7JjilNa66LRZ40sBFC2groGcm1nW2XVkV35P3u6aH4XbNTCfvU+ttGkDBju/t0zsHxfXnjZ5pqqwS4YtAWFMA4t8i4my9fkUTTub+VZStzGcSlxQ8V1GqWenRZ1cGxpQ7LNPx8mtQWuS7EzaXOyqJNst7Je3AL+zcZStzMrRDr6L8zwf+Py849AoGBAP2mjMKpiNKYXWAGMBhbu0K3f2Eu/SO5LfdHI4qNzK3uErp5Ifv8GlRDF+a3eY9b6p6rw2DgmjOTm9MvrdDjpwEjtMgD7NSd6ibNNRiJVFJCxvoyOgSO2eSOpqdpNsIykoMEnScndEKa7TEKD4CqK3WS4eoMRqm915d7MjWkfrfrAoGBAMVEqTTWGPAThE96Zf9HKwXDVj9ZeqlazdF5Fygdli4Q9pi4j0Jt/Yu1uqsbYnvg8oCkIjuCc9YAIcYUK59fxkViOaf9Vi+/g480vAdYiZzy4igBaFLojMDWZkwoBJqOPi18U2J5evH0OOBEne1WULgCn4DI67L7DnF7Nyv/e0jrAoGAfbZq8xuVPVLYjHvkoF3ubH2He0IPogHoXzL50XS/6cAhthvNFRd4cSSjlux+KegTWzqj5cLLih5xT3TE/8+keLMaqTsQyLvPThXMZ/HAQdjoxx3XlWS7Z0SwIi7KPetUo+zIepxaSZyBTBnBXzJ3wZjfsOEOsJfvXxtm4iE50KsCgYBc9vea287SzQ/MeM06mapvw9eQcTW6O/3E2wELua29tebQoCF7V+RmA9Wdr4EhCiiecTtkuhym3FcORxErwXHp3tl3Do+gXuu8AEkgWRw5J8lmuwsUD13NvvxkpXNN9vzcaLvPK5rCDasEHbIjWEsf/LR4d7eEGIZ8+mlMxdCu0wKBgDBZiMFr1dKY5J1e36j6HutXlBoKfJW0DnVbpT0Fa+KuqRD0q2afv1bcF6QrVSQw0APHvW/6Wt1DufZegM1EhCDvHG3auYSQlunaEOMfIwbn62uTAga4o2De8j/kJLB55MXGmyJgFbxO063bg6ce/s9HC6ZU1xAVP2UKsKifFrit",  # noqa: E501
        "privateKey": "MIIEowIBAAKCAQEAw3UyNn0OWwRZiOVeOEAlxpfKdTl1ezx8rCUBpGHw5UtKomCvNUcc9Bv7hzUsBLCq/GgwZFvOvMmB/K1KyKujr8mGVH/fCTsGFyZxCusAEgGgDC0Z/tLqxsQBAS0PxNbAJVlQghJfgbixCiMBenpPhu/xy5CdFxhOoJBkLm6ec5hs72vO9ek8xoY9nfnxoS6cX1uJ6Xj6wjHgxF1VJ/0ZUA7lGM9t4dsKrbLkHO49s8O74d+TaQUZEiPyifA3prz2ucQOvPKeHCqchFUIthVWK1v6YpvVBGjR1op4xRbLmpnPIqQPyLXUwb5KWt/2YWfH7mvsqSAzy/w2i9EQFvXsuQIDAQABAoIBAQDA/oyJHuw41M+vi4OAGV7ze9fN7eFhwPT9aUD41jhtv+0+7iayfbhKFQNEmy0OqH784ce+oKQ+5t2x6E5qXIgwv9UixGwvChfWbf+6nxYfsXkd7L65TfvCLbEsPxlN7BooBsum04t4ZCxzbOM9012JSI1AyldCgZ7JjilNa66LRZ40sBFC2groGcm1nW2XVkV35P3u6aH4XbNTCfvU+ttGkDBju/t0zsHxfXnjZ5pqqwS4YtAWFMA4t8i4my9fkUTTub+VZStzGcSlxQ8V1GqWenRZ1cGxpQ7LNPx8mtQWuS7EzaXOyqJNst7Je3AL+zcZStzMrRDr6L8zwf+Py849AoGBAP2mjMKpiNKYXWAGMBhbu0K3f2Eu/SO5LfdHI4qNzK3uErp5Ifv8GlRDF+a3eY9b6p6rw2DgmjOTm9MvrdDjpwEjtMgD7NSd6ibNNRiJVFJCxvoyOgSO2eSOpqdpNsIykoMEnScndEKa7TEKD4CqK3WS4eoMRqm915d7MjWkfrfrAoGBAMVEqTTWGPAThE96Zf9HKwXDVj9ZeqlazdF5Fygdli4Q9pi4j0Jt/Yu1uqsbYnvg8oCkIjuCc9YAIcYUK59fxkViOaf9Vi+/g480vAdYiZzy4igBaFLojMDWZkwoBJqOPi18U2J5evH0OOBEne1WULgCn4DI67L7DnF7Nyv/e0jrAoGAfbZq8xuVPVLYjHvkoF3ubH2He0IPogHoXzL50XS/6cAhthvNFRd4cSSjlux+KegTWzqj5cLLih5xT3TE/8+keLMaqTsQyLvPThXMZ/HAQdjoxx3XlWS7Z0SwIi7KPetUo+zIepxaSZyBTBnBXzJ3wZjfsOEOsJfvXxtm4iE50KsCgYBc9vea287SzQ/MeM06mapvw9eQcTW6O/3E2wELua29tebQoCF7V+RmA9Wdr4EhCiiecTtkuhym3FcORxErwXHp3tl3Do+gXuu8AEkgWRw5J8lmuwsUD13NvvxkpXNN9vzcaLvPK5rCDasEHbIjWEsf/LR4d7eEGIZ8+mlMxdCu0wKBgDBZiMFr1dKY5J1e36j6HutXlBoKfJW0DnVbpT0Fa+KuqRD0q2afv1bcF6QrVSQw0APHvW/6Wt1DufZegM1EhCDvHG3auYSQlunaEOMfIwbn62uTAga4o2De8j/kJLB55MXGmyJgFbxO063bg6ce/s9HC6ZU1xAVP2UKsKifFrit",  # noqa: E501
    },
    "idp": {
        "entityId": "https://bssobeta.blpprofessional.com",
        "singleSignOnService": {
            "url": "https://bssobeta.bloomberg.com/idp/SSO.saml2",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "singleLogoutService": {
            "url": "https://bssobeta.bloomberg.com/idp/SSO.saml2",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "x509cert": "MIIDejCCAmKgAwIBAgIGAVPEn4eqMA0GCSqGSIb3DQEBCwUAMH4xCzAJBgNVBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxFjAUBgNVBAoTDUJsb29tYmVyZyBMLlAxDDAKBgNVBAsMA1ImRDEjMCEGA1UEAxMaYnNzb2JldGEtaWRwLmJsb29tYmVyZy5jb20wHhcNMTYwMzI5MjMwNTAyWhcNMjYwMzI3MjMwNTAyWjB+MQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlvcmsxETAPBgNVBAcTCE5ldyBZb3JrMRYwFAYDVQQKEw1CbG9vbWJlcmcgTC5QMQwwCgYDVQQLDANSJkQxIzAhBgNVBAMTGmJzc29iZXRhLWlkcC5ibG9vbWJlcmcuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoW1r4QVEkArX+uzM5wNBj6cwPT8gfNTU9UFvHm1HQALjOt8Po6kuzYUE3BK9exi/w+9Qg5TvyDBo+/KqtPACRhjcZsj9XCRfb7mnLjSzEQHHjSqui64JPR8v5h746Sy4E4anRcFF1YSVfB+SH9l0qKGvsApwWNbxSfemDgh9eFAy5yaezlS1ldhJhA3cxDKEXsXo7Z9VEgHEQW1SLhsgrjSiXDH3kecEO5cplwPfDKNBTaxIKSMObKOD1XaczHY55ygTrj9n78aOVeQb0cG1RjOQD//voiHokCNNcasEst1kKMkAsfqGKQR0JY0uvRXnwmS7PjjhZ7MyiGsVNd9UzwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQAW+Z8v5EIyNqPTwQZVdfwbjNq2UD9AkgmKvO7+p+ke5zwZ3qqXj0fZ/hiaWv5i1hDUEJkZ+uPk6idXS+svseFrLgIkHbsaEx945pY7kXiAAGFiaAXOZBwW7RLD1r9JAnS3sdE/N3Afjjksr97PFKLedp9EXpldn940F0QvPK4TwVyPi7XyxLILBpTMkyynhNTOz1keJjlDYNwDowkgfWvMaSRFPMDzN6qTx2lp2AjILqZP/yFT/HB6ltoDmVzcfnQc2x0j3kDs8WvnvMIJNl9aPMyANjRq88GM3mnG/TY/9LnF5FwxKLGripVan+tM8eJI+vidGahQmHwGp5bZnRCM",  # noqa: E501
    },
    "security": {"authnRequestsSigned": True},
}



PRODUCTS_SUBPRODUCTS = {
    'BGOV': ['Government Affairs', 'Government Contracting'],
    'BLAW': ['BBNA Tax', 'BLAW Acquisition', 'Caselaw', 'Citator', 'Dockets', 'Legal Data Analysis',
        'Primary Legal Content', 'Secondary Legal Content', 'Data Coordinator', 'Data Technology'],
    'BLAW Managers / Support': ['Managers & Support'],
    'Commodities & Energy': ['BNEF', 'Commodities'],
    'Companies': ['Entity Management', 'Company Filings', 'MiFID II'],
    'Economics': ['Economics'],
    'Equity': ['BICS', 'Earnings Estimates', 'ESG', 'EVTS / Transcripts', 'Fundamentals',
        'M&A / Equity Capital Markets', 'Private Equity', 'Dividend Forecasting-BDVD', 'Corporate Actions',
        'Bloomberg Intelligence Support', 'Industry Experts', 'BRES', 'Deep Estimates', 'IR/Management',
        'Supply Chain'],
    'Event Bus': ['Event Bus'],
    'Exchanges': ['Market Structure', 'Business Analyst', 'Business Manager', 'CABM Managers / Support',
        'Project Manager'],
    'F&O/FX/MSG Mining': ['F&O', 'FX', 'MSG Mining'],
    'Fixed Income': ['CAST', 'Municipals', 'Mortgages', "Corporates, Govt's & MMKT", 'Loans',
        'Muni FA', 'Ratings & Curves'],
    'Funds & Holdings': ['Funds', 'Hedge Funds', 'Investor Profiles', 'Ownership', 'Portfolios',
        'Mandates', 'Separately Managed Accounts'],
    'GD Managers / Support': ['CABM Managers / Support', 'Admin', 'Business Development',
        'Business Support', 'Managers & Support', 'Managers BS', 'Managers BZ', 'Managers DM',
        'Managers DT', 'Managers LS', 'Managers NO', 'Managers PW', 'Managers TL', 'Training',
        'Vendor Support'],
    'GDA': ['GDA'],
    'GEI': ['GEI'],
    'GIS/Maps': ['GIS/Maps'],
    'Green Markets': ['Green Markets'],
    'ID Services': ['LEI', 'Regulation', 'BBGID'],
    'Indices': ['3rd Party Indices', 'Bloomberg Indices'],
    'KYC': ['Entity Exchange'],
    'Lifestyles': ['Lifestyles'],
    'Localization': ['Localization'],
    'News Support': ['Automation', 'Indexing', 'News Acquisition', 'News Extraction', 'Web Content'],
    'Non-GD': ['Enterprise', 'News', 'Sales'],
    'PORT': ['PORT QA'],
    'Pricing': ['Account Management', 'CABM Managers / Support', 'Content Specialist',
        'Pricing - Placeholder', 'Product Development'],
    'Product Development': ['DATA <GO>'],
    'Profiles': ['Profiles'],
    'Regulation': ['Regulation'],
    'Research': ['Account Management', 'CABM Managers / Support', 'Content Specialist',
        'Entitlement Specialist', 'Product Development'],
    'Search Bar': ['Search Bar'],
    'Technology': ['Automated Quality Control', 'Business Intelligence', 'Data Engineering', 'Data Governance',
        'Data Pipelining', 'Data Sciences', 'EMEA TechOps', 'GDTO Managers / Support', 'Integration & Support',
        'NY TechOps', 'Operational Analysis', 'Project Management Office', 'Technology Advocates'],
    'Third Party': ['CABM Managers / Support', 'Third Party'],
    'Training': ['GDTP']
}