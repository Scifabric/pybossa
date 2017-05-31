# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
from factories import ProjectFactory, HelpingMaterialFactory, UserFactory
from pybossa.model.helpingmaterial import HelpingMaterial



class TestHelpingMaterialAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_given_helpingmaterial(self):
        """Test anonymous users cannot create helping materials for a project"""

        project = ProjectFactory.create()
        helping = HelpingMaterialFactory.build(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to, 'create', helping)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_helpingmaterials_for_given_project(self):
        """Test anonymous users cannot create helpingmaterials for a given project"""

        project = ProjectFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'create', HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_helpingmaterials(self):
        """Test anonymous users cannot create any helpingmaterials"""

        assert_raises(Unauthorized, ensure_authorized_to, 'create', HelpingMaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_create_given_helpingmaterial(self):
        """Test authenticated user cannot create a given helpingmaterial if is not the
        project owner"""

        project = ProjectFactory.create()
        helpingmaterial = HelpingMaterialFactory.build(project_id=project.id)

        assert self.mock_authenticated.id != project.owner_id
        assert_raises(Forbidden, ensure_authorized_to,
                      'create', helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_create_helpingmaterial_for_given_project(self):
        """Test authenticated user cannot create helpingmaterials for a given project
        if is not the project owner"""

        owner = UserFactory.create(id=3)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'create',
                      HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_given_helpingmaterial(self):
        """Test authenticated user can create a given helpingmaterial if it's project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)
        helpingmaterial = HelpingMaterialFactory.build(project_id=project.id)

        assert self.mock_authenticated.id == project.owner_id
        assert_not_raises(Exception, ensure_authorized_to, 'create', helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_create_helpingmaterial_for_given_project(self):
        """Test authenticated user can create helpingmaterials for a given project
        if it's project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'create',
                          HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_create_helpingmaterial_for_given_project(self):
        """Test admin user can create helpingmaterials for a given project
        even if it's not project owner"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'create',
                          HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_given_helpingmaterial(self):
        """Test anonymous users can read a given helpingmaterial"""

        project = ProjectFactory.create(published=True)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to,
                          'read', helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_helpingmaterials_for_given_project(self):
        """Test anonymous users can read helpingmaterials of a given project"""

        project = ProjectFactory.create(published=True)
        assert_not_raises(Exception, ensure_authorized_to,
                          'read', HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_given_helpingmaterial_draft_project(self):
        """Test anonymous users cannot read a given helpingmaterial of
        a draft project"""

        project = ProjectFactory.create(published=False)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to,
                      'read', helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read_helpingmaterials_for_given_draft_project(self):
        """Test anonymous users cannot read helpingmaterials of a
        given project if is a draft"""

        project = ProjectFactory.create(published=False)

        assert_raises(Unauthorized, ensure_authorized_to, 'read',
                      HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_given_helpingmaterial(self):
        """Test authenticated user can read a given helpingmaterial
        if is not the project owner"""

        project = ProjectFactory.create(published=True)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_authenticated.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to,
                          'read', helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_helpingmaterials_for_given_project(self):
        """Test authenticated user can read helpingmaterials of a given project if
        is not the project owner"""

        project = ProjectFactory.create(published=True)

        assert self.mock_authenticated.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to,
                          'read', HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_given_helpingmaterial_draft_project(self):
        """Test authenticated user cannot read a given helpingmaterial of a
        draft project if is not the project owner"""

        project = ProjectFactory.create(published=False)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'read', helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_read_helpingmaterials_for_given_draft_project(self):
        """Test authenticated user cannot read helpingmaterials of a given project if is
        a draft and is not the project owner"""

        project = ProjectFactory.create(published=False)

        assert self.mock_authenticated.id != project.owner.id
        assert_raises(Forbidden, ensure_authorized_to, 'read',
                      HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_given_helpingmaterial(self):
        """Test authenticated user can read a given helpingmaterial
        if is the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=True)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_helpingmaterials_for_given_project(self):
        """Test authenticated user can read helpingmaterials of a given project
        if is the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=True)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_given_helpingmaterial_draft_project(self):
        """Test authenticated user can read a given helpingmaterial
        of a draft project if it's the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=False)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_read_helpingmaterials_for_given_draft_project(self):
        """Test authenticated user can read helpingmaterials of a given
        draft project if it's the project owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner, published=False)

        assert self.mock_authenticated.id == project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_read_given_helpingmaterial_draft_project(self):
        """Test admin can read a given helpingmaterial of a draft project"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner, published=False)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_read_helpingmaterials_for_given_draft_project(self):
        """Test admin can read helpingmaterials of a given draft project"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(published=False, owner=owner)

        assert self.mock_admin.id != project.owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'read',
                          HelpingMaterial, project_id=project.id)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_update_helpingmaterial(self):
        """Test anonymous users cannot update helpingmaterials"""

        project = ProjectFactory.create(published=True)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to, 'update',
                      helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_update_helpingmaterial(self):
        """Test authenticated user can update helpingmaterial
        if it's the post owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to, 'update',
                          helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_owner_update_helpingmaterial(self):
        """Test admins can update helpingmaterial
        even if it's not the post owner"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to, 'update',
                          helpingmaterial)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_helpingmaterial(self):
        """Test anonymous users cannot delete helpingmaterials"""

        project = ProjectFactory.create(published=True)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert_raises(Unauthorized, ensure_authorized_to, 'delete',
                      helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_non_owner_authenticated_user_delete_helpingmaterial(self):
        """Test authenticated user cannot delete a helpingmaterial if is not the post
        owner and is not admin"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner, published=True)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_authenticated.id != owner.id
        assert not self.mock_authenticated.admin
        assert_raises(Forbidden, ensure_authorized_to, 'delete',
                      helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_delete_helpingmaterial(self):
        """Test authenticated user can delete a helpingmaterial if is the post
        owner"""

        owner = UserFactory.create(id=2)
        project = ProjectFactory.create(owner=owner)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete',
                          helpingmaterial)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_authenticated_user_delete_helpingmaterial(self):
        """Test authenticated user can delete any helpingmaterial if
        it's admin"""

        owner = UserFactory.create(id=5)
        project = ProjectFactory.create(owner=owner)
        helpingmaterial = HelpingMaterialFactory.create(project_id=project.id)

        assert self.mock_admin.id != owner.id
        assert_not_raises(Exception, ensure_authorized_to, 'delete',
                          helpingmaterial)
