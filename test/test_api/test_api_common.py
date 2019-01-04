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
import datetime
from default import with_context
from nose.tools import assert_equal, assert_raises
from test_api import TestAPI
from pybossa.core import project_repo

from factories import ProjectFactory, TaskFactory, TaskRunFactory, UserFactory



class TestApiCommon(TestAPI):

    def setUp(self):
        super(TestApiCommon, self).setUp()

    @with_context
    def test_limits_query(self):
        """Test API GET limits works"""
        owner = UserFactory.create()
        projects = ProjectFactory.create_batch(30, owner=owner)
        project_created = ProjectFactory.create(created='2000-01-01T12:08:47.134025')
        for project in projects:
            task = TaskFactory.create(project=project)
            TaskRunFactory.create(task=task)

        res = self.app.get('/api/project')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)
        assert res.mimetype == 'application/json'

        res = self.app.get('/api/project?limit=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)

        # DEPRECATED
        res = self.app.get('/api/project?limit=10&offset=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == projects[10].name, data[0]

        # Keyset pagination
        url = '/api/project?limit=10&last_id=%s' % projects[9].id
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == projects[10].name, data[0]

        res = self.app.get('/api/task')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/taskrun')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        UserFactory.create_batch(30)

        res = self.app.get('/api/user')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/user?limit=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)

        # DEPRECATED
        res = self.app.get('/api/user?limit=10&offset=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == 'user11', data

        res = self.app.get('/api/user?limit=10&last_id=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == 'user11', data

        # By date created
        res = self.app.get('/api/project?created=2000-01')
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        assert data[0].get('id') == project_created.id
        year = datetime.datetime.now().year
        res = self.app.get('/api/project?created=%s' % year)
        data = json.loads(res.data)
        assert len(data) == 20, len(data)
        res = self.app.get('/api/project?created=%s&limit=100' % year)
        data = json.loads(res.data)
        assert len(data) == 30, len(data)


    @with_context
    def test_get_query_with_api_key_and_all(self):
        """ Test API GET query with an API-KEY requesting all results"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner, info={'total': 150, 'onesignal': 'something', 'onesignal_app_id': 1}, published=True)
        task = TaskFactory.create(project=project, info={'url': 'my url'})
        taskrun = TaskRunFactory.create(task=task, user=admin,
                                        info={'answer': 'annakarenina'})

        year = datetime.datetime.now().year

        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + user.api_key + '&all=1'
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 1, data
                project_res = data[0]
                assert 'total' not in list(project_res['info'].keys()), data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 1, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 1, data
                taskrun = data[0]
                assert taskrun['info']['answer'] == 'annakarenina', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'user':
                assert len(data) == 3, data
                user_res = data[0]
                assert user_res['name'] == 'user1', data
                assert res.mimetype == 'application/json', res

        tmp = project_repo.get(project.id)

        assert tmp.id == project.id, tmp
        assert tmp.info['total'] == 150, tmp

        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + owner.api_key + '&all=1'
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 1, data
                project_res = data[0]
                assert 'total' in list(project_res['info'].keys()), data
                assert project_res['info']['total'] == 150, data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 1, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 1, data
                taskrun = data[0]
                assert taskrun['info']['answer'] == 'annakarenina', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'user':
                assert len(data) == 3, data
                user_res = data[0]
                assert user_res['name'] == 'user1', data
                assert res.mimetype == 'application/json', res

        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + admin.api_key + '&all=1'
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 1, data
                project_res = data[0]
                assert 'total' in list(project_res['info'].keys()), data
                assert project_res['info']['total'] == 150, data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 1, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 1, data
                taskrun = data[0]
                assert taskrun['info']['answer'] == 'annakarenina', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'user':
                assert len(data) == 3, data
                user_res = data[0]
                assert user_res['name'] == 'user1', data
                assert res.mimetype == 'application/json', res



    @with_context
    def test_get_query_with_api_key_context(self):
        """ Test API GET query with an API-KEY requesting only APIKEY results."""
        users = UserFactory.create_batch(4)
        project_oc = ProjectFactory.create(owner=users[0], info={'total': 150})
        projects = ProjectFactory.create_batch(3, owner=users[1])
        task_oc = TaskFactory.create(project=project_oc, info={'url': 'my url'})
        taskrun_oc = TaskRunFactory.create(task=task_oc, user=users[0],
                                        info={'answer': 'annakarenina'})
        for p in projects:
            task_tmp = TaskFactory.create(project=p)
            TaskRunFactory.create(task=task_tmp)

        # For project owner with associated data
        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + users[0].api_key
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 1, data
                project = data[0]
                assert project['owner_id'] == users[0].id, project['owner_id']
                assert project['info']['total'] == 150, data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 1, data
                task = data[0]
                assert task['project_id'] == project_oc.id, task
                assert task['info']['url'] == 'my url', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 1, data
                taskrun = data[0]
                assert taskrun['project_id'] == project_oc.id, taskrun
                assert taskrun['info']['answer'] == 'annakarenina', data
                assert res.mimetype == 'application/json', res

        # For authenticated with non-associated data
        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + users[3].api_key

            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 0, data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 0, data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 0, data
                assert res.mimetype == 'application/json', res


    @with_context
    def test_query_search_wrongfield(self):
        """ Test API query search works"""
        # Test first a non-existant field for all end-points
        for endpoint in self.endpoints:
            res = self.app.get("/api/%s?wrongfield=value" % endpoint)
            err = json.loads(res.data)
            assert res.status_code == 415, err
            assert err['status'] == 'failed', err
            assert err['action'] == 'GET', err
            assert err['exception_cls'] == 'AttributeError', err

    @with_context
    def test_query_search_fulltext(self):
        """ Test API query search fulltext works"""
        # Test first a non-existant field for all end-points
        TaskFactory.create(info={'foo': 'fox'})
        TaskFactory.create(info={'foo': 'foxes something'})
        res = self.app.get('/api/task?all=1&info=foo::fox&fulltextsearch=1')
        data = json.loads(res.data)
        assert len(data) == 2, res.data
        for d in data:
            assert 'fox' in d['info']['foo']
            assert 'rank' in list(d.keys())
            assert 'headline' in list(d.keys())

        # Without the fulltextsearch
        res = self.app.get('/api/task?all=1&info=foo::fox')
        data = json.loads(res.data)
        assert len(data) == 1, res.data
        for d in data:
            assert 'fox' in d['info']['foo']
            assert 'rank' not in list(d.keys())
            assert 'headline'  not in list(d.keys())


    @with_context
    def test_query_sql_injection(self):
        """Test API SQL Injection is not allowed works"""

        q = '1%3D1;SELECT%20*%20FROM%20task%20WHERE%201=1'
        res = self.app.get('/api/task?' + q)
        error = json.loads(res.data)
        assert res.status_code == 415, error
        assert error['action'] == 'GET', error
        assert error['status'] == 'failed', error
        assert error['target'] == 'task', error

        q = 'project_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api/apappp?' + q)
        assert res.status_code == 404, res.data

        q = 'project_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api/' + q)
        assert res.status_code == 404, res.data

        q = 'project_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api' + q)
        assert res.status_code == 404, res.data

    @with_context
    def test_jsonpify(self):
        """Test API jsonpify decorator works."""
        project = ProjectFactory.create()
        res = self.app.get('/api/project/%s?callback=mycallback' % project.id)
        err_msg = "mycallback should be included in the response"
        assert "mycallback" in str(res.data), err_msg
        err_msg = "Status code should be 200"
        assert res.status_code == 200, err_msg


    def test_cors(self):
        """Test CORS decorator works."""
        res = self.app.options('/api/project/1',
                           headers={'Access-Control-Request-Method': 'GET',
                                    'Access-Control-Request-Headers': 'Authorization',
                           })
        err_msg = "CORS should be enabled"
        assert res.headers['Access-Control-Allow-Origin'] == '*', err_msg
        methods = ['PUT', 'HEAD', 'DELETE', 'OPTIONS', 'GET']
        for m in methods:
            err_msg = "Access-Control-Allow-Methods: %s is missing" % m
            assert m in res.headers['Access-Control-Allow-Methods'], err_msg
        assert res.headers['Access-Control-Max-Age'] == '21600', err_msg
        test_headers = ['Content-Type', 'Authorization']
        for header in test_headers:
            err_msg = "Access-Control-Allow-Headers: %s is missing" % header
            headers={'Access-Control-Request-Method': 'GET',
                     'Access-Control-Request-Headers': header}
            res = self.app.options('/api/project/1', headers=headers)
            assert res.headers['Access-Control-Allow-Headers'] == header, err_msg
