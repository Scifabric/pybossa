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

import settings_test
from pybossa.sentinel import Sentinel
from pybossa.contributions_guard import ContributionsGuard
from pybossa.model.task import Task
from mock import patch

class FakeApp(object):
    def __init__(self):
        if all(hasattr(settings_test, attr) for attr in 
            ['REDIS_MASTER_DNS', 'REDIS_SLAVE_DNS', 'REDIS_PORT']):
            self.config = dict(REDIS_MASTER_DNS=settings_test.REDIS_MASTER_DNS,
                REDIS_SLAVE_DNS=settings_test.REDIS_SLAVE_DNS,
                REDIS_PORT=settings_test.REDIS_PORT)
        else:
            self.config = { 'REDIS_SENTINEL': settings_test.REDIS_SENTINEL }

class TestContributionsGuard(object):

    def setUp(self):
        db = getattr(settings_test, 'REDIS_DB', 0)
        sentinel = Sentinel(app=FakeApp())
        self.connection = sentinel.master
        self.connection.flushall()
        self.guard = ContributionsGuard(self.connection)
        self.anon_user = {'user_id': None, 'user_ip': '127.0.0.1'}
        self.auth_user = {'user_id': 33, 'user_ip': None}
        self.task = Task(id=22)

    # Task requested guard tests

    def test_stamp_registers_specific_user_id_and_task(self):
        key = 'pybossa:task_requested:user:33:task:22'

        self.guard.stamp(self.task, self.auth_user)

        assert key in self.connection.keys(), self.connection.keys()

    def test_stamp_registers_specific_user_ip_and_task_if_no_id_provided(self):
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'

        self.guard.stamp(self.task, self.anon_user)

        assert key in self.connection.keys(), self.connection.keys()

    def test_stamp_expires_in_one_hour(self):
        key = 'pybossa:task_requested:user:33:task:22'
        ONE_HOUR = 60 * 60

        self.guard.stamp(self.task, self.auth_user)

        assert self.connection.ttl(key) == ONE_HOUR, self.connection.ttl(key)

    @patch('pybossa.contributions_guard.make_timestamp')
    def test_stamp_adds_a_timestamp_when_the_task_is_stamped(self, make_timestamp):
        make_timestamp.return_value = "now"
        key = 'pybossa:task_requested:user:127.0.0.1:task:22'

        self.guard.stamp(self.task, self.anon_user)

        assert self.connection.get(key) == 'now'

    def test_check_task_stamped_returns_False_for_non_stamped_task(self):
        assert self.guard.check_task_stamped(self.task, self.auth_user) is False

    def test_check_task_stamped_returns_True_for_auth_user_who_requested_task(self):
        self.guard.stamp(self.task, self.auth_user)

        assert self.guard.check_task_stamped(self.task, self.auth_user) is True

    def test_check_task_stamped_returns_True_for_anon_user_who_requested_task(self):
        self.guard.stamp(self.task, self.anon_user)

        assert self.guard.check_task_stamped(self.task, self.anon_user) is True

    def test_retrieve_timestamp_returns_None_for_non_stamped_task(self):
        assert self.guard.retrieve_timestamp(self.task, self.auth_user) is None

    @patch('pybossa.contributions_guard.make_timestamp')
    def test_retrieve_timestamp_returs_the_timestamp_for_stamped_task(self, make_timestamp):
        make_timestamp.return_value = "now"
        self.guard.stamp(self.task, self.auth_user)

        assert self.guard.retrieve_timestamp(self.task, self.auth_user) == 'now'


    # Task presented guard tests

    def test_stamp_presented_time_registers_specific_user_id_and_task(self):
        key = 'pybossa:task_presented:user:33:task:22'

        self.guard.stamp_presented_time(self.task, self.auth_user)

        assert key in self.connection.keys(), self.connection.keys()

    def test_stamp_presented_time_registers_user_as_None_and_task_if_no_id_provided(self):
        key = 'pybossa:task_presented:user:None:task:22'

        self.guard.stamp_presented_time(self.task, self.anon_user)

        assert key in self.connection.keys(), self.connection.keys()

    def test_stamp_presented_time_expires_in_one_hour(self):
        key = 'pybossa:task_presented:user:33:task:22'
        ONE_HOUR = 60 * 60

        self.guard.stamp_presented_time(self.task, self.auth_user)

        assert self.connection.ttl(key) == ONE_HOUR, self.connection.ttl(key)

    @patch('pybossa.contributions_guard.make_timestamp')
    def test_stamp_presented_time_adds_a_timestamp_when_the_task_is_stamped(self, make_timestamp):
        make_timestamp.return_value = "now"
        key = 'pybossa:task_presented:user:33:task:22'

        self.guard.stamp_presented_time(self.task, self.auth_user)

        assert self.connection.get(key) == 'now'

    def test_check_task_presented_stamped_returns_False_for_non_stamped_task(self):
        assert self.guard.check_task_presented_timestamp(self.task, self.auth_user) is False

    def test_check_task_presented_stamped_returns_True_for_auth_user_who_was_presented_task(self):
        self.guard.stamp_presented_time(self.task, self.auth_user)

        assert self.guard.check_task_presented_timestamp(self.task, self.auth_user) is True

    def test_check_task_presented_stamped_returns_True_for_anon_user_who_was_presented_task(self):
        self.guard.stamp_presented_time(self.task, self.anon_user)

        assert self.guard.check_task_presented_timestamp(self.task, self.anon_user) is True

    def test_retrieve_presented_timestamp_returns_None_for_non_stamped_task(self):
        assert self.guard.retrieve_presented_timestamp(self.task, self.anon_user) is None

    @patch('pybossa.contributions_guard.make_timestamp')
    def test_retrieve_presented_timestamp_returs_the_timestamp_for_stamped_task(self, make_timestamp):
        make_timestamp.return_value = "now"
        self.guard.stamp_presented_time(self.task, self.auth_user)

        assert self.guard.retrieve_presented_timestamp(self.task, self.auth_user) == 'now'
