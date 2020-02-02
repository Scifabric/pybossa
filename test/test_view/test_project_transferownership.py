# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric 
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
from default import db, with_context
from factories import ProjectFactory, UserFactory
from helper import web
from pybossa.repositories import UserRepository, ProjectRepository
import json

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)

class TestProjectTransferOwnership(web.Helper):

    @with_context
    def test_transfer_anon_get(self):
        """Test transfer ownership page is not shown to anon."""
        project = ProjectFactory.create()
        url = '/project/%s/transferownership' % project.short_name
        res = self.app_get_json(url, follow_redirects=True)
        assert 'signin' in str(res.data), res.data

    @with_context
    def test_transfer_auth_not_owner_get(self):
        """Test transfer ownership page is forbidden for not owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            user.api_key)
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['code'] == 403, data

    @with_context
    def test_transfer_auth_owner_get(self):
        """Test transfer ownership page is ok for owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            owner.api_key)
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['form'], data
        assert data['form']['errors'] == {}, data
        assert data['form']['email_addr'] is '', data
        assert data['form']['csrf'] is not None, data

    @with_context
    def test_transfer_auth_admin_get(self):
        """Test transfer ownership page is ok for admin."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            admin.api_key)
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['form'], data
        assert data['form']['errors'] == {}, data
        assert data['form']['email_addr'] is '', data
        assert data['form']['csrf'] is not None, data

    @with_context
    def test_transfer_auth_owner_post(self):
        """Test transfer ownership page post is ok for owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            owner.api_key)

        assert project.owner_id == owner.id
        payload = dict(email_addr=user.email_addr)
        res = self.app_post_json(url, data=payload,
                                 follow_redirects=True)
        data = json.loads(res.data)
        assert data['next'] is not None, data

        err_msg = "The project owner id should be different"
        assert project.owner_id == user.id, err_msg

    @with_context
    def test_transfer_auth_owner_post_wrong_email(self):
        """Test transfer ownership page post is ok for wrong email."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            owner.api_key)

        assert project.owner_id == owner.id
        payload = dict(email_addr="wrong@email.com")
        res = self.app_post_json(url, data=payload,
                                 follow_redirects=True)
        data = json.loads(res.data)
        assert data['next'] is not None, data
        assert "project owner not found" in data['flash'], data
        err_msg = "The project owner id should be the same"
        assert project.owner_id == owner.id, err_msg

    @with_context
    def test_transfer_auth_admin_post(self):
        """Test transfer ownership page post is ok for admin."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            admin.api_key)

        assert project.owner_id == owner.id
        payload = dict(email_addr=user.email_addr)
        res = self.app_post_json(url, data=payload,
                                 follow_redirects=True)
        data = json.loads(res.data)
        assert data['next'] is not None, data

        err_msg = "The project owner id should be different"
        assert project.owner_id == user.id, err_msg

    @with_context
    def test_transfer_auth_user_post(self):
        """Test transfer ownership page post is forbidden for not owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/transferownership?api_key=%s' % (project.short_name,
                                                            user.api_key)

        assert project.owner_id == owner.id
        payload = dict(email_addr=user.email_addr)
        res = self.app_post_json(url, data=payload,
                                 follow_redirects=True)
        data = json.loads(res.data)
        assert data['code'] == 403, data
