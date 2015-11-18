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

from redis import StrictRedis
from pybossa.contributions_guard import ContributionsGuard
from pybossa.model.task import Task
from mock import patch

class TestContributionsGuard(object):

    def setUp(self):
        self.connection = StrictRedis()
        self.connection.flushall()
        self.guard = ContributionsGuard(self.connection)

    def test_stamp_registers_specific_user_id_and_task(self):
        user = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:33:task:22'

        self.guard.stamp(task, user)

        assert key in self.connection.keys(), self.connection.keys()

    def test_stamp_registers_specific_user_ip_and_task_if_no_id_provided(self):
        user = {'user_id': None, 'user_ip': '127.0.0.1'}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'

        self.guard.stamp(task, user)

        assert key in self.connection.keys(), self.connection.keys()

    def test_stamp_expires_in_one_hour(self):
        user = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:33:task:22'
        ONE_HOUR = 60 * 60

        self.guard.stamp(task, user)

        assert self.connection.ttl(key) == ONE_HOUR, self.connection.ttl(key)

    @patch('pybossa.contributions_guard.make_timestamp')
    def test_stamp_adds_a_timestamp_when_the_task_is_stamped(self, make_timestamp):
        make_timestamp.return_value = "now"
        user = {'user_id': None, 'user_ip': '127.0.0.1'}
        task = Task(id=22)
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'

        self.guard.stamp(task, user)

        assert self.connection.get(key) == 'now'


    def test_check_task_stamped_returns_False_for_non_stamped_task(self):
        user = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)

        assert self.guard.check_task_stamped(task, user) is False

    def test_check_task_stamped_returns_True_for_auth_user_who_requested_task(self):
        user = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)

        self.guard.stamp(task, user)

        assert self.guard.check_task_stamped(task, user) is True

    def test_check_task_stamped_returns_True_for_anon_user_who_requested_task(self):
        user = {'user_id': None, 'user_ip': '127.0.0.1'}
        task = Task(id=22)

        self.guard.stamp(task, user)

        assert self.guard.check_task_stamped(task, user) is True

    def test_check_task_stamped_returns_False_for_auth_if_called_second_time(self):
        user = {'user_id': 33, 'user_ip': None}
        task = Task(id=22)
        self.guard.stamp(task, user)

        self.guard.check_task_stamped(task, user)

        assert self.guard.check_task_stamped(task, user) is False

    def test_check_task_stamped_returns_True_for_anon_if_called_second_time(self):
        user = {'user_id': None, 'user_ip': '127.0.0.1'}
        task = Task(id=22)
        self.guard.stamp(task, user)

        self.guard.check_task_stamped(task, user)

        assert self.guard.check_task_stamped(task, user) is True
