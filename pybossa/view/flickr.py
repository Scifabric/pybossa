# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
"""Flickr view for PyBossa."""
from flask import Blueprint, request, url_for, flash, redirect, session, current_app
from pybossa.core import flickr
from flask_oauthlib.client import OAuthException

blueprint = Blueprint('flickr', __name__)


@blueprint.route('/')
def login():
    """Login using Flickr view."""
    callback_url = url_for('.oauth_authorized', next=request.args.get('next'))
    return flickr.authorize(callback=callback_url, perms='read')


@blueprint.route('/revoke-access')
def logout():
    """Log out."""
    next_url = request.args.get('next') or url_for('home.home')
    flickr.remove_credentials(session)
    return redirect(next_url)


@blueprint.route('/oauth-authorized')
def oauth_authorized():
    """Authorize Flickr login."""
    next_url = request.args.get('next')
    resp = flickr.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
    if isinstance(resp, OAuthException):
        flash('Access denied: %s' % resp.message)
        current_app.logger.error(resp)
        return redirect(next_url)
    flickr_token = dict(oauth_token=resp['oauth_token'],
                        oauth_token_secret=resp['oauth_token_secret'])
    flickr_user = dict(username=resp['username'], user_nsid=resp['user_nsid'])
    flickr.save_credentials(session, flickr_token, flickr_user)
    return redirect(next_url)
