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

from pybossa.repositories import ResultRepository


class TestResultAPI(TestAPI):

    def setUp(self):
        super(TestResultAPI, self).setUp()
        self.result_repo = ResultRepository(db)


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
            return self.result_repo.filter_by(project_id=1)
        else:
            return self.result_repo.get_by(project_id=1)


    @with_context
    def test_result_query_without_params(self):
        """ Test API Result query"""
        result = self.create_result(n_answers=10)
        res = self.app.get('/api/result')
        results = json.loads(res.data)
        assert len(results) == 1, results
        result = results[0]
        assert result['info'] is None, result
        assert len(result['task_run_ids']) == 10, result
        assert result['task_run_ids'] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], result
        assert result['project_id'] == 1, result
        assert result['task_id'] == 1, result
        assert result['created'] is not None, result

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res


    @with_context
    def test_result_query_with_params(self):
        """Test API query for result with params works"""
        results = self.create_result(n_results=10, filter_by=True)
        # Test for real field
        res = self.app.get("/api/result?project_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['project_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/result?project_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/result?project_id=1&task_id=1')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        # Limits
        res = self.app.get("/api/result?project_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, len(data)

        # Keyset pagination
        url = "/api/result?project_id=1&limit=5&last_id=1"
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data
        assert data[0]['id'] == 2, data[0]


    @with_context
    def test_result_post(self):
        """Test API Result creation"""
        admin = UserFactory.create()
        user = UserFactory.create()
        non_owner = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = dict(info='final result')

        # anonymous user
        # no api-key
        res = self.app.post('/api/result', data=json.dumps(data))
        error_msg = 'Should not be allowed to create'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed as not owner!
        res = self.app.post('/api/result?api_key=' + non_owner.api_key,
                            data=json.dumps(data))

        error_msg = 'Should not be able to post tasks for projects of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # now a real user
        res = self.app.post('/api/result?api_key=' + user.api_key,
                            data=json.dumps(data))
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # now the root user
        res = self.app.post('/api/result?api_key=' + admin.api_key,
                            data=json.dumps(data))
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # POST with not JSON data
        url = '/api/result?api_key=%s' % user.api_key
        res = self.app.post(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post(url + '&foo=bar', data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        data['wrongfield'] = 13
        res = self.app.post(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err

    def test_result_post_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = {'created': 'today',
                'id': 222, 'project_id': project.id}

        res = self.app.post('/api/result?api_key=' + user.api_key,
                            data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    def test_result_put_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        result = self.create_result(owner=user)
        print result
        url = '/api/result/%s?api_key=%s' % (result.id, user.api_key)
        data = {'created': 'today',
                'project_id': 1,
                'id': 222}

        res = self.app.put(url, data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    @with_context
    def test_result_update(self):
        """Test API result update"""
        admin = UserFactory.create()
        user = UserFactory.create()
        non_owner = UserFactory.create()
        data = dict(info=dict(foo='bar'))
        datajson = json.dumps(data)
        result = self.create_result(owner=user)

        ## anonymous
        res = self.app.put('/api/result/%s' % result.id, data=datajson)
        assert_equal(res.status, '401 UNAUTHORIZED', res.status)
        ### real user but not allowed as not owner!
        url = '/api/result/%s?api_key=%s' % (result.id, non_owner.api_key)
        res = self.app.put(url, data=datajson)
        assert_equal(res.status, '403 FORBIDDEN', res.status)

        ### real user
        url = '/api/result/%s?api_key=%s' % (result.id, user.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        assert_equal(result.info['foo'], data['info']['foo'])
        assert result.id == out['id'], out

        ### root
        res = self.app.put('/api/result/%s?api_key=%s' % (result.id, admin.api_key),
                           data=datajson)
        assert_equal(res.status, '403 FORBIDDEN', res.status)

        # PUT with not JSON data
        res = self.app.put(url, data=None)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        data['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err


    @with_context
    def test_result_delete(self):
        """Test API result delete"""
        admin = UserFactory.create()
        user = UserFactory.create()
        non_owner = UserFactory.create()
        result = self.create_result(owner=user)

        ## anonymous
        res = self.app.delete('/api/result/%s' % result.id)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/result/%s?api_key=%s' % (result.id, non_owner.api_key)
        res = self.app.delete(url)
        error_msg = 'Should not be able to update tasks of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        #### real user
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar")
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'result', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # DELETE returns 403
        url = '/api/result/%s?api_key=%s' % (result.id, user.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '403 FORBIDDEN', res.data)

        #### root user
        url = '/api/result/%s?api_key=%s' % (result.id, admin.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '403 FORBIDDEN', res.data)


    #@patch('pybossa.repositories.task_repository.uploader')
    #def test_task_delete_deletes_zip_files(self, uploader):
    #    """Test API task delete deletes also zip files with tasks and taskruns"""
    #    admin = UserFactory.create()
    #    project = ProjectFactory.create(owner=admin)
    #    task = TaskFactory.create(project=project)
    #    url = '/api/task/%s?api_key=%s' % (task.id, admin.api_key)
    #    res = self.app.delete(url)
    #    expected = [call('1_project1_task_json.zip', 'user_1'),
    #                call('1_project1_task_csv.zip', 'user_1'),
    #                call('1_project1_task_run_json.zip', 'user_1'),
    #                call('1_project1_task_run_csv.zip', 'user_1')]
    #    assert uploader.delete_file.call_args_list == expected


    #@with_context
    #def test_delete_task_cascade(self):
    #    """Test API delete task deletes associated taskruns"""
    #    task = TaskFactory.create()
    #    task_runs = TaskRunFactory.create_batch(3, task=task)
    #    url = '/api/task/%s?api_key=%s' % (task.id, task.project.owner.api_key)
    #    res = self.app.delete(url)

    #    assert_equal(res.status, '204 NO CONTENT', res.data)
    #    task_runs = task_repo.filter_task_runs_by(task_id=task.id)
    #    assert len(task_runs) == 0, "There should not be any task run for task"
