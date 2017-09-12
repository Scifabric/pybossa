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
Syncer modeule for syncing objects on different domains.
"""

import json
from pybossa.core import sentinel


class Syncer(object):
    """Syncs one object with another."""

    SYNC_KEY = 'pybossa::sync::{}::target_url:{}::short_name:{}'
    CACHE_TIMEOUT = 300

    def cache_target(self, target, target_url, target_id):
        """Cache target.

        :param target: a domain object dict
        :param target_url: the target URL
        :param target_id: any identifier that
            can be used to create a unique key
        """
        target = json.dumps(target)
        sentinel.master.set(
            self.SYNC_KEY.format(
                self.__class__.__name__,
                target_url,
                target_id),
            target)

    def get_target_cache(self, target_url, target_id):
        """Get cached target value.

        :param target_url: the target URL
        :param target_id: the identifier used
            to create a unique key
        """
        target = sentinel.master.get(
            self.SYNC_KEY.format(
                self.__class__.__name__,
                target_url,
                target_id))
        return json.loads(target)
