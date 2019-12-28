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
"""
This module tests the RateLimit class and decorator for the API.

It tests all the actions: GET, POST, DEL and PUT, as well as the specific
API endpoints like userprogress.

"""
import json

from default import flask_app, sentinel
from factories import ProjectFactory, UserFactory
from mock import patch


class TestAPI(object):

    app = flask_app.test_client()

    def setUp(self):
        sentinel.connection.master_for('mymaster').flushall()

    limit = flask_app.config.get('LIMIT')


    def check_limit(self, url, action, obj, data=None):
        # Set the limit
        limit = self.limit - 1
        # Start check
        for i in range(limit, -1, -1):
            if action == 'get':
                res = self.app.get(url)
            elif action == 'post':
                if obj == 'project':
                    data = dict(name=i,
                                short_name=i,
                                long_description='something')
                data = json.dumps(data)
                res = self.app.post(url, data=data)
            elif action == 'put':
                _url = '/api/%s/%s' % (obj, i)

                if obj == 'project':
                    data = dict(name=i,
                                short_name=i,
                                long_description='something')
                data = json.dumps(data)

                res = self.app.put(_url + url, data=data)
            elif action == 'delete':
                _url = '/api/%s/%s' % (obj, i)
                res = self.app.delete(_url + url)
            else:
                raise Exception("action not found")
            # Error message
            err_msg = "GET X-RateLimit-Remaining not working"
            # Tests
            print("X-RateLimit-Remaining: %s" % res.headers['X-RateLimit-Remaining'])
            print("Expected value: %s" % i)
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
        self.check_limit(url, action, 'project')

    @patch('pybossa.api.api_base.APIBase._db_query')
    def test_00_project_get(self, mock):
        """Test API.project GET rate limit."""
        mock.return_value = {}
        # GET as Anonymous
        url = '/api/project'
        action = 'get'
        self.check_limit(url, action, 'project')

    @patch('pybossa.api.api_base.APIBase._create_instance_from_request')
    def test_01_project_post(self, mock):
        """Test API.project POST rate limit."""
        mock.return_value = {}
        url = '/api/project'
        self.check_limit(url, 'post', 'project')

    @patch('pybossa.api.api_base.APIBase._delete_instance')
    def test_02_project_delete(self, mock):
        """Test API.project DELETE rate limit."""
        mock.return_value = {}
        url = ''
        self.check_limit(url, 'delete', 'project')

    @patch('pybossa.api.api_base.APIBase._update_instance')
    def test_03_project_put(self, mock):
        """Test API.project PUT rate limit."""
        mock.return_value = {}
        url = ''
        self.check_limit(url, 'put', 'project')

    @patch('pybossa.api._retrieve_new_task')
    def test_04_new_task(self, mock):
        """Test API.new_task(project_id) GET rate limit."""
        mock.return_value = {}
        url = '/api/project/1/newtask'
        self.check_limit(url, 'get', 'project')

    @patch('pybossa.api.project_repo')
    def test_05_user_progress(self, mock):
        """Test API.user_progress GET rate limit."""

        url = '/api/project/1/userprogress'
        self.check_limit(url, 'get', 'project')
