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
import json
from flask import Response
from default import with_context, Test
from mock import patch, MagicMock
from pybossa.messages import *
from pybossa.core import user_repo
from factories import UserFactory


class TestLDAP(Test):

    ldap_user = dict(cn=['cn'], givenName=['John Doe'],
                     uid=['johndoe'])

    @with_context
    def test_register_404(self):
        """Test register is disabled for ldap."""
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            url = '/account/register'
            res = self.app_get_json(url)
            data = json.loads(res.data)
            assert data['code'] == 404, data

    @with_context
    def test_account_signin(self):
        """Test signin."""
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            url = '/account/signin'
            res = self.app_get_json(url)
            data = json.loads(res.data)
            assert data['form']['csrf'] is not None, data
            assert data['auth']['twitter'] is False, data
            assert data['auth']['facebook'] is False, data
            assert data['auth']['google'] is False, data

    @with_context
    @patch('pybossa.view.account.ldap')
    def test_signin_create(self, ldap_mock):
        """Test signin creates a PYBOSSA user."""
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            url = '/account/signin'
            payload = {'email': 'cn', 'password': 'password'}
            ldap_mock.bind_user.return_value = True
            ldap_mock.get_object_details.return_value = self.ldap_user
            res = self.app.post(url, data=json.dumps(payload),
                                content_type='application/json')
            user = user_repo.get_by(ldap='cn')
            data = json.loads(res.data)
            assert data['status'] == SUCCESS, data
            assert data['next'] == '/', data
            assert user.name == self.ldap_user['uid'][0], user
            assert user.email_addr == self.ldap_user['cn'][0], user

            ldap_mock.bind_user.return_value = False
            res = self.app.post(url, data=json.dumps(payload),
                                content_type='application/json')
            data = json.loads(res.data)
            msg = 'User LDAP credentials are wrong.'
            assert data['flash'] == msg, data
            assert data['status'] == 'info', data

    @with_context
    @patch('pybossa.view.account._create_account')
    @patch('pybossa.view.account.ldap')
    def test_signin_existing(self, ldap_mock, create_mock):
        """Test signin logs in an LDAP existing PYBOSSA user."""
        user = UserFactory.create(name='cn', email_addr='cn', ldap='cn')
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            url = '/account/signin'
            payload = {'email': 'cn', 'password': 'password'}
            ldap_mock.bind_user.return_value = True
            ldap_mock.get_object_details.return_value = self.ldap_user
            res = self.app.post(url, data=json.dumps(payload),
                                content_type='application/json')
            user = user_repo.get_by(ldap='cn')
            data = json.loads(res.data)
            assert data['next'] == '/', data
            assert create_mock.called is False

    @with_context
    def test_twitter_login(self):
        """Test Twitter login is disabled."""
        url = '/twitter/'
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            res = self.app.get(url)
            assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.view.twitter.url_for')
    @patch('pybossa.view.twitter.twitter.oauth')
    def test_twitter_no_login(self, mock_twitter, url_for_mock):
        """Test Twitter no_login arg allows using Twitter importer."""
        url = '/twitter/?no_login=1'
        mock_twitter.authorize.return_value = 'OK'
        url_for_mock.return_value = 'url'
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            res = self.app.get(url)
            assert res.data == b'OK'
            assert mock_twitter.authorize.called_with('url')

    @with_context
    def test_facebook_login(self):
        """Test Facebook login is disabled."""
        url = '/facebook/'
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            res = self.app.get(url)
            assert res.status_code == 404, res.status_code

    @with_context
    def test_google_login(self):
        """Test Google login is disabled."""
        url = '/google/'
        with patch.dict(self.flask_app.config, {'LDAP_HOST': '127.0.0.1'}):
            res = self.app.get(url)
            assert res.status_code == 404, res.status_code
