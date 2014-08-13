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

import hashlib
from mock import patch
from pybossa.cache import get_key_to_hash, get_hash_key, cache, memoize
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
        key_to_hash = get_key_to_hash(1, vowel=u'ñ')
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

        assert test_sentinel.master.keys() == [key], test_sentinel.master.keys()


    def test_cache_gets_function_from_cache_second_after_first_call(self):
        """Test CACHE cache retrieves the function value from cache after it has
        been called the first time, and does not call the function but once"""

        @cache(key_prefix='my_cached_func')
        def my_func(call_count = 0):
            call_count = call_count + 1
            return call_count
        first_call = my_func()
        second_call = my_func()

        assert second_call == 1, second_call
        assert second_call is first_call, second_call


    def test_cache_returns_expected_value(self):
        """Test CACHE cache decorator returns the expected function return value"""

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
            return {'args': args, 'kwargs': kwargs}
        my_func()
        key_pattern = "%s:%s_args:*" % (REDIS_KEYPREFIX, my_func.__name__)

        assert len(test_sentinel.master.keys(key_pattern)) == 1

