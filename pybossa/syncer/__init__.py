# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
Syncer module for syncing objects on different domains.
"""

import json
from pybossa.core import sentinel


ONE_WEEK = 60 * 60 * 24 * 7


class Syncer(object):
    """Syncs one object with another."""

    SYNC_KEY = 'pybossa::sync::{}::target_url:{}::short_name:{}'
    CACHE_TIMEOUT = ONE_WEEK

    def __init__(self, target_url):
        """Initialize a Syncer.

        :param target_url: the target URL to sync with
        """
        self.target_url = target_url

    def cache_target(self, target, target_id):
        """Cache target.

        :param target: a domain object dict
        :param target_id: any identifier that
            can be used to create a unique key
        """
        target = json.dumps(target)
        sentinel.master.setex(
            self._get_key(target_id),
            self.CACHE_TIMEOUT,
            target)

    def get_target_cache(self, target_id):
        """Get cached target value.

        :param target_id: the identifier used
            to create a unique key
        :return: a dict of the target
        """
        target = sentinel.master.get(self._get_key(target_id))
        if target:
            return json.loads(target)
        else:
            return

    def delete_target_cache(self,  target_id):
        """Delete cached target value.

        :param target_id: the identifier used
            to create a unique key
        """
        sentinel.master.delete(self._get_key(target_id))

    def _get_key(self, target_id):
        target_id = target_id.encode('utf-8')
        return self.SYNC_KEY.format(
            self.__class__.__name__,
            self.target_url,
            target_id)


class NotEnabled(Exception):
    """An exception indicating that an error
    has occurred where a syncer tried to sync,
    but could not due to the target not being
    enabled for syncing.
    """
    pass
