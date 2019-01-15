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
from pybossa.view.facebook import manage_user, manage_user_login
from mock import patch
from factories import UserFactory
from pybossa.util import username_from_full_name
from pybossa.core import newsletter


class TestFacebook(Test):

    def setUp(self):
        super(TestFacebook, self).setUp()
        self.user_data = {
            "id": 1234567890,
            "email": 'me@facebook.com',
            "first_name": 'Mauricio',
            "last_name": 'Perez Sanchez',
            "name": 'Mauricio Perez Sanchez'
        }
        self.name = username_from_full_name(self.user_data['name'])
        newsletter.app = None

    @with_context
    def test_manage_user_with_email_new_user(self):
        """Test FACEBOOK manage_user works for a new user."""
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name.decode('utf-8'), user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user
        assert user.info['facebook_token'] == dict(oauth_token=token), user

    @with_context
    def test_manage_user_with_email_facebook_account_user_registered(self):
        """Test FACEBOOK manage_user works for a user already registered with Facebook."""
        token = 't'
        manage_user(token, self.user_data)
        new_token = 'new_token'
        user = manage_user(new_token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        print(user.name, self.name)
        assert user.name == self.name.decode('utf-8'), user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user
        assert user.info['facebook_token'] == dict(oauth_token=new_token), user

    @with_context
    def test_manage_user_without_email_new_user(self):
        """Test FACEBOOK manage_user works for a new user without email in his
        FB account."""
        del self.user_data['email']
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name.decode('utf-8'), user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user
        assert user.info['facebook_token'] == dict(oauth_token=token), user

    @with_context
    def test_manage_user_without_email_facebook_account_user_registered(self):
        """Test FACEBOOK manage_user works for a user already registered with
        Facebook without email on his FB account."""
        del self.user_data['email']
        token = 't'
        manage_user(token, self.user_data)
        new_token = 'new_token'
        user = manage_user(new_token, self.user_data)
        print(user.email_addr, self.user_data['email'])
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name.decode('utf-8'), user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user
        assert user.info['facebook_token'] == dict(oauth_token=new_token), user

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    def test_manage_user_with_email_newsletter(self, newsletter):
        """Test FACEBOOK manage_user newsletter works."""
        newsletter.app = True
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name.decode('utf-8'), user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user

        newsletter.subscribe_user.assert_called_once_with(user)

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    def test_manage_user_without_email_newsletter(self, newsletter):
        """Test FACEBOOK manage_user without e-mail newsletter works."""
        newsletter.app = True
        del self.user_data['email']
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name.decode('utf-8'), user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user
        err_msg = "It should not be called."
        assert newsletter.subscribe_user.called is False, err_msg

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_local(self, redirect,
                                     url_for_app_type, flash,
                                     login_user,
                                     newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user = UserFactory.create()
        user_data = dict(name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for_app_type.assert_called_once_with('account.forgot_password',
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_google_token(self, redirect,
                                            url_for_app_type, flash,
                                            login_user,
                                            newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user = UserFactory.create(info={'google_token': 'k'})
        user_data = dict(name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for_app_type.assert_called_once_with('account.signin',
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_empty(self, redirect,
                                     url_for_app_type, flash,
                                     login_user,
                                     newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user_data = dict(name='algo', email='email')
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for_app_type.assert_called_once_with('account.signin',
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_empty_no_email(self, redirect,
                                              url_for_app_type, flash,
                                              login_user,
                                              newsletter):
        """Test manage login user new user with no email from facebook"""
        newsletter.app = True
        user_data = dict(name='algo')
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for_app_type.assert_called_once_with('account.signin',
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_update_email(self, redirect,
                                            url_for_app_type, flash,
                                            login_user,
                                            newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user = UserFactory.create(name='johndoe', email_addr='johndoe')
        user_data = dict(name=user.name)
        next_url = '/'
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        redirect.assert_called_once_with('/')

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_good_email(self, redirect,
                                          url_for_app_type, flash,
                                          login_user,
                                          newsletter):
        """Test manage login user with good email works."""
        newsletter.app = True
        user = UserFactory.create()
        user_data = dict(name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for_app_type.assert_called_once_with('account.newsletter_subscribe',
                                                 next=next_url,
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for_app_type', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_already_asked(self, redirect,
                                             url_for_app_type, flash,
                                             login_user,
                                             newsletter):
        """Test manage login user already asked works."""
        newsletter.app = True
        user = UserFactory.create(newsletter_prompted=True)
        user_data = dict(name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        redirect.assert_called_once_with(next_url)
