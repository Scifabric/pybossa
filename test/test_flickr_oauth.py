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

from default import flask_app#, with_context
from mock import patch
from flask import Response, session

class TestFlickrOauth(object):


    @patch('pybossa.view.flickr.flickr')
    def test_flickr_login_specifies_callback(self, flickr_oauth):
        flickr_oauth.oauth.authorize.return_value = Response(302)
        flask_app.test_client().get('/flickr/')
        flickr_oauth.oauth.authorize.assert_called_with(callback='/flickr/oauth-authorized')


    def test_flickr_get_flickr_token_returns_None_if_no_token(self):
        from pybossa.view.flickr import get_flickr_token
        with flask_app.test_request_context():
            token = get_flickr_token()

        assert token is None, token


    def test_flickr_get_flickr_token_returns_existing_token(self):
        from pybossa.view.flickr import get_flickr_token
        with flask_app.test_request_context():
            session['flickr_token'] = 'fake_token'
            token = get_flickr_token()

        assert token is 'fake_token', token


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


    @patch('pybossa.view.flickr.redirect')
    def test_logout_redirects_to_url_specified_by_next_param(self, redirect):
        redirect.return_value = Response(302)
        flask_app.test_client().get('/flickr/revoke-access?next=http://mynext_url')

        redirect.assert_called_with('http://mynext_url')


    @patch('pybossa.view.flickr.flickr')
    def test_oauth_authorized_adds_token_and_user_to_session(self, flickr_oauth):
        fake_resp = {'oauth_token_secret': u'secret',
                     'username': u'palotespaco',
                     'fullname': u'paco palotes',
                     'oauth_token':u'token',
                     'user_nsid': u'user'}
        flickr_oauth.oauth.authorized_response.return_value = fake_resp

        with flask_app.test_client() as c:
            c.get('/flickr/oauth-authorized')
            flickr_token = session.get('flickr_token')
            flickr_user = session.get('flickr_user')

        assert flickr_token == {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        assert flickr_user == {'username': u'palotespaco', 'user_nsid': u'user'}


    @patch('pybossa.view.flickr.flickr')
    @patch('pybossa.view.flickr.redirect')
    def test_oauth_authorized_redirects_to_url_specified_by_next_param(
            self, redirect, flickr_oauth):
        fake_resp = {'oauth_token_secret': u'secret',
                     'username': u'palotespaco',
                     'fullname': u'paco palotes',
                     'oauth_token':u'token',
                     'user_nsid': u'user'}
        flickr_oauth.oauth.authorized_response.return_value = fake_resp
        redirect.return_value = Response(302)
        flask_app.test_client().get('/flickr/oauth-authorized?next=http://next')

        redirect.assert_called_with('http://next')
