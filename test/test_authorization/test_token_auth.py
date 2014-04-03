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

from base import web, model, Fixtures, db, redis_flushall, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user



class TestTokenAuthorization:

    auth_providers = ('twitter', 'facebook', 'google')
    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete(self):
        """Test anonymous user is not allowed to delete an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').delete,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete(self):
        """Test authenticated user is not allowed to delete an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').delete,
                          token)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create(self):
        """Test anonymous user is not allowed to create an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').create,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create(self):
        """Test authenticated user is not allowed to create an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').create,
                          token)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update(self):
        """Test anonymous user is not allowed to update an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').update,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update(self):
        """Test authenticated user is not allowed to update an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').update,
                          token)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_read(self):
        """Test anonymous user is not allowed to read an oauth token"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Unauthorized,
                          getattr(require, 'token').read,
                          token)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_read(self):
        """Test authenticated user is allowed to read his own oauth tokens"""
        with web.app.test_request_context('/'):
            for token in self.auth_providers:
                assert_raises(Forbidden,
                          getattr(require, 'token').read,
                          token)
