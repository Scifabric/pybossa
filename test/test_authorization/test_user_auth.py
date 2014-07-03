# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

from default import Test, db, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import AppFactory, BlogpostFactory, UserFactory
from factories import reset_all_pk_sequences



class TestUserAuthorization(Test):


    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.user.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_create(self):
        """Test anonymous users cannot create users"""
        assert_raises(Unauthorized, getattr(require, 'user').create)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.user.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_create(self):
        """Test authenticated users cannot create users"""
        assert_raises(Forbidden, getattr(require, 'user').create)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.user.current_user', new=mock_admin)
    def test_admins_can_create(self):
        """Test admins users can create users"""
        assert_not_raises(Exception, getattr(require, 'user').create)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.user.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read(self):
        """Test anonymous users can read users"""
        assert_not_raises(Exception, getattr(require, 'user').read)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.user.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read(self):
        """Test authenticated users can read users"""
        assert_not_raises(Exception, getattr(require, 'user').read)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.user.current_user', new=mock_admin)
    def test_admins_can_read(self):
        """Test admins users can read users"""
        assert_not_raises(Exception, getattr(require, 'user').read)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.user.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read_given_user(self):
        """Test anonymous users can read a given user"""
        user = UserFactory.create()
        assert_not_raises(Exception, getattr(require, 'user').read, user)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.user.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read_given_user(self):
        """Test authenticated users can read a given user"""
        user = UserFactory.create()
        assert_not_raises(Exception, getattr(require, 'user').read, user)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.user.current_user', new=mock_admin)
    def test_admins_can_read_given_user(self):
        """Test admins users can read a given user"""
        user = UserFactory.create()
        assert_not_raises(Exception, getattr(require, 'user').read, user)
