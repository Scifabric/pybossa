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

"""Twitter view for PYBOSSA."""
from flask import Blueprint, request, url_for, redirect, flash, current_app
from flask import abort
from flask_login import login_user, current_user
from flask_oauthlib.client import OAuthException

from pybossa.core import twitter, user_repo, newsletter
from pybossa.model.user import User
from pybossa.util import get_user_signup_method, url_for_app_type

blueprint = Blueprint('twitter', __name__)

NO_LOGIN = 'no_login'


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    """Login with Twitter."""
    next_url = request.args.get("next")
    no_login = request.args.get(NO_LOGIN)
    ldap_enabled = current_app.config.get('LDAP_HOST', False)
    if (ldap_enabled and no_login is None):
        return abort(404)
    if ((ldap_enabled and no_login) or (not ldap_enabled)):
        callback = url_for('.oauth_authorized',
                           next=next_url,
                           no_login=no_login)
        return twitter.oauth.authorize(callback=callback)


@twitter.oauth.tokengetter
def get_twitter_token():  # pragma: no cover
    """Get Twitter token from session."""
    if current_user.is_anonymous:
        return None

    return((current_user.info['twitter_token']['oauth_token'],
            current_user.info['twitter_token']['oauth_token_secret']))


@blueprint.route('/oauth-authorized')
def oauth_authorized():  # pragma: no cover
    """Called after authorization.

    After this function finished handling,
    the OAuth information is removed from the session again. When this
    happened, the tokengetter from above is used to retrieve the oauth
    token and secret.

    Because the remote application could have re-authorized the application
    it is necessary to update the values in the database.

    If the application redirected back after denying, the response passed
    to the function will be `None`. Otherwise a dictionary with the values
    the application submitted. Note that Twitter itself does not really
    redirect back unless the user clicks on the application name.
    """
    resp = twitter.oauth.authorized_response()
    next_url = request.args.get('next') or url_for_app_type('home.home')
    if resp is None:
        flash('You denied the request to sign in.', 'error')
        return redirect(next_url)
    if isinstance(resp, OAuthException):
        flash('Access denied: %s' % resp.message)
        current_app.logger.error(resp)
        return redirect(url_for_app_type('home.home', _hash_last_flash=True))

    access_token = dict(oauth_token=resp['oauth_token'],
                        oauth_token_secret=resp['oauth_token_secret'])

    no_login = int(request.args.get(NO_LOGIN, 0))
    if no_login == 1:
        return manage_user_no_login(access_token, next_url)

    user_data = dict(screen_name=resp['screen_name'],
                     user_id=resp['user_id'])
    user = manage_user(access_token, user_data)
    return manage_user_login(user, user_data, next_url)


def manage_user(access_token, user_data):
    """Manage the user after signin"""
    # Twitter API does not provide a way
    # to get the e-mail so we will ask for it
    # only the first time
    info = dict(twitter_token=access_token)

    user = user_repo.get_by(twitter_user_id=user_data['user_id'])

    if user is not None:
        user.info['twitter_token'] = access_token
        user_repo.save(user)
        return user

    user = user_repo.get_by_name(user_data['screen_name'])
    if user is not None:
        return None

    user = User(fullname=user_data['screen_name'],
                name=user_data['screen_name'],
                email_addr=user_data['screen_name'],
                twitter_user_id=user_data['user_id'],
                info=info)
    user_repo.save(user)
    return user


def manage_user_login(user, user_data, next_url):
    """Manage user login."""
    if user is None:
        user = user_repo.get_by_name(user_data['screen_name'])
        msg, method = get_user_signup_method(user)
        flash(msg, 'info')
        if method == 'local':
            return redirect(url_for_app_type('account.forgot_password',
                                             _hash_last_flash=True))
        else:
            return redirect(url_for_app_type('account.signin',
                                             _hash_last_flash=True))

    login_user(user, remember=True)
    flash("Welcome back %s" % user.fullname, 'success')
    if ((user.email_addr != user.name) and user.newsletter_prompted is False
            and newsletter.is_initialized()):
        return redirect(url_for_app_type('account.newsletter_subscribe',
                                         next=next_url, _hash_last_flash=True))
    return redirect(next_url)


def manage_user_no_login(access_token, next_url):
    if current_user.is_authenticated:
        user = user_repo.get(current_user.id)
        user.info['twitter_token'] = access_token
        user_repo.save(user)
    return redirect(next_url)
