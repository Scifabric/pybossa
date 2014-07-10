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

from flask import Blueprint, request, url_for, flash, redirect, session
from flask.ext.login import login_user, current_user

from pybossa.core import db, google
from pybossa.model.user import User
from pybossa.util import get_user_signup_method
# Required to access the config parameters outside a context as we are using
# Flask 0.8
# See http://goo.gl/tbhgF for more info
import requests

# This blueprint will be activated in web.py if the FACEBOOK APP ID and SECRET
# are available
blueprint = Blueprint('google', __name__)

from pybossa.repositories import UserRepository
user_repo = UserRepository(db)


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    if request.args.get("next"):
        request_token_params = {
            'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
            'response_type': 'code'}
        google.oauth.request_token_params = request_token_params
    return google.oauth.authorize(callback=url_for('.oauth_authorized',
                                  _external=True))


@google.oauth.tokengetter
def get_google_token():  # pragma: no cover
    if current_user.is_anonymous():
        return session.get('oauth_token')
    else:
        return (current_user.info['google_token']['oauth_token'], '')


def manage_user(access_token, user_data, next_url):
    """Manage the user after signin"""
    # We have to store the oauth_token in the session to get the USER fields

    user = user_repo.get_by(google_user_id=user_data['id'])

    # user never signed on
    if user is None:
        google_token = dict(oauth_token=access_token)
        info = dict(google_token=google_token)
        name = user_data['name'].encode('ascii', 'ignore').lower().replace(" ", "")
        user = user_repo.get_by_name(name)

        email = user_repo.get_by(email_addr=user_data['email'])

        if ((user is None) and (email is None)):
            user = User(fullname=user_data['name'],
                   name=user_data['name'].encode('ascii', 'ignore')
                                         .lower().replace(" ", ""),
                   email_addr=user_data['email'],
                   google_user_id=user_data['id'],
                   info=info)
            user_repo.save(user)
            return user
        else:
            return None
    else:
        # Update the name to fit with new paradigm to avoid UTF8 problems
        if type(user.name) == unicode or ' ' in user.name:
            user.name = user.name.encode('ascii', 'ignore').lower().replace(" ", "")
            user_repo.save(user)
        return user


@blueprint.route('/oauth_authorized')
@google.oauth.authorized_handler
def oauth_authorized(resp):  # pragma: no cover
    #print "OAUTH authorized method called"
    next_url = url_for('home.home')

    if resp is None or request.args.get('error'):
        flash(u'You denied the request to sign in.', 'error')
        flash(u'Reason: ' + request.args['error'], 'error')
        if request.args.get('error'):
                return redirect(url_for('account.signin'))
        return redirect(next_url)

    headers = {'Authorization': ' '.join(['OAuth', resp['access_token']])}
    url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.http_error:
        # Unauthorized - bad token
        if r.status_code == 401:
            return redirect(url_for('account.signin'))
        return r.content

    access_token = resp['access_token']
    session['oauth_token'] = access_token
    import json
    user_data = json.loads(r.content)
    user = manage_user(access_token, user_data, next_url)
    if user is None:
        # Give a hint for the user
        user = user_repo.get_by(email_addr=user_data['email'])
        if user is None:
            name = user_data['name'].encode('ascii', 'ignore').lower().replace(' ', '')
            user = user_repo.get_by_name(name)

        msg, method = get_user_signup_method(user)
        flash(msg, 'info')
        if method == 'local':
            return redirect(url_for('account.forgot_password'))
        else:
            return redirect(url_for('account.signin'))
    else:
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        return redirect(next_url)
