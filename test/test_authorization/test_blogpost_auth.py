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
from pybossa.model.blogpost import Blogpost



class TestBlogpostAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False,
                                           id=555555)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_given_blogpost(self):
        """Test anonymous users cannot create a given blogpost"""

        project = ProjectFactory.create()
        blogpost = BlogpostFactory.build(project=project, owner=None)

        assert_raises(Unauthorized, ensure_authorized_to, 'create', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_blogposts_for_given_project(self):
        """Test anonymous users cannot create blogposts for a given project"""

        project = ProjectFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'create', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_blogposts(self):
        """Test anonymous users cannot create any blogposts"""

        assert_raises(Unauthorized, ensure_authorized_to, 'create', Blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_create_given_blogpost(self):
        """Test authenticated user cannot create a given blogpost if is not the
        project owner, even if is admin"""

        admin = UserFactory.create()
        project = ProjectFactory.create()
        blogpost = BlogpostFactory.build(project=project, owner=admin)

        assert self.mock_authenticated.id != project.owner_id
        assert_raises(Forbidden, ensure_authorized_to, 'create',
                      blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_create_blogpost_for_given_project(self):
        """Test authenticated user cannot create blogposts for a given project
        if is not the project owner, even if it's admin"""

        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'create',
                      Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_given_blogpost(self):
        """Test authenticated user can create a given blogpost 
        if is project owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner)
        blogpost = BlogpostFactory.build(project=project,
                                         owner=owner)

        assert self.mock_authenticated.id == project.owner_id
        assert_not_raises(Exception, ensure_authorized_to,
                          'create', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_blogpost_for_given_project(self):
        """Test authenticated user can create blogposts for a given project
        if is project owner"""

        #admin, owner, user = UserFactory.create_batch(3)
        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'create', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_blogpost_as_other_user(self):
        """Test authenticated user cannot create blogpost if is project owner but
        sets another person as the author of the blogpost"""

        another_user = UserFactory.create(id=99999)
        project = ProjectFactory.create(owner=another_user)
        blogpost = BlogpostFactory.build(project_id=project.id,
                                          user_id=another_user.id)

        assert self.mock_authenticated.id != project.owner_id
        assert_raises(Forbidden, ensure_authorized_to, 'create',
                      blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_given_blogpost(self):
        """Test anonymous users can read a given blogpost"""

        project = ProjectFactory.create(published=True)
        blogpost = BlogpostFactory.create(project=project)

        assert_not_raises(Exception, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_blogposts_for_given_project(self):
        """Test anonymous users can read blogposts of a given project"""

        project = ProjectFactory.create(published=True)
        assert_not_raises(Exception, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_given_blogpost_draft_project(self):
        """Test anonymous users cannot read a given blogpost of a draft project"""

        project = ProjectFactory.create(published=False)
        blogpost = BlogpostFactory.create(project=project)

        assert_raises(Unauthorized, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_blogposts_for_given_draft_project(self):
        """Test anonymous users cannot read blogposts of a given project if is a draft"""

        project = ProjectFactory.create(published=False)

        assert_raises(Unauthorized, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_given_blogpost(self):
        """Test authenticated user can read a given blogpost if is not the project owner"""

        project = ProjectFactory.create(published=True)
        user = UserFactory.create()
        blogpost = BlogpostFactory.create(project=project)

        assert self.mock_authenticated.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_blogposts_for_given_project(self):
        """Test authenticated user can read blogposts of a given project if
        is not the project owner"""

        project = ProjectFactory.create(published=True)
        user = UserFactory.create()

        assert self.mock_authenticated.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_given_blogpost_draft_project(self):
        """Test authenticated user cannot read a given blogpost of a draft project
        if is not the project owner"""

        project = ProjectFactory.create(published=False)
        user = UserFactory.create()
        blogpost = BlogpostFactory.create(project=project)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_blogposts_for_given_draft_project(self):
        """Test authenticated user cannot read blogposts of a given project if is
        a draft and is not the project owner"""

        project = ProjectFactory.create(published=False)
        user = UserFactory.create()

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_given_blogpost(self):
        """Test authenticated user can read a given blogpost if is the project owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner, published=True)
        blogpost = BlogpostFactory.create(project=project)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_blogposts_for_given_project(self):
        """Test authenticated user can read blogposts of a given project if is the
        project owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner,
                                        published=True)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_given_blogpost_draft_project(self):
        """Test authenticated user can read a given blogpost of a draft project if
        is the project owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner, published=False)
        blogpost = BlogpostFactory.create(project=project)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_blogposts_for_given_draft_project(self):
        """Test authenticated user can read blogposts of a given draft project if
        is the project owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner,
                                        published=False)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_read_given_blogpost_draft_project(self):
        """Test admin can read a given blogpost of a draft project"""

        admin = UserFactory.create()
        project = ProjectFactory.create(published=False)
        blogpost = BlogpostFactory.create(project=project)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_read_blogposts_for_given_draft_project(self):
        """Test admin can read blogposts of a given draft project"""

        admin = UserFactory.create()
        project = ProjectFactory.create(published=False)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read', Blogpost, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_update_blogpost(self):
        """Test anonymous users cannot update blogposts"""

        blogpost = BlogpostFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'update', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_update_blogpost(self):
        """Test authenticated user cannot update a blogpost if is not the post
        owner, even if is admin"""

        admin = UserFactory.create()
        project = ProjectFactory.create()
        blogpost = BlogpostFactory.create(project=project)

        assert self.mock_authenticated.id != blogpost.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'update',
                      blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_update_blogpost(self):
        """Test authenticated user can update blogpost if is the post owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create()
        blogpost = BlogpostFactory.create(project=project, owner=owner)

        assert self.mock_authenticated.id == blogpost.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'update', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_blogpost(self):
        """Test anonymous users cannot delete blogposts"""

        blogpost = BlogpostFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'delete', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_delete_blogpost(self):
        """Test authenticated user cannot delete a blogpost if is not the post
        owner and is not admin"""

        blogpost = BlogpostFactory.create()

        assert self.mock_authenticated.id != blogpost.owner.id
        assert not self.mock_authenticated.admin
        assert_raises(Forbidden, ensure_authorized_to, 'delete', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_delete_blogpost(self):
        """Test authenticated user can delete a blogpost 
        if it is the post owner"""

        owner = UserFactory.create(id=self.mock_authenticated.id,
                                   admin=False)
        project = ProjectFactory.create(owner=owner)
        blogpost = BlogpostFactory.create(project=project,
                                          owner=owner)

        assert self.mock_authenticated.id == blogpost.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete', blogpost)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_authenticated_user_delete_blogpost(self):
        """Test authenticated user can delete any blogpost if is admin"""

        admin = UserFactory.create()
        blogpost = BlogpostFactory.create()

        assert self.mock_admin.id != blogpost.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete', blogpost)
