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
import hashlib
import os
from random import choice
from redis.sentinel import Sentinel
from werkzeug.contrib.cache import RedisCache
from functools import wraps
try:
    import cPickle as pickle
except ImportError: # pragma: no cover
    import pickle

try:
    import settings_local as settings
except ImportError: # pragma: no cover
    os.environ.set('PYBOSSA_REDIS_CACHE_DISABLED', '1')

ONE_DAY = 24 * 60 * 60
ONE_HOUR = 60 * 60
HALF_HOUR = 30 * 60
FIVE_MINUTES = 5 * 60


def cache(key_prefix, timeout=300):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                key = "%s::%s" % (settings.REDIS_KEYPREFIX, key_prefix)
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
            else:
                return f(*args, **kwargs)
        return wrapper
    return decorator


def memoize(timeout=300, debug=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, f.__name__)
                key_to_hash = ""
                for i in args:
                    key_to_hash += ":%s" % i
                print key_to_hash
                key = key + ":" + hashlib.md5(key_to_hash).hexdigest()
                #key += "_kwargs"
                #for i in frozenset(kwargs.items()):
                #    key += ":%s" % i
                sentinel = Sentinel(settings.REDIS_SENTINEL, socket_timeout=0.1)
                master = sentinel.master_for(settings.REDIS_MASTER)
                slave = sentinel.slave_for(settings.REDIS_MASTER)
                output = slave.get(key)
                if output:
                    return pickle.loads(output)
                else:
                    output = f(*args, **kwargs)
                    master.setex(key, timeout, pickle.dumps(output))
                    return output
            else:
                return f(*args, **kwargs)
        return wrapper
    return decorator


def delete_memoized(function, arg=None):
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        sentinel = Sentinel(settings.REDIS_SENTINEL, socket_timeout=0.1)
        master = sentinel.master_for(settings.REDIS_MASTER)
        keys = []
        if arg:
            key_to_hash = ":%s" % arg
            key = "%s:%s_args::%s" % (settings.REDIS_KEYPREFIX, function.__name__,
                                     hashlib.md5(key_to_hash).hexdigest())
            keys.append(key)
        else:
            key = "%s:%s_args::*" % (settings.REDIS_KEYPREFIX, function.__name__)
            keys = master.keys(key)
        for k in keys:
            master.delete(k)
        return True


def delete_cached(key):
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        sentinel = Sentinel(settings.REDIS_SENTINEL, socket_timeout=0.1)
        master = sentinel.master_for(settings.REDIS_MASTER)
        key = "%s::%s" % (settings.REDIS_KEYPREFIX, key)
        return master.delete(key)
