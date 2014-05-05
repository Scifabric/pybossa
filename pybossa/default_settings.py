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
ALLOWED_EXTENSIONS = ['js', 'css', 'png', 'jpg', 'jpeg', 'gif']
UPLOAD_METHOD = 'local'

## Default number of users shown in the leaderboard
LEADERBOARD = 20

## Default configuration for debug toolbar
ENABLE_DEBUG_TOOLBAR = False

## Default cache timeouts
APP_TIMEOUT = 15 * 60
REGISTERED_USERS_TIMEOUT = 15 * 60