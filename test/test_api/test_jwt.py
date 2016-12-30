# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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
import json
from default import flask_app, with_context
from mock import patch, Mock
from test_api import TestAPI
from factories import ProjectFactory
from pybossa.auth import jwt_authorize_project


class TestJwtAPI(TestAPI):

    @with_context
    def test_jwt_existing_project(self):
        """Test JWT for non existing project works."""
        project = ProjectFactory.create()
        url = '/api/auth/project/%s/token' % project.short_name
        resp = self.app.get(url)
        err_msg = "It should return a 403 as no Authorization headers."
        assert resp.status_code == 403, err_msg

        url = '/api/auth/project/nonexisting/token'
        resp = self.app.get(url)
        err_msg = "It should return a 403 as no Authorization headers."
        assert resp.status_code == 403, err_msg

    @with_context
    def test_jwt_with_auth_headers(self):
        """Test JWT with Auth headers."""
        project = ProjectFactory.create()
        headers = {'Authorization': project.secret_key}
        url = '/api/auth/project/%s/token' % project.short_name
        resp = self.app.get(url, headers=headers)

        err_msg = "It should get the token"
        assert resp.status_code == 200, err_msg
        bearer = "Bearer %s" % resp.data
        data = jwt_authorize_project(project, bearer)
        assert data, err_msg

    @with_context
    def test_jwt_with_auth_headers_nonproject(self):
        """Test JWT with Auth headers but no project."""
        project = ProjectFactory.create()
        headers = {'Authorization': project.secret_key}
        url = '/api/auth/project/nnon/token'
        resp = self.app.get(url, headers=headers)

        err_msg = "It should return 404 as project does not exist"
        assert resp.status_code == 404, err_msg

    @with_context
    def test_jwt_with_auth_headers_wrong_secret(self):
        """Test JWT with Auth headers but wrong project secret."""
        project = ProjectFactory.create()
        headers = {'Authorization': 'foobar'}
        url = '/api/auth/project/%s/token'
        resp = self.app.get(url, headers=headers)

        err_msg = "It should return 404 as project does not exist"
        assert resp.status_code == 404, err_msg
