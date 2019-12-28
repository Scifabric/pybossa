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

import hashlib
from mock import patch
from pybossa.cache import (get_key_to_hash, get_hash_key, cache, memoize,
                           delete_cached, delete_memoized)
from pybossa.sentinel import Sentinel
from settings_test import REDIS_SENTINEL, REDIS_KEYPREFIX



class TestCacheHashFunctions(object):

    def test_00_get_key_to_hash_with_args(self):
        """Test CACHE get_key_to_hash with args works."""
        expected = ':1:a'
        key_to_hash = get_key_to_hash(1, 'a')
        err_msg = "Different key_to_hash %s != %s" % (key_to_hash, expected)
        assert key_to_hash == expected, err_msg


    def test_01_get_key_to_hash_with_kwargs(self):
        """Test CACHE get_key_to_hash with kwargs works."""
        expected = ':1:a'
        key_to_hash = get_key_to_hash(page=1, vowel='a')
        err_msg = "Different key_to_hash %s != %s" % (key_to_hash, expected)
        assert key_to_hash == expected, err_msg


    def test_02_get_key_to_hash_with_args_and_kwargs(self):
        """Test CACHE get_key_to_hash with args and kwargs works."""
        expected = ':1:a'
        key_to_hash = get_key_to_hash(1, vowel='a')
        err_msg = "Different key_to_hash %s != %s" % (key_to_hash, expected)
        assert key_to_hash == expected, err_msg


    def test_03_get_hash_key(self):
        """Test CACHE get_hash_key works."""
        prefix = 'prefix'
        key_to_hash = get_key_to_hash(1, vowel='ñ')
        tmp = key_to_hash.encode('utf-8')
        expected = prefix + ":" + hashlib.md5(tmp).hexdigest()
        key = get_hash_key(prefix, key_to_hash)
        err_msg = "The expected key is different %s != %s" % (expected, key)
        assert expected == key, err_msg



class FakeApp(object):
    def __init__(self):
        self.config = { 'REDIS_SENTINEL': REDIS_SENTINEL }

test_sentinel = Sentinel(app=FakeApp())

@patch('pybossa.cache.sentinel', new=test_sentinel)
class TestCacheMemoizeFunctions(object):

    @classmethod
    def setup_class(cls):
        # Enable the cache for tests within this class
        import os
        cls.cache = None
        if os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED'):
            cls.cache = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')
            del os.environ['PYBOSSA_REDIS_CACHE_DISABLED']

    @classmethod
    def teardown_class(cls):
        # Restore the environment variables to its previous state
        if cls.cache:
            import os
            os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = cls.cache

    def setUp(self):
        test_sentinel.master.flushall()

    def test_cache_stores_function_call_first_time_called(self):
        """Test CACHE cache decorator stores the result of calling a function
        in the cache the first time it's called"""

        @cache(key_prefix='my_cached_func')
        def my_func():
            return 'my_func was called'
        my_func()
        key = "%s::%s" % (REDIS_KEYPREFIX, 'my_cached_func')

        assert list(test_sentinel.master.keys()) == [key.encode('utf-8')], list(test_sentinel.master.keys())


    def test_cache_gets_function_from_cache_after_first_call(self):
        """Test CACHE cache retrieves the function value from cache after it has
        been called the first time, and does not call the function but once"""

        @cache(key_prefix='my_cached_func')
        def my_func(call_count=[]):
            call_count.append(1)
            return len(call_count)
        first_call = my_func()
        second_call = my_func()

        assert second_call == 1, second_call
        assert second_call == first_call, second_call


    def test_cached_function_returns_expected_value(self):
        """Test CACHE cache decorator returns the expected function return value
        in every call"""

        @cache(key_prefix='my_cached_func')
        def my_func():
            return 'my_func was called'
        first_call = my_func()
        second_call = my_func()

        assert first_call == 'my_func was called', first_call
        assert second_call == 'my_func was called', second_call


    def test_memoize_stores_function_call_first_time_called(self):
        """Test CACHE memoize decorator stores the result of calling a function
        in the cache the first time it's called"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        my_func('arg')
        key_pattern = "%s:%s_args:*" % (REDIS_KEYPREFIX, my_func.__name__)

        assert len(test_sentinel.master.keys(key_pattern)) == 1


    def test_memoize_stores_function_call_only_first_time_called(self):
        """Test CACHE memoize decorator stores the result of calling a function
        in the cache only the first time it's called"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        my_func('arg')
        my_func('arg')
        key_pattern = "%s:%s_args:*" % (REDIS_KEYPREFIX, my_func.__name__)

        assert len(test_sentinel.master.keys(key_pattern)) == 1


    def test_memoize_stores_function_calls_for_different_arguments(self):
        """Test CACHE memoize decorator stores the result of calling a function
        every time it's called with different argument values"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        key_pattern = "%s:%s_args:*" % (REDIS_KEYPREFIX, my_func.__name__)
        my_func('arg')
        assert len(test_sentinel.master.keys(key_pattern)) == 1
        my_func('another_arg')
        assert len(test_sentinel.master.keys(key_pattern)) == 2


    def test_memoize_gets_value_from_cache_after_first_call(self):
        """Test CACHE memoize decorator gets the value from cache for the same
        function arguments (but not for calls with different args)"""

        @memoize()
        def my_func(arg, call_count=[]):
            call_count.append(1)
            return len(call_count)

        first_call = my_func(arg='arg')
        second_call = my_func(arg='arg')
        third_call_with_other_arg = my_func(arg='other_arg')

        assert second_call == 1, second_call
        assert second_call == first_call, second_call
        assert third_call_with_other_arg == 2, third_call_with_other_arg


    def test_memoized_function_returns_expected_values(self):
        """Test CACHE memoized function returns the expected value every time"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        first_call = my_func('arg', kwarg='kwarg')
        second_call = my_func('arg', kwarg='kwarg')
        first_call_other_arg = my_func('other', kwarg='other')
        second_call_other_arg = my_func('other', kwarg='other')

        assert first_call == [('arg',), {'kwarg': 'kwarg'}], first_call
        assert second_call == [('arg',), {'kwarg': 'kwarg'}], first_call
        assert first_call_other_arg == [('other',), {'kwarg': 'other'}], first_call
        assert second_call_other_arg == [('other',), {'kwarg': 'other'}], first_call


    def test_delete_cached_returns_true_when_delete_succeeds(self):
        """Test CACHE delete_cached deletes a stored key and returns True if
        deletion is successful"""

        @cache(key_prefix='my_cached_func')
        def my_func():
            return 'my_func was called'
        key = "%s::%s" % (REDIS_KEYPREFIX, 'my_cached_func')
        my_func()
        assert list(test_sentinel.master.keys()) == [key.encode('utf-8')]

        delete_succedeed = delete_cached('my_cached_func')
        assert delete_succedeed is True, delete_succedeed
        assert list(test_sentinel.master.keys()) == [], 'Key was not deleted!'


    def test_delete_cached_returns_false_when_delete_fails(self):
        """Test CACHE delete_cached returns False if deletion is not successful"""

        @cache(key_prefix='my_cached_func')
        def my_func():
            return 'my_func was called'
        key = "%s::%s" % (REDIS_KEYPREFIX, 'my_cached_func')
        assert list(test_sentinel.master.keys()) == []

        delete_succedeed = delete_cached('my_cached_func')
        assert delete_succedeed is False, delete_succedeed


    def test_delete_memoized_returns_true_when_delete_succeeds(self):
        """Test CACHE delete_memoized deletes a stored key and returns True if
        deletion is successful"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        my_func('arg', kwarg='kwarg')
        assert len(list(test_sentinel.master.keys())) == 1

        delete_succedeed = delete_memoized(my_func, 'arg', kwarg='kwarg')
        assert delete_succedeed is True, delete_succedeed
        assert list(test_sentinel.master.keys()) == [], 'Key was not deleted!'


    def test_delete_memoized_returns_false_when_delete_fails(self):
        """Test CACHE delete_memoized returns False if deletion is not successful"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        my_func('arg', kwarg='kwarg')
        assert len(list(test_sentinel.master.keys())) == 1

        delete_succedeed = delete_memoized(my_func, 'badarg', kwarg='barkwarg')
        assert delete_succedeed is False, delete_succedeed
        assert len(list(test_sentinel.master.keys())) == 1, 'Key was unexpectedly deleted'


    def test_delete_memoized_deletes_only_requested(self):
        """Test CACHE delete_memoized deletes only the values it's asked and
        leaves the rest untouched"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        my_func('arg', kwarg='kwarg')
        my_func('other', kwarg='other')
        assert len(list(test_sentinel.master.keys())) == 2

        delete_succedeed = delete_memoized(my_func, 'arg', kwarg='kwarg')
        assert delete_succedeed is True, delete_succedeed
        assert len(list(test_sentinel.master.keys())) == 1, 'Everything was deleted!'


    def test_delete_memoized_deletes_all_function_calls(self):
        """Test CACHE delete_memoized deletes all the function calls stored if
        only function is specified and no arguments of the calls are provided"""

        @memoize()
        def my_func(*args, **kwargs):
            return [args, kwargs]
        @memoize()
        def my_other_func(*args, **kwargs):
            return [args, kwargs]
        my_func('arg', kwarg='kwarg')
        my_func('other', kwarg='other')
        my_other_func('arg', kwarg='kwarg')
        assert len(list(test_sentinel.master.keys())) == 3

        delete_succedeed = delete_memoized(my_func)
        assert delete_succedeed is True, delete_succedeed
        assert len(list(test_sentinel.master.keys())) == 1
