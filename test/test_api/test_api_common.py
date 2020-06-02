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
from test_api import TestAPI
from pybossa.core import project_repo

from factories import ProjectFactory, TaskFactory, TaskRunFactory, UserFactory

from mock import patch
from pybossa.repositories import TaskRepository
from default import db


class TestApiCommon(TestAPI):

    def setUp(self):
        super(TestApiCommon, self).setUp()

    data_classification=dict(input_data="L4 - public", output_data="L4 - public")

    @with_context
    @patch('pybossa.api.task.TaskAPI._verify_auth')
    def test_limits_query(self, auth):
        """Test API GET limits works"""
        admin, owner, user = UserFactory.create_batch(3)
        projects = ProjectFactory.create_batch(30, owner=owner)
        project_created = ProjectFactory.create(created='2000-01-01T12:08:47.134025')
        auth.return_value = True
        for project in projects:
            task = TaskFactory.create(project=project)
            TaskRunFactory.create(task=task)

        res = self.app.get('/api/project')
        data = json.loads(res.data)
        assert data['status_code'] == 401, "anonymous user should not have acess to project api"
        res = self.app.get('/api/project?all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 20, len(data)
        assert res.mimetype == 'application/json'

        res = self.app.get('/api/project?limit=10&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)

        # DEPRECATED
        res = self.app.get('/api/project?all=1&limit=10&offset=10&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == projects[10].name, data[0]

        # Keyset pagination
        url = '/api/project?all=1&limit=10&last_id=%s&api_key=%s' % (projects[9].id, user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == projects[10].name, data[0]

        res = self.app.get('/api/task?api_key=' + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/taskrun?api_key=' + owner.api_key)
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        UserFactory.create_batch(30)

        res = self.app.get('/api/user')
        data = json.loads(res.data)
        assert data['status_code'] == 401, "anonymous user should not have acess to user api"
        # now access with admin user
        res = self.app.get('/api/user?api_key=' + admin.api_key)
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/user?limit=10&api_key=' + admin.api_key)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)

        # DEPRECATED
        res = self.app.get('/api/user?limit=10&offset=10&api_key=' + admin.api_key)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == 'user11', data

        res = self.app.get('/api/user?limit=10&last_id=10&api_key=' + admin.api_key)
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == 'user11', data

        # By date created
        res = self.app.get('/api/project?created=2000-01')
        data = json.loads(res.data)
        assert data['status_code'] == 401, "anonymous user should not have acess to project api"

        res = self.app.get('/api/project?all=1&created=2000-01&api_key=%s' % admin.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        assert data[0].get('id') == project_created.id
        year = datetime.datetime.now().year
        res = self.app.get('/api/project?all=1&created=%s&api_key=%s' % (year, owner.api_key))
        data = json.loads(res.data)
        assert len(data) == 20, len(data)
        res = self.app.get('/api/project?all=1&created=%s&limit=100&api_key=%s' % (year, owner.api_key))
        data = json.loads(res.data)
        assert len(data) == 30, len(data)


    @with_context
    def test_get_query_with_api_key_and_all(self):
        """ Test API GET query with an API-KEY requesting all results"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(
            owner=owner,
            info={
                'total': 150,
                'onesignal': 'something',
                'onesignal_app_id': 1,
                'data_classification': self.data_classification
            },
            published=True)
        task = TaskFactory.create(project=project, info={'url': 'my url'})
        taskrun = TaskRunFactory.create(task=task, user=admin,
                                        info={'answer': 'annakarenina'})

        year = datetime.datetime.now().year

        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + user.api_key + '&all=1'
            self.set_proj_passwd_cookie(project, user)
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 1, data
                project_res = data[0]
                assert 'total' not in project_res['info'].keys(), data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 1, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert res.status_code == 200
                assert len(data) == 0, "No taskrun to be returned for regular user"

            if endpoint == 'user':
                assert res.status_code == 200, data
                assert len(data) == 1
                assert data[0]['id'] == user.id

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
                assert 'total' in project_res['info'].keys(), data
                assert project_res['info']['total'] == 150, data
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 1, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert res.status_code == 200
                assert len(data) == 1, data
                taskrun = data[0]
                assert taskrun['info']['answer'] == 'annakarenina', data
                assert res.mimetype == 'application/json', res

            if endpoint == 'user':
                assert res.status_code == 200, data
                assert len(data) == 1
                assert data[0]['id'] == owner.id

        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + admin.api_key + '&all=1'
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'project':
                assert len(data) == 1, data
                project_res = data[0]
                assert 'total' in project_res['info'].keys(), data
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
        project_oc = ProjectFactory.create(owner=users[0], info={'total': 150, 'data_classification': self.data_classification})
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
                assert res.status_code == 200
                assert len(data) == 0, "No taskrun to be returned for regular user"


    @with_context
    def test_query_search_wrongfield(self):
        """ Test API query search works"""
        admin = UserFactory.create()
        # Test first a non-existant field for all end-points
        for endpoint in self.endpoints:
            res = self.app.get("/api/%s?wrongfield=value&api_key=%s" % (endpoint, admin.api_key))
            err = json.loads(res.data)
            assert res.status_code == 415, err
            assert err['status'] == 'failed', err
            assert err['action'] == 'GET', err
            assert err['exception_cls'] == 'AttributeError', err

    @with_context
    @patch('pybossa.api.task.TaskAPI._verify_auth')
    def test_query_search_fulltext(self, auth):
        """ Test API query search fulltext works"""
        # Test first a non-existant field for all end-points
        TaskFactory.create(info={'foo': 'fox'})
        TaskFactory.create(info={'foo': 'foxes something'})
        user = UserFactory.create()
        res = self.app.get('/api/task?all=1&info=foo::fox&fulltextsearch=1&api_key=' + user.api_key)
        auth.return_value = True
        data = json.loads(res.data)
        assert len(data) == 2, res.data
        for d in data:
            assert 'fox' in d['info']['foo']
            assert 'rank' in d.keys()
            assert 'headline' in d.keys()

        # Without the fulltextsearch
        res = self.app.get('/api/task?all=1&info=foo::fox&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, res.data
        for d in data:
            assert 'fox' in d['info']['foo']
            assert 'rank' not in d.keys()
            assert 'headline'  not in d.keys()


    @with_context
    def test_query_sql_injection(self):
        """Test API SQL Injection is not allowed works"""

        user = UserFactory.create()
        q = '1%3D1;SELECT%20*%20FROM%20task%20WHERE%201=1'
        res = self.app.get('/api/task?%s&api_key=%s' % (q, user.api_key))
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
        print res.data
        assert "mycallback" in res.data, err_msg
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


    @with_context
    def test_api_app_access_with_secure_app_access_enabled(self):
        """Test API and APP access with SECURE_APP_ACCESS enabled"""

        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2,
                                  state='ongoing')
        task_repo = TaskRepository(db)

        admin = UserFactory.create()
        with patch.dict(self.flask_app.config,
            {'SECURE_APP_ACCESS': True}):
            url = '/api/completedtask?project_id=1&api_key=api-key1'
            res = self.app.get(url)
            assert res.status_code == 401, res.data
            url = '/api/completedtask?project_id=1'
            headers = {'Authorization': 'api-key1'}
            res = self.app.get(url, headers=headers)
            data = json.loads(res.data)
            # no completedtask yet, should return zero
            assert len(data) == 0, data

            #  task is completed
            task_runs = TaskRunFactory.create_batch(2, task=task)
            task.state = 'completed'
            task_repo.update(task)
            url = '/api/completedtask?project_id=1'
            res = self.app.get(url, headers=headers)
            data = json.loads(res.data)

            # correct result
            assert data[0]['project_id'] == 1, data
            assert data[0]['state'] == u'completed', data

            # test api with incorrect api_key
            url = '/api/completedtask?project_id=1&api_key=BAD-api-key'
            res = self.app.get(url)
            err_msg = 'Status code should be 401'
            assert res.status_code == 401, err_msg

            url = "/project/%s?api_key=api-key1" % project.short_name
            res = self.app.get(url, follow_redirects=True, headers=headers)
            err_msg = 'app access should not be allowed with SECURE_APP_ACCESS enabled'
            assert "Sign in" in res.data, err_msg


    @with_context
    def test_api_app_access_with_secure_app_access_disabled(self):
        """Test API and APP access with SECURE_APP_ACCESS disabled"""

        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2,
                                  state='ongoing')
        task_repo = TaskRepository(db)

        with patch.dict(self.flask_app.config,
            {'SECURE_APP_ACCESS': False}):
            # Test no completedtask yet
            url = '/api/completedtask?project_id=1&api_key=api-key1'
            res = self.app.get(url)
            data = json.loads(res.data)
            assert len(data) == 0, data

            #  test task is completed
            task_runs = TaskRunFactory.create_batch(2, task=task)
            task.state = 'completed'
            task_repo.update(task)
            url = '/api/completedtask?project_id=1&api_key=api-key1'
            res = self.app.get(url)
            data = json.loads(res.data)

            # correct result
            assert data[0]['project_id'] == 1, data
            assert data[0]['state'] == u'completed', data

            # test api with incorrect api_key
            url = '/api/completedtask?project_id=1&api_key=bad-api-key'
            res = self.app.get(url)
            err_msg = 'Status code should be 401'
            assert res.status_code == 401, err_msg

            url = "/project/%s?api_key=api-key1" % project.short_name
            res = self.app.get(url, follow_redirects=True)
            err_msg = 'app access should be allowed with SECURE_APP_ACCESS disabled'
            assert not "Sign in" in res.data, err_msg
            assert "Statistics" in res.data
            assert 'id="percent-completed"' in res.data
            assert "<div>100%</div>" in res.data
