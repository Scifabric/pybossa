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

from pybossa.core import facebook, user_repo, newsletter
from pybossa.model.user import User
#from pybossa.util import Facebook, get_user_signup_method
from pybossa.util import get_user_signup_method
# Required to access the config parameters outside a context as we are using
# Flask 0.8
# See http://goo.gl/tbhgF for more info
#from pybossa.core import app

# This blueprint will be activated in core.py if the FACEBOOK APP ID and SECRET
# are available
blueprint = Blueprint('facebook', __name__)


@blueprint.route('/', methods=['GET', 'POST'])
def login():  # pragma: no cover
    return facebook.oauth.authorize(callback=url_for('.oauth_authorized',
                                                     next=request.args.get("next"),
                                                     _external=True))


@facebook.oauth.tokengetter
def get_facebook_token():  # pragma: no cover
    if current_user.is_anonymous():
        return session.get('oauth_token')
    else:
        return (current_user.info['facebook_token']['oauth_token'], '')


@blueprint.route('/oauth-authorized')
@facebook.oauth.authorized_handler
def oauth_authorized(resp):  # pragma: no cover
    next_url = request.args.get('next') or url_for('home.home')
    if resp is None:
        flash(u'You denied the request to sign in.', 'error')
        flash(u'Reason: ' + request.args['error_reason'] +
              ' ' + request.args['error_description'], 'error')
        return redirect(next_url)

    # We have to store the oauth_token in the session to get the USER fields
    access_token = resp['access_token']
    session['oauth_token'] = (resp['access_token'], '')
    user_data = facebook.oauth.get('/me').data

    user = manage_user(access_token, user_data, next_url)
    return manage_user_login(user, user_data, next_url)


def manage_user(access_token, user_data, next_url):
    """Manage the user after signin"""
    user = user_repo.get_by(facebook_user_id=user_data['id'])

    if user is None:
        facebook_token = dict(oauth_token=access_token)
        info = dict(facebook_token=facebook_token)
        user = user_repo.get_by_name(user_data['username'])
        # NOTE: Sometimes users at Facebook validate their accounts without
        # registering an e-mail (see this http://stackoverflow.com/a/17809808)
        email = None
        if user_data.get('email'):
            email = user_repo.get_by(email_addr=user_data['email'])

        if user is None and email is None:
            if not user_data.get('email'):
                user_data['email'] = "None"
            user = User(fullname=user_data['name'],
                   name=user_data['username'],
                   email_addr=user_data['email'],
                   facebook_user_id=user_data['id'],
                   info=info)
            user_repo.save(user)
            if newsletter.app and user.email_addr != "None":
                newsletter.subscribe_user(user)
            return user
        else:
            return None
    else:
        return user

def manage_user_login(user, user_data, next_url):
    """Manage user login."""
    if user is None:
        # Give a hint for the user
        user = user_repo.get_by(email_addr=user_data['email'])
        if user is not None:
            msg, method = get_user_signup_method(user)
            flash(msg, 'info')
            if method == 'local':
                return redirect(url_for('account.forgot_password'))
            else:
                return redirect(url_for('account.signin'))
        else:
            return redirect(url_for('account.signin'))
    else:
        first_login = False
        login_user(user, remember=True)
        flash("Welcome back %s" % user.fullname, 'success')
        request_email = False
        if (user.email_addr == "None"):
            request_email = True
        if request_email:
            if first_login:
                flash("This is your first login, please add a valid e-mail")
            else:
                flash("Please update your e-mail address in your profile page")
            return redirect(url_for('account.update_profile', name=user.name))
        if (user.email_addr != "None" and user.newsletter_prompted is False
                and newsletter.app):
            return redirect(url_for('account.newsletter_subscribe', next=next_url))
        return redirect(next_url)
