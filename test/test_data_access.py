# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
from default import with_context, db, Test
from mock import patch
from factories import ProjectFactory, TaskFactory, UserFactory
from nose.tools import nottest, assert_raises
from pybossa.core import user_repo

class TestAccessLevels(Test):

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

    def test_can_assign_user(self):
        from pybossa import data_access

        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            proj_levels = ["L3"]
            user_levels = ["L2", "L4"]
            assign_users = data_access.can_assign_user(proj_levels, user_levels)
            assert assign_users

            proj_levels = ["L5"]
            user_levels = ["L2", "L4"]
            assign_users = data_access.can_assign_user(proj_levels, user_levels)
            assert not assign_users, "project level should be reported invalid"

            proj_levels = ["L3"]
            user_levels = ["L2", "L6"]
            assign_users = data_access.can_assign_user(proj_levels, user_levels)
            assert not assign_users, "user levels should be reported invalid"

            proj_levels = ["L1"]
            user_levels = ["L2", "L4"]
            assign_users = data_access.can_assign_user(proj_levels, user_levels)
            assert not assign_users, "user with level L2, L4 cannot be assigned to project with level L1"

            proj_levels = ["L2"]
            user_levels = ["L1"]
            assign_users = data_access.can_assign_user(proj_levels, user_levels)
            assert assign_users, "user with level L1 can work on project with level L2; user should be assigned"


    @with_context
    def test_get_valid_project_levels_for_task(self):
        from pybossa import data_access

        task = TaskFactory.create(info={})
        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            self.patch_data_access_levels['valid_project_levels_for_task_level'] = {'A': ['B']}
            assert data_access.get_valid_project_levels_for_task(task) == set()
            task.info['data_access'] = ['A']
            assert data_access.get_valid_project_levels_for_task(task) == set(['B'])


    @with_context
    def test_get_valid_task_levels_for_project(self):

        from pybossa import data_access

        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            self.patch_data_access_levels['valid_task_levels_for_project_level'] = {'A': ['B'], 'B': ['C']}
            project = ProjectFactory.create(info={})
            assert data_access.get_valid_task_levels_for_project(project) == set()
            project.info['data_access'] = ['A', 'B']
            assert data_access.get_valid_task_levels_for_project(project) == set(['B', 'C'])


    @with_context
    def test_ensure_task_assignment_to_project(self):
        from pybossa import data_access

        project = ProjectFactory.create(info={})
        task = TaskFactory.create(info={})
        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            self.patch_data_access_levels['valid_project_levels_for_task_level'] = {'A': ['A']}
            self.patch_data_access_levels['valid_task_levels_for_project_level'] = {'A': ['A']}
            with assert_raises(Exception):
                data_access.ensure_task_assignment_to_project(task, project)
            project.info['data_access'] = ['A']
            with assert_raises(Exception):
                data_access.ensure_task_assignment_to_project(task, project)
            project.info['data_access'] = []
            task.info['data_access'] = ['A']
            with assert_raises(Exception):
                data_access.ensure_task_assignment_to_project(task, project)
            project.info['data_access'] = ['A', 'B']
            task.info['data_access'] = ['A']
            with assert_raises(Exception):
                data_access.ensure_task_assignment_to_project(task, project)
            project.info['ext_config'] = {'data_access': {'tracking_id': '123'}}
            data_access.ensure_task_assignment_to_project(task, project)


    @with_context
    def test_task_save_sufficient_permissions(self):

        from pybossa import data_access

        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            self.patch_data_access_levels['valid_project_levels_for_task_level'] = {'A': ['B']}
            self.patch_data_access_levels['valid_task_levels_for_project_level'] = {'A': ['B']}
            project = ProjectFactory.create(info={
                'data_access': ['A'],
                'ext_config': {'data_access': {'tracking_id': '123'}}
            })
            TaskFactory.create(project_id=project.id, info={'data_access': ['A']})


    @with_context
    def test_task_save_insufficient_permissions(self):

        from pybossa import data_access

        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            self.patch_data_access_levels['valid_project_levels_for_task_level'] = {'A': ['B']}
            self.patch_data_access_levels['valid_task_levels_for_project_level'] = {'B': ['C']}
            project = ProjectFactory.create(info={'data_access': ['B']})
            with assert_raises(Exception):
                TaskFactory.create(project_id=project.id, info={'data_access': ['A']})
