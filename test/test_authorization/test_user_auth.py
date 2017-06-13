# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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

from default import Test, assert_not_raises, with_context
from pybossa.auth import ensure_authorized_to
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import ProjectFactory, BlogpostFactory, UserFactory
from pybossa.model.user import User


class TestUserAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_create(self):
        """Test anonymous users cannot create users"""
        assert_raises(Unauthorized, ensure_authorized_to, 'create', User)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_create(self):
        """Test authenticated users cannot create users"""
        assert_raises(Forbidden, ensure_authorized_to, 'create', User)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admins_can_create(self):
        """Test admins users can create users"""
        assert_not_raises(Exception, ensure_authorized_to, 'create', User)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read(self):
        """Test anonymous users can read users"""
        assert_not_raises(Exception, ensure_authorized_to, 'read', User)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read(self):
        """Test authenticated users can read users"""
        assert_not_raises(Exception, ensure_authorized_to, 'read', User)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admins_can_read(self):
        """Test admins users can read users"""
        assert_not_raises(Exception, ensure_authorized_to, 'read', User)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read_given_user(self):
        """Test anonymous users can read a given user"""
        user = UserFactory.create()
        assert_not_raises(Exception, ensure_authorized_to, 'read', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read_given_user(self):
        """Test authenticated users can read a given user"""
        user = UserFactory.create()
        assert_not_raises(Exception, ensure_authorized_to, 'read', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admins_can_read_given_user(self):
        """Test admins users can read a given user"""
        user = UserFactory.create()
        assert_not_raises(Exception, ensure_authorized_to, 'read', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_update_given_user(self):
        """Test anonymous users cannot update a given user"""
        user = UserFactory.create()
        assert_raises(Unauthorized, ensure_authorized_to, 'update', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_update_another_user(self):
        """Test authenticated users cannot update another user than themselves"""
        user = UserFactory.create()

        assert user.id != self.mock_authenticated.id, user.id
        assert_raises(Forbidden, ensure_authorized_to, 'update', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_update_themselves(self):
        """Test authenticated users can update themselves"""
        user = UserFactory.create_batch(2)[1]

        assert user.id == self.mock_authenticated.id, user.id
        assert_not_raises(Exception, ensure_authorized_to, 'update', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admins_can_update_any_user(self):
        """Test admins users can update any given user"""
        himself = UserFactory.create()
        other_user = UserFactory.create()

        assert himself.id == self.mock_admin.id
        assert other_user.id != self.mock_admin.id
        assert_not_raises(Exception, ensure_authorized_to, 'update', other_user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_delete_given_user(self):
        """Test anonymous users cannot delete a given user"""
        user = UserFactory.create()
        assert_raises(Unauthorized, ensure_authorized_to, 'delete', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_delete_another_user(self):
        """Test authenticated users cannot delete another user than themselves"""
        user = UserFactory.create()

        assert user.id != self.mock_authenticated.id, user.id
        assert_raises(Forbidden, ensure_authorized_to, 'delete', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_delete_themselves(self):
        """Test authenticated users can delete themselves"""
        user = UserFactory.create_batch(2)[1]

        assert user.id == self.mock_authenticated.id, user.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete', user)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admins_can_delete_any_user(self):
        """Test admins users can delete any given user"""
        himself = UserFactory.create()
        other_user = UserFactory.create()

        assert himself.id == self.mock_admin.id
        assert other_user.id != self.mock_admin.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete', other_user)
