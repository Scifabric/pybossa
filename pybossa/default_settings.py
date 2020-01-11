# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

DEBUG = False

# webserver host and port
HOST = '0.0.0.0'
PORT = 5000

SECRET = 'foobar'
SECRET_KEY = 'my-session-secret'

ITSDANGEROUSKEY = 'its-dangerous-key'

# project configuration
BRAND = 'PYBOSSA'
TITLE = 'PYBOSSA'
COPYRIGHT = 'Set Your Institution'
DESCRIPTION = 'Set the description in your config'
TERMSOFUSE = 'http://okfn.org/terms-of-use/'
DATAUSE = 'http://opendatacommons.org/licenses/by/'
LOGO = ''
DEFAULT_LOCALE = 'en'
LOCALES = [('en', 'English'), ('es', u'Español'),
           ('it', 'Italiano'), ('fr', u'Français'),
           ('ja', u'日本語'), ('el', u'ελληνικά')]

# Default THEME
THEME = 'default'

# Default number of apps per page
APPS_PER_PAGE = 20

# Default allowed extensions
ALLOWED_EXTENSIONS = ['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'zip']
UPLOAD_METHOD = 'local'

# Default number of users shown in the leaderboard
LEADERBOARD = 20

# Default configuration for debug toolbar
ENABLE_DEBUG_TOOLBAR = False

# Cache default key prefix
REDIS_SENTINEL = [('localhost', 26379)]
REDIS_MASTER = 'mymaster'
REDIS_DB = 0
REDIS_SOCKET_TIMEOUT = None
REDIS_RETRY_ON_TIMEOUT = True

REDIS_KEYPREFIX = 'pybossa_cache'

# Default cache timeouts
# Project cache
AVATAR_TIMEOUT = 30 * 24 * 60 * 60
APP_TIMEOUT = 15 * 60
REGISTERED_USERS_TIMEOUT = 15 * 60
ANON_USERS_TIMEOUT = 5 * 60 * 60
STATS_FRONTPAGE_TIMEOUT = APP_TIMEOUT
STATS_APP_TIMEOUT = 12 * 60 * 60
STATS_DRAFT_TIMEOUT = 24 * 60 * 60
N_APPS_PER_CATEGORY_TIMEOUT = 60 * 60
BROWSE_TASKS_TIMEOUT = 3 * 60 * 60
# Category cache
CATEGORY_TIMEOUT = 24 * 60 * 60
# User cache
USER_TIMEOUT = 15 * 60
USER_TOP_TIMEOUT = 24 * 60 * 60
USER_TOTAL_TIMEOUT = 24 * 60 * 60

# Project Presenters
PRESENTERS = ["basic", "image", "sound", "video", "map", "pdf"]
# Default Google Docs spreadsheet template tasks URLs
TEMPLATE_TASKS = {
    'image': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc&usp=sharing",
    'video': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdGZ2UGhxSTJjQl9YNVhfUVhGRUdoRWc&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE&usp=sharing"}

# Rate limits default values
LIMIT = 300
PER = 15 * 60

# Expiration time for password protected project cookies
PASSWD_COOKIE_TIMEOUT = 60 * 30

# Expiration time for account confirmation / password recovery links
ACCOUNT_LINK_EXPIRATION = 5 * 60 * 60

# Rate limits default values
LIMIT = 300
PER = 15 * 60

# Disable new account confirmation (via email)
ACCOUNT_CONFIRMATION_DISABLED = True

# Send emails weekly update every
WEEKLY_UPDATE_STATS = 'Sunday'

# Enable Server Sent Events
SSE = False

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

CORS_RESOURCES = {r"/api/*": {"origins": "*",
                              "allow_headers": ['Content-Type',
                                                'Authorization'],
                              "max_age": 21600
                              }}

FAILED_JOBS_RETRIES = 3
FAILED_JOBS_MAILS = 7

FULLTEXTSEARCH_LANGUAGE = 'english'

STRICT_SLASHES = True

# Background jobs default time outs
MINUTE = 60
TIMEOUT = 10 * MINUTE

# OneSignal GCM Sender ID
# DO NOT MODIFY THIS
GCM_SENDER_ID = "482941778795"

# Unpublish inactive projects
UNPUBLISH_PROJECTS = True

# TTL for ZIP files of personal data
TTL_ZIP_SEC_FILES = 3

# Default cryptopan key
CRYPTOPAN_KEY = '32-char-str-for-AES-key-and-pad.'

# Instruct PYBOSSA to generate absolute paths or not for avatars
AVATAR_ABSOLUTE = True

# Spam accounts to avoid
SPAM = []

# Inactive users months to send email notification
USER_INACTIVE_NOTIFICATION = 5
# Inactive users months to delete users
USER_INACTIVE_DELETE = 6
