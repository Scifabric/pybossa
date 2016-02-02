# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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

import json
from mock import patch, MagicMock
from flask import Response, session
from default import flask_app

class TestAmazonOAuth(object):

    @patch('pybossa.view.amazon.amazon.oauth')
    def test_amazon_login_converts_next_param_to_state_param(self, oauth):
        oauth.authorize.return_value = Response(302)
        next_url = 'http://next'
        flask_app.test_client().get('/amazon/?next=%s' % next_url)
        oauth.authorize.assert_called_with(
            callback='http://localhost/amazon/oauth-authorized',
            state=next_url)

    @patch('pybossa.view.amazon.amazon.oauth')
    def test_oauth_authorized_saves_token_to_session_if_authentication_succeeds(
            self, oauth):
        fake_resp = {u'access_token': u'access_token',
                     u'token_type': u'bearer',
                     u'expires_in': 3600,
                     u'refresh_token': u'refresh_token'}
        oauth.authorized_response.return_value = fake_resp

        with flask_app.test_client() as c:
            c.get('/amazon/oauth-authorized')

            assert session.get('amazon_token') == u'access_token'

    @patch('pybossa.view.amazon.amazon.oauth')
    @patch('pybossa.view.amazon.redirect')
    def test_oauth_authorized_redirects_to_next_url_on_authorization(
            self, redirect, oauth):
        fake_resp = {u'access_token': u'access_token',
                     u'token_type': u'bearer',
                     u'expires_in': 3600,
                     u'refresh_token': u'refresh_token'}
        oauth.authorized_response.return_value = fake_resp
        next_url = 'http://next'
        redirect.return_value = Response(302)

        flask_app.test_client().get('/amazon/oauth-authorized?state=%s' % next_url)

        redirect.assert_called_with(next_url)

    @patch('pybossa.view.amazon.amazon.oauth')
    @patch('pybossa.view.amazon.redirect')
    def test_oauth_authorized_redirects_to_next_url_on_non_authorization(
            self, redirect, oauth):
        fake_resp = None
        oauth.authorized_response.return_value = fake_resp
        next_url = 'http://next'
        redirect.return_value = Response(302)

        flask_app.test_client().get('/amazon/oauth-authorized?state=%s' % next_url)

        redirect.assert_called_with(next_url)


class TestAmazonS3API(object):

    @patch('pybossa.view.amazon.S3Client')
    def test_buckets_endpoint_returns_list_of_user_buckets(self, S3Client):
        buckets = ['Bucket 1', 'Bucket 2']
        client_instance = MagicMock()
        S3Client.return_value = client_instance
        client_instance.buckets.return_value = buckets

        resp = flask_app.test_client().get('/amazon/buckets')

        assert resp.data == json.dumps(buckets), resp.data
