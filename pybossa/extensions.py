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
    * misaka: for app.long_description markdown support,
    * babel: for i18n support,
    * uploader: for file uploads support,
    * csrf: for CSRF protection
    * newsletter: for subscribing users to Mailchimp newsletter
    * assets: for assets management (SASS, etc.)
    * JSONEncoder: a custom JSON encoder to handle specific types
    * cors: the Flask-Cors library object

"""
from pybossa.anonymizer import Anonymizer
import flask_profiler
from flask_simpleldap import LDAP
from flask_cors import CORS
from speaklater import _LazyString
from flask.json import JSONEncoder as BaseEncoder
from flask_assets import Environment
from flask_plugins import PluginManager
from .importers import Importer
from .newsletter import Newsletter
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from flask_misaka import Misaka
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from pybossa.signer import Signer
from flask_sqlalchemy import SQLAlchemy
__all__ = ['sentinel', 'db', 'signer', 'mail', 'login_manager',
           'misaka', 'babel', 'uploader', 'debug_toolbar',
           'csrf', 'timeouts', 'ratelimits', 'user_repo', 'project_repo',
           'task_repo', 'announcement_repo', 'blog_repo', 'auditlog_repo', 'webhook_repo',
           'result_repo', 'newsletter', 'importer',
           'plugin_manager', 'assets', 'JSONEncoder', 'cors', 'ldap',
           'flask_profiler', 'anonymizer']

# CACHE
from pybossa.sentinel import Sentinel
sentinel = Sentinel()

# DB
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
signer = Signer()

# Mail
mail = Mail()

# Login Manager
login_manager = LoginManager()

# Debug Toolbar
debug_toolbar = DebugToolbarExtension()

# Markdown support
misaka = Misaka()

# Babel
babel = Babel()

# Uploader
uploader = None

# Exporters
json_exporter = None
csv_exporter = None

# CSRF protection
csrf = CSRFProtect()

# Timeouts
timeouts = dict()

# Ratelimits
ratelimits = dict()

# Newsletter
newsletter = Newsletter()

# Importer
importer = Importer()

plugin_manager = PluginManager()

assets = Environment()


class JSONEncoder(BaseEncoder):  # pragma: no cover
    """JSON Encoder to deal with Babel lazy strings."""

    def default(self, o):
        if isinstance(o, _LazyString):
            return str(o)

        return BaseEncoder.default(self, o)


# CORS
cors = CORS()

# Strong password
enable_strong_password = None

# LDAP
ldap = LDAP()

# Flask Profiler

# IP anonymizer
anonymizer = Anonymizer()
