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
"""
This module tests the RateLimit class and decorator for the API.

It tests all the actions: GET, POST, DEL and PUT, as well as the specific
API endpoints like userprogress or vmcp.

"""
import json

from base import web, model, Fixtures, db, redis_flushall


class TestAPI:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        redis_flushall()
        Fixtures.create()

    def tearDown(self):
        db.session.remove()
        redis_flushall()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()
        redis_flushall()

    def check_limit(self, url, action, obj, data=None):
        # Set the limit
        limit = 299
        # Start check
        for i in range(limit, -1, -1):
            if action == 'get':
                res = self.app.get(url)
            elif action == 'post':
                if obj == 'app':
                    data = dict(name=i,
                                short_name=i,
                                long_description=u'something')
                data = json.dumps(data)
                res = self.app.post(url, data=data)
            elif action == 'put':
                _url = '/api/%s/%s' % (obj, i)

                if obj == 'app':
                    data = dict(name=i,
                                short_name=i,
                                long_description=u'something')
                data = json.dumps(data)

                res = self.app.put(_url + url, data)
            elif action == 'delete':
                _url = '/api/%s/%s' % (obj, i)
                res = self.app.delete(_url + url)
            else:
                raise Exception("action not found")
            # Error message
            err_msg = "GET X-RateLimit-Remaining not working"
            # Tests
            assert int(res.headers['X-RateLimit-Remaining']) == i, err_msg
            if res.headers['X-RateLimit-Remaining'] == 0:
                error = json.loads(res.data)
                err_msg = "The status_code should be 429"
                assert error['status_code'] == 429, err_msg
                err_msg = "The status should be failed"
                assert error['status'] == 'failed', err_msg
                err_msg = "The exception_cls should be TooManyRequests"
                assert error['exception_cls'] == 'TooManyRequests', err_msg

    def test_00_api_get(self):
        """Test API GET rate limit."""
        # GET as Anonymous
        url = '/api/'
        action = 'get'
        self.check_limit(url, action, 'app')

    def test_00_app_get(self):
        """Test API.app GET rate limit."""
        # GET as Anonymous
        url = '/api/app'
        action = 'get'
        self.check_limit(url, action, 'app')

    def test_01_app_post(self):
        """Test API.app POST rate limit."""
        url = '/api/app?api_key=' + Fixtures.api_key
        self.check_limit(url, 'post', 'app')

    def test_02_app_delete(self):
        """Test API.app DELETE rate limit."""
        for i in range(300):
            app = model.App(name=str(i), short_name=str(i),
                            description=str(i), owner_id=1)
            db.session.add(app)
        db.session.commit()

        url = '?api_key=%s' % (Fixtures.api_key)
        self.check_limit(url, 'delete', 'app')

    def test_03_app_put(self):
        """Test API.app PUT rate limit."""
        for i in range(300):
            app = model.App(name=str(i), short_name=str(i),
                            description=str(i), owner_id=1)
            db.session.add(app)
        db.session.commit()

        url = '?api_key=%s' % (Fixtures.api_key)
        self.check_limit(url, 'put', 'app')

    def test_04_new_task(self):
        """Test API.new_task(app_id) GET rate limit."""
        url = '/api/app/1/newtask'
        self.check_limit(url, 'get', 'app')

    def test_05_vmcp(self):
        """Test API.vmcp GET rate limit."""
        url = '/api/vmcp'
        self.check_limit(url, 'get', 'app')

    def test_05_user_progress(self):
        """Test API.user_progress GET rate limit."""
        url = '/api/app/1/userprogress'
        self.check_limit(url, 'get', 'app')
