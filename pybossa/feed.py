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
import json
from time import time
from pybossa.core import sentinel
try:
    import pickle as pickle
except ImportError:  # pragma: no cover
    import pickle


FEED_KEY = 'pybossa_feed'


def update_feed(obj):
    """Add domain object to update feed in Redis."""
    pipeline = sentinel.master.pipeline()
    serialized_object = pickle.dumps(obj)
    mapping = dict()
    mapping[serialized_object] = time()
    pipeline.zadd(FEED_KEY, mapping)
    pipeline.execute()


def get_update_feed():
    """Return update feed list."""
    feed = []
    data = sentinel.slave.zrevrange(FEED_KEY, 0, 99, withscores=True)
    for u in data:
        tmp = pickle.loads(u[0])
        tmp['updated'] = u[1]
        if tmp.get('info') and type(tmp.get('info')) == str:
            tmp['info'] = json.loads(tmp['info'])
        feed.append(tmp)
    return feed
