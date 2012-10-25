# This file is part of PyBOSSA.
# 
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
from flask import Flask
from flaskext.login import LoginManager, current_user
from flaskext.gravatar import Gravatar
from flask.ext.sqlalchemy import SQLAlchemy

from pybossa import default_settings as settings

from raven.contrib.flask import Sentry

def create_app():
    app = Flask(__name__)
    configure_app(app)
    setup_error_email(app)
    setup_logging(app)
    login_manager.setup_app(app)
    # Set up Gravatar for users
    gravatar = Gravatar(app, size = 100, rating = 'g', default = 'mm', force_default = False, force_lower = False)
    return app

def configure_app(app):
    app.config.from_object(settings)
    app.config.from_envvar('PYBOSSA_SETTINGS', silent=True)
    # parent directory
    here = os.path.dirname(os.path.abspath( __file__ ))
    config_path = os.path.join(os.path.dirname(here), 'settings_local.py')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)

from logging.handlers import SMTPHandler
def setup_error_email(app):
    ADMINS = app.config.get('ADMINS', '')
    if not app.debug and ADMINS:
        mail_handler = SMTPHandler('127.0.0.1',
                                   'server-error@no-reply.com',
                                   ADMINS, 'error')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

from logging.handlers import RotatingFileHandler
from logging import Formatter
def setup_logging(app):
    log_file_path = app.config.get('LOG_FILE')
    log_level = app.config.get('LOG_LEVEL', logging.WARN)
    if log_file_path:
        file_handler = RotatingFileHandler(log_file_path)
        file_handler.setFormatter(Formatter(
            '%(name)s:%(levelname)s:[%(asctime)s] %(message)s '
            '[in %(pathname)s:%(lineno)d]'
            ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        logger = logging.getLogger('pybossa')
        logger.setLevel(log_level)
        logger.addHandler(file_handler)

login_manager = LoginManager()
login_manager.login_view = "/account/signin"
login_manager.login_message = u"Please sign in to access this page."
app = create_app()
db = SQLAlchemy(app)
if app.config.get('SENTRY_DSN'):
    sentr = Sentry(app)
