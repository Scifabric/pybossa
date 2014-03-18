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
from base import web, model, Fixtures, db
from nose.tools import assert_equal, assert_raises
from test_api import HelperAPI



class TestApiCommon(HelperAPI):

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

        # Register 30 new users to test limit on users too
        for i in range(30):
            self.register(fullname="User%s" %i, username="user%s" %i)

        res = self.app.get('/api/user')
        data = json.loads(res.data)
        assert len(data) == 20, len(data)

        res = self.app.get('/api/user?limit=10')
        data = json.loads(res.data)
        print data
        assert len(data) == 10, len(data)

        res = self.app.get('/api/user?limit=10&offset=10')
        data = json.loads(res.data)
        assert len(data) == 10, len(data)
        assert data[0].get('name') == 'user7', data


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

            if endpoint == 'user':
                # With Fixtures.create() 3 users are created in the DB
                assert len(data) == 3, data
                user = data[0]
                assert user['name'] == 'root', data
                # The output should have a mime-type: application/json
                assert res.mimetype == 'application/json', res


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
