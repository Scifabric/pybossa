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

"""Facebook view for PYBOSSA."""
from flask import Blueprint, request, url_for, flash, redirect, session, current_app
from flask import abort
from flask_login import login_user, current_user
from flask_oauthlib.client import OAuthException

from pybossa.core import facebook, user_repo, newsletter
from pybossa.model.user import User
from pybossa.util import get_user_signup_method, username_from_full_name
from pybossa.util import url_for_app_type
# Required to access the config parameters outside a context as we are using
# Flask 0.8
# See http://goo.gl/tbhgF for more info

blueprint = Blueprint('facebook', __name__)


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    """Login using Facebook Oauth."""
    if not current_app.config.get('LDAP_HOST', False):
        next_url = request.args.get("next")
        callback = url_for('.oauth_authorized',
                           next=next_url,
                           _external=True)
        return facebook.oauth.authorize(callback=callback)
    else:
        return abort(404)


@facebook.oauth.tokengetter
def get_facebook_token():  # pragma: no cover
    """Get Facebook token from session."""
    if current_user.is_anonymous:
        return session.get('oauth_token')
    else:
        return (current_user.info['facebook_token']['oauth_token'], '')


@blueprint.route('/oauth-authorized')
def oauth_authorized():  # pragma: no cover
    """Authorize facebook login."""
    resp = facebook.oauth.authorized_response()
    next_url = request.args.get('next') or url_for_app_type('home.home')
    if resp is None:
        flash('You denied the request to sign in.', 'error')
        flash('Reason: ' + request.args['error_reason'] +
              ' ' + request.args['error_description'], 'error')
        next_url = (request.args.get('next') or
                    url_for_app_type('home.home', _hash_last_flash=True))
        return redirect(next_url)
    if isinstance(resp, OAuthException):
        flash('Access denied: %s' % resp.message)
        current_app.logger.error(resp)
        return redirect(url_for_app_type('home.home', _hash_last_flash=True))
    # We have to store the oauth_token in the session to get the USER fields
    access_token = resp['access_token']
    session['oauth_token'] = (resp['access_token'], '')
    user_data = facebook.oauth.get('/me?fields=id,email,name').data

    user = manage_user(access_token, user_data)
    return manage_user_login(user, user_data, next_url)


def manage_user(access_token, user_data):
    """Manage the user after signin"""
    user = user_repo.get_by(facebook_user_id=user_data['id'])
    facebook_token = dict(oauth_token=access_token)

    if user is None:
        info = dict(facebook_token=facebook_token)
        name = username_from_full_name(user_data['name'])
        user_exists = user_repo.get_by_name(name) is not None
        # NOTE: Sometimes users at Facebook validate their accounts without
        # registering an e-mail (see this http://stackoverflow.com/a/17809808)
        email_exists = (user_data.get('email') is not None and
                        user_repo.get_by(email_addr=user_data['email']) is not None)

        if not user_exists and not email_exists:
            if not user_data.get('email'):
                user_data['email'] = name
            user = User(fullname=user_data['name'],
                        name=name,
                        email_addr=user_data['email'],
                        facebook_user_id=user_data['id'],
                        info=info)
            user_repo.save(user)
            if newsletter.is_initialized() and user.email_addr != name:
                newsletter.subscribe_user(user)
            return user
        else:
            return None
    else:
        user.info['facebook_token'] = facebook_token
        user_repo.save(user)
        return user


def manage_user_login(user, user_data, next_url):
    """Manage user login."""
    if user is None:
        # Give a hint for the user
        user = user_repo.get_by(email_addr=user_data.get('email'))
        if user is not None:
            msg, method = get_user_signup_method(user)
            flash(msg, 'info')
            if method == 'local':
                return redirect(url_for_app_type('account.forgot_password',
                                                 _hash_last_flash=True))
            else:
                return redirect(url_for_app_type('account.signin',
                                                 _hash_last_flash=True))
        else:
            return redirect(url_for_app_type('account.signin',
                                             _hash_last_flash=True))
    else:
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        if ((user.email_addr != user.name) and user.newsletter_prompted is False
                and newsletter.is_initialized()):
            return redirect(url_for_app_type('account.newsletter_subscribe',
                                             next=next_url,
                                             _hash_last_flash=True))
        return redirect(next_url)
