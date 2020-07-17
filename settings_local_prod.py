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

# DEBUG = False

## webserver host and port
from collections import OrderedDict
from os import environ
import json

DEBUG = False
FORCE_HTTPS = True

HOST = '0.0.0.0'
PORT = 5000
SERVER_URL = 'https://gigwork.prod.blpprofessional.com'
SERVER_TYPE = 'Private PROD'
DISPLAY_PLATFORM_IDENTIFIER = True

SECRET_KEY = environ.get('PYB_SECRET_KEY')

SQLALCHEMY_DATABASE_URI = environ.get('PYB_SQLALCHEMY_DATABASE_URI')

##Slave, bulkdel configuration for DB
SQLALCHEMY_BINDS = {
    'bulkdel': environ.get('PYB_SQLALCHEMY_BULK_DEL_URI')
}

DATA_ACCESS_MESSAGE = 'Please be sure to <a href="/project/SHORT_NAME/update#data-access">categorize</a> your data according to the <a href="bbg://screens/POLY ID:3606434">Bloomberg Data Classification and Handling Standard</a>.'

CONTACT_ENABLE = ['all']
CONTACT_SUBJECT = 'GIGwork message for project {short_name} by {email}'
CONTACT_BODY = 'A GIGwork support request has been sent for the project: {project_name}.'

ITSDANGEROUSKEY = environ.get('PYB_ITSDANGEROUSKEY')

## project configuration
BRAND = 'GIGwork'
TITLE = 'GIGwork'
LOGO = 'gigwork.png'
COPYRIGHT = 'Set Your Institution'
DESCRIPTION = 'Set the description in your config'
TERMSOFUSE = 'http://okfn.org/terms-of-use/'
DATAUSE = 'http://opendatacommons.org/licenses/by/'
CONTACT_EMAIL = 'gigwork_priv@bloomberg.net'

## Default number of projects per page
APPS_PER_PAGE = 40

## Supported Languages
## NOTE: You need to create a symbolic link to the translations folder, otherwise
## this wont work.
## ln -s pybossa/themes/your-theme/translations pybossa/translations
#DEFAULT_LOCALE = 'en'

LOCALES = [('en', 'English'), ('es', u'Español'),
           ('it', 'Italiano'), ('fr', u'Français'),
           ('ja', u'日本語'),('pt_BR','Brazilian Portuguese')]


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
            'level': 'INFO',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['stdout'],
        'formatter': 'default'
    }
}

## Mail setup
MAIL_SERVER = 'relay.bloomberg.com'
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_PORT = 25
MAIL_FAIL_SILENTLY = False
MAIL_DEFAULT_SENDER = 'GIGwork Support <gigwork_priv@bloomberg.net>'

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
REDIS_SENTINEL = json.loads(environ['PYB_REDIS_SENTINEL'])
REDIS_SENTINELS = ','.join(':'.join(str(x) for x in s) for s in REDIS_SENTINEL)
REDIS_MASTER = environ['PYB_REDIS_MASTER']
REDIS_MASTER_NAME = REDIS_MASTER
REDIS_DB = 0
REDIS_KEYPREFIX = 'pybossa_cache'
REDIS_PWD = environ['PYB_REDIS_PWD']
REDIS_PASSWORD = REDIS_PWD
REDIS_SOCKET_TIMEOUT = 450

## Allowed upload extensions
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'zip']

## If you want to use the local uploader configure which folder
UPLOAD_METHOD = 'cloudproxy'
UPLOAD_BUCKET = 'gigwork-uploads'
UPLOAD_FOLDER = 'uploads'

## If you want to use Rackspace for uploads, configure it here
# RACKSPACE_USERNAME = 'username'
# RACKSPACE_API_KEY = 'apikey'
# RACKSPACE_REGION = 'ORD'

## Default number of users shown in the leaderboard
# LEADERBOARD = 20

# Default Google Docs spreadsheet template tasks URLs
TEMPLATE_TASKS = {}

# Expiration time for password protected project cookies
PASSWD_COOKIE_TIMEOUT = 60 * 30

# Login settings
REMEMBER_COOKIE_NAME = 'gw_remember_token'

from datetime import timedelta
PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
SESSION_REFRESH_EACH_REQUEST = True

# Expiration time for account confirmation / password recovery links
ACCOUNT_LINK_EXPIRATION = 5 * 60

## Ratelimit configuration
LIMIT = 600
PER = 5 * 60
ADMIN_RATE_MULTIPLIER = 4
RATE_LIMIT_BY_USER_ID = True

# Disable new account confirmation (via email)
ACCOUNT_CONFIRMATION_DISABLED = True

# Enable Server Sent Events
# WARNING: this will require to run PyBossa in async mode. Check the docs.
# WARNING: if you don't enable async when serving PyBossa, the server will lock
# WARNING: and it will not work. For this reason, it's disabled by default.
# SSE = False

# Add here any other ATOM feed that you want to get notified.
# NEWS_URL = []

# Pro user features. False will make the feature available to all regular users,
# while True will make it available only to pro users
# PRO_FEATURES = {
#     'auditlog':              True,
#     'webhooks':              True,
#     'updated_exports':       True,
#     'notify_blog_updates':   True,
#     'project_weekly_report': True,
#     'autoimporter':          True,
#     'better_stats':          True
# }

# Libsass style. You can use nested, expanded, compact and compressed
# LIBSASS_STYLE = 'compressed'

# CORS resources configuration.
CORS_RESOURCES = {}
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
FAILED_JOBS_RETRIES = 0

# Language to use stems, full text search, etc. from postgresql.
# FULLTEXTSEARCH_LANGUAGE = 'english'


# Use strict slashes at endpoints, by default True
# This will return a 404 if and endpoint does not have the api/endpoint/
# while if you configured as False, it will return the resource with and without the trailing /
# STRICT_SLASHES = True

# Enable two factor authentication
ENABLE_TWO_FACTOR_AUTH = True

# Strong password policy for user accounts
ENABLE_STRONG_PASSWORD = True

# Create new leaderboards based on info field keys from user
# LEADERBOARDS = ['foo', 'bar']

AVAILABLE_IMPORTERS = ['localCSV']

# Unpublish inactive projects
# UNPUBLISH_PROJECTS = True

# Use this config variable to create valid URLs for your SPA
# SPA_SERVER_NAME = 'https://yourserver.com'

USER_MANUAL_LABEL = 'GIGwork user manual'
USER_MANUAL_URL = 'https://s3.amazonaws.com/cf-s3uploads/gigdocumentation/GIGworkWorkerManual.pdf'
ADMIN_MANUAL_LABEL='{TEAM 770968768 <GO>}'
ADMIN_MANUAL_URL='https://cms.prod.bloomberg.com/team/pages/viewpage.action?pageId=770968768'
ALLOWED_S3_BUCKETS = []
IS_QA = False
PRIVACY_POLICY_PAGE = 'https://www.bloomberg.com/notices/privacy/'
HISTORICAL_CONTRIBUTIONS_AS_CATEGORY = True

# disallow api access without login using api key that can bypass two factor authentication
SECURE_APP_ACCESS = True

# allow admin access to particular email addresses or to specific email accounts
SUPERUSER_WHITELIST_EMAILS = ['@bloomberg.net$$']

SYNC_ENABLED = True
DEFAULT_SYNC_TARGET = 'https://gigwork.prod.blpprofessional.com'
PROJECT_URL = 'https://github.com/bloomberg/pybossa'
GA_ID = 'UA-148346373-1'

ANNOUNCEMENT_LEVELS = {
    'admin': {'display': 'Admin', 'level': 0},
    'owner': {'display': 'Project Creator', 'level': 10},
    'subadmin': {'display': 'Subadmin', 'level': 20},
    'user': {'display': 'User', 'level': 30}
}

ANNOUNCEMENT_LEVEL_OPTIONS = [
    {'text': v['display'], 'value': v['level']} for k, v in ANNOUNCEMENT_LEVELS.iteritems()
]

_bcos = {
    'host': 'bcos.prod.blpprofessional.com',
    'port': 443,
    'host_suffix': '/v1',
    'auth_headers': [('x-bbg-bcos-account', 'access_key'), ('x-bbg-bcos-secret-key', 'secret_key')]
}

S3_UPLOAD = _bcos
S3_TASK_REQUEST = _bcos
S3_TASKRUN = _bcos
S3_IMPORT = _bcos
S3_PRES_CONN = _bcos

S3_BUCKET = 'gigwork-private-response-bcos'
S3_REQUEST_BUCKET = 'gigwork-private-request-bcos'
S3_UPLOAD_DIRECTORY = 'gig-results'
S3_IMPORT_BUCKET=S3_REQUEST_BUCKET
S3_CONN_TYPE = 'bcos-prod'

## Default shown presenters
PRESENTERS = ["basic", "annex", "helper-components", "entity-tagging", "pointshoot-base"]
S3_PRESENTER_BUCKET = "gigwork-task-presenter-templates"
S3_PRESENTERS = {
    "annex": "annex_presenter.html",
    "helper-components": "helper_components_presenter.html",
    "entity-tagging": "entity_tagging_presenter.html",
    "pointshoot-base": "pointshoot-base.html"
}

TASK_REQUIRED_FIELDS = {
    'data_owner': {'val': None, 'check_val': False, 'require_int': True},
    'data_source_id': {'val': None, 'check_val': False, 'require_int': True}
}

EXTERNAL_CONFIGURATIONS = OrderedDict([
    ('gigwork_poller', {
        'display': 'Response File & Consensus Location (BCOS)',
        'fields': {
            'target_bucket': ('TextField', 'BCOS bucket', None)
        }
    }),
    ('hdfs', {
        'display': 'Response File & Consensus Location (HDFS)',
        'fields': {
            'cluster': ('SelectField', 'Cluster', None, {
                'choices': [('pnj2-gen', 'PNJ2-GEN'), ('pob2-gen', 'POB2-GEN')]
            }),
            'path': ('TextField', 'Path for responses', None)
        }
    }),
    ('encryption', {
        'display': 'Encryption for request/response files',
        'fields': {
            'bpv_key_id': ('TextField', 'BPV ID for Private Key', None)
        }
    })
])

EXTERNAL_CONFIGURATIONS_VUE = OrderedDict([
    ('gigwork_poller', {
        'display': 'Response File & Consensus Location (BCOS)',
        'fields': [{
            'type': 'TextField',
            'name': 'target_bucket'
        }]
    }),
    ('hdfs', {
        'display':  'Response File & Consensus Location (HDFS)',
        'fields': [{
            'type': 'SelectField',
            'choices': [('pnj2-gen', 'PNJ2-GEN'), ('pob2-gen', 'POB2-GEN')],
            'name': 'cluster',
        },
        {
            'type': 'TextField',
            'name': 'path'
        }]
    }),
    ('encryption', {
        'display': 'Encryption for request/response files (BPV)',
        'fields': [{
            'type': 'TextField',
            'name': 'bpv_key_id'
        }]
    }),
    ('data_access', {
        'display': 'Data Access (SDSK Number)',
        'fields': [{
            'type': 'TextField',
            'name': 'tracking_id'
        }]
    })
])

AVAILABLE_SCHEDULERS = [
    ('default', 'Default'),
    ('locked_scheduler', 'Locked'),
    ('user_pref_scheduler', 'User Preference Scheduler')
]

PRIVATE_INSTANCE = True

DISABLE_TASK_PRESENTER_EDITOR = False
SIGNATURE_SECRET = environ.get('PYB_SIGNATURE_SECRET')
REDUNDANCY_UPDATE_EXPIRATION = 60

# Access control configurations
ENABLE_ACCESS_CONTROL = True

VALID_USER_ACCESS_LEVELS  = [("L1", "L1"), ("L2", "L2"),
        ("L3", "L3"), ("L4", "L4")]

# Given project level, return valid user levels
# Project with L1, users only with level L1 permitted
# Project with L2, users with levels L1, L2 permitted ...
# Key: project level, Value: implicit valid user levels
VALID_USER_LEVELS_FOR_PROJECT_LEVEL = dict(L1=[],
    L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"])

# Given a user level, return valid project levels
# Users with L1 can work on project with level L2, L3, L4
# Key: user level, Value: implicit valid levels for project
VALID_PROJECT_LEVELS_FOR_USER_LEVEL = dict(L1=["L2", "L3", "L4"],
    L2=["L3", "L4"], L3=["L4"], L4=[])

# Defined data access levels based on user type
VALID_ACCESS_LEVELS_FOR_USER_TYPES = {
    'Full-time Employee': ["L1", "L2", "L3", "L4"],
    'Intern': ["L1", "L2", "L3", "L4"],
    'Part-time Employee': ["L1", "L2", "L3", "L4"],
    'Temporary Employee': ["L1", "L2", "L3", "L4"],
    'Formax Vendor': ["L2", "L3", "L4"],
    'Infosys Vendor': ["L2", "L3", "L4"],
    'Innodata Vendor': ["L2", "L3", "L4"],
    'Liberty Vendor': ["L2", "L3", "L4"],
    'Mindcrest Vendor': ["L2", "L3", "L4"],
    'Tata Vendor': ["L2", "L3", "L4"],
    'Wipro Vendor': ["L2", "L3", "L4"],
    'iMerit Vendor': ["L2", "L3", "L4"]
}

DATA_CLASSIFICATION = [
    ('', True),
    ('L1 - Restricted Client Data', True),
    ('L1 - Limited Access Client Data', True),
    ('L2 - Community-Wide Client Data', True),
    ('L2 - Restricted Internal Data', True),
    ('L2 - Limited Access internal Data', True),
    ('L2 - Restricted Third-Party Data', True),
    ('L2 - Limited Access Third-Party Data', True),
    ('L3 - Community-Wide Internal Data', True),
    ('L4 - Public Internal Data', True),
    ('L4 - Public Third-Party Data', True)
]
VALID_DATA_CLASSES = [data_class for data_class, enabled in DATA_CLASSIFICATION if enabled and data_class]
VALID_ACCESS_LEVELS = sorted(set(data_class.split('-')[0].strip() for data_class in VALID_DATA_CLASSES))

ENABLE_ENCRYPTION = True
FILE_ENCRYPTION_KEY = environ.get('PYB_FILE_ENCRYPTION_KEY')
ENCRYPTION_CONFIG_PATH = ['ext_config', 'encryption']

BSSO_SETTINGS = {
    "strict": True,
    "debug": True,
    "sp": {
        "entityId": "https://gigwork.prod.blpprofessional.com",
        "assertionConsumerService": {
            "url": "https://gigwork.prod.blpprofessional.com/bloomberg/login",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        },
        "singleLogoutService": {
            "url": "https://gigwork.prod.blpprofessional.com/login/callback",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"
    },
    "idp": {
        "entityId": "https://bsso.bloomberg.com",
        "singleSignOnService": {
            "url": "https://bsso.blpprofessional.com/idp/SSO.saml2",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "singleLogoutService": {
            "url": "https://bsso.blpprofessional.com/idp/SSO.saml2",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "x509cert": "MIIDgjCCAmqgAwIBAgIGAVDZ0PdZMA0GCSqGSIb3DQEBCwUAMIGBMQswCQYDVQQGEwJVUzELMAkGA1UECBMCTlkxETAPBgNVBAcTCE5ldyBZb3JrMSIwIAYDVQQKExlCbG9vbWJlcmcgU3lzdGVtIFNlY3VyaXR5MQ0wCwYDVQQLEwRORElTMR8wHQYDVQQDExZic3NvLWlkcC5ibG9vbWJlcmcuY29tMB4XDTE1MTEwNTIyNDI0MloXDTIwMTEwMzIyNDI0MlowgYExCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJOWTERMA8GA1UEBxMITmV3IFlvcmsxIjAgBgNVBAoTGUJsb29tYmVyZyBTeXN0ZW0gU2VjdXJpdHkxDTALBgNVBAsTBE5ESVMxHzAdBgNVBAMTFmJzc28taWRwLmJsb29tYmVyZy5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDAm8cWAVrpr5giRNWBabmQSaigfoQb0ge5jtH6b7JrGmP9qJ7yhoZro39i0IslWxQp71afY/cgtyiJJFjWoultMvt0Tgv1eKLxuKo0kXwhfcFM2UWQ0f9YbyFsYL3+CPFdH0H58mjNwEm6fddEFw2+pML776dZ9XUdrAx/RDT2aotCEd2QlAYBc1rlc1uHcSrVYP/yR664Pck7R07qEiy5/yt9A7xZ82UOiC5JJzpFxJgkgUqS9UFc6WJ1uos5AaSlaVWrBdGV9X43dp4NRKoFPsEBrqqXPhLRkb91K9FVAKJ6vllg5hUcSfycKiueJLAVu/my17Y3yL5uH/uemXrVAgMBAAEwDQYJKoZIhvcNAQELBQADggEBABa9UYS65bcl1KSyTsTqobSzqKHT9oVdativVxGVMROMmw1GuOrY5bsKSVl5mVniU1fUnCS0mlXUycCc8P520Jr1tKWyOziRqOCwc3ero6/vi4WZ8EtU/rJRU/2zIyh7oM8Cz6t9cSJvBwPW2A250bUDRAOsXvjRPxiwc9s6Au0yp+cKvm5iCZy2Er/XWAApVU1ZR2E1lLBYi0oq900hbNzxCwX9q9ZTr/Jpvi3ok49So/PLztyASHGPkI+bsW4xq+DwIEA7crtN72BFXGufeBNXgVEekuJmDOOd5oZJY/arqTYnD880ZG6EYfJgTc+EFmaQOA6GgiNJ1Pv8FP1+M94="
    },
    "security": {
        "authnRequestsSigned": False,
        "wantAssertionsSigned": True
    }
}

HDFS_CONFIG = {
    'pnj2-gen': {
        'url': 'http://pnj2-bach-r1n2.bloomberg.com:50070;http://pnj2-bach-r2n2.bloomberg.com:50070',
        'user': 'dtws_gigwork',
        'keytab': '/bb/data/gig/gigwork.keytab'
    },
    'pob2-gen': {
        'url': 'http://pob2-bach-r1n02.bloomberg.com:50070;http://pob2-bach-r2n02.bloomberg.com:50070',
        'user': 'dtws_gigwork',
        'keytab': '/bb/data/gig/gigwork.keytab'
    }
}

VAULT_CONFIG = {
    'url': 'https://bpv.bloomberg.com/API/ID/{bpv_key_id}',
    'request': {
        'cert': ('/bb/bin/dtwebservices/gigwork/bpv.crt', '/bb/data/gig/bpv.key')
    },
    'response': ['password', 0],
    'error': ['msg']
}

TEMPLATE_DIR = environ.get('TEMPLATES_DIR', '')
SQLALCHEMY_TRACK_MODIFICATIONS = False
RQ_POLL_INTERVAL = 2500

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

ENRICHMENT_TYPES = {
    'OOTB': ['NLPNED', 'NLPLKP']
}

# Wizard Steps
# 'step_name': {
#
#        'title': 'Step 1', [Title that will be displayed on the UI]
#        'icon': 'fa fa-pencil', [Icon class that will be use to be displayed on the UI]
#        'href': {'url_for': 'project.new' [Url that will be redirected to when user click at step]
#                 'args': ['short_name', 'published'] [arguments for url_for function possible values are "short_name" and "published" or empty]
#                }
#        'done_checks': {'always': False, 'and': [''], 'or': []},  [if True Step is going to be filled]
#        'enable_checks': {'always': True, 'and': [''], 'or': []}, [if True Step border are going to be blue]
#        'visible_checks': {'and': ['not_project_exist'], 'or': []}, [if True Step is going to be visible]
#        [Checks:
#           The 'always' key must be used to keep a static value {always: True/False}, it means no its not dependent on
#           any logic.
#
#           All 'check-names' keys represent specific checks functions that can be found on the wizard.py class as check_options.
#               each step can have combinations of checks in {'and':[], 'or': []} and the final result will be a bolean condition
#               equivalent to"any('or') or all(and)"
#         ]
#    }

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
    ('ext_config', {
        'title': 'External Configuration',
        'icon': 'fa fa-cogs',
        'href': {'url_for': 'project.ext_config',
                 'args': ['short_name']},
        'done_checks': {'and': ['ext_config'], 'or': []},
        'enable_checks': {'and': ['project_exist'], 'or': []},
        'visible_checks': {'always': True},
        'config_for_checks': {
                'condition': {'and': [], 'or': ['hdfs', 'gigwork_poller']},
                'attrs': {'hdfs': 'info.ext_config.hdfs.path',
                          'gigwork_poller': 'info.ext_config.gigwork_poller.target_bucket'}}
    }),
    ('task_imports', {
        'title': 'Import Tasks',
        'icon': 'fa fa-file',
        'href': {'url_for': 'project.import_task',
                 'args': ['short_name']},
        'done_checks': {'and': ['tasks_amount', 'ext_config'], 'or': []},
        'enable_checks': {'and': ['ext_config'], 'or': ['tasks_amount', 'project_publish']},
        'visible_checks': {'always': True}
    }),
    ('task_presenter', {
        'title': 'Task Presenter',
        'icon': 'fa fa-pencil',
        'href': {'url_for': 'project.task_presenter_editor',
                 'args': ['short_name']},
        'done_checks': {'and': ['task_presenter', 'task_guidelines'], 'or': []},
        'enable_checks': {'and': ['tasks_amount'], 'or': ['task_presenter', 'task_guidelines', 'project_publish']},
        'visible_checks': {'always': True}
    }),
    ('assign_users', {
        'title': 'Assign Users',
        'icon': 'fa fa-user-plus',
        'href': {'url_for': 'project.assign_users',
                 'args': ['short_name']},
        'done_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'enable_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'visible_checks': {'always': True}
    }),
    ('task_settings', {
        'title': 'Settings',
        'icon': 'fa fa-cogs',
        'href': {'url_for': 'project.summary',
                 'args': ['short_name']},
        'done_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'enable_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'visible_checks': {'always': True}
    }),
    ('publish', {
        'title': 'Publish',
        'icon': 'fa fa-check',
        'href': {'url_for': 'project.publish',
                 'args': ['short_name']},
        'done_checks': {'always': False},
        'enable_checks': {'and': ['task_presenter', 'tasks_amount'], 'or': ['project_publish']},
        'visible_checks': {'and': ['not_project_publish'], 'or': ['not_project_exist']},
    }),
    ('published', {
        'title': 'Published',
        'icon': 'fa fa-check',
        'href': {'url_for': 'project.publish',
                 'args': ['short_name']},
        'done_checks': {'always': True},
        'enable_checks': {'always': True},
        'visible_checks': {'and': ['project_publish'], 'or': []},
    })]
)

PROXY_SERVICE_CONFIG = {
    'uri': 'http://prodbasv.bdns.bloomberg.com:10799',
    'services':
        {
            'autocsvc': {
                'headers': {'CCRT-Subject': '/O=Bloomberg L.P./1.3.6.1.4.1.1814.3.1.1=23286142/1.3.6.1.4.1.1814.3.1.4=9001', 'content-type': 'application/json'},
                'requests': ['queryInline2'],
                'context': ['GENERIC_SECURITY'],
                'validators': ['is_valid_query', 'is_valid_context']
            }
        }
}

REQUEST_FILE_VALIDITY_IN_DAYS = 60
STALE_USERS_MONTHS = 3
EXTENDED_STALE_USERS_MONTHS = 9
EXTENDED_STALE_USERS_DOMAINS = ['bloomberg.net']