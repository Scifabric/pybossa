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
import json
from default import db, with_context
from test_api import TestAPI
from mock import patch, MagicMock

from factories import ProjectFactory, TaskFactory, UserFactory

from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository


class TestTaskSignature(TestAPI):

    @with_context
    @patch('pybossa.api.task.TaskAPI._verify_auth')
    def test_task_no_sign(self, auth):
        """Get a list of tasks using a list of project_ids."""
        auth.return_value = True
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        tasks = TaskFactory.create_batch(2, project=project)

        url = '/api/task/%s?api_key=%s'

        for u in [owner, admin, user]:
            res = self.app.get(url % (tasks[0].id, u.api_key), follow_redirects=True)
            assert 'signature' not in json.loads(res.data)

    @with_context
    @patch('pybossa.api.task.TaskAPI._verify_auth')
    def test_task_with_signature(self, auth):
        """Get a list of tasks using a list of project_ids."""
        auth.return_value = True
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        tasks = TaskFactory.create_batch(2, project=project)

        url = '/api/task/%s?api_key=%s'

        with patch.dict(self.flask_app.config, {'ENABLE_ENCRYPTION': True}):
            for u in [owner, admin]:
                res = self.app.get(url % (tasks[0].id, u.api_key), follow_redirects=True)
                assert 'signature' in json.loads(res.data)

            res = self.app.get(url % (tasks[0].id, user.api_key), follow_redirects=True)
            assert 'signature' not in json.loads(res.data)

    @with_context
    @patch('pybossa.api.task.TaskAPI._verify_auth')
    def test_list_tasks(self, auth):
        """Get a list of tasks using a list of project_ids."""
        auth.return_value = True
        users = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=users[1])
        tasks = TaskFactory.create_batch(2, project=project)

        url = '/api/task?api_key=%s&all=1'

        with patch.dict(self.flask_app.config, {'ENABLE_ENCRYPTION': True}):
            for u in users:
                res = self.app.get(url % u.api_key, follow_redirects=True)
                tasks = json.loads(res.data)
                for task in tasks:
                    assert 'signature' not in task

    @with_context
    @patch('pybossa.api.task.TaskAPI._verify_auth')
    @patch('pybossa.api.get_pwd_manager')
    def test_newtask(self, get_pwd_manager, auth):
        """Get a list of tasks using a list of project_ids."""
        auth.return_value = True
        pwd_manager = MagicMock()
        pwd_manager.password_needed.return_value = False
        get_pwd_manager.return_value = pwd_manager

        users = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=users[1])
        tasks = TaskFactory.create_batch(2, project=project)

        url = '/api/project/%s/newtask?api_key=%s'

        with patch.dict(self.flask_app.config, {'ENABLE_ENCRYPTION': True}):
            for u in users:
                res = self.app.get(url % (project.id, u.api_key), follow_redirects=True)
                task = json.loads(res.data)
                assert 'signature' in task
