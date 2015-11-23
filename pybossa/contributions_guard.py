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

from pybossa.model import make_timestamp


class ContributionsGuard(object):

    KEY_PREFIX = 'pybossa:task_requested:user:%s:task:%s'
    STAMP_TTL = 60 * 60

    def __init__(self, redis_conn):
        self.conn = redis_conn

    def stamp(self, task, user):
        key = self._create_key(task, user)
        self.conn.setex(key, self.STAMP_TTL, make_timestamp())

    def check_task_stamped(self, task, user):
        key = self._create_key(task, user)
        task_requested = self.conn.get(key) is not None
        return task_requested

    def retrieve_timestamp(self, task, user):
        key = self._create_key(task, user)
        return self.conn.get(key)

    def _create_key(self, task, user):
        user_id = user['user_id'] or user['user_ip']
        return self.KEY_PREFIX % (user_id, task.id)
