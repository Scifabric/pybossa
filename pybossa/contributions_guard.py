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

from pybossa.model import make_timestamp


class ContributionsGuard(object):

    KEY_PREFIX = 'pybossa:task_requested:user:{0}:task:{1}'
    PRESENTED_KEY_PREFIX = 'pybossa:task_presented:user:{0}:task:{1}'
    STAMP_TTL = 60 * 60
    OTP_TTL = 60 * 5

    def __init__(self, redis_conn):
        self.conn = redis_conn


    # Task requested guards

    def stamp(self, task, user):
        """Cache the time that a task was requested by a client
        for a given user.
        """
        key = self._create_key(task, user)
        self.conn.setex(key, self.STAMP_TTL, make_timestamp())

    def check_task_stamped(self, task, user):
        """Check if a task was requested by a user."""
        key = self._create_key(task, user)
        task_requested = self.conn.get(key) is not None
        return task_requested

    def retrieve_timestamp(self, task, user):
        """Get the cached timestamp for a task requested by a user."""
        key = self._create_key(task, user)
        return self.conn.get(key)

    def _create_key(self, task, user):
        """Create a Redis key for a given task and a user."""
        user_id = user['user_id'] or user['user_ip']
        if user.get('external_uid'):
            user_id = user['external_uid']
        return self.KEY_PREFIX % (user_id, task.id)

    def _remove_task_stamped(self, task, user):
        key = self._create_key(task, user)
        return self.conn.delete(key)


    # Task presented guards

    def stamp_presented_time(self, task, user):
        """Cache the time that a task was presented on a client."""
        key = self._create_presented_time_key(task, user)
        self.conn.setex(key, self.STAMP_TTL, make_timestamp())

    def check_task_presented_timestamp(self, task, user):
        """Check if a task was presented to a user."""
        key = self._create_presented_time_key(task, user)
        task_presented = self.conn.get(key) is not None
        return task_presented

    def retrieve_presented_timestamp(self, task, user):
        """Get the cached timestamp for a task presented to a user."""
        key = self._create_presented_time_key(task, user)
        return self.conn.get(key)

    def _create_presented_time_key(self, task, user):
        """Create a Redis key for the presented time of a given task
        to a given user. user must have a user_id. We only cache
        presented time for users with a user_id to prevent calling
        /cachePresentedTime directly.
        """
        user_id = user['user_id'] or None
        return self.PRESENTED_KEY_PREFIX.format(user_id, task)

    # OTP

    def _create_otpsecret_key(self, user_email):
        return "OTPSECRET:user_email:{0}".format(user_email)

    def add_otp_secret(self, user_email, otpsecret):
        key = self._create_otpsecret_key(user_email)
        self.conn.setex(key, self.OTP_TTL, otpsecret)

    def retrieve_user_otp_secret(self, user_email):
        key = self._create_otpsecret_key(user_email)
        return self.conn.get(key)
