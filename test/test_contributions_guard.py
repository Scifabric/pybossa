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

from pybossa.contributions_guard import ContributionsGuard
from pybossa.model.task import Task
from mock import patch
import settings_test
from redis.sentinel import Sentinel


class TestContributionsGuard(object):

    def setUp(self):
        sentinel = Sentinel(settings_test.REDIS_SENTINEL)
        db = getattr(settings_test, 'REDIS_DB', 0)
        self.connection = sentinel.master_for('mymaster', db=db)
        self.connection.flushall()
        self.guard = ContributionsGuard(self.connection)
        self.anon_user = {'user_id': None, 'user_ip': '127.0.0.1'}
        self.auth_user = {'user_id': 33, 'user_ip': None}
        self.task = Task(id=22)

    def test_stamp_registers_specific_user_id_and_task(self):
        key = b'pybossa:task_requested:user:33:task:22'

        self.guard.stamp(self.task, self.auth_user)

        assert key in list(self.connection.keys()), list(self.connection.keys())

    def test_stamp_registers_specific_user_ip_and_task_if_no_id_provided(self):
        key = b'pybossa:task_requested:user:127.0.0.1:task:22'

        self.guard.stamp(self.task, self.anon_user)

        assert key in list(self.connection.keys()), list(self.connection.keys())

    def test_stamp_expires_in_one_hour(self):
        key = 'pybossa:task_requested:user:33:task:22'
        ONE_HOUR = 60 * 60

        self.guard.stamp(self.task, self.auth_user)

        assert self.connection.ttl(key) == ONE_HOUR, self.connection.ttl(key)

    @patch('pybossa.contributions_guard.make_timestamp')
    def test_stamp_adds_a_timestamp_when_the_task_is_stamped(self, make_timestamp):
        make_timestamp.return_value = b'now'
        key = b'pybossa:task_requested:user:127.0.0.1:task:22'

        self.guard.stamp(self.task, self.anon_user)

        assert self.connection.get(key) == b'now', self.connection.get(key)

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
    def test_retrieve_timestamp_returns_the_timestamp_for_stamped_task(self, make_timestamp):
        make_timestamp.return_value = 'now'
        self.guard.stamp(self.task, self.auth_user)

        assert self.guard.retrieve_timestamp(self.task, self.auth_user) == 'now'
