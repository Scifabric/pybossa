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
from pybossa.repositories import UserRepository, ProjectRepository, TaskRepository, WebhookRepository, ResultRepository
from pybossa.view.projects import render_template

project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
user_repo = UserRepository(db)
webhook_repo = WebhookRepository(db)
result_repo = ResultRepository(db)


class TestProjectPublicationView(web.Helper):

    @with_context
    def setUp(self):
        super(TestProjectPublicationView, self).setUp()
        self.owner = UserFactory.create(email_addr='a@a.com')
        self.owner.set_password('1234')
        user_repo.save(self.owner)
        self.project = ProjectFactory.create(owner=self.owner, published=False)
        self.signin(email='a@a.com', password='1234')

    @with_context
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

    @with_context
    def test_template_returned_when_get(self):
        TaskFactory.create(project=self.project)
        url = '/project/%s/publish' % self.project.short_name
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['template'] == '/projects/publish.html'

    @with_context
    def test_it_changes_project_to_published_after_post(self):
        TaskFactory.create(project=self.project)
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)

        project = project_repo.get(self.project.id)
        assert resp.status_code == 200, resp.status_code
        assert project.published == True, project

    @with_context
    @patch('pybossa.view.projects.webhook_repo.delete_entries_from_project')
    @patch('pybossa.view.projects.result_repo.delete_results_from_project')
    @patch('pybossa.view.projects.task_repo')
    def test_it_deletes_project_taskruns_before_publishing(self, mock_task_repo,
                                                           mock_result_repo,
                                                           mock_webhook_repo):
        task = TaskFactory.create(project=self.project, n_answers=1)
        TaskRunFactory.create(task=task)
        result = result_repo.get_by(project_id=task.project_id)
        assert result, "There should be a result"
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)

        taskruns = task_repo.filter_task_runs_by(project_id=self.project.id)

        repo_call = mock_task_repo.delete_taskruns_from_project.call_args_list[0][0][0]
        assert repo_call.id == self.project.id, repo_call

        mock_webhook_repo.assert_called_with(self.project)
        mock_result_repo.assert_called_with(self.project)

        # Try again
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)
        assert 'Project already published' in str(resp.data)


    @with_context
    @patch('pybossa.view.projects.auditlogger')
    def test_it_logs_the_event_in_auditlog(self, fake_logger):
        TaskFactory.create(project=self.project)
        resp = self.app.post('/project/%s/publish' % self.project.short_name,
                             follow_redirects=True)

        assert fake_logger.log_event.called, "Auditlog not called"

    @with_context
    def test_published_get(self):
        project = ProjectFactory.create(info=dict())
        url = '/project/%s/publish?api_key=%s' % (project.short_name,
                                                  project.owner.api_key)
        # Without tasks should return 403
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code

        # With a task should return 403 and no task presenter
        TaskFactory.create(project=project)
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code

        project.info['task_presenter'] = 'task presenter'

        project_repo.update(project)

        res = self.app.get(url)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_published_disable_task_presenter_get(self):
        with patch.dict(self.flask_app.config,
                        {'DISABLE_TASK_PRESENTER': True}):
            project = ProjectFactory.create(info=dict())
            url = '/project/%s/publish?api_key=%s' % (project.short_name,
                                                      project.owner.api_key)
            # Without tasks should return 403
            res = self.app.get(url)
            assert res.status_code == 403, res.status_code

            # With a task should return 200 as task presenter is disabled.
            TaskFactory.create(project=project)
            res = self.app.get(url)
            assert res.status_code == 200, res.status_code
