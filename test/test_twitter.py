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
from default import Test
from pybossa.view.twitter import manage_user, manage_user_login
from pybossa.core import user_repo
from mock import patch
from factories import UserFactory


class TestTwitter(Test):

    def test_manage_user(self):
        """Test TWITTER manage_user works."""
        # First with a new user
        user_data = dict(user_id=1, screen_name='twitter')
        token = dict(oauth_token='token', oauth_token_secret='secret')
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['screen_name'], user
        assert user.name == user_data['screen_name'], user
        assert user.fullname == user_data['screen_name'], user
        assert user.twitter_user_id == user_data['user_id'], user

        # Second with the same user
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['screen_name'], user
        assert user.name == user_data['screen_name'], user
        assert user.fullname == user_data['screen_name'], user
        assert user.twitter_user_id == user_data['user_id'], user

        # Finally with a user that already is in the system
        user_data = dict(user_id=10, screen_name=self.name)
        token = dict(oauth_token='token2', oauth_token_secret='secret2')
        user = manage_user(token, user_data, None)
        err_msg = "It should return the same user"
        assert user.twitter_user_id == 10, err_msg


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
        manage_user_login(user, next_url)
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
        user.email_addr = user.name
        user_repo.update(user)
        manage_user_login(user, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for.assert_called_once_with('account.update_profile',
                                        name=user.name)
