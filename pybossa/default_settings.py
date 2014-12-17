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

DEBUG = False

# webserver host and port
HOST = '0.0.0.0'
PORT = 5000

SECRET = 'foobar'
SECRET_KEY = 'my-session-secret'

ITSDANGEROUSKEY = 'its-dangerous-key'

## project configuration
BRAND = 'PyBossa'
TITLE = 'PyBossa'
COPYRIGHT = 'Set Your Institution'
DESCRIPTION = 'Set the description in your config'
TERMSOFUSE = 'http://okfn.org/terms-of-use/'
DATAUSE = 'http://opendatacommons.org/licenses/by/'
LOGO = ''
LOCALES = ['en', 'es']

## Default THEME
THEME = 'default'

## Default number of apps per page
APPS_PER_PAGE = 20

## Default allowed extensions
ALLOWED_EXTENSIONS = ['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'zip']
UPLOAD_METHOD = 'local'

## Default number of users shown in the leaderboard
LEADERBOARD = 20

## Default configuration for debug toolbar
ENABLE_DEBUG_TOOLBAR = False

# Cache default key prefix
REDIS_CACHE_ENABLED = False
REDIS_SENTINEL = [('localhost', 26379)]
REDIS_MASTER = 'mymaster'
REDIS_DB = 0

REDIS_KEYPREFIX = 'pybossa_cache'

## Default cache timeouts
# App cache
APP_TIMEOUT = 15 * 60
REGISTERED_USERS_TIMEOUT = 15 * 60
ANON_USERS_TIMEOUT = 5 * 60 * 60
STATS_FRONTPAGE_TIMEOUT = 12 * 60 * 60
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
    'image': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE"
             "&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc"
             "&usp=sharing",
    'video': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdGZ2UGhxSTJjQl9YNVhfUVhGRUdoRWc"
             "&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc"
           "&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE"
           "&usp=sharing"}

# Rate limits default values
LIMIT = 300
PER = 15 * 60

# Expiration time for password protected project cookies
PASSWD_COOKIE_TIMEOUT = 60 * 30

# Rate limits default values
LIMIT = 300
PER = 15 * 60

# Disable new account confirmation (via email)
ACCOUNT_CONFIRMATION_DISABLED = True
