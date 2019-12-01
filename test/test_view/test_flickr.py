# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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
from mock import patch, MagicMock
import json
from flask import Response, session
from default import flask_app, with_context


class TestFlickrOauth(object):

    @with_context
    @patch('pybossa.view.flickr.flickr.oauth')
    def test_flickr_login_specifies_callback_and_read_permissions(self, oauth):
        oauth.authorize.return_value = "OK"
        flask_app.test_client().get('/flickr/')
        oauth.authorize.assert_called_with(
            callback='/flickr/oauth-authorized', perms='read')

    @with_context
    def test_logout_removes_token_and_user_from_session(self):
        with flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess['flickr_token'] = 'fake_token'
                sess['flickr_user'] = 'fake_user'

                assert 'flickr_token' in sess
                assert 'flickr_user' in sess

            c.get('/flickr/revoke-access')

            assert 'flickr_token' not in session
            assert 'flickr_user' not in session

    @with_context
    @patch('pybossa.view.flickr.redirect')
    def test_logout_redirects_to_url_specified_by_next_param(self, redirect):
        redirect.return_value = "OK"
        flask_app.test_client().get('/flickr/revoke-access?next=http://mynext_url')

        redirect.assert_called_with('http://mynext_url')

    @with_context
    @patch('pybossa.view.flickr.flickr.oauth')
    def test_oauth_authorized_saves_token_and_user_to_session(self, oauth):
        fake_resp = {'oauth_token_secret': 'secret',
                     'username': 'palotespaco',
                     'fullname': 'paco palotes',
                     'oauth_token':'token',
                     'user_nsid': 'user'}
        oauth.authorized_response.return_value = fake_resp
        expected_token = {
            'oauth_token_secret': 'secret',
            'oauth_token': 'token'
        }
        expected_user = {'username': 'palotespaco', 'user_nsid': 'user'}

        with flask_app.test_client() as c:
            c.get('/flickr/oauth-authorized')

            assert session['flickr_token'] == expected_token, session['flickr_token']
            assert session['flickr_user'] == expected_user, session['flickr_user']

    @with_context
    @patch('pybossa.view.flickr.flickr')
    @patch('pybossa.view.flickr.redirect')
    def test_oauth_authorized_redirects_to_url_next_param_on_authorization(
            self, redirect, flickr):
        fake_resp = {'oauth_token_secret': 'secret',
                     'username': 'palotespaco',
                     'fullname': 'paco palotes',
                     'oauth_token':'token',
                     'user_nsid': 'user'}
        flickr.authorized_response.return_value = fake_resp
        redirect.return_value = "OK"
        flask_app.test_client().get('/flickr/oauth-authorized?next=http://next')

        redirect.assert_called_with('http://next')

    @with_context
    @patch('pybossa.view.flickr.flickr')
    @patch('pybossa.view.flickr.redirect')
    def test_oauth_authorized_redirects_to_url_next_param_on_user_no_authorizing(
            self, redirect, flickr):
        flickr.authorized_response.return_value = None
        redirect.return_value = "OK"
        flask_app.test_client().get('/flickr/oauth-authorized?next=http://next')

        redirect.assert_called_with('http://next')


class TestFlickrAPI(object):

    @with_context
    @patch('pybossa.view.flickr.FlickrClient')
    def test_albums_endpoint_returns_user_albums_in_JSON_format(self, client):
        client_instance = MagicMock()
        client.return_value = client_instance
        albums = ['one album', 'another album']
        client_instance.get_user_albums.return_value = albums
        resp = flask_app.test_client().get('/flickr/albums')
        assert resp.data == json.dumps(albums).encode('utf-8'), resp.data
