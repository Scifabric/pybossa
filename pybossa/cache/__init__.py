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

try:
    import cPickle as pickle
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
ONE_WEEK = 7 * ONE_DAY

management_dashboard_stats = [
    'project_chart', 'category_chart', 'task_chart',
    'submission_chart', 'number_of_active_jobs',
    'number_of_created_jobs', 'number_of_created_tasks',
    'number_of_completed_tasks', 'avg_time_to_complete_task',
    'number_of_active_users', 'categories_with_new_projects',
    'avg_task_per_job', 'tasks_per_category'
]


def get_key_to_hash(*args, **kwargs):
    """Return key to hash for *args and **kwargs."""
    key_to_hash = ""
    # First args
    for i in args:
        key_to_hash += u":%s" % i
    # Attach any kwargs
    for key in sorted(kwargs.iterkeys()):
        key_to_hash += ":%s" % kwargs[key]
    return key_to_hash


def get_hash_key(prefix, key_to_hash):
    """Return hash for a prefix and a key to hash."""
    key_to_hash = key_to_hash.encode('utf-8')
    key = prefix + ":" + hashlib.md5(key_to_hash).hexdigest()
    return key


def get_cache_group_key(key):
    return '{}:memoize_cache_group:{}'.format(settings.REDIS_KEYPREFIX, key)


def add_key_to_cache_groups(key_to_add, cache_group_keys_arg, *args, **kwargs):
    for cache_group_key_arg in (cache_group_keys_arg or []):
        cache_group_key = None
        if isinstance(cache_group_key_arg, list):
            cache_group_key = '_'.join(str(args[i]) for i in cache_group_key_arg)
        elif isinstance(cache_group_key_arg, basestring):
            cache_group_key = cache_group_key_arg
        elif callable(cache_group_key_arg):
            cache_group_key = cache_group_key_arg(*args, **kwargs)
        elif cache_group_key_arg is not None:
            raise Exception('Invalid cache_group_key_arg: {}'.format(cache_group_key_arg))
        else:
            return
        key = get_cache_group_key(cache_group_key)
        sentinel.master.sadd(key, key_to_add)


def delete_cache_group(cache_group_key):
    key = get_cache_group_key(cache_group_key)
    keys_to_delete = list(sentinel.slave.smembers(key)) + [key]
    sentinel.master.delete(*keys_to_delete)


def cache(key_prefix, timeout=300, cache_group_keys=None):
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
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                output = sentinel.slave.get(key)
                if output:
                    return pickle.loads(output)
                output = f(*args, **kwargs)
                sentinel.master.setex(key, timeout, pickle.dumps(output))
                add_key_to_cache_groups(key, cache_group_keys, *args, **kwargs)
                return output
            output = f(*args, **kwargs)
            sentinel.master.setex(key, timeout, pickle.dumps(output))
            add_key_to_cache_groups(key, cache_group_keys, *args, **kwargs)
            return output
        return wrapper
    return decorator


def memoize(timeout=300, cache_group_keys=None):
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
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                output = sentinel.slave.get(key)
                if output:
                    return pickle.loads(output)
                output = f(*args, **kwargs)
                sentinel.master.setex(key, timeout, pickle.dumps(output))
                add_key_to_cache_groups(key, cache_group_keys, *args, **kwargs)
                return output
            output = f(*args, **kwargs)
            sentinel.master.setex(key, timeout, pickle.dumps(output))
            add_key_to_cache_groups(key, cache_group_keys, *args, **kwargs)
            return output
        return wrapper
    return decorator


def memoize_essentials(timeout=300, essentials=None, cache_group_keys=None):
    """
    Decorator for caching functions using its arguments as part of the key.

    Essential arguments aren't hashed to make it possible to remove a group of cache entries

    Returns the cached value, or the function if the cache is disabled

    """
    if timeout is None:
        timeout = 300
    if essentials is None:
        essentials = []
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, f.__name__)
            essential_args = [args[i] for i in essentials]
            key += get_key_to_hash(*essential_args) + ":"
            key_to_hash = get_key_to_hash(*args, **kwargs)
            key = get_hash_key(key, key_to_hash)
            if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
                output = sentinel.slave.get(key)
                if output:
                    return pickle.loads(output)
                output = f(*args, **kwargs)
                sentinel.master.setex(key, timeout, pickle.dumps(output))
                add_key_to_cache_groups(key, cache_group_keys, *args, **kwargs)
                return output
            output = f(*args, **kwargs)
            sentinel.master.setex(key, timeout, pickle.dumps(output))
            add_key_to_cache_groups(key, cache_group_keys, *args, **kwargs)
            return output
        return wrapper
    return decorator


def delete_cached(key):
    """
    Delete a cached value from the cache.

    Returns True if success or no cache is enabled

    """
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        key = "%s::%s" % (settings.REDIS_KEYPREFIX, key)
        return bool(sentinel.master.delete(key))
    return True


def delete_memoized(function, *args, **kwargs):
    """
    Delete a memoized value from the cache.

    Returns True if success or no cache is enabled

    """
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, function.__name__)
        if args or kwargs:
            key_to_hash = get_key_to_hash(*args, **kwargs)
            key = get_hash_key(key, key_to_hash)
            return bool(sentinel.master.delete(key))
        keys_to_delete = list(sentinel.slave.scan_iter(match=key + '*', count=10000))
        if not keys_to_delete:
            return False
        return bool(sentinel.master.delete(*keys_to_delete))
    return True


def delete_memoized_essential(function, *args, **kwargs):
    """
    Use the essential arguments list to delete all matching memoized values from the cache.

    Returns True if success or no cache is enabled

    """
    if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED') is None:
        key = "%s:%s_args:" % (settings.REDIS_KEYPREFIX, function.__name__)
        if args or kwargs:
            key += get_key_to_hash(*args, **kwargs)
        keys_to_delete = list(sentinel.slave.scan_iter(match=key + '*', count=10000))
        if not keys_to_delete:
            return False
        return bool(sentinel.master.delete(*keys_to_delete))
    return True
