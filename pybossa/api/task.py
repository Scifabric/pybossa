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
"""
PyBossa api module for exposing domain object Task via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * tasks

"""
from pybossa.model.task import Task
from pybossa.util import get_user_id_or_ip
from api_base import APIBase
from pybossa.core import sentinel


def mark_task_as_requested_by_user(task_id, redis_conn):
    usr = get_user_id_or_ip()['user_id'] or get_user_id_or_ip()['user_ip']
    key = 'pybossa:task_requested:user:%s:task:%s' % (usr, task_id)
    timeout = 60 * 60
    redis_conn.setex(key, timeout, True)


class TaskAPI(APIBase):

    """Class for domain object Task."""

    __class__ = Task

    def get(self, oid):
        mark_task_as_requested_by_user(oid, sentinel.master)
        return super(TaskAPI, self).get(oid)
