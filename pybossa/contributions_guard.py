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

class ContributionsGuard(object):
    def __init__(self, redis_conn):
        self.conn = redis_conn

    def stamp(self, task, user):
        user_id = user['user_id'] or user['user_ip']
        key = 'pybossa:task_requested:user:%s:task:%s' % (user_id, task.id)
        timeout = 60 * 60
        self.conn.setex(key, timeout, True)
