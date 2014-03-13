# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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
from mock import patch
from base import web, model, Fixtures, db, redis_flushall
from nose.tools import assert_equal, assert_raises


class TestAPI:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()
        self.endpoints = ['app', 'task', 'taskrun']

    def tearDown(self):
        db.session.remove()
        redis_flushall()


    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Helper functions
    def register(self, method="POST", fullname="John Doe", username="johndoe",
                 password="p4ssw0rd", password2=None, email=None):
        """Helper function to register and sign in a user"""
        if password2 is None:
            password2 = password
        if email is None:
            email = username + '@example.com'
        if method == "POST":
            return self.app.post('/account/register',
                                 data={'fullname': fullname,
                                       'username': username,
                                       'email_addr': email,
                                       'password': password,
                                       'confirm': password2,
                                       },
                                 follow_redirects=True)
        else:
            return self.app.get('/account/register', follow_redirects=True)

    def signin(self, method="POST", email="johndoe@example.com", password="p4ssw0rd",
               next=None):
        """Helper function to sign in current user"""
        url = '/account/signin'
        if next is not None:
            url = url + '?next=' + next
        if method == "POST":
            return self.app.post(url,
                                 data={'email': email,
                                       'password': password},
                                 follow_redirects=True)
        else:
            return self.app.get(url, follow_redirects=True)

    def signout(self):
        """Helper function to sign out current user"""
        return self.app.get('/account/signout', follow_redirects=True)


    def test_00_limits_query(self):
        """Test API GET limits works"""
        for i in range(30):
            app = model.App(name="name%s" % i,
                            short_name="short_name%s" % i,
                            description="desc",
                            owner_id=1)

            info = dict(a=0)
            task = model.Task(app_id=1, info=info)
            taskrun = model.TaskRun(app_id=1, task_id=1)
            db.session.add(app)
            db.session.add(task)
            db.session.add(taskrun)
        db.session.commit()

        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/app?limit=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)

        res = self.app.get('/api/app?limit=10&offset=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == 'name9'

        res = self.app.get('/api/task')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/taskrun')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

    def test_01_app_query(self):
        """ Test API App query"""
        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 1, data
        app = data[0]
        assert app['info']['total'] == 150, data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Test a non-existant ID
        res = self.app.get('/api/app/3434209')
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err

    def test_get_query_with_api_key(self):
        """ Test API GET query with an API-KEY"""
        for endpoint in self.endpoints:
            url = '/api/' + endpoint + '?api_key=' + Fixtures.api_key
            res = self.app.get(url)
            data = json.loads(res.data)

            if endpoint == 'app':
                assert len(data) == 1, data
                app = data[0]
                assert app['info']['total'] == 150, data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res

            if endpoint == 'task':
                assert len(data) == 10, data
                task = data[0]
                assert task['info']['url'] == 'my url', data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res

            if endpoint == 'taskrun':
                assert len(data) == 10, data
                taskrun = data[0]
                assert taskrun['info']['answer'] == 'annakarenina', data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res

    def test_query_search_wrongfield(self):
        """ Test API query search works"""
        # Test first a non-existant field for all end-points
        endpoints = ['app', 'task', 'taskrun']
        for endpoint in endpoints:
            res = self.app.get("/api/%s?wrongfield=value" % endpoint)
            err = json.loads(res.data)
            assert res.status_code == 415, err
            assert err['status'] == 'failed', err
            assert err['action'] == 'GET', err
            assert err['exception_cls'] == 'AttributeError', err

    def test_query_sql_injection(self):
        """Test API SQL Injection is not allowed works"""

        q = '1%3D1;SELECT%20*%20FROM%20task%20WHERE%201=1'
        res = self.app.get('/api/task?' + q)
        error = json.loads(res.data)
        assert res.status_code == 415, error
        assert error['action'] == 'GET', error
        assert error['status'] == 'failed', error
        assert error['target'] == 'task', error

        q = 'app_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api/apappp?' + q)
        assert res.status_code == 404, res.data

        q = 'app_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api/' + q)
        assert res.status_code == 404, res.data

        q = 'app_id=1%3D1;SELECT%20*%20FROM%20task%20WHERE%201'
        res = self.app.get('/api' + q)
        assert res.status_code == 404, res.data

    def test_query_app(self):
        """Test API query for app endpoint works"""
        # Test for real field
        res = self.app.get("/api/app?short_name=test-app")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data

        # Valid field but wrong value
        res = self.app.get("/api/app?short_name=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/app?short_name=test-app&name=My New App')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['name'] == 'My New App', data

        # Limits
        res = self.app.get("/api/taskrun?app_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

    def test_query_category(self):
        """Test API query for category endpoint works"""
        # Test for real field
        url = "/api/category"
        res = self.app.get(url + "?short_name=thinking")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'thinking', data

        # Valid field but wrong value
        res = self.app.get(url + "?short_name=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get(url + '?short_name=thinking&name=thinking')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'thinking', data
        assert data[0]['name'] == 'thinking', data

        # Limits
        res = self.app.get(url + "?limit=1")
        data = json.loads(res.data)
        for item in data:
            assert item['short_name'] == 'thinking', item
        assert len(data) == 1, data

        # Errors
        res = self.app.get(url + "?something")
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        res.status_code == 415, err_msg
        err['action'] = 'GET', err_msg
        err['status'] = 'failed', err_msg
        err['exception_cls'] = 'AttributeError', err_msg

    def test_query_task(self):
        """Test API query for task endpoint works"""
        # Test for real field
        res = self.app.get("/api/task?app_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['app_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/task?app_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/task?app_id=1&state=0')
        data = json.loads(res.data)
        # One result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['app_id'] == 1, data
        assert data[0]['state'] == '0', data

        # Limits
        res = self.app.get("/api/task?app_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

    def test_query_taskrun(self):
        """Test API query for taskrun endpoint works"""
        # Test for real field
        res = self.app.get("/api/taskrun?app_id=1")
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 10, data
        # Correct result
        assert data[0]['app_id'] == 1, data

        # Valid field but wrong value
        res = self.app.get("/api/taskrun?app_id=99999999")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/taskrun?app_id=1&task_id=1')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['app_id'] == 1, data
        assert data[0]['task_id'] == 1, data

        # Limits
        res = self.app.get("/api/taskrun?app_id=1&limit=5")
        data = json.loads(res.data)
        for item in data:
            assert item['app_id'] == 1, item
        assert len(data) == 5, data

    def test_02_task_query(self):
        """ Test API Task query"""
        res = self.app.get('/api/task')
        tasks = json.loads(res.data)
        assert len(tasks) == 10, tasks
        task = tasks[0]
        assert task['info']['question'] == 'My random question', task

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_03_taskrun_query(self):
        """Test API TaskRun query"""
        res = self.app.get('/api/taskrun')
        taskruns = json.loads(res.data)
        assert len(taskruns) == 10, taskruns
        taskrun = taskruns[0]
        assert taskrun['info']['answer'] == 'annakarenina', taskrun

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

    def test_04_category_post(self):
        """Test API Category creation and auth"""
        name = u'Category'
        category = dict(
            name=name,
            short_name='category',
            description=u'description')
        data = json.dumps(category)
        # no api-key
        url = '/api/category'
        res = self.app.post(url, data=data)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 401, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Unauthorized', err_msg

        # now a real user but not admin
        res = self.app.post(url + '?api_key=' + Fixtures.api_key, data=data)
        err = json.loads(res.data)
        err_msg = 'Should not be allowed to create'
        assert res.status_code == 403, err_msg
        assert err['action'] == 'POST', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg

        # now as an admin
        res = self.app.post(url + '?api_key=' + Fixtures.root_api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = 'Admin should be able to create a Category'
        assert res.status_code == 200, err_msg
        cat = db.session.query(model.Category)\
                .filter_by(short_name=category['short_name']).first()
        id_ = err['id']
        assert err['id'] == cat.id, err_msg
        assert err['name'] == category['name'], err_msg
        assert err['short_name'] == category['short_name'], err_msg
        assert err['description'] == category['description'], err_msg

        # test re-create should fail
        res = self.app.post(url + '?api_key=' + Fixtures.root_api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "IntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', wrong=15)
        res = self.app.post(url + '?api_key=' + Fixtures.root_api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "ValueError exception should be raised"
        assert res.status_code == 415, err
        assert err['action'] == 'POST', err
        assert err['status'] == 'failed', err
        assert err['exception_cls'] == "ValueError", err_msg
        # Now with a JSON object but not valid
        data = json.dumps(data)
        res = self.app.post(url + '?api_key=' + Fixtures.api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "TypeError exception should be raised"
        assert err['action'] == 'POST', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == "TypeError", err_msg
        assert res.status_code == 415, err_msg

        # test update
        data = {'name': 'My New Title'}
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put(url + '/%s' % id_,
                           data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        ### real user but not allowed as not admin!
        url = '/api/category/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Forbidden', error

        # Now as an admin
        res = self.app.put('/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key),
                           data=datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Category).get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error

        # With fake data
        data['algo'] = 13
        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

        # With not JSON data
        datajson = data
        res = self.app.put('/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # With wrong args in the URL
        data = dict(
            name='Category3',
            short_name='category3',
            description=u'description3')

        datajson = json.dumps(data)
        res = self.app.put('/api/category/%s?api_key=%s&search=select1' % (id_, Fixtures.root_api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # test delete
        ## anonymous
        res = self.app.delete(url + '/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error
        ### real user but not admin
        url = '/api/category/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.delete(url, data=datajson)
        error_msg = 'Should not be able to delete apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error

        # As admin
        url = '/api/category/%s?api_key=%s' % (id_, Fixtures.root_api_key)
        res = self.app.delete(url, data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

        # delete a category that does not exist
        url = '/api/category/5000?api_key=%s' % Fixtures.root_api_key
        res = self.app.delete(url, data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'category', error
        assert error['exception_cls'] == 'NotFound', error

        # delete a category that does not exist
        url = '/api/category/?api_key=%s' % Fixtures.root_api_key
        res = self.app.delete(url, data=datajson)
        assert res.status_code == 404, error

    def test_04_app_post(self):
        """Test API App creation and auth"""
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=1,
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/app', data=data)
        assert_equal(res.status, '401 UNAUTHORIZED',
                     'Should not be allowed to create')
        # now a real user
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        out = db.session.query(model.App).filter_by(name=name).one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester')
        id_ = out.id
        db.session.remove()

        # now a real user with headers auth
        headers = [('Authorization', Fixtures.api_key)]
        new_app = dict(
            name=name + '2',
            short_name='xxxx-project2',
            description='description2',
            owner_id=1,
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        new_app = json.dumps(new_app)
        res = self.app.post('/api/app', headers=headers,
                            data=new_app)
        out = db.session.query(model.App).filter_by(name=name + '2').one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project2'), out
        assert_equal(out.owner.name, 'tester')
        id_ = out.id
        db.session.remove()

        # test re-create should fail
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "IntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', link='hateoas', wrong=15)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "ValueError exception should be raised"
        assert res.status_code == 415, err
        assert err['action'] == 'POST', err
        assert err['status'] == 'failed', err
        assert err['exception_cls'] == "ValueError", err_msg
        # Now with a JSON object but not valid
        data = json.dumps(data)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "TypeError exception should be raised"
        assert err['action'] == 'POST', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == "TypeError", err_msg
        assert res.status_code == 415, err_msg

        # test update
        data = {'name': 'My New Title'}
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put('/api/app/%s' % id_,
                           data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        ### real user but not allowed as not owner!
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Forbidden', error

        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)

        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error

        # With wrong id
        res = self.app.put('/api/app/5000?api_key=%s' % Fixtures.api_key,
                           data=datajson)
        assert_equal(res.status, '404 NOT FOUND', res.data)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'NotFound', error

        # With fake data
        data['algo'] = 13
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

        # With empty fields
        data.pop('algo')
        data['name'] = None
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'IntegrityError', err

        data['name'] = ''
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'IntegrityError', err

        data['name'] = 'something'
        data['short_name'] = ''
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'IntegrityError', err


        # With not JSON data
        datajson = data
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # With wrong args in the URL
        data = dict(
            name=name,
            short_name='xxxx-project',
            long_description=u'<div id="longdescription">\
                               Long Description</div>')

        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s?api_key=%s&search=select1' % (id_, Fixtures.api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # test delete
        ## anonymous
        res = self.app.delete('/api/app/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'app', error
        ### real user but not allowed as not owner!
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.delete(url, data=datajson)
        error_msg = 'Should not be able to delete apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'app', error

        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.delete(url, data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

        # delete an app that does not exist
        url = '/api/app/5000?api_key=%s' % Fixtures.api_key
        res = self.app.delete(url, data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'app', error
        assert error['exception_cls'] == 'NotFound', error

        # delete an app that does not exist
        url = '/api/app/?api_key=%s' % Fixtures.api_key
        res = self.app.delete(url, data=datajson)
        assert res.status_code == 404, error

    def test_04_admin_app_post(self):
        """Test API App update/delete for ADMIN users"""
        self.register()
        user = db.session.query(model.User).first()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            owner_id=user.id,
            description='description',
            long_description=u'<div id="longdescription">\
                               Long Description</div>')
        datajson = json.dumps(data)
        # now a real user (we use the second api_key as first user is an admin)
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
                            data=datajson)


        out = db.session.query(model.App).filter_by(name=name).one()
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'tester-2')
        id_ = out.id
        db.session.remove()

        # POST with not JSON data
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'ValueError', err

        # POST with not allowed args
        res = self.app.post('/api/app?api_key=%s&foo=bar' % Fixtures.api_key_2,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'AttributeError', err

        # POST with fake data
        data['wrongfield'] = 13
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key_2,
                            data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        # test update
        data = {'name': 'My New Title'}
        datajson = json.dumps(data)
        ### admin user but not owner!
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.root_api_key)
        res = self.app.put(url, data=datajson)

        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])

        # PUT with not JSON data
        res = self.app.put(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        data['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        # test delete
        url = '/api/app/%s?api_key=%s' % (id_, Fixtures.root_api_key)
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'app', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        ### DELETE success real user  not owner!
        res = self.app.delete(url, data=json.dumps(data))
        assert_equal(res.status, '204 NO CONTENT', res.data)

    def test_05_task_post(self):
        '''Test API Task creation and auth'''
        user = db.session.query(model.User)\
                 .filter_by(name=Fixtures.name)\
                 .one()
        app = db.session.query(model.App)\
                .filter_by(owner_id=user.id)\
                .one()
        data = dict(app_id=app.id, state='0', info='my task data')
        root_data = dict(app_id=app.id, state='0', info='my root task data')
        root_data = json.dumps(root_data)

        ########
        # POST #
        ########

        # anonymous user
        # no api-key
        res = self.app.post('/api/task', data=json.dumps(data))
        error_msg = 'Should not be allowed to create'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed as not owner!
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key_2,
                            data=json.dumps(data))

        error_msg = 'Should not be able to post tasks for apps of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # now a real user
        res = self.app.post('/api/task?api_key=' + Fixtures.api_key,
                            data=json.dumps(data))
        assert res.data, res
        datajson = json.loads(res.data)
        out = db.session.query(model.Task)\
                .filter_by(id=datajson['id'])\
                .one()
        assert out, out
        assert_equal(out.info, 'my task data'), out
        assert_equal(out.app_id, app.id)
        id_ = out.id

        # now the root user
        res = self.app.post('/api/task?api_key=' + Fixtures.root_api_key,
                            data=root_data)
        assert res.data, res
        datajson = json.loads(res.data)
        out = db.session.query(model.Task)\
                .filter_by(id=datajson['id'])\
                .one()
        assert out, out
        assert_equal(out.info, 'my root task data'), out
        assert_equal(out.app_id, app.id)
        root_id_ = out.id

        # POST with not JSON data
        url = '/api/task?api_key=%s' % Fixtures.api_key
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
        data.pop('wrongfield')

        ##########
        # UPDATE #
        ##########
        data = {'state': '1'}
        datajson = json.dumps(data)
        root_data = {'state': '4'}
        root_datajson = json.dumps(root_data)

        ## anonymous
        res = self.app.put('/api/task/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        ### real user but not allowed as not owner!
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update tasks of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        ### real user
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Task).get(id_)
        assert_equal(out2.state, data['state'])
        assert out2.id == out['id'], out

        ### root
        res = self.app.put('/api/task/%s?api_key=%s' % (root_id_, Fixtures.root_api_key),
                           data=root_datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.Task).get(root_id_)
        assert_equal(out2.state, root_data['state'])

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
        data.pop('wrongfield')

        ##########
        # DELETE #
        ##########
        ## anonymous
        res = self.app.delete('/api/task/%s' % id_)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key_2)
        res = self.app.delete(url)
        error_msg = 'Should not be able to update tasks of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        #### real user
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'task', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # DELETE returns 204
        url = '/api/task/%s?api_key=%s' % (id_, Fixtures.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)
        assert res.data == '', res.data

        #### root user
        url = '/api/task/%s?api_key=%s' % (root_id_, Fixtures.root_api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = db.session.query(model.Task)\
                  .filter_by(app_id=app.id)\
                  .all()
        assert tasks, tasks

    def test_06_taskrun_post(self):
        """Test API TaskRun creation and auth for anonymous users"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        task_runs = db.session.query(model.TaskRun).all()
        for tr in task_runs:
            db.session.delete(tr)
        db.session.commit()
        app_id = app.id

        # Create taskrun
        data = dict(
            app_id=app_id,
            task_id=task.id,
            info='my task result')

        datajson = json.dumps(data)

        # anonymous user

        # Get NotFound for an non-existing app
        url = '/api/app/5000/newtask'
        res = self.app.get(url)
        err = json.loads(res.data)
        err_msg = "The app does not exist"
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 404, err_msg
        assert err['exception_cls'] == 'NotFound', err_msg
        assert err['target'] == 'app', err_msg

        # Get an empty task
        url = '/api/app/%s/newtask?offset=1000' % app_id
        res = self.app.get(url)
        assert res.data == '{}', res.data

        # With wrong app_id
        data['app_id'] = 100000000000000000
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        err_msg = "This post should fail as the app_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, tmp.data
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid app_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['app_id'] = task.app_id
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
            app_id=task.app_id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        tmp = self.app.post('/api/taskrun', data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun

        # If the anonymous tries again it should be forbidden
        tmp = self.app.post('/api/taskrun', data=datajson)
        err_msg = ("Anonymous users should be only allowed to post \
                    one task_run per task")
        assert tmp.status_code == 403, err_msg

    def test_06_taskrun_authenticated_post(self):
        """Test API TaskRun creation and auth for authenticated users"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        task_runs = db.session.query(model.TaskRun).all()
        for tr in task_runs:
            db.session.delete(tr)
        db.session.commit()
        app_id = app.id

        # Create taskrun
        data = dict(
            app_id=app_id,
            task_id=task.id,
            info='my task result')

        # With wrong app_id
        data['app_id'] = 100000000000000000
        datajson = json.dumps(data)
        url = '/api/taskrun?api_key=%s' % Fixtures.api_key
        tmp = self.app.post(url, data=datajson)
        err_msg = "This post should fail as the app_id is wrong"
        err = json.loads(tmp.data)
        assert tmp.status_code == 403, err_msg
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 403, err_msg
        assert err['exception_msg'] == 'Invalid app_id', err_msg
        assert err['exception_cls'] == 'Forbidden', err_msg
        assert err['target'] == 'taskrun', err_msg

        # With wrong task_id
        data['app_id'] = task.app_id
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

        # Now with everything fine
        data = dict(
            app_id=task.app_id,
            task_id=task.id,
            info='my task result')
        datajson = json.dumps(data)
        tmp = self.app.post(url, data=datajson)
        r_taskrun = json.loads(tmp.data)
        assert tmp.status_code == 200, r_taskrun

        # If the user tries again it should be forbidden
        tmp = self.app.post(url, data=datajson)
        err_msg = ("Authorized users should be only allowed to post \
                    one task_run per task")
        task_runs = self.app.get('/api/taskrun')
        assert tmp.status_code == 403, tmp.data


    def test_06_taskrun_post_with_bad_data(self):
        """Test API TaskRun error messages."""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        app_id = app.id
        task_run = dict(app_id=app_id, task_id=task.id, info='my task result')
        url = '/api/taskrun?api_key=%s' % Fixtures.api_key

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
        task_run.pop('wrongfield')


    def test_06_taskrun_update(self):
        """Test TaskRun API update works."""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()
        task = db.session.query(model.Task)\
                  .filter_by(app_id=app.id).first()
        task_runs = db.session.query(model.TaskRun).all()
        for tr in task_runs:
            db.session.delete(tr)
        db.session.commit()
        app_id = app.id
        task_run = dict(app_id=app_id, task_id=task.id, info='my task result')

        # Post a task_run
        url = '/api/taskrun'
        tmp = self.app.post(url, data=json.dumps(task_run))

        # Save task_run ID for anonymous user
        _id_anonymous = json.loads(tmp.data)['id']

        url = '/api/taskrun?api_key=%s' % Fixtures.api_key
        tmp = self.app.post(url, data=json.dumps(task_run))

        # Save task_run ID for real user
        _id = json.loads(tmp.data)['id']

        task_run['info'] = 'another result, I had a typo in the previous one'
        datajson = json.dumps(task_run)

        # anonymous user
        # No one can update anonymous TaskRuns
        url = '/api/taskrun/%s' % _id_anonymous
        res = self.app.put(url, data=datajson)
        taskrun = db.session.query(model.TaskRun)\
                    .filter_by(id=_id_anonymous)\
                    .one()
        assert taskrun, taskrun
        assert_equal(taskrun.user, None)
        error_msg = 'Should not be allowed to update'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key_2)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        # real user
        url = '/api/taskrun/%s' % _id
        out = self.app.get(url, follow_redirects=True)
        task = json.loads(out.data)
        datajson = json.loads(datajson)
        datajson['link'] = task['link']
        datajson['links'] = task['links']
        datajson = json.dumps(datajson)
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key)
        res = self.app.put(url, data=datajson)
        out = json.loads(res.data)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.TaskRun).get(_id)
        assert_equal(out2.info, task_run['info'])
        assert_equal(out2.user.name, Fixtures.name)
        assert out2.id == out['id'], out

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
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.root_api_key)
        res = self.app.put(url, data=datajson)
        assert_equal(res.status, '200 OK', res.data)
        out2 = db.session.query(model.TaskRun).get(_id)
        assert_equal(out2.info, task_run['info'])
        assert_equal(out2.user.name, Fixtures.name)

        ##########
        # DELETE #
        ##########

        ## anonymous
        res = self.app.delete('/api/taskrun/%s' % _id)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)

        ### real user but not allowed to delete anonymous TaskRuns
        url = '/api/taskrun/%s?api_key=%s' % (_id_anonymous, Fixtures.api_key)
        res = self.app.delete(url)
        error_msg = 'Authenticated user should not be allowed ' \
                    'to delete anonymous TaskRuns'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        ### real user but not allowed as not owner!
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key_2)
        res = self.app.delete(url)
        error_msg = 'Should not be able to delete TaskRuns of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)

        #### real user
        # DELETE with not allowed args
        url = '/api/taskrun/%s?api_key=%s' % (_id, Fixtures.api_key)
        res = self.app.delete(url + "&foo=bar", data=json.dumps(task_run))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'taskrun', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        # Owner with valid args can delete
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.data)

        tasks = db.session.query(model.Task)\
                  .filter_by(app_id=app_id)\
                  .all()
        assert tasks, tasks

        ### root
        url = '/api/taskrun/%s?api_key=%s' % (_id_anonymous, Fixtures.root_api_key)
        res = self.app.delete(url)
        error_msg = 'Admin should be able to delete TaskRuns of others'
        assert_equal(res.status, '204 NO CONTENT', error_msg)

    def test_taskrun_newtask(self):
        """Test API App.new_task method and authentication"""
        app = db.session.query(model.App)\
                .filter_by(short_name=Fixtures.app_short_name)\
                .one()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/app/%s/newtask' % app.id)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # as a real user
        url = '/api/app/%s/newtask?api_key=%s' % (app.id, Fixtures.api_key)
        res = self.app.get(url)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # test wit no TaskRun items in the db
        db.session.query(model.TaskRun).delete()
        db.session.commit()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/app/%s/newtask' % app.id)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

        # as a real user
        url = '/api/app/%s/newtask?api_key=%s' % (app.id, Fixtures.api_key)
        res = self.app.get(url)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['app_id'], app.id)

    def test_07_user_progress_anonymous(self):
        """Test API userprogress as anonymous works"""
        self.signout()
        app = db.session.query(model.App).get(1)
        tasks = db.session.query(model.Task)\
                  .filter(model.Task.app_id == app.id)\
                  .all()

        # User ID = 2 because, the 1 is the root user
        taskruns = db.session.query(model.TaskRun)\
                     .filter(model.TaskRun.app_id == app.id)\
                     .filter(model.TaskRun.user_id == 2)\
                     .all()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)

        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], data

        res = self.app.get('/api/app/1/newtask')
        data = json.loads(res.data)
        # Add a new TaskRun and check again
        tr = model.TaskRun(app_id=1, task_id=data['id'], user_id=1,
                           info={'answer': u'annakarenina'})
        db.session.add(tr)
        db.session.commit()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg

    def test_08_user_progress_authenticated_user(self):
        """Test API userprogress as an authenticated user works"""
        self.register()
        self.signin()
        user = db.session.query(model.User)\
                 .filter(model.User.name == 'johndoe')\
                 .first()
        app = db.session.query(model.App)\
                .get(1)
        tasks = db.session.query(model.Task)\
                  .filter(model.Task.app_id == app.id)\
                  .all()

        taskruns = db.session.query(model.TaskRun)\
                     .filter(model.TaskRun.app_id == app.id)\
                     .filter(model.TaskRun.user_id == user.id)\
                     .all()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/app/%s/userprogress' % app.short_name
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/app/5000/userprogress'
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        url = '/api/app/userprogress'
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], error_msg

        res = self.app.get('/api/app/1/newtask')
        data = json.loads(res.data)

        # Add a new TaskRun and check again
        tr = model.TaskRun(app_id=1, task_id=data['id'], user_id=user.id,
                           info={'answer': u'annakarenina'})
        db.session.add(tr)
        db.session.commit()

        res = self.app.get('/api/app/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg
        self.signout()

    def test_09_delete_app_cascade(self):
        """Test API delete app deletes associated tasks and taskruns"""
        tasks = self.app.get('/api/task?app_id=1&limit=1000')
        tasks = json.loads(tasks.data)

        task_runs = self.app.get('/api/taskrun?app_id=1&limit=1000')
        task_runs = json.loads(task_runs.data)
        url = '/api/app/%s?api_key=%s' % (1, Fixtures.api_key)
        self.app.delete(url)

        for task in tasks:
            t = db.session.query(model.Task)\
                  .filter_by(app_id=1)\
                  .filter_by(id=task['id'])\
                  .all()
            assert len(t) == 0, "There should not be any task"

            tr = db.session.query(model.TaskRun)\
                   .filter_by(app_id=1)\
                   .filter_by(task_id=task['id'])\
                   .all()
            assert len(tr) == 0, "There should not be any task run"

    def test_10_delete_task_cascade(self):
        """Test API delete app deletes associated tasks and taskruns"""
        tasks = self.app.get('/api/task?app_id=1&limit=1000')
        tasks = json.loads(tasks.data)

        for t in tasks:
            url = '/api/task/%s?api_key=%s' % (t['id'], Fixtures.api_key)
            res = self.app.delete(url)
            assert_equal(res.status, '204 NO CONTENT', res.data)
            tr = []
            tr = db.session.query(model.TaskRun)\
                   .filter_by(app_id=1)\
                   .filter_by(task_id=t['id'])\
                   .all()
            assert len(tr) == 0, "There should not be any task run for task"

    def test_11_allow_anonymous_contributors(self):
        """Test API allow anonymous contributors works"""
        app = db.session.query(model.App).first()

        # All users are allowed to participate by default
        # As Anonymous user
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id is different from the app.id"
        assert task['app_id'] == app.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'My random question', err_msg

        # As registered user
        self.register()
        self.signin()
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id is different from the app.id"
        assert task['app_id'] == app.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'My random question', err_msg
        self.signout()

        # Now only allow authenticated users
        app.allow_anonymous_contributors = False
        db.session.add(app)
        db.session.commit()

        # As Anonymous user
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id should be null"
        assert task['app_id'] is None, err_msg
        err_msg = "There should be an error message"
        err = "This application does not allow anonymous contributors"
        assert task['info'].get('error') == err, err_msg
        err_msg = "There should not be a question"
        assert task['info'].get('question') is None, err_msg

        # As registered user
        res = self.signin()
        url = '/api/app/%s/newtask' % app.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.app_id is different from the app.id"
        assert task['app_id'] == app.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'My random question', err_msg
        self.signout()

    def test_vcmp(self):
        """Test VCMP without key fail works."""
        if web.app.config.get('VMCP_KEY'):
            web.app.config.pop('VMCP_KEY')
        res = self.app.get('api/vmcp', follow_redirects=True)
        err = json.loads(res.data)
        assert res.status_code == 501, err
        assert err['status_code'] == 501, err
        assert err['status'] == "failed", err
        assert err['target'] == "vmcp", err
        assert err['action'] == "GET", err

    @patch.dict(web.app.config, {'VMCP_KEY': 'invalid.key'})
    def test_vmcp_file_not_found(self):
        """Test VMCP with invalid file key works."""
        res = self.app.get('api/vmcp', follow_redirects=True)
        err = json.loads(res.data)
        assert res.status_code == 501, err
        assert err['status_code'] == 501, err
        assert err['status'] == "failed", err
        assert err['target'] == "vmcp", err
        assert err['action'] == "GET", err

    @patch.dict(web.app.config, {'VMCP_KEY': 'invalid.key'})
    def test_vmcp_01(self):
        """Test VMCP errors works"""
        # Even though the key does not exists, let's patch it to test
        # all the errors
        with patch('os.path.exists', return_value=True):
            res = self.app.get('api/vmcp', follow_redirects=True)
            err = json.loads(res.data)
            assert res.status_code == 415, err
            assert err['status_code'] == 415, err
            assert err['status'] == "failed", err
            assert err['target'] == "vmcp", err
            assert err['action'] == "GET", err
            assert err['exception_msg'] == 'cvm_salt parameter is missing'

    @patch.dict(web.app.config, {'VMCP_KEY': 'invalid.key'})
    def test_vmcp_02(self):
        """Test VMCP signing works."""
        signature = dict(signature='XX')
        with patch('os.path.exists', return_value=True):
            with patch('pybossa.vmcp.sign', return_value=signature):
                res = self.app.get('api/vmcp?cvm_salt=testsalt',
                                   follow_redirects=True)
                out = json.loads(res.data)
                assert res.status_code == 200, out
                assert out['signature'] == signature['signature'], out

                # Now with a post
                res = self.app.post('api/vmcp?cvm_salt=testsalt',
                                   follow_redirects=True)
                assert res.status_code == 405, res.status_code

    def test_global_stats(self):
        """Test Global Stats works."""
        res = self.app.get('api/globalstats')
        stats = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        keys = ['n_projects', 'n_pending_tasks', 'n_users', 'n_task_runs']
        for k in keys:
            err_msg = "%s should be in stats JSON object" % k
            assert k in stats.keys(), err_msg

    def test_post_global_stats(self):
        """Test Global Stats Post works."""
        res = self.app.post('api/globalstats')
        assert res.status_code == 405, res.status_code
