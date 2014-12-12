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
from pybossa.view.facebook import manage_user, manage_user_login
from mock import patch
from factories import UserFactory


class TestFacebook(Test):

    def test_manage_user_with_email(self):
        """Test FACEBOOK manage_user works."""
        # First with a new user
        user_data = dict(id=1, username='facebook',
                         email='f@f.com', name='name')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        # Second with the same user
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        # Finally with a user that already is in the system
        user_data = dict(id=10, username=self.name,
                         email=self.email_addr, name=self.fullname)
        token = 'tA'
        user = manage_user(token, user_data, None)
        err_msg = "It should return the same user"
        assert user.facebook_user_id == 10, err_msg


    def test_manage_user_without_email(self):
        """Test FACEBOOK manage_user without e-mail works."""
        # First with a new user
        user_data = dict(id=1, username='facebook', name='name')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        # Second with the same user
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        # Finally with a user that already is in the system
        user_data = dict(id=10, username=self.name,
                         email=self.email_addr, name=self.fullname)
        token = 'tA'
        user = manage_user(token, user_data, None)
        err_msg = "It should return the same user"
        assert user.facebook_user_id == 10, err_msg

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    def test_manage_user_with_email_newsletter(self, newsletter):
        """Test FACEBOOK manage_user newsletter works."""
        newsletter.app = True
        # First with a new user
        user_data = dict(id=1, username='facebook',
                         email='f@f.com', name='name')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        newsletter.subscribe_user.assert_called_once_with(user)


    @patch('pybossa.view.facebook.newsletter', autospec=True)
    def test_manage_user_without_email_newsletter(self, newsletter):
        """Test FACEBOOK manage_user without e-mail newsletter works."""
        newsletter.app = True
        # First with a new user
        user_data = dict(id=1, username='facebook', name='name')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user
        err_msg = "It should not be called."
        assert newsletter.subscribe_user.called is False, err_msg

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_local(self, redirect,
                                     url_for, flash,
                                     login_user,
                                     newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user = UserFactory.create()
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for.assert_called_once_with('account.forgot_password')

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_google_token(self, redirect,
                                            url_for, flash,
                                            login_user,
                                            newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user = UserFactory.create(info={'google_token': 'k'})
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for.assert_called_once_with('account.signin')

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_empty(self, redirect,
                                     url_for, flash,
                                     login_user,
                                     newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user_data = dict(id='3', name='algo', email='email')
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for.assert_called_once_with('account.signin')

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_update_email(self, redirect,
                                            url_for, flash,
                                            login_user,
                                            newsletter):
        """Test manage login user works."""
        newsletter.app = True
        user = UserFactory.create(email_addr="None")
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for.assert_called_once_with('account.update_profile',
                                        name=user.name)
