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

from base import web, model, Fixtures, db, redis_flushall
from nose.tools import assert_equal


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

    def check_limit(self, url, action, obj, data=None):
        # Reset keys in Redis
        redis_flushall()
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


    def test_00_app_get(self):
        """Test API.app GET rate limit"""
        # GET as Anonymous
        url = '/api/app'
        action = 'get'
        self.check_limit(url, action, 'app')

    def test_01_app_post(self):
        """Test API.app POST rate limit"""
        url = '/api/app?api_key=' + Fixtures.api_key
        self.check_limit(url, 'post', 'app')

    def test_02_app_delete(self):
        """Test API.app DELETE rate limit"""
        for i in range(300):
            app = model.App(name=str(i), short_name=str(i), description=str(i))
            db.session.add(app)
        db.session.commit()

        url = '?api_key=%s' % (Fixtures.api_key)
        self.check_limit(url, 'delete', 'app')

    def test_02_app_put(self):
        """Test API.app PUT rate limit"""
        for i in range(300):
            app = model.App(name=str(i), short_name=str(i), description=str(i))
            db.session.add(app)
        db.session.commit()

        url = '?api_key=%s' % (Fixtures.api_key)
        self.check_limit(url, 'put', 'app')
