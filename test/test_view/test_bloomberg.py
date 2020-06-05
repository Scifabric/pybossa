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
from default import Test, with_context
from mock import patch
from mock import MagicMock
from factories import UserFactory
from pybossa.view import bloomberg as bb


class TestBloomberg(Test):
    def setUp(self):
        super(TestBloomberg, self).setUp()

    @with_context
    def test_login_get(self):
        res = self.app.get('/bloomberg/login')
        redirect_url = self.flask_app.config['BSSO_SETTINGS']['idp']['singleSignOnService']['url']
        assert res.status_code == 302, res.status_code
        assert res.headers['Location'].startswith(redirect_url), res.headers

    @with_context
    @patch('pybossa.view.bloomberg.OneLogin_Saml2_Auth', autospec=True)
    def test_login_post_errors(self, mock):
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = True
        mock.return_value = mock_auth
        res = self.app.post('/bloomberg/login')
        assert res.status_code == 302, res.status_code

    @with_context
    @patch('pybossa.view.bloomberg.OneLogin_Saml2_Auth', autospec=True)
    def test_login_post_success(self, mock_one_login):
        user = UserFactory.create()
        redirect_url = 'http://localhost'
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = False
        mock_auth.is_authenticated.return_value = True
        mock_auth.get_attributes.return_value = {'emailAddress': [user.email_addr]}
        mock_one_login.return_value = mock_auth
        res = self.app.post('/bloomberg/login', content_type='multipart/form-data', data={'RelayState': redirect_url})
        assert res.status_code == 302, res.status_code
        assert res.headers['Location'] == redirect_url, res.headers

    @with_context
    @patch('pybossa.view.bloomberg.OneLogin_Saml2_Auth', autospec=True)
    def test_login_post_not_authenticated(self, mock_one_login):
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = False
        mock_auth.is_authenticated.return_value = False
        mock_one_login.return_value = mock_auth
        res = self.app.post('/bloomberg/login')
        assert res.status_code == 302, res.status_code

    @with_context
    @patch('pybossa.view.account._sign_in_user', autospec=True)
    @patch('pybossa.view.account.create_account', autospec=True)
    @patch('pybossa.view.bloomberg.OneLogin_Saml2_Auth', autospec=True)
    def test_login_create_account_fail(self, mock_one_login, mock_create_account, mock_sign_in):
        redirect_url = 'http://localhost'
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = False
        mock_auth.process_response.return_value = None
        mock_auth.is_authenticated = False
        mock_one_login.return_value = mock_auth
        mock_auth.get_attributes.return_value = {'UUID': [u'1234567'], 'FirstName': [u'test'], 'LastName': [u'test'], 'PVFLevels': [u'PVF_GUTS_3'], 'LoginID': [u'test']}
        mock_create_account.return_value = None
        res = self.app.post('/bloomberg/login', method='POST', content_type='multipart/form-data', data={'RelayState': redirect_url})
        assert res.status_code == 302, res.status_code

    @with_context
    @patch('pybossa.view.account._sign_in_user', autospec=True)
    @patch('pybossa.view.account.create_account', autospec=True)
    @patch('pybossa.view.bloomberg.OneLogin_Saml2_Auth', autospec=True)
    def test_login_create_account_success(self, mock_one_login, mock_create_account, mock_sign_in):
        redirect_url = 'http://localhost'
        mock_auth = MagicMock()
        mock_auth.get_errors.return_value = False
        mock_auth.process_response.return_value = None
        mock_auth.is_authenticated = False #Are all these other tests not working correctly?  "return_value" was not working for me
        mock_one_login.return_value = mock_auth
        mock_auth.get_attributes.return_value = {'UUID': [u'1234567'], 'FirstName': [u'test'], 'LastName': [u'test'], 'PVFLevels': [u'PVF_GUTS_3'], 'emailAddress': [u'test@bloomberg.net'], 'LoginID': [u'test']}
        mock_create_account.return_value = None
        res = self.app.post('/bloomberg/login', method='POST', content_type='multipart/form-data', data={'RelayState': redirect_url})
        assert res.status_code == 302, res.status_code
        assert res.headers['Location'] == redirect_url, res.headers