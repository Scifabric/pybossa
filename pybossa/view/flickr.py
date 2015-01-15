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
from flask import Blueprint, request, url_for, flash, redirect, session

from pybossa.core import flickr

# This blueprint will be activated in core.py
# if the FLICKR API KEY and SECRET
# are available
blueprint = Blueprint('flickr', __name__)


@flickr.oauth.tokengetter
def get_flickr_token():  # pragma: no cover
    return session.get('flickr_token')

@blueprint.route('/')
def login():
    return flickr.oauth.authorize(callback=url_for('.oauth_authorized',
                                             next=request.args.get('next')))

@blueprint.route('/revoke-access')
def logout():
    next_url = request.args.get('next') or url_for('home.home')
    session.pop('flickr_token')
    session.pop('flickr_user')
    return redirect(next_url)

@blueprint.route('/oauth-authorized')
def oauth_authorized():
    next_url = request.args.get('next')
    resp = flickr.oauth.authorized_response()
    flickr_token = dict(oauth_token=resp['oauth_token'],
                        oauth_token_secret=resp['oauth_token_secret'])
    flickr_user = dict(username=resp['username'], user_nsid=resp['user_nsid'])
    session['flickr_token'] = flickr_token
    session['flickr_user'] = flickr_user
    print resp
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    return redirect(next_url)
