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
from flask_oauthlib.client import OAuthException
from pybossa.core import amazon
from pybossa.s3_client import S3Client

blueprint = Blueprint('amazon', __name__)


@blueprint.route('/')
def login():
    callback_url = url_for('.oauth_authorized', _external=True)
    next_url = request.args.get('next')
    return amazon.oauth.authorize(callback=callback_url, state=next_url)


@blueprint.route('/oauth-authorized')
def oauth_authorized():
    next_url = request.args.get('state')
    resp = amazon.oauth.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
    if isinstance(resp, OAuthException):
        flash('Access denied: %s' % resp.message)
        current_app.logger.error(resp)
        return redirect(next_url)
    amazon_token = resp['access_token']
    print amazon_token
    session['amazon_token'] = amazon_token
    return redirect(next_url)


@blueprint.route('/buckets')
def buckets():
    client = S3Client()
    buckets = client.buckets()
    return Response(json.dumps(buckets), mimetype='application/json')


@blueprint.route('/buckets/<string:bucket>')
def objects(bucket):
    client = S3Client()
    buckets = client.buckets()
    bucket_content = client.objects(bucket)
    return Response(json.dumps(bucket_content), mimetype='application/json')
