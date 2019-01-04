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

"""Google view for PYBOSSA."""
from flask import Blueprint, request, url_for, flash, redirect, session, current_app
from flask import abort
from flask_login import login_user, current_user
from flask_oauthlib.client import OAuthException

from pybossa.core import google, user_repo, newsletter
from pybossa.model.user import User
from pybossa.util import get_user_signup_method, username_from_full_name
from pybossa.util import url_for_app_type
# Required to access the config parameters outside a context as we are using
# Flask 0.8
# See http://goo.gl/tbhgF for more info
import requests

blueprint = Blueprint('google', __name__)


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    """Login with Google."""
    if not current_app.config.get('LDAP_HOST', False):
        if request.args.get("next"):
            request_token_params = {'scope': 'profile email'}
            google.oauth.request_token_params = request_token_params
        callback = url_for('.oauth_authorized', _external=True)
        return google.oauth.authorize(callback=callback)
    else:
        return abort(404)


@google.oauth.tokengetter
def get_google_token():  # pragma: no cover
    """Get Google Token from session."""
    if current_user.is_anonymous:
        return session.get('oauth_token')
    else:
        return (current_user.info['google_token']['oauth_token'], '')


@blueprint.route('/oauth_authorized')
def oauth_authorized():  # pragma: no cover
    """Authorize Oauth."""
    resp = google.oauth.authorized_response()
    if resp is None or request.args.get('error'):
        flash('You denied the request to sign in.', 'error')
        flash('Reason: ' + request.args['error'], 'error')
        if request.args.get('error'):
            current_app.logger.error(resp)
            return redirect(url_for_app_type('account.signin',
                            _hash_last_flash=True))
        next_url = (request.args.get('next') or
                    url_for_app_type('home.home', _hash_last_flash=True))
        return redirect(next_url)
    if isinstance(resp, OAuthException):
        flash('Access denied: %s' % resp.message)
        current_app.logger.error(resp)
        next_url = (request.args.get('next') or
                    url_for_app_type('home.home', _hash_last_flash=True))
        return redirect(next_url)
    headers = {'Authorization': ' '.join(['OAuth', resp['access_token']])}
    url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.http_error:
        # Unauthorized - bad token
        if r.status_code == 401:
            return redirect(url_for_app_type('account.signin'))
        return r.content

    access_token = resp['access_token']
    session['oauth_token'] = access_token
    import json
    user_data = json.loads(r.content)
    user = manage_user(access_token, user_data)
    next_url = request.args.get('next') or url_for_app_type('home.home')
    return manage_user_login(user, user_data, next_url)


def manage_user(access_token, user_data):
    """Manage the user after signin"""
    # We have to store the oauth_token in the session to get the USER fields

    user = user_repo.get_by(google_user_id=user_data['id'])
    google_token = dict(oauth_token=access_token)

    # user never signed on
    if user is None:
        info = dict(google_token=google_token)
        name = username_from_full_name(user_data['name'])
        user = user_repo.get_by_name(name)

        email = user_repo.get_by(email_addr=user_data['email'])

        if ((user is None) and (email is None)):
            user = User(fullname=user_data['name'],
                        name=name,
                        email_addr=user_data['email'],
                        google_user_id=user_data['id'],
                        info=info)
            user_repo.save(user)
            if newsletter.is_initialized():
                newsletter.subscribe_user(user)
            return user
        else:
            return None
    else:
        user.info['google_token'] = google_token
        # Update the name to fit with new paradigm to avoid UTF8 problems
        if type(user.name) == str or ' ' in user.name:
            user.name = username_from_full_name(user.name)
        user_repo.save(user)
        return user


def manage_user_login(user, user_data, next_url):
    """Manage user login."""
    if user is None:
        # Give a hint for the user
        user = user_repo.get_by(email_addr=user_data['email'])
        if user is None:
            name = username_from_full_name(user_data['name'])
            user = user_repo.get_by_name(name)

        msg, method = get_user_signup_method(user)
        flash(msg, 'info')
        if method == 'local':
            return redirect(url_for_app_type('account.forgot_password',
                                             _hash_last_flash=True))
        else:
            return redirect(url_for_app_type('account.signin',
                                             _hash_last_flash=True))
    else:
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        if user.newsletter_prompted is False and newsletter.is_initialized():
            return redirect(url_for_app_type('account.newsletter_subscribe',
                                             next=next_url,
                                             _hash_last_flash=True))
        return redirect(next_url)
