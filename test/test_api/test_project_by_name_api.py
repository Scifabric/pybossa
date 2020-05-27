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
from mock import patch, call, MagicMock
from default import db, with_context
from nose.tools import assert_equal, assert_raises
from test_api import TestAPI
from helper.gig_helper import make_subadmin

from factories import (ProjectFactory, TaskFactory, TaskRunFactory, AnonymousTaskRunFactory, UserFactory,
                       CategoryFactory)

from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
from pybossa.repositories import ResultRepository
from pybossa.model.project import Project
project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestProjectAPI(TestAPI):

    def setUp(self):
        super(TestProjectAPI, self).setUp()
        db.session.query(Project).delete()

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
    def test_project_query(self):
        """ Test API project query"""
        project1 = ProjectFactory.create(
            updated='2015-01-01T14:37:30.642119',
            info={
                'total': 150,
                'task_presenter': 'foo',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })
        projects = ProjectFactory.create_batch(8,
            info={
                'total': 150,
                'task_presenter': 'foo',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })

        project2 = ProjectFactory.create(
            updated='2019-01-01T14:37:30.642119',
            info={
                'total': 150,
                'task_presenter': 'foo',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")})
        projects.insert(0, project1)
        projects.append(project2)

        # Test a non-existant ID
        res = self.app.get('/api/projectbyname/notthere')
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'projectbynameapi', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err


    @with_context
    def test_project_query_with_context(self):
        """ Test API project query with context."""
        user = UserFactory.create()
        project_oc = ProjectFactory.create(
            owner=user,
            info={
                'total': 150,
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })
        ProjectFactory.create()

        # Test a non-existant ID
        res = self.app.get('/api/projectbyname/notthere?api_key=' + user.api_key)
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'projectbynameapi', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err

        # Limits
        user_two = UserFactory.create()
        projects = ProjectFactory.create_batch(9, owner=user)


    @with_context
    def test_query_project(self):
        """Test API query for project endpoint works"""
        ProjectFactory.create(short_name='test-app', name='My New Project')
        user = UserFactory.create()
        # Test for real field
        res = self.app.get('/api/projectbyname/test-app?api_key=' + user.api_key, follow_redirects=True)
        data = json.loads(res.data)
        # Should return one result
        # Correct result
        assert data['short_name'] == 'test-app', data

        # Valid field but wrong value
        res = self.app.get('/api/projectbyname/wrongvalue?api_key=' + user.api_key)
        data = json.loads(res.data)
        assert data['status_code'] == 404, data

        # Multiple fields
        res = self.app.get('/api/projectbyname/test-app?name=My New Project&api_key=' + user.api_key)
        data = json.loads(res.data)
        # Correct result
        assert data['short_name'] == 'test-app', data
        assert data['name'] == 'My New Project', data

    @with_context
    def test_query_project_with_context(self):
        """Test API query for project endpoint with context works"""
        user = UserFactory.create()
        user_two = UserFactory.create()
        project_oc = ProjectFactory.create(owner=user, short_name='test-app',
                                           name='My New Project',
                                           info=dict(
                                               foo='fox',
                                               data_classification=dict(input_data="L4 - public", output_data="L4 - public")
                                            ))
        ProjectFactory.create()
        # Test for real field
        url = "/api/projectbyname/test-app?api_key=" + user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        # Correct result
        assert data['short_name'] == 'test-app', data
        assert data['owner_id'] == user.id, data[0]

        # Test for real field
        url = "/api/projectbyname/test-app?api_key=" + user_two.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['short_name'] == 'test-app', data

        # Test for real field
        url = "/api/projectbyname/test-app?api_key=" + user_two.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        # Correct result
        assert data['short_name'] == 'test-app', data
        assert data['owner_id'] == user.id, data[0]

        # Valid field but wrong value
        url = "/api/projectbyname/wrongvalue?api_key=" + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        assert data['status_code'] == 404, data

        # Multiple fields
        url = '/api/projectbyname/test-app?name=My New Project&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # Correct result
        assert data['short_name'] == 'test-app', data
        assert data['name'] == 'My New Project', data
        assert data['owner_id'] == user.id, data

    @with_context
    def test_project_put_invalid_short_name(self):
        """Test API project PUT returns error if try to update short_name(i.e. is
            a name used by the Flask app as a URL endpoint"""
        user = UserFactory.create()
        CategoryFactory.create()
        project = ProjectFactory.create(owner=user)
        name = u'XXXX Project'
        data = {'short_name': 'new'}
        datajson = json.dumps(data)
        res = self.app.put('/api/projectbyname/%s?api_key=%s' % (project.short_name, user.api_key),
                            data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 403, res.status_code
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['target'] == 'project', error
        assert error['exception_cls'] == 'Forbidden', error
        message = "Cannot change short_name via API"
        assert error['exception_msg'] == message, error

    @with_context
    def test_delete_project_cascade(self):
        """Test API delete project deletes associated tasks and taskruns"""
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project)
        task_runs = TaskRunFactory.create_batch(2, project=project)
        url = '/api/projectbyname/%s?api_key=%s' % (project.short_name, project.owner.api_key)
        self.app.delete(url)

        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert len(tasks) == 0, "There should not be any task"

        task_runs = task_repo.filter_task_runs_by(project_id=project.id)
        assert len(task_runs) == 0, "There should not be any task run"

    @with_context
    @patch('pybossa.repositories.project_repository.uploader')
    def test_project_delete_deletes_zip_files(self, uploader):
        """Test API project delete deletes also zip files of tasks and taskruns"""
        admin = UserFactory.create()
        project = ProjectFactory.create(owner=admin)
        task = TaskFactory.create(project=project)
        url = '/api/projectbyname/%s?api_key=%s' % (project.short_name, admin.api_key)
        res = self.app.delete(url)
        expected = [call('1_project1_task_json.zip', 'user_1'),
                    call('1_project1_task_csv.zip', 'user_1'),
                    call('1_project1_task_run_json.zip', 'user_1'),
                    call('1_project1_task_run_csv.zip', 'user_1')]
        assert uploader.delete_file.call_args_list == expected

    @with_context
    def test_project_put_with_reserved_returns_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        url = '/api/projectbyname/%s?api_key=%s' % (project.short_name, user.api_key)
        data = {'created': 'today', 'updated': 'now',
                'contacted': False, 'completed': False,'id': 222}

        res = self.app.put(url, data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    @with_context
    def test_project_update_with_published_attribute_is_forbidden(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = dict(published=True)
        data = json.dumps(data)
        url = '/api/projectbyname/%s?api_key=%s' % (project.short_name, user.api_key)

        res = self.app.put(url, data=data)
        print res.data
        error_msg = json.loads(res.data)['exception_msg']
        assert res.status_code == 403, res.status_code
        assert error_msg == 'You cannot publish a project via the API', res.data

    @with_context
    def test_project_delete_with_results(self):
        """Test API delete project with results can be deleted."""
        result = self.create_result()
        project = project_repo.get(result.project_id)
        url = '/api/projectbyname/%s?api_key=%s' % (project.short_name,
                                                    project.owner.api_key)

        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.status)

    @with_context
    def test_project_delete_with_results_var(self):
        """Test API delete project with results can be deleted by admin."""
        root = UserFactory.create(admin=True)
        result = self.create_result()
        project = project_repo.get(result.project_id)

        url = '/api/projectbyname/%s?api_key=%s' % (project.short_name,
                                                    root.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.status)
