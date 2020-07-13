# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
from mock import patch

from default import db, with_context
from factories import ProjectFactory, TaskFactory, UserFactory, TaskRunFactory
from helper import web
from helper.gig_helper import make_subadmin, make_admin
from pybossa.repositories import UserRepository, ProjectRepository, TaskRepository, WebhookRepository, ResultRepository
from pybossa.view.projects import render_template, task_queue
from pybossa.cache import projects as cached_projects


project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
user_repo = UserRepository(db)
webhook_repo = WebhookRepository(db)
result_repo = ResultRepository(db)


class TestProjectDeleteTasks(web.Helper):

    @with_context
    def setUp(self):
        super(TestProjectDeleteTasks, self).setUp()
        self.owner = UserFactory.create(email_addr='a@a.com')
        self.owner.set_password('1234')
        user_repo.save(self.owner)
        project = ProjectFactory.create(owner=self.owner, published=False)
        self.project_id = project.id
        self.signin(email='a@a.com', password='1234')

    @with_context
    def test_delete_tasks(self):
        """Test that small number of tasks are deleted"""
        project = project_repo.get(self.project_id)
        
        # delete small number of tasks
        TaskFactory.create_batch(10, project=project, n_answers=1)
        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert len(tasks) == 10

        expected = "Tasks and taskruns with no associated results have been deleted"
        resp = self.app.post('/project/%s/tasks/delete' % project.short_name,
                             follow_redirects=True, data={'force_reset': 'on'})
        assert expected in resp.data
        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert len(tasks) == 0

    @with_context
    def test_delete_tasks_bulk(self):
        """Test that request to delete large number of tasks results in job being queued"""
        project = project_repo.get(self.project_id)

        # delete large number of tasks
        TaskFactory.create_batch(101, project=project, n_answers=1)
        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert len(tasks) == 101
        assert len(task_queue) == 0

        expected = "You will receive an email when the tasks deletion is complete."
        resp = self.app.post('/project/%s/tasks/delete' % project.short_name,
                             follow_redirects=True, data={'force_reset': 'on'})
        assert expected in resp.data
        tasks = task_repo.filter_tasks_by(project_id=project.id)
        # deletion task added to queue
        assert len(task_queue) == 1
        # assert delete tasks data?
