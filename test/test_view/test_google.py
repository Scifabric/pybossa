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
from pybossa.view.google import manage_user, manage_user_login, google
from mock import patch
from factories import UserFactory


class TestGoogle(Test):

    @with_context
    def test_manage_user_new_user(self):
        """Test GOOGLE manage_user with a new user"""
        user_data = dict(id='1', name='google', email='g@g.com')
        token = 't'
        user = manage_user(token, user_data)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user.name
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user
        assert user.info['google_token'] == dict(oauth_token=token), user

    @with_context
    def test_manage_user_twitter_registered_user(self):
        """Test GOOGLE manage_user with an existing user registered with Google"""
        user_data = dict(id='1', name='google', email='g@g.com')
        token = 't'
        user = manage_user(token, user_data)
        print(user.name, user.email_addr)
        new_token = "new_t"
        user = manage_user(new_token, user_data)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user
        assert user.info['google_token'] == dict(oauth_token=new_token), user

    @with_context
    def test_manage_user_with_existing_non_twitter_account_user(self):
        """Test GOOGLE manage_user user with a username that already exists
        and registered without Google"""
        user_data = dict(id='10', name=self.name, email=self.email_addr)
        token = 'tA'
        user = manage_user(token, user_data)
        err_msg = "User should be the same"
        assert user.google_user_id == '10', err_msg
        assert user.info['google_token'] == dict(oauth_token=token), user

    @with_context
    @patch('pybossa.view.google.newsletter', autospec=True)
    def test_manage_user_with_newsletter(self, newsletter):
        """Test GOOGLE manage_user with newsletter works."""
        # First with a new user
        newsletter.app = True
        user_data = dict(id='1', name='google',
                         email='g@g.com')
        token = 't'
        user = manage_user(token, user_data)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user
        newsletter.subscribe_user.assert_called_once_with(user)

    @with_context
    @patch('pybossa.view.google.newsletter', autospec=True)
    def test_manage_user_with_newsletter_only_once(self, newsletter):
        """Test GOOGLE manage_user with newsletter only once works."""
        # Second with the same user
        token = 't'
        user = UserFactory.create(fullname='john', name='john',
                                  google_user_id='1')
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        r_user = manage_user(token, user_data)
        assert r_user.email_addr == user_data['email'], user
        assert r_user.name == user_data['name'], user
        assert r_user.fullname == user_data['name'], user
        assert r_user.google_user_id == user_data['id'], user
        assert newsletter.subscribe_user.called is False, newsletter.subscribe_user.called

    @with_context
    @patch('pybossa.view.google.newsletter', autospec=True)
    @patch('pybossa.view.google.login_user', return_value=True)
    @patch('pybossa.view.google.flash', return_value=True)
    @patch('pybossa.view.google.url_for_app_type', return_value=True)
    @patch('pybossa.view.google.redirect', return_value=True)
    def test_manage_user_with_oauth_newsletter(self, redirect,
                                               url_for_app_type, flash,
                                               login_user,
                                               newsletter):
        """Test GOOGLE manage_user_login shows newsletter works."""
        user = UserFactory.create(fullname='john', name='john',
                                  google_user_id='1')
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(user, user_data, next_url=next_url)
        login_user.assert_called_with(user, remember=True)
        assert user.newsletter_prompted is False
        url_for_app_type.assert_called_with('account.newsletter_subscribe',
                                            next=next_url, _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.google.newsletter', autospec=True)
    @patch('pybossa.view.google.login_user', return_value=True)
    @patch('pybossa.view.google.flash', return_value=True)
    @patch('pybossa.view.google.url_for_app_type', return_value=True)
    @patch('pybossa.view.google.redirect', return_value=True)
    def test_manage_user_is_not_asked_twice(self, redirect,
                                            url_for_app_type, flash,
                                            login_user,
                                            newsletter):
        """Test GOOGLE manage_user_login shows newsletter only once works."""
        user = UserFactory.create(fullname='john', name='john',
                                  google_user_id='1',
                                  newsletter_prompted=True)
        next_url = '/'
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        manage_user_login(user, user_data, next_url=next_url)
        login_user.assert_called_with(user, remember=True)
        assert user.newsletter_prompted is True
        assert url_for_app_type.called is False

    @with_context
    @patch('pybossa.view.google.newsletter', autospec=True)
    @patch('pybossa.view.google.login_user', return_value=True)
    @patch('pybossa.view.google.flash', return_value=True)
    @patch('pybossa.view.google.url_for_app_type', return_value=True)
    @patch('pybossa.view.google.redirect', return_value=True)
    def test_manage_login_without_user(self, redirect,
                                       url_for_app_type, flash,
                                       login_user,
                                       newsletter):
        """Test GOOGLE manage_user_login without user works."""
        user = UserFactory.create(fullname='john', name='john')
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(None, user_data, next_url=next_url)
        assert login_user.called is False
        url_for_app_type.assert_called_with('account.forgot_password',
                                            _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.google.newsletter', autospec=True)
    @patch('pybossa.view.google.login_user', return_value=True)
    @patch('pybossa.view.google.flash', return_value=True)
    @patch('pybossa.view.google.url_for_app_type', return_value=True)
    @patch('pybossa.view.google.redirect', return_value=True)
    def test_manage_login_without_user_facebook(self, redirect,
                                                url_for_app_type, flash,
                                                login_user,
                                                newsletter):
        """Test GOOGLE manage_user_login without user facebook works."""
        user = UserFactory.create(fullname='john', name='john',
                                  info={'facebook_token': 't'})
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(None, user_data, next_url=next_url)
        assert login_user.called is False
        url_for_app_type.assert_called_with('account.signin',
                                            _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.google.url_for', return_value=True)
    def test_request_token_params_set_correctly_with_next(self, url_for):
        self.app.get('/google/?next=somewhere')
        assert google.oauth.request_token_params == {
            'scope': 'profile email'
        }
        url_for.assert_called_with('.oauth_authorized', _external=True)
