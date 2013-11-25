# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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
# Cache global variables for timeouts
from random import choice
import settings_local as settings
from redis.sentinel import Sentinel
from werkzeug.contrib.cache import RedisCache
from functools import wraps
try:
    import cPickle as pickle
except ImportError: # pragma: no cover
    import pickle

ONE_DAY = 24 * 60 * 60
ONE_HOUR = 60 * 60
HALF_HOUR = 30 * 60
FIVE_MINUTES = 5 * 60


def memoize(timeout=300):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = "pybossa_cache:%s" % f.__name__
            key += "_args"
            for i in args:
                key += ":%s" % i
            #key += "_kwargs"
            #for i in frozenset(kwargs.items()):
            #    key += ":%s" % i
            print key
            sentinel = Sentinel(settings.REDIS_SENTINEL, socket_timeout=0.1)
            master = sentinel.master_for('mymaster')
            slave = sentinel.slave_for('mymaster')
            output = slave.get(key)
            if output:
                return pickle.loads(output)
            else:
                output = f(*args, **kwargs)
                master.setex(key, timeout, pickle.dumps(output))
                return output
        return wrapper
    return decorator
