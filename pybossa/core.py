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

import os
import logging
from itsdangerous import URLSafeTimedSerializer
from flask import Flask, url_for, session, request
from flask.ext.login import LoginManager, current_user
from flaskext.gravatar import Gravatar
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
#from flask.ext.debugtoolbar import DebugToolbarExtension
from flask.ext.heroku import Heroku
from flask.ext.babel import Babel
from redis.sentinel import Sentinel

from pybossa import default_settings as settings
import settings_local

from raven.contrib.flask import Sentry


def create_app(theme='default'):
    template_folder = os.path.join('themes', theme, 'templates')
    static_folder = os.path.join('themes', theme, 'static')
    app = Flask(__name__, template_folder=template_folder,
                static_folder=static_folder)
    if 'DATABASE_URL' in os.environ:  # pragma: no cover
        heroku = Heroku(app)
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
    if os.path.exists(config_path): # pragma: no cover
        app.config.from_pyfile(config_path)

from logging.handlers import SMTPHandler
def setup_error_email(app):
    ADMINS = app.config.get('ADMINS', '')
    if not app.debug and ADMINS: # pragma: no cover
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
    if log_file_path: # pragma: no cover
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
login_manager.login_view = 'account.signin'
login_manager.login_message = u"Please sign in to access this page."
# Configure theme
app = create_app(theme=settings_local.THEME)

sentinel = Sentinel(app.config['REDIS_SENTINEL'], socket_timeout=0.1)
redis_master = sentinel.master_for('mymaster')
redis_slave = sentinel.slave_for('mymaster')

#toolbar = DebugToolbarExtension(app)
db = SQLAlchemy(app)
mail = Mail(app)
signer = URLSafeTimedSerializer(app.config['ITSDANGEORUSKEY'])
if app.config.get('SENTRY_DSN'): # pragma: no cover
    sentr = Sentry(app)

babel = Babel(app)


@babel.localeselector
def get_locale():
    if current_user.is_authenticated():
        lang = current_user.locale
    else:
        lang = session.get('lang',
                           request.accept_languages.best_match(app.config['LOCALES']))
    if lang is None:
        lang = 'en'
    return lang
