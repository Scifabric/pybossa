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
import pybossa.util as util
from mock import MagicMock
from mock import patch
from default import with_context, db, Test
from datetime import datetime, timedelta
from flask_wtf import Form
from factories import UserFactory
import calendar
import time
import csv
import tempfile
import os
import json
import base64
import hashlib


def myjsonify(data):
    return data


def myrender(template, **data):
    return template, data


class TestPybossaUtil(Test):

    # TODO: test this decorator in a more unitary way. The following tests have
    # been moved to test_api_common.py
    # def test_jsonpify(self):
    #     """Test jsonpify decorator works."""
    #     res = self.app.get('/api/app/1?callback=mycallback')
    #     err_msg = "mycallback should be included in the response"
    #     assert "mycallback" in res.data, err_msg
    #     err_msg = "Status code should be 200"
    #     assert res.status_code == 200, err_msg

    @with_context
    @patch('pybossa.util.hmac.HMAC')
    @patch('pybossa.util.base64.b64encode')
    def test_disqus_sso_payload_auth_user(self, mock_b64encode, mock_hmac):
        """Test Disqus SSO payload auth works."""
        user = UserFactory.create()

        DISQUS_PUBLIC_KEY = 'public'
        DISQUS_SECRET_KEY = 'secret'
        patch_dict = {'DISQUS_PUBLIC_KEY': DISQUS_PUBLIC_KEY,
                      'DISQUS_SECRET_KEY': DISQUS_SECRET_KEY}
        data = json.dumps({'id': user.id,
                           'username': user.name,
                           'email': user.email_addr})

        mock_b64encode.return_value = data

        with patch.dict(self.flask_app.config, patch_dict):
            message, timestamp, sig, pub_key = util.get_disqus_sso_payload(user)
            mock_b64encode.assert_called_with(data.encode('utf-8'))
            tmp = '{} {}'.format(data, timestamp)
            mock_hmac.assert_called_with(DISQUS_SECRET_KEY.encode('utf-8'), tmp.encode('utf-8'),
                                         hashlib.sha1)
            assert timestamp
            assert sig
            assert pub_key == DISQUS_PUBLIC_KEY

    @with_context
    @patch('pybossa.util.hmac.HMAC')
    @patch('pybossa.util.base64.b64encode')
    def test_disqus_sso_payload_auth_user_no_keys(self, mock_b64encode, mock_hmac):
        """Test Disqus SSO without keys works."""
        user = UserFactory.create()
        message, timestamp, sig, pub_key = util.get_disqus_sso_payload(user)
        assert message is None
        assert timestamp is None
        assert sig is None
        assert pub_key is None


    @with_context
    @patch('pybossa.util.hmac.HMAC')
    @patch('pybossa.util.base64.b64encode')
    def test_disqus_sso_payload_anon_user(self, mock_b64encode, mock_hmac):
        """Test Disqus SSO payload anon works."""

        DISQUS_PUBLIC_KEY = 'public'
        DISQUS_SECRET_KEY = 'secret'
        patch_dict = {'DISQUS_PUBLIC_KEY': DISQUS_PUBLIC_KEY,
                      'DISQUS_SECRET_KEY': DISQUS_SECRET_KEY}

        data = json.dumps({})

        mock_b64encode.return_value = data

        with patch.dict(self.flask_app.config, patch_dict):
            message, timestamp, sig, pub_key = util.get_disqus_sso_payload(None)
            mock_b64encode.assert_called_with(data.encode('utf-8'))
            tmp = '{} {}'.format(data, timestamp)
            mock_hmac.assert_called_with(DISQUS_SECRET_KEY.encode('utf-8'),
                                         tmp.encode('utf-8'),
                                         hashlib.sha1)
            assert timestamp
            assert sig
            assert pub_key == DISQUS_PUBLIC_KEY


    @with_context
    def test_disqus_sso_payload_anon_user_no_keys(self):
        """Test Disqus SSO without keys anon works."""
        message, timestamp, sig, pub_key = util.get_disqus_sso_payload(None)
        assert message is None
        assert timestamp is None
        assert sig is None
        assert pub_key is None


    @patch('pybossa.util.get_flashed_messages')
    def test_last_flashed_messages(self, mockflash):
        """Test last_flashed_message returns the last one."""
        messages = ['foo', 'bar']
        mockflash.return_value = messages
        msg = util.last_flashed_message()
        err_msg = "It should be the last message"
        assert msg == messages[-1], err_msg

    @patch('pybossa.util.get_flashed_messages')
    def test_last_flashed_messages_none(self, mockflash):
        """Test last_flashed_message returns the none."""
        messages = []
        mockflash.return_value = messages
        msg = util.last_flashed_message()
        err_msg = "It should be None"
        assert msg is None, err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    @patch('pybossa.util.last_flashed_message')
    def test_handle_content_type_json(self, mocklast, mockjsonify,
                                      mockrender, mockrequest):
        fake_d = {'Content-Type': 'application/json'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        res = util.handle_content_type(dict(template='example.html'))
        err_msg = "template key should exist"
        assert res.get('template') == 'example.html', err_msg
        err_msg = "jsonify should be called"
        assert mockjsonify.called, err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    @patch('pybossa.util.last_flashed_message')
    def test_handle_content_type_json_error(self, mocklast, mockjsonify,
                                            mockrender, mockrequest):
        fake_d = {'Content-Type': 'application/json'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        res, code = util.handle_content_type(
                                             dict(
                                                 template='example.html',
                                                 code=404,
                                                 description="Not found"))
        err_msg = "template key should exist"
        assert res.get('template') == 'example.html', err_msg
        err_msg = "jsonify should be called"
        assert mockjsonify.called, err_msg
        err_msg = "Error code should exist"
        assert res.get('code') == 404, err_msg
        assert code == 404, err_msg
        err_msg = "Error description should exist"
        assert res.get('description') is not None, err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    @patch('pybossa.util.generate_csrf')
    @patch('pybossa.util.last_flashed_message')
    def test_handle_content_type_json_form(self, mocklast, mockcsrf,
                                           mockjsonify, mockrender,
                                           mockrequest):
        fake_d = {'Content-Type': 'application/json'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        mockcsrf.return_value = "yourcsrf"
        form = MagicMock(spec=Form, data=dict(foo=1), errors=None)
        res = util.handle_content_type(dict(template='example.html',
                                            form=form))
        err_msg = "template key should exist"
        assert res.get('template') == 'example.html', err_msg
        err_msg = "jsonify should be called"
        assert mockjsonify.called, err_msg
        err_msg = "Form should exist"
        assert res.get('form'), err_msg
        err_msg = "Form should have a csrf key/value"
        assert res.get('form').get('csrf') == 'yourcsrf', err_msg
        err_msg = "There should be the keys of the form"
        keys = ['foo', 'errors', 'csrf']
        assert list(res.get('form').keys()).sort() == keys.sort(), err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    @patch('pybossa.util.last_flashed_message')
    def test_handle_content_type_json_pagination(self, mocklast, mockjsonify,
                                                 mockrender, mockrequest):
        fake_d = {'Content-Type': 'application/json'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        pagination = util.Pagination(page=1, per_page=5, total_count=10)
        res = util.handle_content_type(dict(template='example.html',
                                            pagination=pagination))
        err_msg = "template key should exist"
        assert res.get('template') == 'example.html', err_msg
        err_msg = "jsonify should be called"
        assert mockjsonify.called, err_msg
        err_msg = "Pagination should exist"
        assert res.get('pagination') is not None, err_msg
        assert res.get('pagination') == pagination.to_json(), err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    def test_handle_content_type_html(self, mockjsonify,
                                      mockrender, mockrequest):
        fake_d = {'Content-Type': 'text/html'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        mockrender.side_effect = myrender
        pagination = util.Pagination(page=1, per_page=5, total_count=10)
        template, data = util.handle_content_type(dict(template='example.html',
                                                       pagination=pagination))
        err_msg = "Template should be rendered"
        assert template == 'example.html', err_msg
        err_msg = "Template key should not exist"
        assert data.get('template') is None, err_msg
        err_msg = "jsonify should not be called"
        assert mockjsonify.called is False, err_msg
        err_msg = "render_template should be called"
        assert mockrender.called is True, err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    def test_handle_content_type_html_error(self, mockjsonify,
                                            mockrender, mockrequest):
        fake_d = {'Content-Type': 'text/html'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        mockrender.side_effect = myrender
        template, code = util.handle_content_type(dict(template='example.html',
                                                       code=404))
        data = template[1]
        template = template[0]
        err_msg = "Template should be rendered"
        assert template == 'example.html', err_msg
        err_msg = "Template key should not exist"
        assert data.get('template') is None, err_msg
        err_msg = "jsonify should not be called"
        assert mockjsonify.called is False, err_msg
        err_msg = "render_template should be called"
        assert mockrender.called is True, err_msg
        err_msg = "There should be an error"
        assert code == 404, err_msg
        err_msg = "There should not be code key"
        assert data.get('code') is None, err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    @patch('pybossa.util.last_flashed_message')
    def test_redirect_content_type_json(
        self,
        mocklast,
        mockjsonify,
        mockrender,
     mockrequest):
        fake_d = {'Content-Type': 'application/json'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        res = util.redirect_content_type('http://next.uri')
        err_msg = "next URI is wrong in redirction"
        assert res.get('next') == 'http://next.uri', err_msg
        err_msg = "jsonify should be called"
        assert mockjsonify.called, err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    @patch('pybossa.util.last_flashed_message')
    def test_redirect_content_type_json_message(
            self, mocklast, mockjsonify, mockrender, mockrequest):
        mocklast.return_value = None
        fake_d = {'Content-Type': 'application/json'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        res = util.redirect_content_type('http://next.uri', status='hallo123')
        err_msg = "next URI is wrong in redirction"
        assert res.get('next') == 'http://next.uri', err_msg
        err_msg = "jsonify should be called"
        assert mockjsonify.called, err_msg
        err_msg = "status should exist"
        assert res.get('status') == 'hallo123', err_msg

    @with_context
    @patch('pybossa.util.request')
    @patch('pybossa.util.render_template')
    @patch('pybossa.util.jsonify')
    def test_redirect_content_type_json_html(
            self, mockjsonify, mockrender, mockrequest):
        fake_d = {'Content-Type': 'text/html'}
        mockrequest.headers.__getitem__.side_effect = fake_d.__getitem__
        mockrequest.headers.get.side_effect = fake_d.get
        mockrequest.headers.__iter__.side_effect = fake_d.__iter__
        mockjsonify.side_effect = myjsonify
        res = util.redirect_content_type('/')
        err_msg = "redirect 302 should be the response"
        assert res.status_code == 302, err_msg
        err_msg = "redirect to / should be done"
        assert res.location == "/", err_msg
        err_msg = "jsonify should not be called"
        assert mockjsonify.called is False, err_msg

    @with_context
    @patch('pybossa.util.url_for')
    def test_url_for_app_type_spa(self, mock_url_for):
        """Test that the correct SPA URL is returned"""
        spa_name = 'http://local.com'
        fake_endpoint = '/example'
        mock_url_for.return_value = fake_endpoint
        with patch.dict(self.flask_app.config, {'SPA_SERVER_NAME': spa_name}):
            spa_url = util.url_for_app_type('home.home')
            expected = spa_name + fake_endpoint
            assert spa_url == expected, spa_url

    @with_context
    @patch('pybossa.util.url_for')
    @patch('pybossa.util.hash_last_flash_message')
    def test_url_for_app_type_spa_with_hashed_flash(self, mock_hash_last_flash, mock_url_for):
        """Test that the hashed flash is returned with the SPA URL"""
        flash = 'foo'
        endpoint = 'bar'
        mock_hash_last_flash.return_value = flash
        with patch.dict(self.flask_app.config, {'SPA_SERVER_NAME': 'example.com'}):
            util.url_for_app_type(endpoint, _hash_last_flash=True)
            err = "Hashed flash should be included"
            mock_url_for.assert_called_with(endpoint, flash=flash), err

    @with_context
    @patch('pybossa.util.url_for')
    def test_url_for_app_type_mvc(self, mock_url_for):
        """Test that the correct MVC URL is returned"""
        fake_endpoint = '/example'
        mock_url_for.return_value = fake_endpoint
        spa_url = util.url_for_app_type('home.home')
        assert spa_url == fake_endpoint, spa_url

    @with_context
    @patch('pybossa.util.url_for')
    @patch('pybossa.util.hash_last_flash_message')
    def test_url_for_app_type_mvc_with_hashed_flash(self, mock_hash_last_flash, mock_url_for):
        """Test that the hashed flash is not returned with the MVC URL"""
        endpoint = 'bar'
        util.url_for_app_type(endpoint, _hash_last_flash=True)
        mock_url_for.assert_called_with(endpoint)
        err = "Hashed flash should not be called"
        assert not mock_hash_last_flash.called, err

    @patch('pybossa.util.last_flashed_message')
    def test_last_flashed_message_hashed(self, last_flash):
        """Test the last flash message is hashed."""
        message_and_status = ['foo', 'bar']
        last_flash.return_value = message_and_status
        tmp = json.dumps({
            'flash': message_and_status[1],
            'status': message_and_status[0]
        })
        expected = base64.b64encode(tmp.encode('utf-8'))
        hashed_flash = util.hash_last_flash_message()
        assert hashed_flash == expected

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

        err_msg = "It should return JSON"
        expected = dict(page=page-1,
                        per_page=per_page,
                        total=total_count,
                        next=False,
                        prev=True)
        assert expected == p.to_json(), err_msg

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
        assert call_with_kwargs == original_func(
            'Hello, ', second_value='there')

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
        expected_username = b"johnbenjamintoshack"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_capital_letters(self):
        name = "JOHN"
        expected_username = b'john'

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, (obtained, expected_username)

    def test_it_removes_non_ascii_chars(self):
        name = "ßetaÑapa"
        expected_username = b"etaapa"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_whitespaces_unicode(self):
        name = "john benjamin toshack"
        expected_username = b"johnbenjamintoshack"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_capital_letters_unicode(self):
        name = "JOHN"
        expected_username = b"john"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained

    def test_it_removes_non_ascii_chars_unicode(self):
        name = "ßetaÑapa"
        expected_username = b"etaapa"

        obtained = util.username_from_full_name(name)

        assert obtained == expected_username, obtained


class TestRankProjects(object):

    def test_it_gives_priority_to_projects_with_an_avatar(self):
        projects = [
            {'info': {},
             'n_tasks': 4, 'short_name': 'noavatar', 'name': 'with avatar',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {'container': 'user_7', 'thumbnail': 'avatar.png'},
             'n_tasks': 4, 'short_name': 'avatar', 'name': 'without avatar',
             'overall_progress': 100, 'n_volunteers': 1}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == "with avatar"
        assert ranked[1]['name'] == "without avatar"

    def test_it_gives_priority_to_uncompleted_projects(self):
        projects = [{'info': {},
                     'n_tasks': 4,
                     'short_name': 'uncompleted',
                     'name': 'uncompleted',
                     'overall_progress': 0,
                     'n_volunteers': 1},
                    {'info': {},
                     'n_tasks': 4,
                     'short_name': 'completed',
                     'name': 'completed',
                     'overall_progress': 100,
                     'n_volunteers': 1}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == "uncompleted"
        assert ranked[1]['name'] == "completed"

    def test_it_penalizes_projects_with_test_in_the_name_or_short_name(self):
        projects = [{'info': {},
                     'n_tasks': 4,
                     'name': 'my test 123',
                     'short_name': '123',
                     'overall_progress': 0,
                     'n_volunteers': 1},
                    {'info': {},
                     'n_tasks': 246,
                     'name': '123',
                     'short_name': 'mytest123',
                     'overall_progress': 0,
                     'n_volunteers': 1},
                    {'info': {},
                     'n_tasks': 246,
                     'name': 'real',
                     'short_name': 'real',
                     'overall_progress': 0,
                     'n_volunteers': 1}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == "real"

    def test_rank_by_number_of_tasks(self):
        projects = [
            {'info': {},
             'n_tasks': 1, 'name': 'last', 'short_name': 'a',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 11, 'name': 'fourth', 'short_name': 'b',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 21, 'name': 'third', 'short_name': 'c',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 51, 'name': 'second', 'short_name': 'd',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 101, 'name': 'first', 'short_name': 'e',
             'overall_progress': 0, 'n_volunteers': 1}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == 'first'
        assert ranked[1]['name'] == 'second'
        assert ranked[2]['name'] == 'third'
        assert ranked[3]['name'] == 'fourth'
        assert ranked[4]['name'] == 'last'

    def test_rank_by_number_of_crafters(self):
        projects = [
            {'info': {},
             'n_tasks': 1, 'name': 'last', 'short_name': 'a',
             'overall_progress': 0, 'n_volunteers': 0},
            {'info': {},
             'n_tasks': 1, 'name': 'fifth', 'short_name': 'b',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 1, 'name': 'fourth', 'short_name': 'b',
             'overall_progress': 0, 'n_volunteers': 11},
            {'info': {},
             'n_tasks': 1, 'name': 'third', 'short_name': 'c',
             'overall_progress': 0, 'n_volunteers': 21},
            {'info': {},
             'n_tasks': 1, 'name': 'second', 'short_name': 'd',
             'overall_progress': 0, 'n_volunteers': 51},
            {'info': {},
             'n_tasks': 1, 'name': 'first', 'short_name': 'e',
             'overall_progress': 0, 'n_volunteers': 101}]
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
        projects = [{'info': {},
                     'n_tasks': 1, 'name': 'last', 'short_name': 'a',
                     'overall_progress': 0, 'n_volunteers': 1,
                     'last_activity_raw': four_days_ago.strftime(
                         '%Y-%m-%dT%H:%M:%S.%f')},
                    {'info': {},
                     'n_tasks': 1, 'name': 'fourth', 'short_name': 'c',
                     'overall_progress': 0, 'n_volunteers': 1,
                     'last_activity_raw': three_days_ago.strftime(
                         '%Y-%m-%dT%H:%M:%S')},
                    {'info': {},
                     'n_tasks': 1, 'name': 'third', 'short_name': 'd',
                     'overall_progress': 0, 'n_volunteers': 1,
                     'updated': two_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%f')},
                    {'info': {},
                     'n_tasks': 1, 'name': 'second', 'short_name': 'e',
                     'overall_progress': 0, 'n_volunteers': 1,
                     'updated': yesterday.strftime('%Y-%m-%dT%H:%M:%S')},
                    {'info': {},
                     'n_tasks': 1, 'name': 'first', 'short_name': 'e',
                     'overall_progress': 0, 'n_volunteers': 1,
                     'updated': today.strftime('%Y-%m-%dT%H:%M:%S.%f')}]
        ranked = util.rank(projects)

        assert ranked[0]['name'] == 'first', ranked[0]['name']
        assert ranked[1]['name'] == 'second', ranked[1]['name']
        assert ranked[2]['name'] == 'third', ranked[2]['name']
        assert ranked[3]['name'] == 'fourth', ranked[3]['name']
        assert ranked[4]['name'] == 'last', ranked[4]['name']

    def test_rank_by_chosen_attribute(self):
        projects = [
            {'info': {},
             'n_tasks': 1, 'name': 'last', 'short_name': 'a',
             'overall_progress': 0, 'n_volunteers': 10},
            {'info': {},
             'n_tasks': 11, 'name': 'fourth', 'short_name': 'b',
             'overall_progress': 0, 'n_volunteers': 25},
            {'info': {},
             'n_tasks': 21, 'name': 'third', 'short_name': 'c',
             'overall_progress': 0, 'n_volunteers': 15},
            {'info': {},
             'n_tasks': 51, 'name': 'second', 'short_name': 'd',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 101, 'name': 'first', 'short_name': 'e',
             'overall_progress': 0, 'n_volunteers': 5}]
        ranked = util.rank(projects, order_by='n_volunteers')

        assert ranked[0]['name'] == 'second'
        assert ranked[1]['name'] == 'first'
        assert ranked[2]['name'] == 'last'
        assert ranked[3]['name'] == 'third'
        assert ranked[4]['name'] == 'fourth'

    def test_rank_by_chosen_attribute_reversed(self):
        projects = [
            {'info': {},
             'n_tasks': 1, 'name': 'last', 'short_name': 'a',
             'overall_progress': 0, 'n_volunteers': 1},
            {'info': {},
             'n_tasks': 11, 'name': 'fourth', 'short_name': 'b',
             'overall_progress': 0, 'n_volunteers': 5},
            {'info': {},
             'n_tasks': 21, 'name': 'third', 'short_name': 'c',
             'overall_progress': 0, 'n_volunteers': 10},
            {'info': {},
             'n_tasks': 51, 'name': 'second', 'short_name': 'd',
             'overall_progress': 0, 'n_volunteers': 20},
            {'info': {},
             'n_tasks': 101, 'name': 'first', 'short_name': 'e',
             'overall_progress': 0, 'n_volunteers': 30}]
        ranked = util.rank(projects, order_by='n_volunteers', desc=True)

        assert ranked[0]['name'] == 'first'
        assert ranked[1]['name'] == 'second'
        assert ranked[2]['name'] == 'third'
        assert ranked[3]['name'] == 'fourth'
        assert ranked[4]['name'] == 'last'

    @with_context
    @patch('pybossa.util.url_for')
    def test_get_avatar_url(self, mock_url_for):
        """Test get_avatar_url works."""
        util.get_avatar_url('rackspace', '1.png', '1', True)
        mock_url_for.assert_called_with('rackspace', container='1', filename='1.png')

        util.get_avatar_url('local', '1.png', '1', True)
        mock_url_for.assert_called_with('uploads.uploaded_file',
                                        _external=True,
                                        _scheme='https',
                                        filename='1/1.png')

        util.get_avatar_url('local', '1.png', '1', False)
        mock_url_for.assert_called_with('uploads.uploaded_file',
                                        _external=False,
                                        _scheme='https',
                                        filename='1/1.png')



class TestJSONEncoder(object):

    def test_jsonencoder(self):
        """Test JSON encoder."""
        from pybossa.extensions import JSONEncoder
        from speaklater import make_lazy_string
        encoder = JSONEncoder()
        sval = "Hello world"
        string = make_lazy_string(lambda: sval)

        encoder = JSONEncoder()

        data = encoder.encode(dict(foo=string))
        data = json.loads(data)
        err_msg = "The encoder should manage lazystrings"
        assert data.get('foo') == sval, err_msg


class TestStrongPassword(object):

    def test_strong_password_missing_special_char(self):
        password = 'Abcd12345'
        valid, _ = util.check_password_strength(password=password)
        assert not valid

    def test_strong_password_missing_uppercase(self):
        password = 'abcd12345!'
        valid, _ = util.check_password_strength(password=password)
        assert not valid

    def test_strong_password_missing_lowercase(self):
        password = 'ABCD12345!'
        valid, _ = util.check_password_strength(password=password)
        assert not valid

    def test_strong_password_missing_lowercase(self):
        password = 'ABCD12345!'
        valid, _ = util.check_password_strength(password=password)
        assert not valid

    def test_strong_password_min_length(self):
        password = 'abc'
        valid, _ = util.check_password_strength(password=password)
        assert not valid

    def test_valid_strong_password_works(self):
        password = 'AaBbCD12345!'
        valid, _ = util.check_password_strength(password=password)
        assert valid
