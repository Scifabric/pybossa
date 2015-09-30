# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
import pybossa.util as util
from mock import MagicMock
from datetime import datetime, timedelta
import calendar
import time
import csv
import tempfile
import os
import json


class TestPybossaUtil(object):


# TODO: test these 2 decorators in a more unitary way. The following tests have
# been moved to test_api_common.py
    # def test_jsonpify(self):
    #     """Test jsonpify decorator works."""
    #     res = self.app.get('/api/app/1?callback=mycallback')
    #     err_msg = "mycallback should be included in the response"
    #     assert "mycallback" in res.data, err_msg
    #     err_msg = "Status code should be 200"
    #     assert res.status_code == 200, err_msg

    # def test_cors(self):
    #     """Test CORS decorator works."""
    #     res = self.app.get('/api/app/1')
    #     err_msg = "CORS should be enabled"
    #     print res.headers
    #     assert res.headers['Access-Control-Allow-Origin'] == '*', err_msg
    #     methods = ['PUT', 'HEAD', 'DELETE', 'OPTIONS', 'GET']
    #     for m in methods:
    #         assert m in res.headers['Access-Control-Allow-Methods'], err_msg
    #     assert res.headers['Access-Control-Max-Age'] == '21600', err_msg
    #     headers = 'CONTENT-TYPE, AUTHORIZATION'
    #     assert res.headers['Access-Control-Allow-Headers'] == headers, err_msg

    def test_pretty_date(self):
        """Test pretty_date works."""
        now = datetime.now()
        pd = util.pretty_date()
        assert pd == "just now", pd

        pd = util.pretty_date(now.isoformat())
        assert pd == "just now", pd

        pd = util.pretty_date(calendar.timegm(time.gmtime()))
        assert pd == "just now", pd

        d = now + timedelta(days=10)
        pd = util.pretty_date(d.isoformat())
        assert pd == '', pd

        d = now - timedelta(seconds=10)
        pd = util.pretty_date(d.isoformat())
        assert pd == '10 seconds ago', pd

        d = now - timedelta(minutes=1)
        pd = util.pretty_date(d.isoformat())
        assert pd == 'a minute ago', pd

        d = now - timedelta(minutes=2)
        pd = util.pretty_date(d.isoformat())
        assert pd == '2 minutes ago', pd

        d = now - timedelta(hours=1)
        pd = util.pretty_date(d.isoformat())
        assert pd == 'an hour ago', pd

        d = now - timedelta(hours=5)
        pd = util.pretty_date(d.isoformat())
        assert pd == '5 hours ago', pd

        d = now - timedelta(days=1)
        pd = util.pretty_date(d.isoformat())
        assert pd == 'Yesterday', pd

        d = now - timedelta(days=5)
        pd = util.pretty_date(d.isoformat())
        assert pd == '5 days ago', pd

        d = now - timedelta(weeks=1)
        pd = util.pretty_date(d.isoformat())
        assert pd == '1 weeks ago', pd

        d = now - timedelta(days=32)
        pd = util.pretty_date(d.isoformat())
        assert pd == '1 month ago', pd

        d = now - timedelta(days=62)
        pd = util.pretty_date(d.isoformat())
        assert pd == '2 months ago', pd

        d = now - timedelta(days=366)
        pd = util.pretty_date(d.isoformat())
        assert pd == '1 year ago', pd

        d = now - timedelta(days=766)
        pd = util.pretty_date(d.isoformat())
        assert pd == '2 years ago', pd

    def test_pagination(self):
        """Test Class Pagination works."""
        page = 1
        per_page = 5
        total_count = 10
        p = util.Pagination(page, per_page, total_count)
        assert p.page == page, p.page
        assert p.per_page == per_page, p.per_page
        assert p.total_count == total_count, p.total_count

        err_msg = "It should return two pages"
        assert p.pages == 2, err_msg
        p.total_count = 7
        assert p.pages == 2, err_msg
        p.total_count = 10

        err_msg = "It should return False"
        assert p.has_prev is False, err_msg
        err_msg = "It should return True"
        assert p.has_next is True, err_msg
        p.page = 2
        assert p.has_prev is True, err_msg
        err_msg = "It should return False"
        assert p.has_next is False, err_msg

        for i in p.iter_pages():
            err_msg = "It should return the page: %s" % page
            assert i == page, err_msg
            page += 1

    def test_unicode_csv_reader(self):
        """Test unicode_csv_reader works."""
        fake_csv = ['one, two, three']
        err_msg = "Each cell should be encoded as Unicode"
        for row in util.unicode_csv_reader(fake_csv):
            for item in row:
                assert type(item) == unicode, err_msg

    def test_UnicodeWriter(self):
        """Test UnicodeWriter class works."""
        tmp = tempfile.NamedTemporaryFile()
        uw = util.UnicodeWriter(tmp)
        fake_csv = ['one, two, three, {"i": 1}']
        for row in csv.reader(fake_csv):
            # change it for a dict
            row[3] = dict(i=1)
            uw.writerow(row)
        tmp.seek(0)
        err_msg = "It should be the same CSV content"
        with open(tmp.name, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                for item in row:
                    assert item in fake_csv[0], err_msg

    def test_publish_channel_private(self):
        """Test publish_channel private method works."""
        sentinel = MagicMock()
        master = MagicMock()
        sentinel.master = master

        data = dict(foo='bar')
        util.publish_channel(sentinel, 'project', data,
                             type='foobar', private=True)
        channel = 'channel_private_project'
        msg = dict(type='foobar', data=data)
        master.publish.assert_called_with(channel, json.dumps(msg))

    def test_publish_channel_public(self):
        """Test publish_channel public method works."""
        sentinel = MagicMock()
        master = MagicMock()
        sentinel.master = master

        data = dict(foo='bar')
        util.publish_channel(sentinel, 'project', data,
                             type='foobar', private=False)
        channel = 'channel_public_project'
        msg = dict(type='foobar', data=data)
        master.publish.assert_called_with(channel, json.dumps(msg))


class TestIsReservedName(object):
    from flask import Flask
    from pybossa.core import setup_blueprints, create_app
    app = create_app(run_as_server=False)

    def test_returns_true_for_reserved_name_for_app_blueprint(self):
        with self.app.app_context():
            reserved = util.is_reserved_name('project', 'new')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('project', 'category')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('project', 'page')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('project', 'draft')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('project', 'published')
            assert reserved is True, reserved


    def test_returns_false_for_valid_name_for_app_blueprint(self):
        with self.app.app_context():
            reserved = util.is_reserved_name('project', 'test_project')
            assert reserved is False, reserved
            reserved = util.is_reserved_name('project', 'newProject')
            assert reserved is False, reserved


    def test_returns_true_for_reserved_name_for_account_blueprint(self):
        with self.app.app_context():
            reserved = util.is_reserved_name('account', 'register')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('account', 'forgot-password')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('account', 'profile')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('account', 'signin')
            assert reserved is True, reserved
            reserved = util.is_reserved_name('account', 'reset-password')
            assert reserved is True, reserved


    def test_returns_false_for_valid_name_for_account_blueprint(self):
        with self.app.app_context():
            reserved = util.is_reserved_name('account', 'fulanito')
            assert reserved is False, reserved
            reserved = util.is_reserved_name('acount', 'profileFulanito')
            assert reserved is False, reserved


    def test_returns_false_for_empty_name_string(self):
        with self.app.app_context():
            reserved = util.is_reserved_name('account', '')
            assert reserved is False, reserved



class TestWithCacheDisabledDecorator(object):

    def setUp(self):
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '0'

    def tearDown(self):
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'


    def test_it_returns_same_as_original_function(self):
        def original_func(first_value, second_value='world'):
            return 'first_value' + second_value

        decorated_func = util.with_cache_disabled(original_func)
        call_with_args = decorated_func('Hello, ')
        call_with_kwargs = decorated_func('Hello, ', second_value='there')

        assert call_with_args == original_func('Hello, '), call_with_args
        assert call_with_kwargs == original_func('Hello, ', second_value='there')


    def test_it_executes_function_with_cache_disabled(self):
        def original_func():
            return os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')

        decorated_func = util.with_cache_disabled(original_func)

        assert original_func() == '0', original_func()
        assert decorated_func() == '1', decorated_func()


    def test_it_executes_function_with_cache_disabled_triangulation(self):
        def original_func():
            return os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')

        del os.environ['PYBOSSA_REDIS_CACHE_DISABLED']
        decorated_func = util.with_cache_disabled(original_func)

        assert original_func() == None, original_func()
        assert decorated_func() == '1', decorated_func()


    def test_it_leaves_environment_as_it_was_before(self):
        @util.with_cache_disabled
        def decorated_func():
            return

        original_value = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')
        decorated_func()
        left_value = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')

        assert left_value == original_value, left_value


class TestUsernameFromFullnameFunction(object):

    def test_it_removes_whitespaces(self):
        name = "john benjamin toshack"
        expected_username = "johnbenjamintoshack"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_capital_letters(self):
        name = "JOHN"
        expected_username = "john"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_non_ascii_chars(self):
        name = "ßetaÑapa"
        expected_username = "etaapa"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_whitespaces_unicode(self):
        name = u"john benjamin toshack"
        expected_username = u"johnbenjamintoshack"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_capital_letters_unicode(self):
        name = u"JOHN"
        expected_username = u"john"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_non_ascii_chars_unicode(self):
        name = u"ßetaÑapa"
        expected_username = u"etaapa"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained


class TestRankProjects(object):

    def test_it_gives_priority_to_projects_with_an_avatar(self):
        projects = [{'info': {}, 'n_tasks': 4L, 'short_name': 'noavatar', 'name': u'with avatar', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {u'container': u'user_7', u'thumbnail': u'avatar.png'}, 'n_tasks': 4L, 'short_name': 'avatar', 'name': u'without avatar', 'overall_progress': 100L, 'n_volunteers': 1L}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == "with avatar"
        assert ranked[1]['name'] == "without avatar"

    def test_it_gives_priority_to_uncompleted_projects(self):
        projects = [{'info': {}, 'n_tasks': 4L, 'short_name': 'uncompleted', 'name': u'uncompleted', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 4L, 'short_name': 'completed', 'name': u'completed', 'overall_progress': 100L, 'n_volunteers': 1L}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == "uncompleted"
        assert ranked[1]['name'] == "completed"

    def test_it_penalizes_projects_with_test_in_the_name_or_short_name(self):
        projects = [{'info': {}, 'n_tasks': 4L, 'name': u'my test 123', 'short_name': u'123', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 246L, 'name': u'123', 'short_name': u'mytest123', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 246L, 'name': u'real', 'short_name': u'real', 'overall_progress': 0L, 'n_volunteers': 1L}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == "real"

    def test_rank_by_number_of_tasks(self):
        projects = [{'info': {}, 'n_tasks': 1L, 'name': u'last', 'short_name': u'a', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 11L, 'name': u'fourth', 'short_name': u'b', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 21L, 'name': u'third', 'short_name': u'c', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 51L, 'name': u'second', 'short_name': u'd', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 101L, 'name': u'first', 'short_name': u'e', 'overall_progress': 0L, 'n_volunteers': 1L}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == 'first'
        assert ranked[1]['name'] == 'second'
        assert ranked[2]['name'] == 'third'
        assert ranked[3]['name'] == 'fourth'
        assert ranked[4]['name'] == 'last'

    def test_rank_by_number_of_crafters(self):
        projects = [{'info': {}, 'n_tasks': 1L, 'name': u'last', 'short_name': u'a', 'overall_progress': 0L, 'n_volunteers': 0L},
                    {'info': {}, 'n_tasks': 1L, 'name': u'fifth', 'short_name': u'b', 'overall_progress': 0L, 'n_volunteers': 1L},
                    {'info': {}, 'n_tasks': 1L, 'name': u'fourth', 'short_name': u'b', 'overall_progress': 0L, 'n_volunteers': 11L},
                    {'info': {}, 'n_tasks': 1L, 'name': u'third', 'short_name': u'c', 'overall_progress': 0L, 'n_volunteers': 21L},
                    {'info': {}, 'n_tasks': 1L, 'name': u'second', 'short_name': u'd', 'overall_progress': 0L, 'n_volunteers': 51L},
                    {'info': {}, 'n_tasks': 1L, 'name': u'first', 'short_name': u'e', 'overall_progress': 0L, 'n_volunteers': 101L}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == 'first'
        assert ranked[1]['name'] == 'second'
        assert ranked[2]['name'] == 'third'
        assert ranked[3]['name'] == 'fourth'
        assert ranked[4]['name'] == 'fifth'
        assert ranked[5]['name'] == 'last'

    def test_rank_by_recent_updates_or_contributions(self):
        today = datetime.utcnow()
        yesterday = today - timedelta(1)
        two_days_ago = today - timedelta(2)
        three_days_ago = today - timedelta(3)
        four_days_ago = today - timedelta(4)
        projects = [{'info': {}, 'n_tasks': 1L, 'name': u'last', 'short_name': u'a', 'overall_progress': 0L, 'n_volunteers': 1L, 'last_activity_raw': four_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%f')},
                    {'info': {}, 'n_tasks': 1L, 'name': u'fourth', 'short_name': u'c', 'overall_progress': 0L, 'n_volunteers': 1L, 'last_activity_raw': three_days_ago.strftime('%Y-%m-%dT%H:%M:%S')},
                    {'info': {}, 'n_tasks': 1L, 'name': u'third', 'short_name': u'd', 'overall_progress': 0L, 'n_volunteers': 1L, 'updated': two_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%f')},
                    {'info': {}, 'n_tasks': 1L, 'name': u'second', 'short_name': u'e', 'overall_progress': 0L, 'n_volunteers': 1L, 'updated': yesterday.strftime('%Y-%m-%dT%H:%M:%S')},
                    {'info': {}, 'n_tasks': 1L, 'name': u'first', 'short_name': u'e', 'overall_progress': 0L, 'n_volunteers': 1L, 'updated': today.strftime('%Y-%m-%dT%H:%M:%S.%f')}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == 'first', ranked[0]['name']
        assert ranked[1]['name'] == 'second', ranked[1]['name']
        assert ranked[2]['name'] == 'third', ranked[2]['name']
        assert ranked[3]['name'] == 'fourth', ranked[3]['name']
        assert ranked[4]['name'] == 'last', ranked[4]['name']
