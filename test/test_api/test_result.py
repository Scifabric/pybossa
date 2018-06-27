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
from nose.tools import assert_equal
from test_api import TestAPI
from mock import patch, call
from pybossa.core import project_repo, task_repo, result_repo

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

        # Related
        res = self.app.get('/api/result?related=True')
        results = json.loads(res.data)
        assert len(results) == 1, results
        result = results[0]
        assert result['info'] is None, result
        assert len(result['task_run_ids']) == 10, result
        assert result['task_run_ids'] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], result
        assert result['project_id'] == 1, result
        assert result['task_id'] == 1, result
        assert result['created'] is not None, result
        assert result['task']['id'] == result['task_id'], result
        assert len(result['task_runs']) == 10, result
        for tr in result['task_runs']:
            assert tr['task_id'] == result['task_id'], tr
            url = '/api/taskrun?id=%s&related=True' % tr['id']
            taskrun = self.app.get(url)
            taskrun = json.loads(taskrun.data)[0]
            assert taskrun['result']['id'] == result['id'], taskrun['result']
            assert taskrun['task']['id'] == result['task_id'], taskrun['task']
        url = '/api/task?id=%s&related=True' % result['task_id']
        task = self.app.get(url)
        task = json.loads(task.data)[0]
        assert task['result']['id'] == result['id'], task['result']
        for tr in task['task_runs']:
            assert tr['id'] in result['task_run_ids'], task['task']

        result = self.create_result(n_answers=10)
        result = result_repo.get(2)
        result.created = '2119-01-01T14:37:30.642119'
        result_repo.update(result)

        url = '/api/result?orderby=created&desc=true'
        res = self.app.get(url)
        data = json.loads(res.data)
        print(data)
        err_msg = "It should get the last item first."
        assert data[0]['created'] == '2119-01-01T14:37:30.642119', err_msg

        url = '/api/result?orderby=id&desc=false'
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be sorted by id."
        assert data[1]['id'] == result.id, err_msg

        url = '/api/result?orderby=wrongattribute'
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data


        url = '/api/result'
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get not the last item first."
        assert data[0]['created'] != '2119-01-01T14:37:30.642119', err_msg

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    @with_context
    def test_result_query_without_params_with_context(self):
        """ Test API Result query with context."""
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
        owner = UserFactory.create()
        results = self.create_result(n_results=10, filter_by=True, owner=owner)
        # Test for real field
        res = self.app.get("/api/result?api_key=" + owner.api_key)
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        res = self.app.get("/api/project?api_key=" + owner.api_key)
        project = json.loads(res.data)
        assert len(project) == 1, project
        assert project[0]['owner_id'] == owner.id, project

        owner_two = UserFactory.create()
        res = self.app.get("/api/result?api_key=" + owner_two.api_key)
        data = json.loads(res.data)
        # Should return zero results
        assert len(data) == 0, data

        owner_two = UserFactory.create()
        res = self.app.get("/api/result?all=1&api_key=" + owner_two.api_key)
        data = json.loads(res.data)
        # Should return ten results
        assert len(data) == 10, data
        assert data[0]['project_id'] == 1, data

        # Valid field but wrong value
        url = "/api/result?project_id=99999999&api_key=" + owner.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        url = '/api/result?project_id=1&task_id=1&api_key=' + owner.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        # Multiple fields
        url = '/api/result?project_id=1&task_id=1&api_key=' + owner_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # Zero result
        assert len(data) == 0, data
        url = '/api/result?all=1&project_id=1&task_id=1&api_key=' + owner_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['task_id'] == 1, data


        # Limits
        url = "/api/result?project_id=1&limit=5&api_key=" + owner.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, len(data)

        # Limits
        url = "/api/result?project_id=1&limit=5&api_key=" + owner_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Limits
        url = "/api/result?all=1&project_id=1&limit=5&api_key=" + owner_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, len(data)


        # Keyset pagination
        url = "/api/result?project_id=1&limit=5&last_id=1&api_key=" + owner.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        for item in data:
            assert item['project_id'] == 1, item
        assert len(data) == 5, data
        assert data[0]['id'] == 2, data[0]

        # Keyset pagination
        url = "/api/result?project_id=1&limit=5&last_id=1&api_key=" + owner_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Keyset pagination
        url = "/api/result?all=1&project_id=1&limit=5&last_id=1&api_key=" + owner.api_key
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

    @with_context
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

    @with_context
    def test_result_put_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        result = self.create_result(owner=user)
        print(result)
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
        data = dict(info=dict(foo='root'))
        datajson = json.dumps(data)
        res = self.app.put('/api/result/%s?api_key=%s' % (result.id, admin.api_key),
                           data=datajson)
        assert_equal(res.status, '200 OK', res.status)
        assert_equal(result.info['foo'], data['info']['foo'])
        assert result.id == out['id'], out

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

    @with_context
    def test_get_last_version(self):
        """Test API result returns always latest version."""
        result = self.create_result()
        project = project_repo.get(result.project_id)
        task = task_repo.get_task(result.task_id)
        task.n_answers = 2
        TaskRunFactory.create(task=task, project=project)
        result = result_repo.get_by(project_id=project.id)

        assert result.last_version is True, result.last_version

        result_id = result.id

        results = result_repo.filter_by(project_id=project.id, last_version=False)
        assert len(results) == 2, len(results)

        for r in results:
            if r.id == result_id:
                assert r.last_version is True, r.last_version
            else:
                assert r.last_version is False, r.last_version
