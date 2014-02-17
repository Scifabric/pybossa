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
import json
import os

from flask import Response, request, g, render_template,\
        abort, flash, redirect, session, url_for
from flask.ext.login import login_user, logout_user, current_user
from flask.ext.babel import lazy_gettext
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy import func, desc
from werkzeug.exceptions import *

import pybossa
from pybossa.core import app, login_manager, db, babel
import pybossa.model as model
from pybossa.api import blueprint as api
from pybossa.view.account import blueprint as account
from pybossa.view.applications import blueprint as applications
from pybossa.view.admin import blueprint as admin
from pybossa.view.leaderboard import blueprint as leaderboard
from pybossa.view.stats import blueprint as stats
from pybossa.view.help import blueprint as help
from pybossa.cache import apps as cached_apps
from pybossa.cache import users as cached_users
from pybossa.ratelimit import get_view_rate_limit

logger = logging.getLogger('pybossa')

# other views ...
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(applications, url_prefix='/app')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(leaderboard, url_prefix='/leaderboard')
app.register_blueprint(stats, url_prefix='/stats')
app.register_blueprint(help, url_prefix='/help')

# Enable Twitter if available
try:  # pragma: no cover
    if (app.config['TWITTER_CONSUMER_KEY'] and
            app.config['TWITTER_CONSUMER_SECRET']):
        from pybossa.view.twitter import blueprint as twitter
        app.register_blueprint(twitter, url_prefix='/twitter')
        from pybossa.view.twitter import get_twitter_token
        app.jinja_env.globals['twitter_id'] = app.config['TWITTER_CONSUMER_KEY']
except Exception as inst:  # pragma: no cover
    print type(inst)
    print inst.args
    print inst
    print "Twitter signin disabled"

# Enable Facebook if available
try:  # pragma: no cover
    if (app.config['FACEBOOK_APP_ID'] and app.config['FACEBOOK_APP_SECRET']):
        from pybossa.view.facebook import blueprint as facebook
        app.register_blueprint(facebook, url_prefix='/facebook')
        from pybossa.view.facebook import get_facebook_token
        app.jinja_env.globals['facebook_id'] = app.config['FACEBOOK_APP_ID']
except Exception as inst: # pragma: no cover
    print type(inst)
    print inst.args
    print inst
    print "Facebook signin disabled"

# Enable Google if available
try:  # pragma: no cover
    if (app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']):
        from pybossa.view.google import blueprint as google
        app.register_blueprint(google, url_prefix='/google')
        from pybossa.view.google import get_facebook_token
        app.jinja_env.globals['google_id'] = app.config['GOOGLE_CLIENT_ID']
except Exception as inst:  # pragma: no cover
    print type(inst)
    print inst.args
    print inst
    print "Google signin disabled"

def template_get_twitter_token():
    try:
        return get_twitter_token()[0]
    except:
        return None
def template_get_facebook_token():
    try:
        return get_facebook_token()[0]
    except:
        return None
def template_get_google_token():
    try:
        return get_google_token()[0]
    except:
        return None

app.jinja_env.globals['get_twitter_token'] = template_get_twitter_token
app.jinja_env.globals['get_facebook_token'] = template_get_facebook_token
app.jinja_env.globals['get_google_token'] = template_get_google_token

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
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

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


@app.after_request
def inject_x_rate_headers(response):
    limit = get_view_rate_limit()
    if limit and limit.send_x_headers:
        h = response.headers
        h.add('X-RateLimit-Remaining', str(limit.remaining))
        h.add('X-RateLimit-Limit', str(limit.limit))
        h.add('X-RateLimit-Reset', str(limit.reset))
    return response

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
    print request.cookies.get(cookie_name)
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
        version=pybossa.__version__,
        current_user=current_user,
        show_cookies_warning=show_cookies_warning,
        contact_email=contact_email,
        contact_twitter=contact_twitter)


@login_manager.user_loader
def load_user(username):
    return db.session.query(model.User).filter_by(name=username).first()


@app.before_request
def api_authentication():
    """ Attempt API authentication on a per-request basis."""
    apikey = request.args.get('api_key', None)
    from flask import _request_ctx_stack
    if 'Authorization' in request.headers:
        apikey = request.headers.get('Authorization')
    if apikey:
        user = db.session.query(model.User).filter_by(api_key=apikey).first()
        ## HACK:
        # login_user sets a session cookie which we really don't want.
        # login_user(user)
        if user:
            _request_ctx_stack.top.user = user


@app.route('/')
def home():
    """ Render home page with the cached apps and users"""
    d = {'featured': cached_apps.get_featured_front_page(),
         'top_apps': cached_apps.get_top(),
         'top_users': None}

    if app.config['ENFORCE_PRIVACY'] and current_user.is_authenticated():
        if current_user.admin:
            d['top_users'] = cached_users.get_top()
    if not app.config['ENFORCE_PRIVACY']:
        d['top_users'] = cached_users.get_top()
    return render_template('/home/index.html', **d)


@app.route("/about")
def about():
    """Render the about template"""
    return render_template("/home/about.html")

@app.route("/search")
def search():
    """Render search results page"""
    return render_template("/home/search.html")

def get_port():
    port = os.environ.get('PORT', '')
    if port.isdigit():
        return int(port)
    else:
        return app.config['PORT']

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.NOTSET)
    app.run(host=app.config['HOST'], port=get_port(),
            debug=app.config.get('DEBUG', True))
