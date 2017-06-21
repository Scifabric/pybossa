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
from factories import ProjectFactory, UserFactory, TaskFactory
from pybossa.model.project import Project


class TestProjectAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_create(self):
        """Test anonymous users cannot projects"""
        assert_raises(Unauthorized, ensure_authorized_to, 'create', Project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_create(self):
        """Test authenticated users can create projects"""
        assert_not_raises(Exception, ensure_authorized_to, 'create', Project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_a_project_cannot_be_created_as_published(self):
        """Test a project cannot be created directly as published"""
        published_project = ProjectFactory.build(published=True)
        assert_raises(Forbidden, ensure_authorized_to, 'create', published_project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read_all_projects(self):
        """Test anonymous users can read projects"""
        assert_not_raises(Exception, ensure_authorized_to, 'read', Project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read_all_projects(self):
        """Test authenticated users can read projects"""
        assert_not_raises(Exception, ensure_authorized_to, 'read', Project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read_given_published(self):
        """Test anonymous users can read a given published project"""
        project = ProjectFactory.create(published=True)

        assert_not_raises(Exception, ensure_authorized_to, 'read', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read_given_published(self):
        """Test authenticated users can read a given published project"""
        project = ProjectFactory.create(published=True)

        assert_not_raises(Exception, ensure_authorized_to, 'read', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_read_given_draft(self):
        """Test anonymous users cannot read draft projects"""
        project = ProjectFactory.create(published=False)

        assert_raises(Unauthorized, ensure_authorized_to, 'read', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_read_given_draft(self):
        """Test authenticated users cannot read draft projects if are not owners"""
        project = ProjectFactory.create(published=False)

        assert project.owner.id != self.mock_authenticated.id, project.owner
        assert_raises(Forbidden, ensure_authorized_to, 'read', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owners_can_read_given_draft(self):
        """Test the owner of a project can read it despite being a draft"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(published=False, owner=owner)

        assert project.owner.id == self.mock_authenticated.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'read', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_can_read_given_draft(self):
        """Test an admin can read a project despite being a draft"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(published=False, owner=owner)

        assert project.owner.id != self.mock_admin.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'read', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_update(self):
        """Test anonymous users cannot update a project"""
        project = ProjectFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'update', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_update(self):
        """Test authenticated users cannot update a project if aren't owners"""
        project = ProjectFactory.create()

        assert project.owner.id != self.mock_authenticated.id, project.owner
        assert_raises(Forbidden, ensure_authorized_to, 'update', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_can_update(self):
        """Test owners can update a project"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner)

        assert project.owner.id == self.mock_authenticated.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'update', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_can_update(self):
        """Test an admin can update a project"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner)

        assert project.owner.id != self.mock_admin.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'update', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_delete(self):
        """Test anonymous users cannot delete a project"""
        project = ProjectFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'delete', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_delete(self):
        """Test authenticated users cannot delete a project if aren't owners"""
        project = ProjectFactory.create()

        assert project.owner.id != self.mock_authenticated.id, project.owner
        assert_raises(Forbidden, ensure_authorized_to, 'delete', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_can_delete(self):
        """Test owners can delete a project"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner)

        assert project.owner.id == self.mock_authenticated.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'delete', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_can_delete(self):
        """Test an admin can delete a project"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner)

        assert project.owner.id != self.mock_admin.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'delete', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_publish(self):
        """Test anonymous users cannot publish a project"""
        project = ProjectFactory.create(published=False)

        assert_raises(Unauthorized, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_cannot_publish(self):
        """Test non-owners cannot publish a project"""
        project = ProjectFactory.create(published=False)

        assert project.owner.id != self.mock_authenticated.id, project.owner
        assert_raises(Forbidden, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_cannot_publish_if_project_has_no_presenter(self):
        """Test owner cannot publish a project that has no presenter"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner, published=False, info={})
        TaskFactory.create(project=project)

        assert project.owner.id == self.mock_authenticated.id, project.owner
        assert_raises(Forbidden, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_cannot_publish_if_project_has_no_tasks(self):
        """Test owner cannot publish a project that has no tasks"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner, published=False)

        assert project.owner.id == self.mock_authenticated.id, project.owner
        assert_raises(Forbidden, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_can_publish_if_project_has_tasks_and_presenter(self):
        """Test owner can publish a project that has tasks and a presenter"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner, published=False)
        TaskFactory.create(project=project)

        assert project.owner.id == self.mock_authenticated.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_cannot_publish_if_project_has_no_presenter(self):
        """Test admins cannot publish a project that has no presenter"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner, published=False, info={})
        TaskFactory.create(project=project)

        assert_raises(Forbidden, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_cannot_publish_if_project_has_no_tasks(self):
        """Test admins cannot publish a project that has no tasks"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner, published=False)

        assert_raises(Forbidden, ensure_authorized_to, 'publish', project)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_can_publish_if_project_has_tasks_and_presenter(self):
        """Test admins can publish a project that has tasks and a presenter"""
        owner = UserFactory.build_batch(2)[1]
        project = ProjectFactory.create(owner=owner, published=False)
        TaskFactory.create(project=project)

        assert project.owner.id != self.mock_admin.id, project.owner
        assert_not_raises(Exception, ensure_authorized_to, 'publish', project)
