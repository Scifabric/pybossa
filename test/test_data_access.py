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
from werkzeug.exceptions import BadRequest
from collections import namedtuple
from factories import ProjectFactory, TaskFactory, UserFactory
from nose.tools import nottest, assert_raises
from pybossa.core import user_repo, task_repo
from pybossa.model.task import Task
from pybossa import data_access

class TestAccessLevels(Test):

    @staticmethod
    def patched_levels(**kwargs):
        patch_data_access_levels = dict(
            valid_access_levels=[("L1", "L1"), ("L2", "L2"),("L3", "L3"), ("L4", "L4")],
            valid_user_levels_for_project_level=dict(
                L1=[], L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"]),
            valid_project_levels_for_user_level=dict(
                L1=["L2", "L3", "L4"], L2=["L3", "L4"], L3=["L4"], L4=[]),
            valid_user_access_levels=[("L1", "L1"), ("L2", "L2"),("L3", "L3"), ("L4", "L4")]
        )
        patch_data_access_levels.update(kwargs)
        return patch_data_access_levels

    def test_can_assign_user(self):
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
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
    def test_user_type_based_access_levels(self):
        data = [dict(user_type='Researcher', access_levels=["L1"]),
            dict(user_type='Curator', access_levels=["L3", "L4"]),
            dict(user_type='Curator', access_levels=["L1"])]

        patched_levels = self.patched_levels(
            valid_access_levels_for_user_types=dict(Researcher=["L1"], Curator=["L3", "L4"])
        )

        with patch.dict(data_access.data_access_levels, patched_levels):
            res = data_access.valid_user_type_based_data_access(data[0]['user_type'], data[0]['access_levels'])[0]
            assert res
            res = data_access.valid_user_type_based_data_access(data[1]['user_type'], data[1]['access_levels'])[0]
            assert res
            res = data_access.valid_user_type_based_data_access(data[2]['user_type'], data[2]['access_levels'])[0]
            assert not res

    def test_ensure_data_access_assignment_from_form(self):
        class TestForm:
            data_access = namedtuple('data_access', ['data'])

        form = TestForm()
        form.data_access.data = ['L5']
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
            assert_raises(BadRequest, data_access.ensure_data_access_assignment_from_form, dict(), form)

        form.data_access.data = ['L3']
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
            data = dict()
            data_access.ensure_data_access_assignment_from_form(data, form)
            assert data['data_access'] == ['L3']

    def test_ensure_annotation_config_from_form(self):
        class TestForm:
            amp_store = namedtuple('amp_store', ['data'])
            amp_pvf = namedtuple('amp_pvf', ['data'])

        form = TestForm()
        form.amp_store.data = True
        form.amp_pvf.data = 'GIG 999'
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
            data = dict()
            data_access.ensure_annotation_config_from_form(data, form)
            assert data['annotation_config']['amp_store'] == True
            assert data['annotation_config']['amp_pvf'] == 'GIG 999'

    def test_ensure_user_data_access_assignment_from_form(self):
        class TestForm:
            data_access = namedtuple('data_access', ['data'])

        form = TestForm()
        form.data_access.data = ['L5']
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
            assert_raises(BadRequest, data_access.ensure_user_data_access_assignment_from_form, dict(), form)

        form.data_access.data = ['L3']
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
            data = dict()
            data_access.ensure_user_data_access_assignment_from_form(data, form)
            assert data['data_access'] == ['L3']

    def test_copy_user_data_access_levels(self):
        with patch.dict(data_access.data_access_levels, self.patched_levels()):
            target = dict()
            access_level = ['L3']
            data_access.copy_user_data_access_levels(target, access_level)
            assert target['data_access'] == access_level
