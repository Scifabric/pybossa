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
from flask import Response
from default import Test, assert_not_raises
from pybossa.view.twitter import manage_user, manage_user_login, \
    manage_user_no_login
from pybossa.core import user_repo
from mock import patch
from factories import UserFactory


class TestTwitter(Test):

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

    def test_manage_user_twitter_registered_user(self):
        """Test TWITTER manage_user with an existing user registered with Twitter"""
        user_data = dict(user_id=1, screen_name='twitter')
        initial_token = dict(oauth_token='token', oauth_token_secret='secret')
        manage_user(initial_token, user_data)
        updated_token = dict(oauth_token='token2', oauth_token_secret='secret2')
        user = manage_user(updated_token, user_data)
        assert user.email_addr == user_data['screen_name'], user
        assert user.name == user_data['screen_name'], user
        assert user.fullname == user_data['screen_name'], user
        assert user.twitter_user_id == user_data['user_id'], user
        assert user.info['twitter_token'] == updated_token, user

    def test_manage_user_with_existing_non_twitter_account_user(self):
        """Test TWITTER manage_user user with a username that already exists
        and registered without Twitter"""
        user_data = dict(user_id=10, screen_name=self.name)
        token = dict(oauth_token='token2', oauth_token_secret='secret2')
        user = manage_user(token, user_data)
        err_msg = "It should return the same user"
        assert user.twitter_user_id == 10, err_msg
        assert user.info['twitter_token'] == token, user

    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_with_newsletter(self, redirect,
                                               url_for,
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
        url_for.assert_called_once_with('account.newsletter_subscribe',
                                        next=next_url)

    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_with_newsletter_no_email(self, redirect,
                                                        url_for,
                                                        flash,
                                                        login_user,
                                                        newsletter):
        """Test TWITTER manage_user_login without email with newsletter works."""
        newsletter.app = True
        next_url = '/'
        user = UserFactory.create(name='john', email_addr='john')
        user_data = dict(id=user.id, screen_name=user.name)
        user.email_addr = user.name
        user_repo.update(user)
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for.assert_called_once_with('account.update_profile',
                                        name=user.name)

    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_without_user_local(self, redirect,
                                                  url_for,
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
        url_for.assert_called_once_with('account.forgot_password')

    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_without_user(self, redirect,
                                            url_for,
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
        url_for.assert_called_once_with('account.signin')

    @patch('pybossa.view.twitter.newsletter', autospec=True)
    @patch('pybossa.view.twitter.login_user', return_value=True)
    @patch('pybossa.view.twitter.flash', return_value=True)
    @patch('pybossa.view.twitter.url_for', return_value=True)
    @patch('pybossa.view.twitter.redirect', return_value=True)
    def test_manage_user_login_with_newsletter_twice(self, redirect,
                                                     url_for,
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

    @patch('pybossa.view.twitter.twitter.oauth')
    def test_twitter_signin_with_no_login_param(self, oauth):
        oauth.authorize.return_value = Response(302)
        self.app.get('/twitter/?no_login=1')

        oauth.authorize.assert_called_once_with(
            callback='/twitter/oauth-authorized?no_login=1')

    @patch('pybossa.view.twitter.manage_user_no_login')
    @patch('pybossa.view.twitter.twitter.oauth')
    def test_twitter_signin_oauth_callback_no_login_calls_manage_user_no_login(
            self, oauth, manage_user_no_login):
        oauth.authorized_response.return_value = {
            'oauth_token': 'token',
            'oauth_token_secret': 'secret'
            }
        manage_user_no_login.return_value = Response(302)
        self.app.get('/twitter/oauth-authorized?no_login=1')

        manage_user_no_login.assert_called_once_with(
            {'oauth_token_secret': 'secret', 'oauth_token': 'token'},
            '/')

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
        manage_user_no_login.return_value = Response(302)

        assert_not_raises(Exception, self.app.get, '/twitter/oauth-authorized')

    @patch('pybossa.view.twitter.current_user')
    def test_manage_user_no_login_stores_twitter_token_in_current_user_info(
        self, current_user):
        user = UserFactory.create(info={})
        current_user.id = user.id
        token_and_secret = {'oauth_token_secret': 'secret', 'oauth_token': 'token'}

        manage_user_no_login(token_and_secret, '/')

        assert user.info == {'twitter_token': token_and_secret}, user.info
