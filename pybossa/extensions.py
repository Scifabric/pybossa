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
"""
This module exports all the extensions used by PYBOSSA.

The objects are:
    * sentinel: for caching data, ratelimiting, etc.
    * signer: for signing emails, cookies, etc.
    * mail: for sending emails,
    * login_manager: to handle account sigin/signout
    * facebook: for Facebook signin
    * twitter: for Twitter signin
    * google: for Google signin
    * misaka: for app.long_description markdown support,
    * babel: for i18n support,
    * uploader: for file uploads support,
    * csrf: for CSRF protection
    * newsletter: for subscribing users to Mailchimp newsletter
    * assets: for assets management (SASS, etc.)
    * JSONEncoder: a custom JSON encoder to handle specific types
    * cors: the Flask-Cors library object

"""
__all__ = ['sentinel', 'db', 'signer', 'mail', 'login_manager', 'facebook',
           'twitter', 'google', 'misaka', 'babel', 'uploader', 'debug_toolbar',
           'csrf', 'timeouts', 'ratelimits', 'user_repo', 'project_repo',
           'task_repo', 'announcement_repo', 'blog_repo', 'auditlog_repo', 'webhook_repo',
           'result_repo', 'newsletter', 'importer', 'flickr',
           'plugin_manager', 'assets', 'JSONEncoder', 'cors', 'ldap',
           'flask_profiler', 'anonymizer']

# CACHE
from pybossa.sentinel import Sentinel
sentinel = Sentinel()

# DB
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
db.slave_session = db.session

# Repositories
user_repo = None
project_repo = None
announcement_repo = None
blog_repo = None
task_repo = None
auditlog_repo = None
webhook_repo = None
result_repo = None

# Signer
from pybossa.signer import Signer
signer = Signer()

# Mail
from flask_mail import Mail
mail = Mail()

# Login Manager
from flask_login import LoginManager
login_manager = LoginManager()

# Debug Toolbar
from flask_debugtoolbar import DebugToolbarExtension
debug_toolbar = DebugToolbarExtension()

# OAuth providers
from pybossa.oauth_providers import Facebook
facebook = Facebook()

from pybossa.oauth_providers import Twitter
twitter = Twitter()

from pybossa.oauth_providers import Google
google = Google()

from pybossa.oauth_providers import Flickr
flickr = Flickr()

# Markdown support
from flask_misaka import Misaka
misaka = Misaka()

# Babel
from flask_babel import Babel
babel = Babel()

# Uploader
uploader = None

# Exporters
json_exporter = None
csv_exporter = None

# CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

# Timeouts
timeouts = dict()

# Ratelimits
ratelimits = dict()

# Newsletter
from .newsletter import Newsletter
newsletter = Newsletter()

# Importer
from .importers import Importer
importer = Importer()

from flask_plugins import PluginManager
plugin_manager = PluginManager()

from flask_assets import Environment
assets = Environment()

from flask.json import JSONEncoder as BaseEncoder
from speaklater import _LazyString

class JSONEncoder(BaseEncoder): # pragma: no cover
    """JSON Encoder to deal with Babel lazy strings."""
    def default(self, o):
        if isinstance(o, _LazyString):
            return str(o)

        return BaseEncoder.default(self, o)

# CORS
from flask_cors import CORS
cors = CORS()

# Strong password
enable_strong_password = None

# LDAP
from flask_simpleldap import LDAP
ldap = LDAP()

# Flask Profiler
import flask_profiler

# IP anonymizer
from pybossa.anonymizer import Anonymizer
anonymizer = Anonymizer()
