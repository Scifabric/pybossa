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
from flask import Response
from default import Test, assert_not_raises, with_context
from pybossa.view.twitter import manage_user, manage_user_login, \
    manage_user_no_login
from pybossa.core import user_repo
from mock import patch
from factories import UserFactory


class TestTwitter(Test):

    @with_context
    def test_manage_user_new_user(self):
        """Test TWITTER manage_user with a new user"""
        user_data = dict(user_id=1, screen_name='twitter')
        token = dict(oauth_token='token', oauth_token_secret='secret')
        user = manage_user(token, user_data)
        assert user.email_addr == user_data['screen_name'], user
        assert user.name == user_data['screen_name'], user
        assert user.fullname == user_data['screen_name'], user
        assert user.twitter_user_id == user_data['user_id'], user
        assert user.info['twitter_token'] == token, user

    @with_context
    def test_manage_user_twitter_registered_user(self):
        """Test TWITTER manage_user with an existing user registered with Twitter"""
        user_data = dict(user_id=1, screen_name='twitter')
        initial_token = dict(oauth_token='token', oauth_token_secret='secret')
        manage_user(initial_token, user_data)
        updated_token = dict(oauth_token='token2',
                             oauth_token_secret='secret2')
        user = manage_user(updated_token, user_data)
        assert user.email_addr == user_data['screen_name'], user
        assert user.name == user_data['screen_name'], user
        assert user.fullname == user_data['screen_name'], user
        assert user.twitter_user_id == user_data['user_id'], user
        assert user.info['twitter_token'] == updated_token, user

    @with_context
    def test_manage_user_with_existing_non_twitter_account_user(self):
        """Test TWITTER manage_user user with a username that already exists
        and registered without Twitter"""
        user_data = dict(user_id=10, screen_name=self.name)
        token = dict(oauth_token='token2', oauth_token_secret='secret2')
        user = manage_user(token, user_data)
        err_msg = "It should return the same user"
        assert user.twitter_user_id == 10, err_msg
        assert user.info['twitter_token'] == token, user

    @with_context
    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for_app_type', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_with_newsletter(self, redirect,
                                               url_for_app_type,
                                               flash,
                                               login_user,
                                               newsletter):
        """Test TWITTER manage_user_login with newsletter works."""
        newsletter.app = True
        next_url = '/'
        user = UserFactory.create()
        user_data = dict(id=user.id, screen_name=user.name)
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for_app_type.assert_called_once_with('account.newsletter_subscribe',
                                                 next=next_url,
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for_app_type', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_with_newsletter_no_email(self, redirect,
                                                        url_for_app_type,
                                                        flash,
                                                        login_user,
                                                        newsletter):
        """Test TWITTER manage_user_login without email with newsletter works."""
        newsletter.app = True
        next_url = '/spa/account/profile/update'
        user = UserFactory.create(name='john', email_addr='john')
        user_data = dict(id=user.id, screen_name=user.name)
        user.email_addr = user.name
        user_repo.update(user)
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        redirect.assert_called_once_with(next_url)

    @with_context
    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for_app_type', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_without_user_local(self, redirect,
                                                  url_for_app_type,
                                                  flash,
                                                  login_user,
                                                  newsletter):
        """Test TWITTER manage_user_login without user with newsletter works."""
        newsletter.app = True
        next_url = '/'
        user = UserFactory.create()
        user_data = dict(id=user.id, screen_name=user.name)
        user.email_addr = user.name
        user_repo.update(user)
        manage_user_login(None, user_data, next_url)
        assert login_user.called is False
        url_for_app_type.assert_called_once_with('account.forgot_password',
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for_app_type', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_without_user(self, redirect,
                                            url_for_app_type,
                                            flash,
                                            login_user,
                                            newsletter):
        """Test TWITTER manage_user_login without user with newsletter works."""
        newsletter.app = True
        next_url = '/'
        user = UserFactory.create(info={'google_token': 'k'})
        user_data = dict(id=user.id, screen_name=user.name)
        user.email_addr = user.name
        user_repo.update(user)
        manage_user_login(None, user_data, next_url)
        assert login_user.called is False
        url_for_app_type.assert_called_once_with('account.signin',
                                                 _hash_last_flash=True)

    @with_context
    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for_app_type', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_with_newsletter_twice(self, redirect,
                                                     url_for_app_type,
                                                     flash,
                                                     login_user,
                                                     newsletter):
        """Test TWITTER manage_user_login without email with newsletter twice
        works."""
        newsletter.app = True
        next_url = '/'
        user = UserFactory.create(newsletter_prompted=True)
        user_data = dict(id=user.id, screen_name=user.name)
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        redirect.assert_called_once_with(next_url)

    @with_context
    @patch('pybossa.view.twitter.twitter.oauth')
    def test_twitter_signin_with_no_login_param(self, oauth):
        oauth.authorize.return_value = "OK"
        self.app.get('/twitter/?no_login=1')

        oauth.authorize.assert_called_once_with(
            callback='/twitter/oauth-authorized?no_login=1')

    @with_context
    @patch('pybossa.view.twitter.manage_user_no_login')
    @patch('pybossa.view.twitter.twitter.oauth')
    def test_twitter_signin_oauth_callback_no_login_calls_manage_user_no_login(
            self, oauth, manage_user_no_login):
        oauth.authorized_response.return_value = {
            'oauth_token': 'token',
            'oauth_token_secret': 'secret'
        }
        manage_user_no_login.return_value = "OK"
        self.app.get('/twitter/oauth-authorized?no_login=1')

        manage_user_no_login.assert_called_once_with(
            {'oauth_token_secret': 'secret', 'oauth_token': 'token'},
            '/')

    @with_context
    @patch('pybossa.view.twitter.manage_user_no_login')
    @patch('pybossa.view.twitter.twitter.oauth')
    def test_twitter_signin_no_login_param_missing(
            self, oauth, manage_user_no_login):
        oauth.authorized_response.return_value = {
            'oauth_token': 'token',
            'oauth_token_secret': 'secret',
            'screen_name': 'john_doe',
            'user_id': 1
        }
        manage_user_no_login.return_value = "OK"

        assert_not_raises(Exception, self.app.get, '/twitter/oauth-authorized')

    @with_context
    @patch('pybossa.view.twitter.current_user')
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_no_login_stores_twitter_token_in_current_user_info(
            self, redirect, current_user):
        user = UserFactory.create(info={})
        current_user.id = user.id
        token_and_secret = {
            'oauth_token_secret': 'secret', 'oauth_token': 'token'}
        next_url = '/'

        manage_user_no_login(token_and_secret, next_url)

        redirect.assert_called_once_with(next_url)
        assert user.info == {'twitter_token': token_and_secret}, user.info
