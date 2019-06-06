# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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
from factories import ProjectFactory, PageFactory, UserFactory
from pybossa.model.page import Page


class TestPageAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_given_page(self):
        """Test anonymous users cannot create pages for a project"""

        project = ProjectFactory.create()
        page = PageFactory.build(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to, 'create', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_pages_for_given_project(self):
        """Test anonymous users cannot create pages for a given project"""

        project = ProjectFactory.create()

        assert_raises(Unauthorized,
                      ensure_authorized_to,
                      'create',
                      Page,
                      project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_pages(self):
        """Test anonymous users cannot create any pages"""

        assert_raises(Unauthorized, ensure_authorized_to, 'create', Page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_create_given_page(self):
        """Test authenticated user cannot create a given page if is not the
        project owner"""

        project = ProjectFactory.create()
        page = PageFactory.build(project_id=project.id)

        assert self.mock_authenticated.id != project.owner_id
        assert_raises(Forbidden, ensure_authorized_to,
                      'create', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_create_page_for_given_project(self):
        """Test authenticated user cannot create pages for a given project
        if is not the project owner"""

        owner = UserFactory.create(id=3)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'create',
                      Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_given_page(self):
        """Test authenticated user can create a given page
        if it's project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)
        page = PageFactory.build(project_id=project.id)

        assert self.mock_authenticated.id == project.owner_id
        assert_not_raises(Exception, ensure_authorized_to, 'create', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_page_for_given_project(self):
        """Test authenticated user can create pages for a given project
        if it's project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'create',
                          Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_create_page_for_given_project(self):
        """Test admin user can create pages for a given project
        even if it's not project owner"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'create',
                          Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_given_page(self):
        """Test anonymous users can read a given page"""

        project = ProjectFactory.create(published=True)
        page = PageFactory.create(project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to,
                          'read', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_pages_for_given_project(self):
        """Test anonymous users can read pages of a given project"""

        project = ProjectFactory.create(published=True)
        assert_not_raises(Exception, ensure_authorized_to,
                          'read', Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_given_page_draft_project(self):
        """Test anonymous users cannot read a given page of
        a draft project"""

        project = ProjectFactory.create(published=False)
        page = PageFactory.create(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to,
                      'read', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_pages_for_given_draft_project(self):
        """Test anonymous users cannot read pages of a
        given project if is a draft"""

        project = ProjectFactory.create(published=False)

        assert_raises(Unauthorized, ensure_authorized_to, 'read',
                      Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_given_page(self):
        """Test authenticated user can read a given page
        if is not the project owner"""

        project = ProjectFactory.create(published=True)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_authenticated.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to,
                          'read', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_pages_for_given_project(self):
        """Test authenticated user can read pages of a given project if
        is not the project owner"""

        project = ProjectFactory.create(published=True)

        assert self.mock_authenticated.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to,
                          'read', Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_given_page_draft_project(self):
        """Test authenticated user cannot read a given page of a
        draft project if is not the project owner"""

        project = ProjectFactory.create(published=False)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'read', page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_pages_for_given_draft_project(self):
        """Test authenticated user cannot read pages of a given project if is
        a draft and is not the project owner"""

        project = ProjectFactory.create(published=False)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'read',
                      Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_given_page(self):
        """Test authenticated user can read a given page
        if is the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=True)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_pages_for_given_project(self):
        """Test authenticated user can read pages of a given project
        if is the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=True)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_given_page_draft_project(self):
        """Test authenticated user can read a given page
        of a draft project if it's the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=False)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_pages_for_given_draft_project(self):
        """Test authenticated user can read pages of a given
        draft project if it's the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=False)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_read_given_page_draft_project(self):
        """Test admin can read a given page of a draft project"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner, published=False)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_read_pages_for_given_draft_project(self):
        """Test admin can read pages of a given draft project"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(published=False, owner=owner)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          Page, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_update_page(self):
        """Test anonymous users cannot update pages"""

        project = ProjectFactory.create(published=True)
        page = PageFactory.create(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to, 'update',
                      page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_update_page(self):
        """Test authenticated user can update page
        if it's the project's page owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)
        page = PageFactory.create(project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to, 'update',
                          page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_update_page(self):
        """Test admins can update page
        even if it's not the post owner"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner)
        page = PageFactory.create(project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to, 'update',
                          page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_page(self):
        """Test anonymous users cannot delete pages"""

        project = ProjectFactory.create(published=True)
        page = PageFactory.create(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to, 'delete',
                      page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_delete_page(self):
        """Test authenticated user cannot delete a page if is not the page's
        owner and is not admin"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner, published=True)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_authenticated.id != owner.id
        assert not self.mock_authenticated.admin
        assert_raises(Forbidden, ensure_authorized_to, 'delete',
                      page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_delete_page(self):
        """Test authenticated user can delete a page if is the page
        owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete',
                          page)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_authenticated_user_delete_page(self):
        """Test authenticated user can delete any page if
        it's admin"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner)
        page = PageFactory.create(project_id=project.id)

        assert self.mock_admin.id != owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete',
                          page)
