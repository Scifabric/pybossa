# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

from redis import StrictRedis
from mock import patch

from pybossa.api import _mark_task_as_requested_by_user
from pybossa.api.task_run import _check_task_requested_by_user
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun


class TestTasksMarkedForContribution(object):

    def setUp(self):
        self.connection = StrictRedis()
        self.connection.flushall()


    @patch('pybossa.api.get_user_id_or_ip')
    def test_mark_task_as_requested_by_user_creates_key_for_auth(self, user):
        """When an authenticated user requests a task, a key is stored in Redis
        with his id and task id"""
        user.return_value = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:33:task:22'

        _mark_task_as_requested_by_user(task, self.connection)

        assert key in self.connection.keys(), self.connection.keys()


    @patch('pybossa.api.get_user_id_or_ip')
    def test_mark_task_as_requested_by_user_creates_key_for_anon(self, user):
        """When an anonymous user requests a task, a key is stored in Redis
        with his IP and task id"""
        user.return_value = {'user_id': None, 'user_ip': '127.0.0.1'}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'

        _mark_task_as_requested_by_user(task, self.connection)

        assert key in self.connection.keys(), self.connection.keys()


    @patch('pybossa.api.get_user_id_or_ip')
    def test_mark_task_as_requested_by_user_sets_expiration_for_key(self, user):
        """When a user requests a task, a key is stored with TTL of 1 hour"""
        user.return_value = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:33:task:22'

        _mark_task_as_requested_by_user(task, self.connection)

        assert self.connection.ttl(key) == 60 * 60, self.connection.ttl(key)


class TestCheckTasksRequestedByUser(object):

    def setUp(self):
        self.connection = StrictRedis()
        self.connection.flushall()


    @patch('pybossa.api.task_run.get_user_id_or_ip')
    def test_check_task_requested_by_user_authenticated_key_exists(self, user):
        user.return_value = {'user_id': 33, 'user_ip': None}
        taskrun = TaskRun(task_id=22)
        key = 'pybossa:task_requested:user:33:task:22'
        self.connection.setex(key, 10, True)

        check = _check_task_requested_by_user(taskrun, self.connection)

        assert check is True, check


    @patch('pybossa.api.task_run.get_user_id_or_ip')
    def test_check_task_requested_by_user_anonymous_key_exists(self, user):
        user.return_value = {'user_id': None, 'user_ip': '127.0.0.1'}
        taskrun = TaskRun(task_id=22)
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'
        self.connection.setex(key, 10, True)

        check = _check_task_requested_by_user(taskrun, self.connection)

        assert check is True, check


    @patch('pybossa.api.task_run.get_user_id_or_ip')
    def test_check_task_requested_by_user_wrong_key(self, user):
        user.return_value = {'user_id': 33, 'user_ip': None}
        taskrun = TaskRun(task_id=22)
        key = 'pybossa:task_requested:user:88:task:44'
        self.connection.setex(key, 10, True)

        check = _check_task_requested_by_user(taskrun, self.connection)

        assert check is False, check


    @patch('pybossa.api.task_run.get_user_id_or_ip')
    def test_check_task_requested_by_user_authenticated_deletes_key(self, user):
        user.return_value = {'user_id': 33, 'user_ip': None}
        taskrun = TaskRun(task_id=22)
        key = 'pybossa:task_requested:user:33:task:22'
        self.connection.setex(key, 10, True)

        _check_task_requested_by_user(taskrun, self.connection)
        key_deleted = self.connection.get(key) is None

        assert key_deleted is True, key_deleted


    @patch('pybossa.api.task_run.get_user_id_or_ip')
    def test_check_task_requested_by_user_anonymous_preserves_key(self, user):
        user.return_value = {'user_id': None, 'user_ip': '127.0.0.1'}
        taskrun = TaskRun(task_id=22)
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'
        self.connection.setex(key, 10, True)

        _check_task_requested_by_user(taskrun, self.connection)
        key_deleted = self.connection.get(key) is None

        assert key_deleted is False, key_deleted

