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

    def setUp(self):
        self.app = flask_app.test_client()


    @patch('pybossa.view.flickr.flickr')
    def test_flickr_login_specifies_callback(self, flickr_oauth):
        flickr_oauth.oauth.authorize.return_value = Response(302)
        self.app.get('/flickr/')
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
