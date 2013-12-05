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
"""
This module exports a set of decorators for caching functions.

It exports:
    * cache: for caching functions without parameters
    * memoize: for caching functions using its arguments as part of the key
    * delete_cached: to remove a cached value
    * delete_memoized: to remove a cached value from the memoize decorator

"""
import os
import hashlib
from functools import wraps
from pybossa.core import redis_master, redis_slave
try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

try:
    import settings_local as settings
except ImportError:  # pragma: no cover
    os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'

ONE_DAY = 24 * 60 * 60
ONE_HOUR = 60 * 60
HALF_HOUR = 30 * 60
FIVE_MINUTES = 5 * 60


def cache(key_prefix, timeout=300):
    """
    Decorator for caching functions.

    Returns the function value from cache, or the function if cache disabled

    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                key = "%s::%s" % (settings.REDIS_KEYPREFIX, key_prefix)
                output = redis_slave.get(key)
                if output:
                    return pickle.loads(output)
                else:
                    output = f(*args, **kwargs)
                    redis_master.setex(key, timeout, pickle.dumps(output))
                    return output
            else:
                return f(*args, **kwargs)
        return wrapper
    return decorator


def memoize(timeout=300, debug=False):
    """
    Decorator for caching functions using its arguments as part of the key.

    Returns the cached value, or the function if the cache is disabled

    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, f.__name__)
                key_to_hash = ""
                for i in args:
                    key_to_hash += ":%s" % i
                key = key + ":" + hashlib.md5(key_to_hash).hexdigest()
                #key += "_kwargs"
                #for i in frozenset(kwargs.items()):
                #    key += ":%s" % i
                output = redis_slave.get(key)
                if output:
                    return pickle.loads(output)
                else:
                    output = f(*args, **kwargs)
                    redis_master.setex(key, timeout, pickle.dumps(output))
                    return output
            else:
                return f(*args, **kwargs)
        return wrapper
    return decorator


def delete_memoized(function, arg=None):
    """
    Delete a memoized value from the cache.

    Returns True if success

    """
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        keys = []
        if arg:
            key_to_hash = ":%s" % arg
            key = "%s:%s_args::%s" % (settings.REDIS_KEYPREFIX,
                                      function.__name__,
                                      hashlib.md5(key_to_hash).hexdigest())
            keys.append(key)
        else:
            key = "%s:%s_args::*" % (settings.REDIS_KEYPREFIX,
                                     function.__name__)
            keys = redis_master.keys(key)
        for k in keys:
            redis_master.delete(k)
        return True


def delete_cached(key):
    """
    Delete a cached value from the cache.

    Returns True if success

    """
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        key = "%s::%s" % (settings.REDIS_KEYPREFIX, key)
        return redis_master.delete(key)
