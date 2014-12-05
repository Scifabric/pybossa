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

from default import Test, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import AppFactory, UserFactory, TaskFactory



class TestTaskAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_create(self):
        """Test anonymous users cannot create tasks"""
        user = UserFactory.create()
        app = AppFactory.create(owner=user)
        task = TaskFactory.create(app=app)
        with patch('pybossa.auth.task.current_user', new=self.mock_anonymous):
            assert_raises(Unauthorized, getattr(require, 'task').create)
            assert_not_raises(Forbidden, getattr(require, 'task').read, task)
            assert_raises(Unauthorized, getattr(require, 'task').update, task)
            assert_raises(Unauthorized, getattr(require, 'task').delete, task)


    def test_project_owner_can_crud(self):
        """Test project owner can crud tasks"""
        user = UserFactory.create()
        app = AppFactory.create(owner=user)
        task = TaskFactory.create(app=app)
        with patch('pybossa.auth.task.current_user', new=user):
            assert_not_raises(Forbidden, getattr(require, 'task').create, task)
            assert_not_raises(Forbidden, getattr(require, 'task').read, task)
            assert_not_raises(Forbidden, getattr(require, 'task').update, task)
            assert_not_raises(Forbidden, getattr(require, 'task').delete, task)

    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_not_project_owner_cannot_crud(self):
        """Test authenticated user cannot crud tasks"""
        user = UserFactory.create()
        user2 = UserFactory.create()
        app = AppFactory.create(owner=user)
        task = TaskFactory.create(app=app)
        with patch('pybossa.auth.task.current_user', new=user2):
            assert_raises(Forbidden, getattr(require, 'task').create, task)
            assert_not_raises(Forbidden, getattr(require, 'task').read, task)
            assert_raises(Forbidden, getattr(require, 'task').update, task)
            assert_raises(Forbidden, getattr(require, 'task').delete, task)

    def test_admin_can_crud(self):
        """Test admin user can crud tasks"""
        user = UserFactory.create()
        user2 = UserFactory.create()
        app = AppFactory.create(owner=user2)
        task = TaskFactory.create(app=app)
        with patch('pybossa.auth.task.current_user', new=user):
            assert_not_raises(Forbidden, getattr(require, 'task').create, task)
            assert_not_raises(Forbidden, getattr(require, 'task').read, task)
            assert_not_raises(Forbidden, getattr(require, 'task').update, task)
            assert_not_raises(Forbidden, getattr(require, 'task').delete, task)
