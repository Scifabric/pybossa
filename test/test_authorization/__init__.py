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

from default import assert_not_raises
from mock import Mock, patch, PropertyMock
from pybossa.auth import ensure_authorized_to, is_authorized
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from pybossa.model.user import User


def mock_current_user(anonymous=True, admin=None, id=None, pro=False):
    mock = Mock(spec=User)
    mock.is_anonymous = anonymous
    mock.is_authenticated = not anonymous
    if anonymous:
        type(mock).admin = PropertyMock(side_effect=AttributeError)
        type(mock).pro = PropertyMock(side_effect=AttributeError)
        type(mock).id = PropertyMock(side_effect=AttributeError)
    else:
        mock.admin = admin
        mock.pro = pro
        mock.id = id
    return mock


class TestAuthorizationFunctions(object):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)

    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.is_authorized')
    def test_ensure_authorized_raises_401_anonymous_non_authorized(self, auth):
        auth.return_value = False

        assert_raises(Unauthorized, ensure_authorized_to, 'create', User)

    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.is_authorized')
    def test_ensure_authorized_not_raises_exc_anonymous_authorized(self, auth):
        auth.return_value = True

        assert_not_raises(Exception, ensure_authorized_to, 'create', User)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.is_authorized')
    def test_ensure_authorized_raises_403_authenticated_non_authorized(self, auth):
        auth.return_value = False

        assert_raises(Forbidden, ensure_authorized_to, 'create', User)

    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.is_authorized')
    def test_ensure_authorized_not_raises_exc_authenticated_authorized(self, auth):
        auth.return_value = True

        assert_not_raises(Exception, ensure_authorized_to, 'create', User)


    @patch('pybossa.auth._authorizer_for')
    def test_is_authorized_invalid_action(self, auth_factory):
        authorizer = Mock()
        authorizer.specific_actions = []
        auth_factory.return_value = authorizer
        user = self.mock_authenticated

        assert_raises(AssertionError, is_authorized, user, 'invalid', User)

    @patch('pybossa.auth._authorizer_for')
    def test_is_authorized_calls_can_with_None_for_classes(self, auth_factory):
        authorizer = Mock()
        authorizer.specific_actions = []
        auth_factory.return_value = authorizer
        user = self.mock_authenticated
        _class = User

        is_authorized(user, 'read', _class)

        auth_factory.assert_called_with(_class.__name__.lower())
        authorizer.can.assert_called_with(user, 'read', None)

    @patch('pybossa.auth._authorizer_for')
    def test_is_authorized_calls_can_with_object_for_instances(self, auth_factory):
        authorizer = Mock()
        authorizer.specific_actions = []
        auth_factory.return_value = authorizer
        user = self.mock_authenticated
        instance = User()

        is_authorized(user, 'read', instance)

        auth_factory.assert_called_with(instance.__class__.__name__.lower())
        authorizer.can.assert_called_with(user, 'read', instance)

    @patch('pybossa.auth._authorizer_for')
    def test_is_authorized_works_for_token_resource_too(self, auth_factory):
        authorizer = Mock()
        authorizer.specific_actions = []
        auth_factory.return_value = authorizer
        user = self.mock_authenticated

        is_authorized(user, 'read', 'token')

        auth_factory.assert_called_with('token')
        authorizer.can.assert_called_with(user, 'read', 'token')
