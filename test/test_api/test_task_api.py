# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
import json
from default import db, with_context
from nose.tools import assert_equal
from test_api import TestAPI
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
    def test_task_query_without_params(self):
        """ Test API Task query"""
        project = ProjectFactory.create()
        t1 = TaskFactory.create(created='2015-01-01T14:37:30.642119', info={'question': 'answer'})
        tasks = TaskFactory.create_batch(8, project=project, info={'question': 'answer'})
        t2 = TaskFactory.create(created='2019-01-01T14:37:30.642119', info={'question': 'answer'})
        tasks.insert(0, t1)
        tasks.append(t2)

        res = self.app.get('/api/task')
        tasks = json.loads(res.data)
        assert len(tasks) == 10, tasks
        task = tasks[0]
        assert task['info']['question'] == 'answer', task

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Desc filter
        url = "/api/task?desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        assert data[0]['created'] == tasks[len(tasks)-1]['created'], err_msg


    @with_context
    def test_task_query_without_params_with_context(self):
        """ Test API Task query with context"""
        user = UserFactory.create()
        project_oc = ProjectFactory.create(owner=user)
        project_two = ProjectFactory.create()
        TaskFactory.create_batch(10, project=project_oc, info={'question': 'answer'})
        TaskFactory.create_batch(10, project=project_two, info={'question': 'answer'})
        res = self.app.get('/api/task?api_key=' + user.api_key)
        tasks = json.loads(res.data)
        assert len(tasks) == 10, tasks
        for task in tasks:
            assert task['project_id'] == project_oc.id, task
            assert task['info']['question'] == 'answer', task

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        res = self.app.get('/api/task?api_key=' + user.api_key + "&all=1")
        tasks = json.loads(res.data)
        assert len(tasks) == 20, tasks


    @with_context
    def test_task_query_with_params(self):
        """Test API query for task with params works"""
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(10, project=project)
        # Test for real field
        res = self.app.get("/api/task?project_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['project_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/task?project_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/task?project_id=1&state=ongoing')
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['state'] == u'ongoing', data

        # Limits
        res = self.app.get("/api/task?project_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data

        # Keyset pagination
        url = "/api/task?project_id=1&limit=5&last_id=%s" % tasks[4].id
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data
        assert data[0]['id'] == tasks[5].id, data


    @with_context
    def test_task_query_with_params_with_context(self):
        """Test API query for task with params works with context"""
        user = UserFactory.create()
        user_two = UserFactory.create()
        project_oc = ProjectFactory.create(owner=user)
        project_two = ProjectFactory.create()
        tasks = TaskFactory.create_batch(10, project=project_oc)
        TaskFactory.create_batch(10, project=project_two)
        # Test for real field
        res = self.app.get("/api/task?project_id="+ str(project_oc.id) + "&api_key=" + user.api_key)
        data = json.loads(res.data)
        # Should return then results
        assert len(data) == 10, data
        # Correct result
        for t in data:
            assert t['project_id'] == project_oc.id, t

        res = self.app.get("/api/task?api_key=" + user.api_key + "&all=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 20, data


        # Valid field but wrong value
        res = self.app.get("/api/task?project_id=99999999&api_key=" + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/task?project_id=1&state=ongoing&api_key=' + user.api_key)
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        for t in data:
            assert t['project_id'] == project_oc.id, data
            assert t['state'] == u'ongoing', data

        # Limits
        res = self.app.get("/api/task?project_id=1&limit=5&api_key=" + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 5, data
        for item in data:
            assert item['project_id'] == project_oc.id, item

        # Keyset pagination
        url = "/api/task?project_id=1&limit=5&last_id=%s&api_key=%s" % (tasks[4].id, user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, data
        assert data[0]['id'] == tasks[5].id, data
        for item in data:
            assert item['project_id'] == project_oc.id, item

        # Test for real field with user_two
        res = self.app.get("/api/task?project_id="+ str(project_oc.id) + "&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        # Should return then results
        assert len(data) == 0, data
        # Test for real field with user_two
        res = self.app.get("/api/task?all=1&project_id="+ str(project_oc.id) + "&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        # Should return then results
        assert len(data) == 10, data
        # Correct result
        for t in data:
            assert t['project_id'] == project_oc.id, t

        res = self.app.get("/api/task?api_key=" + user_two.api_key + "&all=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 20, data


        # Valid field but wrong value
        res = self.app.get("/api/task?project_id=99999999&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/task?project_id=1&state=ongoing&api_key=' + user_two.api_key)
        data = json.loads(res.data)
        # One result
        assert len(data) == 0, data
        res = self.app.get('/api/task?all=1&project_id=1&state=ongoing&api_key=' + user_two.api_key)
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        for t in data:
            assert t['project_id'] == project_oc.id, data
            assert t['state'] == u'ongoing', data

        # Limits
        res = self.app.get("/api/task?project_id=1&limit=5&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data
        res = self.app.get("/api/task?all=1&project_id=1&limit=5&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        assert len(data) == 5, data
        for item in data:
            assert item['project_id'] == project_oc.id, item

        # Keyset pagination
        url = "/api/task?project_id=1&limit=5&last_id=%s&api_key=%s" % (tasks[4].id, user_two.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data
        url = "/api/task?all=1&project_id=1&limit=5&last_id=%s&api_key=%s" % (tasks[4].id, user_two.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, data
        assert data[0]['id'] == tasks[5].id, data
        for item in data:
            assert item['project_id'] == project_oc.id, item


    @with_context
    def test_task_post(self):
        """Test API Task creation"""
        admin = UserFactory.create()
        user = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = dict(project_id=project.id, info='my task data')
        root_data = dict(project_id=project.id, info='my root task data')

        # anonymous user
        # no api-key
        res = self.app.post('/api/task', data=json.dumps(data))
        error_msg = 'Should not be allowed to create'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed as not owner!
        res = self.app.post('/api/task?api_key=' + non_owner.api_key,
                            data=json.dumps(data))

        error_msg = 'Should not be able to post tasks for projects of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # now a real user
        res = self.app.post('/api/task?api_key=' + user.api_key,
                            data=json.dumps(data))
        assert res.data, res
        datajson = json.loads(res.data)
        out = task_repo.get_task(datajson['id'])
        assert out, out
        assert_equal(out.info, 'my task data'), out
        assert_equal(out.project_id, project.id)

        # now the root user
        res = self.app.post('/api/task?api_key=' + admin.api_key,
                            data=json.dumps(root_data))
        assert res.data, res
        datajson = json.loads(res.data)
        out = task_repo.get_task(datajson['id'])
        assert out, out
        assert_equal(out.info, 'my root task data'), out
        assert_equal(out.project_id, project.id)

        # POST with not JSON data
        url = '/api/task?api_key=%s' % user.api_key
        res = self.app.post(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post(url + '&foo=bar', data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        data['wrongfield'] = 13
        res = self.app.post(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err

    def test_task_post_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = {'created': 'today',
                'state': 'completed',
                'id': 222, 'project_id': project.id}

        res = self.app.post('/api/task?api_key=' + user.api_key,
                            data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    def test_task_put_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)
        url = '/api/task/%s?api_key=%s' % (task.id, user.api_key)
        data = {'created': 'today',
                'state': 'completed',
                'id': 222}

        res = self.app.put(url, data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    @with_context
    def test_task_update(self):
        """Test API task update"""
        admin = UserFactory.create()
        user = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)
        root_task = TaskFactory.create(project=project)
        data = {'n_answers': 1}
        datajson = json.dumps(data)
        root_data = {'n_answers': 4}
        root_datajson = json.dumps(root_data)

        ## anonymous
        res = self.app.put('/api/task/%s' % task.id, data=data)
        assert_equal(res.status, '401 UNAUTHORIZED', res.status)
        ### real user but not allowed as not owner!
        url = '/api/task/%s?api_key=%s' % (task.id, non_owner.api_key)
        res = self.app.put(url, data=datajson)
        assert_equal(res.status, '403 FORBIDDEN', res.status)

        ### real user
        url = '/api/task/%s?api_key=%s' % (task.id, user.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        assert_equal(task.n_answers, data['n_answers'])
        assert_equal(task.state, 'ongoing')
        assert task.id == out['id'], out

        ### root
        res = self.app.put('/api/task/%s?api_key=%s' % (root_task.id, admin.api_key),
                           data=root_datajson)
        assert_equal(res.status, '200 OK', res.data)
        assert_equal(root_task.n_answers, root_data['n_answers'])
        assert_equal(task.state, 'ongoing')

        # PUT with not JSON data
        res = self.app.put(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        data['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

    @with_context
    def test_task_update_state(self):
        """Test API task n_answers updates state properly."""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project, n_answers=1,
                                  state='ongoing')
        data = {'n_answers': 2}
        datajson = json.dumps(data)

        url = '/api/task/%s?api_key=%s' % (task.id, user.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        assert_equal(task.n_answers, data['n_answers'])
        assert_equal(task.state, 'ongoing')
        assert task.id == out['id'], out

        task.state = 'completed'
        task_repo.update(task)

        data = {'n_answers': 1}
        datajson = json.dumps(data)

        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        assert_equal(task.n_answers, data['n_answers'])
        assert_equal(task.state, 'completed')
        assert task.id == out['id'], out

        data = {'n_answers': 5}
        datajson = json.dumps(data)

        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        assert_equal(task.n_answers, data['n_answers'])
        assert_equal(task.state, 'ongoing')
        assert task.id == out['id'], out


    @with_context
    def test_task_delete(self):
        """Test API task delete"""
        admin = UserFactory.create()
        user = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)
        root_task = TaskFactory.create(project=project)

        ## anonymous
        res = self.app.delete('/api/task/%s' % task.id)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/task/%s?api_key=%s' % (task.id, non_owner.api_key)
        res = self.app.delete(url)
        error_msg = 'Should not be able to update tasks of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        #### real user
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar")
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # DELETE returns 204
        url = '/api/task/%s?api_key=%s' % (task.id, user.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)
        assert res.data == '', res.data

        #### root user
        url = '/api/task/%s?api_key=%s' % (root_task.id, admin.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert task not in tasks, tasks
        assert root_task not in tasks, tasks


    @patch('pybossa.repositories.task_repository.uploader')
    def test_task_delete_deletes_zip_files(self, uploader):
        """Test API task delete deletes also zip files with tasks and taskruns"""
        admin = UserFactory.create()
        project = ProjectFactory.create(owner=admin)
        task = TaskFactory.create(project=project)
        url = '/api/task/%s?api_key=%s' % (task.id, admin.api_key)
        res = self.app.delete(url)
        expected = [call('1_project1_task_json.zip', 'user_1'),
                    call('1_project1_task_csv.zip', 'user_1'),
                    call('1_project1_task_run_json.zip', 'user_1'),
                    call('1_project1_task_run_csv.zip', 'user_1')]
        assert uploader.delete_file.call_args_list == expected


    @with_context
    def test_delete_task_cascade(self):
        """Test API delete task deletes associated taskruns"""
        task = TaskFactory.create()
        task_runs = TaskRunFactory.create_batch(3, task=task)
        url = '/api/task/%s?api_key=%s' % (task.id, task.project.owner.api_key)
        res = self.app.delete(url)

        assert_equal(res.status, '204 NO CONTENT', res.data)
        task_runs = task_repo.filter_task_runs_by(task_id=task.id)
        assert len(task_runs) == 0, "There should not be any task run for task"

    @with_context
    def test_delete_task_when_result_associated(self):
        """Test API delete task fails when a result is associated."""
        result = self.create_result()
        project = project_repo.get(result.project_id)

        url = '/api/task/%s?api_key=%s' % (result.task_id,
                                           project.owner.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '403 FORBIDDEN', res.status)

    @with_context
    def test_delete_task_when_result_associated_variation(self):
        """Test API delete task fails when a result is associated after
        increasing the n_answers changing its state from completed to
        ongoing."""
        result = self.create_result()
        project = project_repo.get(result.project_id)
        task = task_repo.get_task(result.task_id)
        task.n_answers = 100
        task_repo.update(task)

        url = '/api/task/%s?api_key=%s' % (result.task_id,
                                           project.owner.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '403 FORBIDDEN', res.status)
