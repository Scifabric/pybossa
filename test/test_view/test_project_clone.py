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
from bs4 import BeautifulSoup

from default import Test, db, with_context
from helper.web import Helper
from factories import ProjectFactory, UserFactory
from mock import patch
from pybossa.core import project_repo

class TestProjectClone(Helper):

    patch_data_access_levels = dict(
        valid_access_levels=[("L1", "L1"), ("L2", "L2"),("L3", "L3"), ("L4", "L4")],
        valid_user_levels_for_project_task_level=dict(
            L1=[], L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"]),
        valid_task_levels_for_user_level=dict(
            L1=["L2", "L3", "L4"], L2=["L3", "L4"], L3=["L4"], L4=[]),
        valid_project_levels_for_task_level=dict(
            L1=["L1"], L2=["L1", "L2"], L3=["L1", "L2", "L3"], L4=["L1", "L2", "L3", "L4"]),
        valid_task_levels_for_project_level=dict(
            L1=["L1", "L2", "L3", "L4"], L2=["L2", "L3", "L4"], L3=["L3", "L4"], L4=["L4"])
    )

    @with_context
    def test_clone_render_current_data(self):
        admin = UserFactory.create()
        project = ProjectFactory.create(owner=admin)
        url = '/project/%s/clone?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res.data
        dom = BeautifulSoup(res.data)
        assert dom.find(id='short_name')['value'] == project.short_name
        assert dom.find(id='name')['value'] == project.name

    @with_context
    def test_clone_project(self):
        admin = UserFactory.create()
        project = ProjectFactory.create(id=40, short_name='oldname', owner=admin)

        data = {'short_name': 'newname', 'name': 'newname', 'password': 'Test123'}
        url = '/project/%s/clone?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.post(url, data=data)

        new_project_url = '/project/%s/?api_key=%s' % ('newname', project.owner.api_key)
        res = self.app.get(new_project_url)
        assert res.status_code == 200, res.data

    @with_context
    def test_clone_project_error(self):
        admin = UserFactory.create()
        project = ProjectFactory.create(id=40, short_name='oldname', owner=admin)

        data = {'short_name': project.short_name, 'name': project.name, 'password': 'Test123'}
        url = '/project/%s/clone?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.post(url, data=data)
        assert res.status_code == 200, res.data
        assert 'Please correct the errors' in res.data, res.data

    @with_context
    def test_clone_project_copy_assigned_users(self):

        from pybossa.view.projects import data_access_levels

        admin = UserFactory.create()
        user2 = UserFactory.create()
        assign_users = [admin.id, user2.id]
        task_presenter = 'test; pybossa.run("oldname"); test;'
        project = ProjectFactory.create(id=40,
                                        short_name='oldname',
                                        info={'task_presenter': task_presenter,
                                              'project_users': assign_users},
                                        owner=admin)

        with patch.dict(data_access_levels, self.patch_data_access_levels):
            data = {'short_name': 'newproj', 'name': 'newproj', 'password': 'Test123', 'copy_users': True}
            url = '/project/%s/clone?api_key=%s' % (project.short_name, project.owner.api_key)
            res = self.app.post(url, data=data)
            new_project = project_repo.get(1)
            task_presenter_expected = 'test; pybossa.run("newproj"); test;'

            assert new_project.get_project_users() == assign_users, new_project.get_project_users()
            assert new_project.info['task_presenter'] == task_presenter_expected, new_project.info['task_presenter']



