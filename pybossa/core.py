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
from flask import Flask, url_for, session, request, render_template, flash
from flask.ext.login import current_user
#from flaskext.gravatar import Gravatar
from flask.ext.heroku import Heroku
from flask.ext.babel import lazy_gettext

from pybossa import default_settings as settings
from pybossa.extensions import (signer, mail, login_manager, sentinel,
                                facebook, twitter, google, misaka,
                                babel, gravatar)
from pybossa.ratelimit import get_view_rate_limit

from raven.contrib.flask import Sentry
from pybossa.model import db
from pybossa import model


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
    setup_login_manager(app)
    login_manager.setup_app(app)
    setup_babel(app)
    setup_markdown(app)
    # Set up Gravatar for users
    setup_gravatar(app)
    #gravatar = Gravatar(app, size=100, rating='g', default='mm',
                        #force_default=False, force_lower=False)
    db.init_app(app)
    mail.init_app(app)
    sentinel.init_app(app)
    signer.init_app(app)
    if app.config.get('SENTRY_DSN'): # pragma: no cover
        sentr = Sentry(app)
    setup_blueprints(app)
    setup_hooks(app)
    setup_error_handlers(app)
    setup_social_networks(app)
    setup_jinja(app)
    setup_geocoding(app)
    #toolbar.init_app(app)
    return app


def configure_app(app):
    app.config.from_object(settings)
    app.config.from_envvar('PYBOSSA_SETTINGS', silent=True)
    # parent directory
    if not os.environ.get('PYBOSSA_SETTINGS'): # pragma: no cover
        here = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(here), 'settings_local.py')
        if os.path.exists(config_path): # pragma: no cover
            app.config.from_pyfile(config_path)
    # Override DB in case of testing
    if app.config.get('SQLALCHEMY_DATABASE_TEST_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_TEST_URI']


def setup_markdown(app):
    misaka.init_app(app)


def setup_gravatar(app):
    gravatar.init_app(app)

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

def setup_login_manager(app):
    login_manager.login_view = 'account.signin'
    login_manager.login_message = u"Please sign in to access this page."
    @login_manager.user_loader
    def load_user(username):
        return db.session.query(model.user.User).filter_by(name=username).first()

# Configure theme
try: # pragma: no cover
    # First with local settings
    import settings_local
    theme = settings_local.THEME
except:
    # Otherwise try with default theme
    theme = settings.THEME

def setup_babel(app):
    """Return babel handler."""
    babel.init_app(app)

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
    return babel
#
def setup_blueprints(app):
    """Configure blueprints."""
    from pybossa.api import blueprint as api
    from pybossa.view.account import blueprint as account
    from pybossa.view.applications import blueprint as applications
    from pybossa.view.admin import blueprint as admin
    from pybossa.view.leaderboard import blueprint as leaderboard
    from pybossa.view.stats import blueprint as stats
    from pybossa.view.help import blueprint as help
    from pybossa.view.home import blueprint as home

    blueprints = [{'handler': home, 'url_prefix': '/'},
                  {'handler': api,  'url_prefix': '/api'},
                  {'handler': account, 'url_prefix': '/account'},
                  {'handler': applications, 'url_prefix': '/app'},
                  {'handler': admin, 'url_prefix': '/admin'},
                  {'handler': leaderboard, 'url_prefix': '/leaderboard'},
                  {'handler': help, 'url_prefix': '/help'},
                  {'handler': stats, 'url_prefix': '/stats'},
                  ]

    for bp in blueprints:
        app.register_blueprint(bp['handler'], url_prefix=bp['url_prefix'])


def setup_social_networks(app):
    try:  # pragma: no cover
        if (app.config['TWITTER_CONSUMER_KEY'] and
                app.config['TWITTER_CONSUMER_SECRET']):
            twitter.init_app(app)
            from pybossa.view.twitter import blueprint as twitter_bp
            app.register_blueprint(twitter_bp, url_prefix='/twitter')
    except Exception as inst:  # pragma: no cover
        print type(inst)
        print inst.args
        print inst
        print "Twitter signin disabled"

    # Enable Facebook if available
    try:  # pragma: no cover
        if (app.config['FACEBOOK_APP_ID'] and app.config['FACEBOOK_APP_SECRET']):
            facebook.init_app(app)
            from pybossa.view.facebook import blueprint as facebook_bp
            app.register_blueprint(facebook_bp, url_prefix='/facebook')
    except Exception as inst: # pragma: no cover
        print type(inst)
        print inst.args
        print inst
        print "Facebook signin disabled"

    # Enable Google if available
    try:  # pragma: no cover
        if (app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']):
            google.init_app(app)
            from pybossa.view.google import blueprint as google_bp
            app.register_blueprint(google_bp, url_prefix='/google')
    except Exception as inst:  # pragma: no cover
        print type(inst)
        print inst.args
        print inst
        print "Google signin disabled"


def setup_geocoding(app):
    # Check if app stats page can generate the map
    geolite = app.root_path + '/../dat/GeoLiteCity.dat'
    if not os.path.exists(geolite):  # pragma: no cover
        app.config['GEO'] = False
        print("GeoLiteCity.dat file not found")
        print("App page stats web map disabled")
    else:  # pragma: no cover
        app.config['GEO'] = True


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

def setup_jinja(app):
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page


def setup_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404


    @app.errorhandler(500)
    def server_error(e):  # pragma: no cover
        return render_template('500.html'), 500


    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403


    @app.errorhandler(401)
    def unauthorized(e):
        return render_template('401.html'), 401


def setup_hooks(app):
    @app.after_request
    def inject_x_rate_headers(response):
        limit = get_view_rate_limit()
        if limit and limit.send_x_headers:
            h = response.headers
            h.add('X-RateLimit-Remaining', str(limit.remaining))
            h.add('X-RateLimit-Limit', str(limit.limit))
            h.add('X-RateLimit-Reset', str(limit.reset))
        return response

    @app.before_request
    def api_authentication():
        """ Attempt API authentication on a per-request basis."""
        apikey = request.args.get('api_key', None)
        from flask import _request_ctx_stack
        if 'Authorization' in request.headers:
            apikey = request.headers.get('Authorization')
        if apikey:
            user = db.session.query(model.user.User).filter_by(api_key=apikey).first()
            ## HACK:
            # login_user sets a session cookie which we really don't want.
            # login_user(user)
            if user:
                _request_ctx_stack.top.user = user

    @app.context_processor
    def global_template_context():
        if current_user.is_authenticated():
            if (current_user.email_addr == current_user.name or
                    current_user.email_addr == "None"):
                flash(lazy_gettext("Please update your e-mail address in your profile page,"
                      " right now it is empty!"), 'error')

        # Cookies warning
        cookie_name = app.config['BRAND'] + "_accept_cookies"
        show_cookies_warning = False
        if not request.cookies.get(cookie_name):
            show_cookies_warning = True

        # Announcement sections
        if app.config.get('ANNOUNCEMENT'):
            announcement = app.config['ANNOUNCEMENT']
            if current_user.is_authenticated():
                for key in announcement.keys():
                    if key == 'admin' and current_user.admin:
                        flash(announcement[key], 'info')
                    if key == 'owner' and len(current_user.apps) != 0:
                        flash(announcement[key], 'info')
                    if key == 'user':
                        flash(announcement[key], 'info')

        if app.config.get('CONTACT_EMAIL'):  # pragma: no cover
            contact_email = app.config.get('CONTACT_EMAIL')
        else:
            contact_email = 'info@pybossa.com'

        if app.config.get('CONTACT_TWITTER'):  # pragma: no cover
            contact_twitter = app.config.get('CONTACT_TWITTER')
        else:
            contact_twitter = 'PyBossa'

        return dict(
            brand=app.config['BRAND'],
            title=app.config['TITLE'],
            logo=app.config['LOGO'],
            copyright=app.config['COPYRIGHT'],
            description=app.config['DESCRIPTION'],
            terms_of_use=app.config['TERMSOFUSE'],
            data_use=app.config['DATAUSE'],
            enforce_privacy=app.config['ENFORCE_PRIVACY'],
            #version=pybossa.__version__,
            current_user=current_user,
            show_cookies_warning=show_cookies_warning,
            contact_email=contact_email,
            contact_twitter=contact_twitter)
