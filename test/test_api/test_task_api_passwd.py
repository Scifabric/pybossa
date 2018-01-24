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
from test_api import TestAPI, get_pwd_cookie
from mock import patch, call
from factories import ProjectFactory, TaskFactory, TaskRunFactory, UserFactory

from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
from pybossa.repositories import ResultRepository

project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestTaskAPI(TestAPI):

    def create_result(self, n_results=1, n_answers=1, owner=None,
                      filter_by=False):
        if owner:
            owner = owner
        else:
            owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        tasks = []
        for i in range(n_results):
            tasks.append(TaskFactory.create(n_answers=n_answers,
                                            project=project))
        for i in range(n_answers):
            for task in tasks:
                TaskRunFactory.create(task=task, project=project)
        if filter_by:
            return result_repo.filter_by(project_id=1)
        else:
            return result_repo.get_by(project_id=1)

    @with_context
    def test_get_task_user_pwd(self):
        """Get a list of tasks."""
        project = ProjectFactory.create()
        tasks = []
        project.set_password('hello')
        project_repo.save(project)
        num_task = 2
        tmp = TaskFactory.create_batch(num_task, project=project)
        for t in tmp:
            tasks.append(t)

        user = UserFactory.create()

        # no password - get a specific task
        url = '/api/task/%d?api_key=%s' % (tmp[0].id, user.api_key)
        res = self.app.get(url)
        assert res.status_code == 403, res.data
        data = json.loads(res.data)

        # no password - no task is returned
        url = '/api/task?project_id=%s&limit=100&all=1&api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, len(data)

        url = '/project/%s/password?api_key=%s' % (project.short_name, user.api_key)
        data = dict(password='hello')
        res = self.app.post(url, data=data)
        c, v, r = get_pwd_cookie(project.short_name, res)

        self.app.set_cookie('/', c, v)

        # get a specific task
        url = '/api/task/%d?api_key=%s' % (tmp[0].id, user.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res.data
        data = json.loads(res.data)
        assert data['info'] == tmp[0].info, data

        # get a list of tasks
        url = '/api/task?project_id=%s&limit=100&all=1&api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == num_task, len(data)

    @with_context
    def test_get_task_admin_pwd(self):
        """Admins do not need password"""
        project = ProjectFactory.create()
        tasks = []
        project.set_password('hello')
        project_repo.save(project)
        num_task = 2
        tmp = TaskFactory.create_batch(num_task, project=project)
        for t in tmp:
            tasks.append(t)

        user = UserFactory.create(admin=True)

        url = '/api/task?project_id=%s&limit=100&all=1&api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == num_task, len(data)

    @with_context
    def test_get_task_owner_pwd(self):
        """Owners do not need password"""
        project = ProjectFactory.create()
        tasks = []
        project.set_password('hello')
        project_repo.save(project)
        num_task = 2
        tmp = TaskFactory.create_batch(num_task, project=project)
        for t in tmp:
            tasks.append(t)

        url = '/api/task?project_id=%s&limit=100&all=1&api_key=%s' % (project.id, project.owner.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == num_task, len(data)
