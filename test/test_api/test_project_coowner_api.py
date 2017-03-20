# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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
import json
from default import db, with_context
from nose.tools import assert_equal
from test_api import TestAPI
from mock import patch, call

from factories import ProjectFactory, UserFactory

from pybossa.repositories import ProjectRepository, ProjectCoownerRepository

project_repo = ProjectRepository(db)
projectcoowner_repo = ProjectCoownerRepository(db)

class TestProjectCoownerAPI(TestAPI):

    @with_context
    def test_project_coowners_get(self):
        import pdb; pdb.set_trace()
        """Test API query for project coowners works."""
        admin = UserFactory.create(admin=True, subadmin=False)
        project = ProjectFactory.create()
        url = 'api/projectcoowner?api_key={0}&project_id={1}'

        # Test no coowner
        res = self.app.get(url.format(admin.api_key, project.id))
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Test single coowner
        subadmin1 = UserFactory.create(admin=False, subadmin=True)
        coowner1 = ProjectCoownerFactory(project_id=project.id, coowner_id=subadmin1.id)
        res = self.app.get(url.format(admin.api_key, project.id))
        data = json.loads(res.data)
        assert len(data) == 1, data

        # Test multiple coowners
        subadmin2 = UserFactory.create(admin=False, subadmin=True)
        coowner2 = ProjectCoownerFactory(project_id=project.id, coowner_id=subadmin2.id)
        res = self.app.get(url.format(admin.api_key, project.id))
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert len(data['cowner_ids']) == 2, data

        # Test subadmin api_key
        res = self.app.get(url.format(subadmin1.api_key, project.id))
        assert len(data) == 1, data
        assert len(data['cowner_ids']) == 2, data

        # Test non-admin/non-subadmin api_key
        user = UserFactory.create(admin=False, subadmin=False)
        res = self.app.get(url.format(user.api_key, project.id))
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 403, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg

        # Test no api_key
        res = self.app.get('api/projectcoowner'.format(project.id)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 403, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg

        res = self.app.get('api/projectcoowner?project_id={0}'.format(project.id)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 403, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg

