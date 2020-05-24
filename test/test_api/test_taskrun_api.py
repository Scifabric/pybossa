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
import datetime
import io
import os.path
import json
from default import with_context, mock_contributions_guard
from nose.tools import assert_equal
from test_api import TestAPI
from mock import patch
from factories import (ProjectFactory, TaskFactory, TaskRunFactory,
                       AnonymousTaskRunFactory, UserFactory)
from pybossa.repositories import ProjectRepository, TaskRepository
from pybossa.repositories import ResultRepository
from pybossa.model.user import User
from pybossa.core import db, anonymizer
from pybossa.auth.errcodes import *
from pybossa.model.task_run import TaskRun

project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestTaskrunAPI(TestAPI):

    def setUp(self):
        super(TestTaskrunAPI, self).setUp()
        db.session.query(TaskRun).delete()

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
    def test_taskrun_query_list_project_ids(self):
        """Get a list of tasks runs using a list of project_ids."""
        projects = ProjectFactory.create_batch(3)
        task_runs = []
        for project in projects:
            tmp = TaskRunFactory.create_batch(2, project=project)
            for t in tmp:
                task_runs.append(t)

        project_ids = [project.id for project in projects]
        url = '/api/taskrun?project_id=%s&limit=100' % project_ids
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 3 * 2, len(data)
        for task in data:
            assert task['project_id'] in project_ids
        task_run_project_ids = list(set([task['project_id'] for task in data]))
        assert sorted(project_ids) == sorted(task_run_project_ids)

        # more filters
        res = self.app.get(url + '&orderby=created&desc=true')
        data = json.loads(res.data)
        assert data[0]['id'] == task_runs[-1].id

    @with_context
    def test_taskrun_query_without_params(self):
        """Test API TaskRun query"""
        owner = UserFactory.create()
        user = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        project_two = ProjectFactory.create()
        TaskRunFactory.create_batch(10, project=project,
                                    info={'answer': 'annakarenina'})
        TaskRunFactory.create_batch(10, project=project_two,
                                    info={'answer': 'annakarenina'})
        date_new = '3019-01-01T14:37:30.642119'
        date_old = '2014-01-01T14:37:30.642119'
        t21 = TaskRunFactory.create(created=date_new)
        t22 = TaskRunFactory.create(created=date_old)

        project_ids = [project.id, project_two.id]
        # As anon, it sould return everything
        res = self.app.get('/api/taskrun')
        taskruns = json.loads(res.data)
        assert len(taskruns) == 20, taskruns
        for tr in taskruns:
            assert tr['project_id'] in project_ids, tr
            assert tr['info']['answer'] == 'annakarenina', tr

        # Related
        res = self.app.get('/api/taskrun?related=True')
        taskruns = json.loads(res.data)
        assert len(taskruns) == 20, taskruns
        for tr in taskruns:
            assert tr['project_id'] in project_ids, tr
            assert tr['info']['answer'] == 'annakarenina', tr
            assert tr['task']['id'] == tr['task_id'], tr
            assert tr['result'] == None, tr

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # User context should return 0 taskruns as none of them belong to this
        # user.
        res = self.app.get('/api/taskrun?api_key=' + user.api_key)
        taskruns = json.loads(res.data)
        assert len(taskruns) == 0, taskruns

        res = self.app.get('/api/taskrun?related=True&api_key=' + user.api_key)
        taskruns = json.loads(res.data)
        assert len(taskruns) == 0, taskruns


        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # User context with all=1 should return everything in the DB, even
        # those task runs that do not belong to the user
        res = self.app.get('/api/taskrun?all=1&api_key=' + user.api_key)
        taskruns = json.loads(res.data)
        assert len(taskruns) == 20, taskruns
        for tr in taskruns:
            assert tr['project_id'] in project_ids, tr
            assert tr['info']['answer'] == 'annakarenina', tr

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Owner should return all the taskruns that belong to his/her
        # projects
        res = self.app.get('/api/taskrun?api_key=' + owner.api_key)
        taskruns = json.loads(res.data)
        assert len(taskruns) == 10, taskruns
        for tr in taskruns:
            assert tr['project_id'] == project.id, tr
            assert tr['info']['answer'] == 'annakarenina', tr

        # Owner should return all the taskruns that belong to his/her
        # projects and those that do not belong
        res = self.app.get('/api/taskrun?all=1&api_key=' + owner.api_key)
        taskruns = json.loads(res.data)
        assert len(taskruns) == 20, taskruns
        for tr in taskruns:
            assert tr['project_id'] in project_ids, tr
            assert tr['info']['answer'] == 'annakarenina', tr

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        url = "/api/taskrun?desc=true&orderby=created"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        assert data[0]['created'] == date_new, err_msg

        # Desc filter
        url = "/api/taskrun?orderby=wrongattribute"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        taskruns.append(t21.dictize())
        taskruns.append(t22.dictize())

        # Desc filter
        url = "/api/taskrun?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        taskruns_by_id = sorted(taskruns, key=lambda x: x['id'], reverse=False)

        for i in range(20):
            assert taskruns_by_id[i]['id'] == data[i]['id']

        # Desc filter
        url = "/api/taskrun?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        taskruns_by_id = sorted(taskruns, key=lambda x: x['id'], reverse=True)
        for i in range(20):
            print((data[i]['id']))
            assert taskruns_by_id[i]['id'] == data[i]['id'], (taskruns_by_id[i]['id'], data[i]['id'])

    @with_context
    def test_query_taskrun(self):
        """Test API query for taskrun with params works"""
        project = ProjectFactory.create()
        task_runs = TaskRunFactory.create_batch(10, project=project)
        # Test for real field
        res = self.app.get("/api/taskrun?project_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['project_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/taskrun?project_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/taskrun?project_id=1&task_id=1')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        # Limits
        res = self.app.get("/api/taskrun?project_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data

        # Keyset pagination
        url = "/api/taskrun?project_id=1&limit=5&last_id=%s" % task_runs[4].id
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data
        assert data[0]['id'] == task_runs[5].id, data[0]['id']


    @with_context
    def test_query_taskrun_with_context(self):
        """Test API query for taskrun with params works with context."""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        project_two = ProjectFactory.create()
        task_runs = TaskRunFactory.create_batch(10, project=project)
        task_runs_two = TaskRunFactory.create_batch(10, project=project_two)

        # Test for real field as anon
        res = self.app.get("/api/taskrun?project_id=" + str(project_two.id))
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        for tr in data:
            assert tr['project_id'] == project_two.id, tr


        # Test for real field as auth user but not owner
        res = self.app.get("/api/taskrun?api_key=" + owner.api_key + "&project_id=" + str(project_two.id))
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 0, data

        # Test for real field as auth user but not owner with all=1j
        res = self.app.get("/api/taskrun?all=1&api_key=" + owner.api_key + "&project_id=" + str(project_two.id))
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        for tr in data:
            assert tr['project_id'] == project_two.id, tr


        # Test for real field as owner
        res = self.app.get("/api/taskrun?api_key=" + owner.api_key + "&project_id=" + str(project.id))
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        for tr in data:
            assert tr['project_id'] == project.id, tr

        # Test for real field as owner
        res = self.app.get("/api/taskrun?all=1&api_key=" + owner.api_key + "&project_id=" + str(project.id))
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        for tr in data:
            assert tr['project_id'] == project.id, tr

        # Valid field but wrong value
        res = self.app.get("/api/taskrun?project_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        res = self.app.get("/api/taskrun?project_id=99999999&api_key=" + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        res = self.app.get("/api/taskrun?project_id=99999999&all=1&api_key=" + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/taskrun?project_id=1&task_id=1')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        res = self.app.get('/api/taskrun?project_id=1&task_id=1&api_key=' + owner.api_key)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        res = self.app.get('/api/taskrun?project_id=1&task_id=1&all=1&api_key=' + owner.api_key)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        url = '/api/taskrun?project_id=%s&task_id=%s&api_key=%s' % (project_two.id,
                                                                    task_runs_two[0].task_id,
                                                                    owner.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        # One result
        assert len(data) == 0, data

        url = '/api/taskrun?all=1&project_id=%s&task_id=%s&api_key=%s' % (project_two.id,
                                                                    task_runs_two[0].task_id,
                                                                    owner.api_key)

        res = self.app.get(url)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == project_two.id, data
        assert data[0]['task_id'] == task_runs_two[0].task_id, data


        # Limits
        res = self.app.get("/api/taskrun?project_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data

        # Limits
        res = self.app.get("/api/taskrun?project_id=" + str(project.id) + "&limit=5&api_key=" + owner.api_key)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data

        res = self.app.get("/api/taskrun?project_id=" + str(project_two.id) + "&limit=5&api_key=" + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        res = self.app.get("/api/taskrun?all=1&project_id=" + str(project_two.id) + "&limit=5&api_key=" + owner.api_key)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == project_two.id, item
        assert len(data) == 5, data

        # Keyset pagination
        url = "/api/taskrun?project_id=1&limit=5&last_id=%s" % task_runs[4].id
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data
        assert data[0]['id'] == task_runs[5].id, data[0]['id']

        # Keyset pagination
        url = "/api/taskrun?project_id=%s&limit=5&last_id=%s&api_key=%s" % (project.id,
                                                                            task_runs[4].id,
                                                                            owner.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data
        assert data[0]['id'] == task_runs[5].id, data[0]['id']

        # Keyset pagination
        url = "/api/taskrun?project_id=%s&limit=5&last_id=%s&api_key=%s" % (project_two.id,
                                                                            task_runs_two[4].id,
                                                                            owner.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, len(data)

        # Keyset pagination
        url = "/api/taskrun?project_id=%s&limit=5&last_id=%s&api_key=%s&all=1" % (project_two.id,
                                                                            task_runs_two[4].id,
                                                                            owner.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == project_two.id, item
        assert len(data) == 5, data
        assert data[0]['id'] == task_runs_two[5].id, data[0]['id']

    @with_context
    @patch('pybossa.api.task_run.request')
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_taskrun_anonymous_post(self, guard, mock_request):
        """Test API TaskRun creation and auth for anonymous users"""
        guard.return_value = mock_contributions_guard(True)
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        data = dict(
            project_id=project.id,
            task_id=task.id,
            info='my task result')
        mock_request.data = json.dumps(data)

        # With wrong project_id
        mock_request.remote_addr = '127.0.0.0'
        data['project_id'] = 100000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        err_msg = "This post should fail as the project_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, tmp.data
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid project_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['project_id'] = task.project_id
        data['task_id'] = 100000000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid task_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # Now with everything fine
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun
        assert r_taskrun['user_ip'] == anonymizer.ip('127.0.0.0')
        assert r_taskrun['user_ip'] != '127.0.0.0'

        # If the anonymous tries again it should be forbidden
        tmp = self.app.post('/api/taskrun', data=datajson)
        err_msg = ("Anonymous users should be only allowed to post \
                    one task_run per task")
        assert tmp.status_code == 403, err_msg

        res = self.app.get('/api/taskrun?task_id=%s&all=1' % task.id)
        tmp = json.loads(res.data)
        print((len(tmp)))
        for tr in tmp:
            assert tr['user_ip'] == anonymizer.ip('127.0.0.0')
            assert tr['user_ip'] != '127.0.0.0'

    @with_context
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_taskrun_authenticated_post(self, guard):
        """Test API TaskRun creation and auth for authenticated users"""
        guard.return_value = mock_contributions_guard(True)
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        data = dict(
            project_id=project.id,
            task_id=task.id,
            info='my task result')

        # With wrong project_id
        data['project_id'] = 100000000000000000
        datajson = json.dumps(data)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key
        tmp = self.app.post(url, data=datajson)
        err_msg = "This post should fail as the project_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid project_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['project_id'] = task.project_id
        data['task_id'] = 100000000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson)
        err_msg = "This post should fail as the task_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid task_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        assert project.owner.notified_at is None

        project.owner.notified_at = datetime.datetime.now()
        db.session.add(project.owner)
        db.session.commit()

        user = User.query.get(project.owner.id)
        assert user.notified_at is not None

        # Now with everything fine
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my task result')
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun
        # Check that notified_at has been updated to None
        user = User.query.get(project.owner.id)
        assert user.notified_at is None, user.notified_at

        # If the user tries again it should be forbidden
        tmp = self.app.post(url, data=datajson)
        assert tmp.status_code == 403, tmp.data


    @with_context
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_taskrun_authenticated_external_uid_post(self, guard):
        """Test API TaskRun creation and auth for authenticated external uid"""
        user = UserFactory.create()
        guard.return_value = mock_contributions_guard(True)
        project = ProjectFactory.create()
        url = '/api/auth/project/%s/token' % project.short_name
        headers = {'Authorization': project.secret_key}
        token = self.app.get(url, headers=headers)
        headers['Authorization'] = b'Bearer %s' % token.data
        external_uid = 'as2d-4cab-3daf-234a-2344x'

        task = TaskFactory.create(project=project)
        data = dict(
            project_id=project.id,
            task_id=task.id,
            info='my task result',
            external_uid=external_uid)

        # With wrong project_id
        data['project_id'] = 100000000000000000
        datajson = json.dumps(data)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key
        tmp = self.app.post(url, data=datajson, headers=headers)
        err_msg = "This post should fail as the project_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid project_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['project_id'] = task.project_id
        data['task_id'] = 100000000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson, headers=headers)
        err_msg = "This post should fail as the task_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid task_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # Now with everything fine
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my task result',
            external_uid=external_uid)
        datajson = json.dumps(data)
        # But without authentication
        tmp = self.app.post(url, data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 403, r_taskrun

        tmp = self.app.post(url, data=datajson, headers=headers)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun
        assert tmp.status_code == 200, r_taskrun
        msg = "user_id & user_ip should be None"
        assert r_taskrun['user_id'] is None, (msg, r_taskrun['user_id'])
        assert r_taskrun['user_ip'] is None, (msg, r_taskrun['user_ip'])


        # If the user tries again it should be forbidden
        tmp = self.app.post(url, data=datajson, headers=headers)
        assert tmp.status_code == 403, tmp.data


    @with_context
    def test_taskrun_post_requires_newtask_first_anonymous(self):
        """Test API TaskRun post fails if task was not previously requested for
        anonymous user"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        data = dict(
            project_id=project.id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        fail = self.app.post('/api/taskrun', data=datajson)
        err = json.loads(fail.data)

        assert fail.status_code == 403, fail.status_code
        assert err['status'] == 'failed', err
        assert err['status_code'] == 403, err
        assert err['exception_msg'] == 'You must request a task first!', err
        assert err['exception_cls'] == 'Forbidden', err
        assert err['target'] == 'taskrun', err

        # Succeeds after requesting a task
        self.app.get('/api/project/%s/newtask' % project.id)
        success = self.app.post('/api/taskrun', data=datajson)
        assert success.status_code == 200, success.data

    @with_context
    def test_taskrun_post_requires_newtask_first_external_uid(self):
        """Test API TaskRun post fails if task was not previously requested for
        external user"""
        project = ProjectFactory.create()
        url = '/api/auth/project/%s/token' % project.short_name
        headers = {'Authorization': project.secret_key}
        token = self.app.get(url, headers=headers)
        headers['Authorization'] = b'Bearer %s' % token.data
        task = TaskFactory.create(project=project)

        # As anon add a taskrun for the current task

        res = self.app.get('/api/project/%s/newtask' % project.id)

        tmp = json.loads(res.data)

        datajson = json.dumps(dict(project_id=project.id,
                                   task_id=tmp['id'],
                                   info='my task result'))
        res = self.app.post('/api/taskrun', data=datajson)

        tmp = json.loads(res.data)

        assert res.status_code == 200

        external_uid = 'as2d-4cab-3daf-234a-2344x'
        data = dict(
            project_id=project.id,
            task_id=task.id,
            info='my task result',
            external_uid=external_uid)
        datajson = json.dumps(data)
        url = '/api/taskrun?external_uid={}'.format(external_uid)
        fail = self.app.post(url, data=datajson, headers=headers)
        err = json.loads(fail.data)

        assert fail.status_code == 403, (fail.status_code, fail.data)
        assert err['status'] == 'failed', err
        assert err['status_code'] == 403, err
        assert err['exception_msg'] == 'You must request a task first!', err
        assert err['exception_cls'] == 'Forbidden', err
        assert err['target'] == 'taskrun', err

        # Succeeds after requesting a task
        res = self.app.get('/api/project/%s/newtask?external_uid=%s' %
                           (project.id, external_uid))
        assert res.status_code == 401
        assert json.loads(res.data) == INVALID_HEADER_MISSING

        # Succeeds after requesting a task
        url = '/api/project/%s/newtask?external_uid=%s' % (project.id,
                                                           external_uid)
        res = self.app.get(url, headers=headers)
        newtask = json.loads(res.data)
        assert newtask['id'] == task.id
        url = '/api/taskrun?external_uid={}'.format(external_uid)
        success = self.app.post(url, data=datajson, headers=headers)
        assert success.status_code == 200, success.data



    @with_context
    def test_taskrun_post_requires_newtask_first_authenticated(self):
        """Test API TaskRun post fails if task was not previously requested for
        authenticated user"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        data = dict(
            project_id=project.id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key
        fail = self.app.post(url, data=datajson)
        err = json.loads(fail.data)

        assert fail.status_code == 403, fail.status_code
        assert err['status'] == 'failed', err
        assert err['status_code'] == 403, err
        assert err['exception_msg'] == 'You must request a task first!', err
        assert err['exception_cls'] == 'Forbidden', err
        assert err['target'] == 'taskrun', err

        # Succeeds after requesting a task
        self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))
        success = self.app.post(url, data=datajson)
        assert success.status_code == 200, success.data


    @with_context
    def test_taskrun_post_with_bad_data(self):
        """Test API TaskRun error messages."""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        project_id = project.id
        task_run = dict(project_id=project.id, task_id=task.id, info='my task result')
        url = '/api/taskrun?api_key=%s' % project.owner.api_key

        # POST with not JSON data
        res = self.app.post(url, data=task_run)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post(url + '&foo=bar', data=task_run)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        task_run['wrongfield'] = 13
        res = self.app.post(url, data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err

    @with_context
    def test_taskrun_update_with_result(self):
        """Test TaskRun API update with result works"""
        admin = UserFactory.create()
        owner = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create(project=project, n_answers=2)
        anonymous_taskrun = AnonymousTaskRunFactory.create(task=task, info='my task result')
        user_taskrun = TaskRunFactory.create(task=task, user=owner, info='my task result')

        task_run = dict(project_id=project.id, task_id=task.id, info='another result')
        datajson = json.dumps(task_run)

        # anonymous user
        # No one can update anonymous TaskRuns
        url = '/api/taskrun/%s' % anonymous_taskrun.id
        res = self.app.put(url, data=datajson)
        assert anonymous_taskrun, anonymous_taskrun
        assert_equal(anonymous_taskrun.user, None)
        error_msg = 'Should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        # real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, non_owner.api_key)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # real user
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, owner.api_key)
        out = self.app.get(url, follow_redirects=True)
        task = json.loads(out.data)
        datajson = json.loads(datajson)
        datajson['link'] = task['link']
        datajson['links'] = task['links']
        datajson = json.dumps(datajson)
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, owner.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # PUT with not JSON data
        res = self.app.put(url, data=task_run)
        err = json.loads(res.data)
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(task_run))
        err = json.loads(res.data)
        assert_equal(res.status, '415 UNSUPPORTED MEDIA TYPE', error_msg)

        # PUT with fake data
        task_run['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(task_run))
        err = json.loads(res.data)
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # root user
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, admin.api_key)
        res = self.app.put(url, data=datajson)
        assert_equal(res.status, '403 FORBIDDEN', error_msg)


    @with_context
    def test_taskrun_update(self):
        """Test TaskRun API update works"""
        admin = UserFactory.create()
        owner = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create(project=project)
        anonymous_taskrun = AnonymousTaskRunFactory.create(task=task, info='my task result')
        user_taskrun = TaskRunFactory.create(task=task, user=owner, info='my task result')

        task_run = dict(project_id=project.id, task_id=task.id, info='another result')
        datajson = json.dumps(task_run)

        # anonymous user
        # No one can update anonymous TaskRuns
        url = '/api/taskrun/%s' % anonymous_taskrun.id
        res = self.app.put(url, data=datajson)
        assert anonymous_taskrun, anonymous_taskrun
        assert_equal(anonymous_taskrun.user, None)
        error_msg = 'Should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        # real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, non_owner.api_key)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # real user
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, owner.api_key)
        out = self.app.get(url, follow_redirects=True)
        task = json.loads(out.data)
        datajson = json.loads(datajson)
        datajson['link'] = task['link']
        datajson['links'] = task['links']
        datajson = json.dumps(datajson)
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, owner.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert res.status_code == 200
        assert out['info'] == 'another result'
        # assert_equal(res.status, '403 FORBIDDEN', res.data)

        # PUT with not JSON data
        res = self.app.put(url, data=task_run)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        task_run['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err
        task_run.pop('wrongfield')

        # root user
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, admin.api_key)
        res = self.app.put(url, data=datajson)
        assert res.status_code == 200
        #assert_equal(res.status, '403 FORBIDDEN', res.data)


    @with_context
    def test_taskrun_delete(self):
        """Test TaskRun API delete works"""
        admin = UserFactory.create()
        owner = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create(project=project)
        anonymous_taskrun = AnonymousTaskRunFactory.create(task=task, info='my task result')
        user_taskrun = TaskRunFactory.create(task=task, user=owner, info='my task result')

        ## anonymous
        res = self.app.delete('/api/taskrun/%s' % user_taskrun.id)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed to delete anonymous TaskRuns
        url = '/api/taskrun/%s?api_key=%s' % (anonymous_taskrun.id, owner.api_key)
        res = self.app.delete(url)
        error_msg = 'Authenticated user should not be allowed ' \
                    'to delete anonymous TaskRuns'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, non_owner.api_key)
        res = self.app.delete(url)
        error_msg = 'Should not be able to delete TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        #### real user
        # DELETE with not allowed args
        url = '/api/taskrun/%s?api_key=%s' % (user_taskrun.id, owner.api_key)
        res = self.app.delete(url + "&foo=bar")
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # Owner with valid args can delete
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        ### root
        url = '/api/taskrun/%s?api_key=%s' % (anonymous_taskrun.id, admin.api_key)
        res = self.app.delete(url)
        error_msg = 'Admin should be able to delete TaskRuns of others'
        assert_equal(res.status, '204 NO CONTENT', error_msg)


    @with_context
    @patch('pybossa.api.task_run.request')
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_taskrun_updates_task_state(self, guard, mock_request):
        """Test API TaskRun POST updates task state"""
        guard.return_value = mock_contributions_guard(True)
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key

        # Post first taskrun
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my task result')
        datajson = json.dumps(data)
        mock_request.data = datajson

        tmp = self.app.post(url, data=datajson)
        r_taskrun = json.loads(tmp.data)

        assert tmp.status_code == 200, r_taskrun

        err_msg = "Task state should be different from completed"
        assert task.state == 'ongoing', err_msg

        # Post second taskrun
        mock_request.remote_addr = '127.0.0.0'
        url = '/api/taskrun'
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            info='my task result anon')
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson)
        r_taskrun = json.loads(tmp.data)

        assert tmp.status_code == 200, r_taskrun
        assert r_taskrun['user_ip'] != '127.0.0.0', r_taskrun
        assert r_taskrun['user_ip'] == anonymizer.ip('127.0.0.0')
        err_msg = "Task state should be equal to completed"
        assert task.state == 'completed', err_msg

    @with_context
    def test_taskrun_create_with_reserved_fields_returns_error(self):
        """Test API taskrun post with reserved fields raises an error"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            created='today',
            finish_time='now',
            id=222)
        datajson = json.dumps(data)

        resp = self.app.post(url, data=datajson)

        assert resp.status_code == 400, resp.status_code
        error = json.loads(resp.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    @with_context
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_taskrun_is_stored_if_project_is_not_published(self, guard):
        """Test API taskrun post stores the taskrun even if project is not published"""
        guard.return_value = mock_contributions_guard(True, "a while ago")
        project = ProjectFactory.create(published=False)
        task = TaskFactory.create(project=project)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my result')
        datajson = json.dumps(data)

        resp = self.app.post(url, data=datajson)
        task_runs = task_repo.filter_task_runs_by(project_id=data['project_id'])

        assert resp.status_code == 200, resp.status_code
        assert len(task_runs) == 1, task_runs
        assert task_runs[0].info == 'my result', task_runs[0]

    @with_context
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_taskrun_created_with_time_it_was_requested_on_creation(self, guard):
        """Test API taskrun post adds the created timestamp of the moment the task
        was requested by the user"""
        guard.return_value = mock_contributions_guard(True, "a while ago")

        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key
        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my result')
        datajson = json.dumps(data)

        resp = self.app.post(url, data=datajson)
        taskrun = task_repo.filter_task_runs_by(task_id=data['task_id'])[0]

        assert taskrun.created == "a while ago", taskrun.created

    @with_context
    def test_taskrun_cannot_be_deleted_associated_result(self):
        """Test API taskrun cannot be deleted when a result is associated."""
        root = UserFactory.create(admin=True)
        results = self.create_result(n_results=10, filter_by=True)
        project = project_repo.get(results[0].project_id)

        # Owner
        for result in results:
            for tr in result.task_run_ids:
                url = '/api/taskrun/%s?api_key=%s' % (tr, project.owner.api_key)
                res = self.app.delete(url)
                assert_equal(res.status, '403 FORBIDDEN', res.status)

        # Admin
        for result in results:
            for tr in result.task_run_ids:
                url = '/api/taskrun/%s?api_key=%s' % (tr, root.api_key)
                res = self.app.delete(url)
                assert_equal(res.status, '403 FORBIDDEN', res.status)

    @with_context
    def test_taskrun_cannot_be_deleted_associated_result_variation(self):
        """Test API taskrun cannot be deleted when a result is associated
        variation."""
        root = UserFactory.create(admin=True)
        results = self.create_result(filter_by=True)
        project = project_repo.get(results[0].project_id)
        task = task_repo.get_task(results[0].task_id)

        task.n_answers = 30

        task_repo.update(task)

        volunteer = UserFactory.create()
        tr_delete = TaskRunFactory.create(task=task, user=volunteer)

        results = result_repo.filter_by(project_id=project.id, task_id=task.id)

        assert len(results) == 1, len(results)
        # Owner
        for result in results:
            for tr in result.task_run_ids:
                url = '/api/taskrun/%s?api_key=%s' % (tr, project.owner.api_key)
                res = self.app.delete(url)
                assert_equal(res.status, '403 FORBIDDEN', res.status)

            url = '/api/taskrun/%s?api_key=%s' % (tr_delete.id,
                                                  volunteer.api_key)
            res = self.app.delete(url)
            assert_equal(res.status, '204 NO CONTENT', res.status)

    @with_context
    def test_taskrun_cannot_be_deleted_associated_result_variation_2(self):
        """Test API taskrun cannot be deleted when a result is associated
        variation."""
        root = UserFactory.create(admin=True)
        results = self.create_result(filter_by=True)
        project = project_repo.get(results[0].project_id)
        task = task_repo.get_task(results[0].task_id)

        task.n_answers = 30

        task_repo.update(task)

        volunteer = UserFactory.create()
        tr_delete = TaskRunFactory.create(task=task, user=volunteer)

        results = result_repo.filter_by(project_id=project.id, task_id=task.id)

        assert len(results) == 1, len(results)
        # Owner
        for result in results:
            for tr in result.task_run_ids:
                url = '/api/taskrun/%s?api_key=%s' % (tr, root.api_key)
                res = self.app.delete(url)
                assert_equal(res.status, '403 FORBIDDEN', res.status)

            url = '/api/taskrun/%s?api_key=%s' % (tr_delete.id,
                                                  volunteer.api_key)
            res = self.app.delete(url)
            assert_equal(res.status, '204 NO CONTENT', res.status)

    @with_context
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_post_taskrun_can_create_result_for_published_project(self, guard):
        """Test API taskrun post creates a result if task is completed and
        project is published."""
        guard.return_value = mock_contributions_guard(True, "a while ago")
        project = ProjectFactory.create(published=True)
        task = TaskFactory.create(project=project, n_answers=1)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key

        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my task result')
        datajson = json.dumps(data)

        res = self.app.post(url, data=datajson)
        print(res.data, 'hola')

        result = result_repo.get_by(project_id=project.id, task_id=task.id)

        assert result is not None, result

    @with_context
    @patch('pybossa.api.task_run.ContributionsGuard')
    def test_post_taskrun_not_creates_result_for_draft_project(self, guard):
        """Test API taskrun post creates a result if project is not published."""
        guard.return_value = mock_contributions_guard(True, "a while ago")
        project = ProjectFactory.create(published=False)
        task = TaskFactory.create(project=project, n_answers=1)
        url = '/api/taskrun?api_key=%s' % project.owner.api_key

        data = dict(
            project_id=task.project_id,
            task_id=task.id,
            user_id=project.owner.id,
            info='my task result')
        datajson = json.dumps(data)

        self.app.post(url, data=datajson)

        result = result_repo.get_by(project_id=project.id, task_id=task.id)

        assert result is not None, result



    @with_context
    def test_taskrun_post_file(self):
        """Test API TASKRUN file upload as authenticated user."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        # As an authenticated user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)
        # Without requesting the task first
        url = '/api/taskrun?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['exception_msg'] == 'You must request a task first!'

        fname = '%s/user_%s/%s' % (self.flask_app.config['UPLOAD_FOLDER'],
                                   user.id,
                                   'test_file.jpg')
        assert os.path.isfile(fname) is False, fname

        # Succeeds after requesting a task
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)

        res = self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id,
                                                                   user.api_key))
        url = '/api/taskrun?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        fname = '%s/%s/%s' % (self.flask_app.config['UPLOAD_FOLDER'],
                              data['info']['container'],
                              data['info']['file_name'])
        assert os.path.isfile(fname) is True, fname
        assert data['info']['container'] == 'user_%s' % user.id, data
        assert data['info']['foo'] == 'bar', data

        # Delete taskrun
        # Owner with valid args can delete
        url = '/api/taskrun/%s?api_key=%s' % (data['id'], user.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        # wrong project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=-1,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)

        url = '/api/taskrun?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data

        # Wrong attribute
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       wrong=img)

        url = '/api/taskrun?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

        # reserved key
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img,
                       id=3)

        url = '/api/taskrun?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert data['exception_msg'] == 'Reserved keys in payload', data

    @with_context
    def test_taskrun_post_file_anon(self):
        """Test API TASKRUN file upload as anon user."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)

        # As an anon user
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)
        # Without requesting the task first
        url = '/api/taskrun'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['exception_msg'] == 'You must request a task first!'

        fname = '%s/anonymous/%s' % (self.flask_app.config['UPLOAD_FOLDER'],
                                     'test_file.jpg')
        assert os.path.isfile(fname) is False, fname

        # Succeeds after requesting a task
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)

        res = self.app.get('/api/project/%s/newtask' % project.id)
        url = '/api/taskrun'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        fname = '%s/%s/%s' % (self.flask_app.config['UPLOAD_FOLDER'],
                              data['info']['container'],
                              data['info']['file_name'])
        assert os.path.isfile(fname) is True, fname
        assert data['info']['container'] == 'anonymous', data

        # wrong project_id
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=-1,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)

        url = '/api/taskrun'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 403, data


        # reserved key
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       file=img)


    @with_context
    def test_taskrun_post_no_filename(self):
        """Test API TASKRUN post file without a name."""
        # Succeeds after requesting a task
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)

        img = (io.BytesIO(b'test'), 'blob')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img)

        res = self.app.get('/api/project/%s/newtask' % project.id)
        url = '/api/taskrun'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        fname = '%s/%s/%s' % (self.flask_app.config['UPLOAD_FOLDER'],
                              data['info']['container'],
                              data['info']['file_name'])
        assert os.path.isfile(fname) is True, fname
        assert data['info']['container'] == 'anonymous', data
        assert 'blob' not in data['media_url']

    @with_context
    def test_taskrun_post_no_info(self):
        """Test API TASKRUN post file without info."""
        # Succeeds after requesting a task
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)

        # With no info data
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       file=img)

        res = self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id,
                                                                   user.api_key))
        url = '/api/taskrun?api_key=%s' % user.api_key
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 200, data
        fname = '%s/%s/%s' % (self.flask_app.config['UPLOAD_FOLDER'],
                              data['info']['container'],
                              data['info']['file_name'])
        assert os.path.isfile(fname) is True, fname
        assert data['info']['container'] == 'user_%s' % user.id, data

    @with_context
    def test_taskrun_post_anon_no_info(self):
        """Test API TASKRUN post file without info."""
        # Succeeds after requesting a task
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)

        # Wrong attribute
        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       wrong=img)

        url = '/api/taskrun'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 415, data

    @with_context
    def test_taskrun_post_anon_reserved(self):
        """Test API TASKRUN post file reserved keys in payload."""
        # Succeeds after requesting a task
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        project2 = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)

        img = (io.BytesIO(b'test'), 'test_file.jpg')

        payload = dict(project_id=project.id,
                       task_id=task.id,
                       info=json.dumps(dict(foo="bar")),
                       file=img,
                       id=3)


        url = '/api/taskrun'
        res = self.app.post(url, data=payload,
                            content_type="multipart/form-data")
        data = json.loads(res.data)
        assert res.status_code == 400, data
        assert data['exception_msg'] == 'Reserved keys in payload', data
