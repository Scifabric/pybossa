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
from factories import CategoryFactory
from pybossa.model.category import Category



class TestProjectAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_crud(self):
        """Test anonymous users cannot crud categories"""
        category = CategoryFactory.build()

        assert_raises(Unauthorized, ensure_authorized_to, 'create', category)
        assert_not_raises(Exception, ensure_authorized_to, 'read', category)
        assert_not_raises(Exception, ensure_authorized_to, 'read', Category)
        assert_raises(Unauthorized, ensure_authorized_to, 'update', category)
        assert_raises(Unauthorized, ensure_authorized_to, 'delete', category)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_crud(self):
        """Test authenticated users cannot crud categories"""
        category = CategoryFactory.build()

        assert_raises(Forbidden, ensure_authorized_to, 'create', category)
        assert_not_raises(Exception, ensure_authorized_to, 'read', category)
        assert_not_raises(Exception, ensure_authorized_to, 'read', Category)
        assert_raises(Forbidden, ensure_authorized_to, 'update', category)
        assert_raises(Forbidden, ensure_authorized_to, 'delete', category)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_can_crud(self):
        """Test admin user can crud categories"""
        category = CategoryFactory.build()

        assert_not_raises(Forbidden, ensure_authorized_to, 'create', category)
        assert_not_raises(Forbidden, ensure_authorized_to, 'read', category)
        assert_not_raises(Forbidden, ensure_authorized_to, 'read', Category)
        assert_not_raises(Forbidden, ensure_authorized_to, 'update', category)
        assert_not_raises(Forbidden, ensure_authorized_to, 'delete', category)
