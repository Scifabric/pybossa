"""
This module exports all the extensions used by PyBossa.

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

"""
__all__ = ['sentinel', 'db', 'signer', 'mail', 'login_manager', 'facebook',
           'twitter', 'google', 'misaka', 'babel', 'uploader', 'debug_toolbar',
           'csrf', 'timeouts', 'ratelimits', 'user_repo', 'project_repo',
           'task_repo', 'blog_repo', 'auditlog_repo', 'newsletter', 'importer',
           'flickr','ldap']

# CACHE
from pybossa.sentinel import Sentinel
sentinel = Sentinel()

# DB
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()
db.slave_session = None

# Repositories
user_repo = None
project_repo = None
blog_repo = None
task_repo = None
auditlog_repo = None

# Signer
from pybossa.signer import Signer
signer = Signer()

# Mail
from flask.ext.mail import Mail
mail = Mail()

# Login Manager
from flask.ext.login import LoginManager
login_manager = LoginManager()

# Debug Toolbar
from flask.ext.debugtoolbar import DebugToolbarExtension
debug_toolbar = DebugToolbarExtension()

# Social Networks
from pybossa.util import Facebook
facebook = Facebook()

from pybossa.util import Twitter
twitter = Twitter()

from pybossa.util import Google
google = Google()

from pybossa.util import Ldap
ldap = Ldap()

# Markdown support
from flask.ext.misaka import Misaka
misaka = Misaka()

# Babel
from flask.ext.babel import Babel
babel = Babel()

# Uploader
uploader = None

# Exporters
json_exporter = None
csv_exporter = None

# CSRF protection
from flask_wtf.csrf import CsrfProtect
csrf = CsrfProtect()

# Timeouts
timeouts = dict()

# Ratelimits
ratelimits = dict()

# Newsletter
from newsletter import Newsletter
newsletter = Newsletter()

# Importer
from importers import Importer
importer = Importer()

# Flickr OAuth integration for importer
from pybossa.flickr_service import FlickrService
flickr = FlickrService()
