# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
from mock import patch

from default import db
from factories import ProjectFactory, TaskFactory, UserFactory, TaskRunFactory
from helper import web
from pybossa.repositories import UserRepository, ProjectRepository, TaskRepository
from pybossa.view.projects import render_template

project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
user_repo = UserRepository(db)


class TestProjectPublicationView(web.Helper):

    def setUp(self):
        super(TestProjectPublicationView, self).setUp()
        self.owner = UserFactory.create(email_addr='a@a.com')
        self.owner.set_password('1234')
        user_repo.save(self.owner)
        self.project = ProjectFactory.create(owner=self.owner, published=False)
        self.signin(email='a@a.com', password='1234')

    @patch('pybossa.view.projects.ensure_authorized_to')
    def test_it_checks_permissions_over_project(self, fake_auth):
        post_resp = self.app.get('/project/%s/publish' % self.project.short_name)
        get_resp = self.app.post('/project/%s/publish' % self.project.short_name)

        call_args = fake_auth.call_args_list

        assert fake_auth.call_count == 2, fake_auth.call_count
        assert call_args[0][0][0] == 'publish', call_args[0]
        assert call_args[0][0][1].id == self.project.id, call_args[0]
        assert call_args[1][0][0] == 'publish', call_args[1]
        assert call_args[1][0][1].id == self.project.id, call_args[1]

    @patch('pybossa.view.projects.render_template', wraps=render_template)
    def test_it_renders_template_when_get(self, fake_render):
        TaskFactory.create(project=self.project)
        resp = self.app.get('/project/%s/publish' % self.project.short_name)

        call_args = fake_render.call_args_list
        assert call_args[0][0][0] == 'projects/publish.html', call_args[0]
        assert call_args[0][1]['project'].id == self.project.id, call_args[0]

    def test_it_changes_project_to_published_after_post(self):
        TaskFactory.create(project=self.project)
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)

        project = project_repo.get(self.project.id)
        assert resp.status_code == 200, resp.status_code
        assert project.published == True, project

    @patch('pybossa.view.projects.task_repo')
    def test_it_deletes_project_taskruns_before_publishing(self, task_repo):
        task = TaskFactory.create(project=self.project)
        TaskRunFactory.create(task=task)
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)

        taskruns = task_repo.filter_task_runs_by(project_id=self.project.id)

        repo_call = task_repo.delete_taskruns_from_project.call_args_list[0][0][0]
        assert repo_call.id == self.project.id, repo_call

    @patch('pybossa.view.projects.auditlogger')
    def test_it_logs_the_event_in_auditlog(self, fake_logger):
        TaskFactory.create(project=self.project)
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)

        assert fake_logger.log_event.called, "Auditlog not called"
