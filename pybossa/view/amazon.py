# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
"""Amazon view for PyBossa."""
import json
from flask import (Blueprint, request, url_for, flash, redirect, session,
    current_app, Response)
from pybossa.core import amazon
from flask_oauthlib.client import OAuthException

blueprint = Blueprint('amazon', __name__)


@blueprint.route('/')
def login():
    """Login using amazon view."""
    callback_url = url_for('.oauth_authorized',
                           next=request.args.get('next'),
                           _external=True)
    return amazon.oauth.authorize(callback=callback_url)


@blueprint.route('/oauth-authorized')
def oauth_authorized():
    """Authorize amazon login."""
    next_url = request.args.get('next')
    resp = amazon.oauth.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
    if isinstance(resp, OAuthException):
        flash('Access denied: %s' % resp.message)
        current_app.logger.error(resp)
        return redirect(next_url)
    amazon_token = resp['access_token']
    session[amazon_token] = amazon_token
    return redirect(next_url)
