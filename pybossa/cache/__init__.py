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
from pybossa.core import sentinel

from pybossa import util

try:
    import pickle as pickle
except ImportError:  # pragma: no cover
    import pickle

try:
    import settings_local as settings
except ImportError:  # pragma: no cover
    import pybossa.default_settings as settings
    os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'

ONE_DAY = 24 * 60 * 60
ONE_HOUR = 60 * 60
HALF_HOUR = 30 * 60
FIVE_MINUTES = 5 * 60


def get_key_to_hash(*args, **kwargs):
    """Return key to hash for *args and **kwargs."""
    key_to_hash = ""
    # First args
    for i in args:
        key_to_hash += ":%s" % i
    # Attach any kwargs
    for key in sorted(kwargs.keys()):
        key_to_hash += ":%s" % kwargs[key]
    return key_to_hash


def get_hash_key(prefix, key_to_hash):
    """Return hash for a prefix and a key to hash."""
    key_to_hash = key_to_hash.encode('utf-8')
    key = prefix + ":" + hashlib.md5(key_to_hash).hexdigest()
    return key


def cache(key_prefix, timeout=300):
    """
    Decorator for caching functions.

    Returns the function value from cache, or the function if cache disabled

    """
    if timeout is None:
        timeout = 300
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = "%s::%s" % (settings.REDIS_KEYPREFIX, key_prefix)
            if util.redis_cache_is_enabled():
                output = sentinel.slave.get(key)
                if output:
                    return pickle.loads(output)
                output = f(*args, **kwargs)
                sentinel.master.setex(key, timeout, pickle.dumps(output))
                return output
            output = f(*args, **kwargs)
            return output
        return wrapper
    return decorator


def memoize(timeout=300):
    """
    Decorator for caching functions using its arguments as part of the key.

    Returns the cached value, or the function if the cache is disabled

    """
    if timeout is None:
        timeout = 300
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, f.__name__)
            key_to_hash = get_key_to_hash(*args, **kwargs)
            key = get_hash_key(key, key_to_hash)
            if util.redis_cache_is_enabled():
                output = sentinel.slave.get(key)
                if output:
                    return pickle.loads(output)
                output = f(*args, **kwargs)
                sentinel.master.setex(key, timeout, pickle.dumps(output))
                return output
            output = f(*args, **kwargs)
            return output
        return wrapper
    return decorator


def delete_cached(key):
    """
    Delete a cached value from the cache.

    Returns True if success or no cache is enabled

    """
    if util.redis_cache_is_enabled():
        key = "%s::%s" % (settings.REDIS_KEYPREFIX, key)
        return bool(sentinel.master.delete(key))
    return True


def delete_memoized(function, *args, **kwargs):
    """
    Delete a memoized value from the cache.

    Returns True if success or no cache is enabled

    """
    if util.redis_cache_is_enabled():
        key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, function.__name__)
        if args or kwargs:
            key_to_hash = get_key_to_hash(*args, **kwargs)
            key = get_hash_key(key, key_to_hash)
            return bool(sentinel.master.delete(key))
        keys_to_delete = sentinel.slave.keys(pattern=key + '*')
        if not keys_to_delete:
            return False
        return bool(sentinel.master.delete(*keys_to_delete))
    return True
