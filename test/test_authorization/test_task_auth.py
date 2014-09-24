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
from factories import reset_all_pk_sequences



class TestTaskAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.task.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_create(self):
        """Test anonymous users cannot create tasks"""
        assert_raises(Unauthorized, getattr(require, 'task').create)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_create(self):
        """Test authenticated users can't create tasks"""
        assert_raises(Exception, getattr(require, 'task').create)

    def test_project_owner_can_create(self):
        """Test project owner can create tasks"""
        admin = UserFactory.create()
        user = UserFactory.create()
        app = AppFactory.create(owner=user)
        task = TaskFactory.build(app=app)
        with patch('pybossa.auth.task.current_user', new=user):
            assert_not_raises(Exception, getattr(require, 'task').create, task)

    def test_not_project_owner_cannot_create(self):
        """Test authenticated user cannot create tasks"""
        user = UserFactory.create()
        user2 = UserFactory.create()
        app = AppFactory.create(owner=user)
        task = TaskFactory.build(app=app)
        with patch('pybossa.auth.task.current_user', new=user2):
            assert_raises(Exception, getattr(require, 'task').create, task)

    def test_admin_can_create(self):
        """Test admin user can create tasks"""
        user = UserFactory.create()
        user2 = UserFactory.create()
        app = AppFactory.create(owner=user2)
        task = TaskFactory.build(app=app)
        with patch('pybossa.auth.task.current_user', new=user):
            assert_not_raises(Exception, getattr(require, 'task').create, task)

#
#
#    @patch('pybossa.auth.current_user', new=mock_anonymous)
#    @patch('pybossa.auth.task.current_user', new=mock_anonymous)
#    def test_anonymous_user_can_read_all_projects(self):
#        """Test anonymous users can read non hidden projects"""
#        assert_not_raises(Exception, getattr(require, 'app').read)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_authenticated_user_can_read_all_projects(self):
#        """Test authenticated users can read non hidden projects"""
#        assert_not_raises(Exception, getattr(require, 'app').read)
#
#
#    @patch('pybossa.auth.current_user', new=mock_anonymous)
#    @patch('pybossa.auth.task.current_user', new=mock_anonymous)
#    def test_anonymous_user_can_read_given_non_hidden(self):
#        """Test anonymous users can read a given non hidden project"""
#        project = AppFactory.create()
#
#        assert_not_raises(Exception, getattr(require, 'app').read, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_authenticated_user_can_read_given_non_hidden(self):
#        """Test authenticated users can read a given non hidden project"""
#        project = AppFactory.create()
#
#        assert_not_raises(Exception, getattr(require, 'app').read, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_anonymous)
#    @patch('pybossa.auth.task.current_user', new=mock_anonymous)
#    def test_anonymous_user_cannot_read_given_hidden(self):
#        """Test anonymous users cannot read hidden projects"""
#        project = AppFactory.create(hidden=1)
#
#        assert_raises(Unauthorized, getattr(require, 'app').read, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_authenticated_user_cannot_read_given_hidden(self):
#        """Test authenticated users cannot read hidden projects if are not owners"""
#        project = AppFactory.create(hidden=1)
#
#        assert project.owner.id != self.mock_authenticated.id, project.owner
#        assert_raises(Forbidden, getattr(require, 'app').read, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_owners_can_read_given_hidden(self):
#        """Test the owner of a project can read it despite being hidden"""
#        owner = UserFactory.build_batch(2)[1]
#        project = AppFactory.create(hidden=1, owner=owner)
#
#        assert project.owner.id == self.mock_authenticated.id, project.owner
#        assert_not_raises(Exception, getattr(require, 'app').read, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_admin)
#    @patch('pybossa.auth.task.current_user', new=mock_admin)
#    def test_admin_can_read_given_hidden(self):
#        """Test an admin can read a project despite being hidden"""
#        owner = UserFactory.build_batch(2)[1]
#        project = AppFactory.create(hidden=1, owner=owner)
#
#        assert project.owner.id != self.mock_admin.id, project.owner
#        assert_not_raises(Exception, getattr(require, 'app').read, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_anonymous)
#    @patch('pybossa.auth.task.current_user', new=mock_anonymous)
#    def test_anonymous_user_cannot_update(self):
#        """Test anonymous users cannot update a project"""
#        project = AppFactory.create()
#
#        assert_raises(Unauthorized, getattr(require, 'app').update, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_authenticated_user_cannot_update(self):
#        """Test authenticated users cannot update a project if aren't owners"""
#        project = AppFactory.create()
#
#        assert project.owner.id != self.mock_authenticated.id, project.owner
#        assert_raises(Forbidden, getattr(require, 'app').update, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_owner_can_update(self):
#        """Test owners can update a project"""
#        owner = UserFactory.build_batch(2)[1]
#        project = AppFactory.create(owner=owner)
#
#        assert project.owner.id == self.mock_authenticated.id, project.owner
#        assert_not_raises(Exception, getattr(require, 'app').update, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_admin)
#    @patch('pybossa.auth.task.current_user', new=mock_admin)
#    def test_admin_can_update(self):
#        """Test an admin can update a project"""
#        owner = UserFactory.build_batch(2)[1]
#        project = AppFactory.create(hidden=1, owner=owner)
#
#        assert project.owner.id != self.mock_admin.id, project.owner
#        assert_not_raises(Exception, getattr(require, 'app').update, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_anonymous)
#    @patch('pybossa.auth.task.current_user', new=mock_anonymous)
#    def test_anonymous_user_cannot_delete(self):
#        """Test anonymous users cannot delete a project"""
#        project = AppFactory.create()
#
#        assert_raises(Unauthorized, getattr(require, 'app').delete, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_authenticated_user_cannot_delete(self):
#        """Test authenticated users cannot delete a project if aren't owners"""
#        project = AppFactory.create()
#
#        assert project.owner.id != self.mock_authenticated.id, project.owner
#        assert_raises(Forbidden, getattr(require, 'app').delete, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_authenticated)
#    @patch('pybossa.auth.task.current_user', new=mock_authenticated)
#    def test_owner_can_delete(self):
#        """Test owners can delete a project"""
#        owner = UserFactory.build_batch(2)[1]
#        project = AppFactory.create(owner=owner)
#
#        assert project.owner.id == self.mock_authenticated.id, project.owner
#        assert_not_raises(Exception, getattr(require, 'app').delete, project)
#
#
#    @patch('pybossa.auth.current_user', new=mock_admin)
#    @patch('pybossa.auth.task.current_user', new=mock_admin)
#    def test_admin_can_delete(self):
#        """Test an admin can delete a project"""
#        owner = UserFactory.build_batch(2)[1]
#        project = AppFactory.create(hidden=1, owner=owner)
#
#        assert project.owner.id != self.mock_admin.id, project.owner
#        assert_not_raises(Exception, getattr(require, 'app').delete, project)

