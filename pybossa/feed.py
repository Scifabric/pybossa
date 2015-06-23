# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
from time import time
from pybossa.core import sentinel
try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle


FEED_KEY = 'pybossa_feed'

def update_feed(obj):
    """Add domain object to update feed in Redis."""
    pipeline = sentinel.master.pipeline()
    serialized_object = pickle.dumps(obj)
    pipeline.zadd(FEED_KEY, time(), serialized_object)
    pipeline.execute()
