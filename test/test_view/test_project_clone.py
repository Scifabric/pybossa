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
        valid_user_levels_for_project_level=dict(
            L1=[], L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"]),
        valid_project_levels_for_user_level=dict(
            L1=["L2", "L3", "L4"], L2=["L3", "L4"], L3=["L4"], L4=[]),
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

        data = {'short_name': 'newname', 'name': 'newname', 'password': 'Test123', 'input_data_class': 'L4 - public','output_data_class': 'L4 - public'}
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
        task_presenter = 'test; url="project/oldname/" pybossa.run("oldname"); test;'
        project = ProjectFactory.create(id=40,
                                        short_name='oldname',
                                        info={'task_presenter': task_presenter,
                                              'quiz': {'test': 123},
                                              'enrichments': [{'test': 123}],
                                              'project_users': assign_users,
                                              'passwd_hash': 'testpass',
                                              'ext_config': {'test': 123}
                                            },
                                        owner=admin)

        with patch.dict(data_access_levels, self.patch_data_access_levels):
            data = {'short_name': 'newproj', 'name': 'newproj', 'password': 'Test123', 'copy_users': True, 'input_data_class': 'L4 - public','output_data_class': 'L4 - public'}
            url = '/project/%s/clone?api_key=%s' % (project.short_name, project.owner.api_key)
            res = self.app.post(url, data=data)
            new_project = project_repo.get(1)
            old_project = project_repo.get(40)
            task_presenter_expected = 'test; url="project/newproj/" pybossa.run("newproj"); test;'
            assert old_project.info['passwd_hash'] == 'testpass', old_project.info['passwd_hash']
            assert new_project.get_project_users() == assign_users, new_project.get_project_users()
            assert new_project.info['task_presenter'] == task_presenter_expected, new_project.info['task_presenter']
            assert new_project.info.get('enrichments') == None, new_project.info.get('enrichments')
            assert new_project.info.get('quiz') == None, new_project.info.get('quiz')
            assert new_project.info.get('ext_config') == {'test': 123}, new_project.info.get('ext_config')
            assert new_project.owner_id == admin.id, new_project.owner_id
            assert new_project.owners_ids == [admin.id], new_project.owners_ids


    @with_context
    def test_clone_project_not_copy_assigned_users(self):

        from pybossa.view.projects import data_access_levels

        admin = UserFactory.create(admin=False, subadmin=True)
        user2 = UserFactory.create()
        assign_users = [user2.id]
        task_presenter = 'test"; url="project/oldname/" pybossa.run("oldname"); test;'
        project = ProjectFactory.create(id=40,
                                        short_name='oldname',
                                        info={'task_presenter': task_presenter,
                                              'quiz': {'test': 123},
                                              'enrichments': [{'test': 123}],
                                              'project_users': assign_users,
                                              'passwd_hash': 'testpass',
                                              'ext_config': {'test': 123}},
                                        owner=user2)

        with patch.dict(data_access_levels, self.patch_data_access_levels):
            data = {'short_name': 'newproj', 'name': 'newproj', 'password': 'Test123', 'input_data_class': 'L4 - public','output_data_class': 'L4 - public'}
            url = '/project/%s/clone?api_key=%s' % (project.short_name, admin.api_key)
            res = self.app.post(url, data=data)
            new_project = project_repo.get(1)
            old_project = project_repo.get(40)
            task_presenter_expected = 'test"; url="project/newproj/" pybossa.run("newproj"); test;'
            assert old_project.owner_id == user2.id, old_project.owner_id
            assert old_project.info['passwd_hash'] == 'testpass', old_project.info['passwd_hash']
            assert new_project.info['task_presenter'] == task_presenter_expected, new_project.info['task_presenter']
            assert new_project.get_project_users() == [], new_project.get_project_users()
            assert new_project.info.get('enrichments') == None, new_project.info.get('enrichments')
            assert new_project.info.get('quiz') == None, new_project.info.get('quiz')
            assert new_project.info.get('ext_config', None) == None, new_project.info.get('ext_config', None)
            assert new_project.owner_id == admin.id, new_project.owner_id
            assert new_project.owners_ids == [admin.id], new_project.owners_ids





