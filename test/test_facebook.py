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
from pybossa.util import username_from_full_name


class TestFacebook(Test):

    def setUp(self):
        super(TestFacebook, self).setUp()
        self.user_data = {
            "id": 1234567890,
            "email": "me@facebook.com",
            "first_name": "Mauricio",
            "last_name": "Perez Sanchez",
            "name": "Mauricio Perez Sanchez"
        }
        self.name = username_from_full_name(self.user_data['name'])

    def test_manage_user_with_email(self):
        """Test FACEBOOK manage_user works."""
        # First with a new user
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name, user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user

        # Second with the same user
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name, user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user

    def test_manage_user_without_email(self):
        """Test FACEBOOK manage_user without e-mail works."""
        # First with a new user
        del self.user_data['email']
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name, user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user

        # Second with the same user
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name, user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    def test_manage_user_with_email_newsletter(self, newsletter):
        """Test FACEBOOK manage_user newsletter works."""
        newsletter.app = True
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name, user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user

        newsletter.subscribe_user.assert_called_once_with(user)

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    def test_manage_user_without_email_newsletter(self, newsletter):
        """Test FACEBOOK manage_user without e-mail newsletter works."""
        newsletter.app = True
        del self.user_data['email']
        token = 't'
        user = manage_user(token, self.user_data)
        assert user.email_addr == self.user_data['email'], user
        assert user.name == self.name, user
        assert user.fullname == self.user_data['name'], user
        assert user.facebook_user_id == self.user_data['id'], user
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
        user_data = dict(name=user.name, email=user.email_addr)
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
        user_data = dict(name=user.name, email=user.email_addr)
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
        user_data = dict(name='algo', email='email')
        next_url = '/'
        manage_user_login(None, user_data, next_url)
        url_for.assert_called_once_with('account.signin')

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_empty_no_email(self, redirect,
                                              url_for, flash,
                                              login_user,
                                              newsletter):
        """Test manage login user new user with no email from facebook"""
        newsletter.app = True
        user_data = dict(name='algo')
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
        user = UserFactory.create(name='johndoe', email_addr='johndoe')
        user_data = dict(name=user.name)
        next_url = '/'
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for.assert_called_once_with('account.update_profile',
                                        name=user.name)

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_good_email(self, redirect,
                                          url_for, flash,
                                          login_user,
                                          newsletter):
        """Test manage login user with good email works."""
        newsletter.app = True
        user = UserFactory.create()
        user_data = dict(name=user.name, email=user.email_addr)
        next_url = '/'
        manage_user_login(user, user_data, next_url)
        login_user.assert_called_once_with(user, remember=True)
        url_for.assert_called_once_with('account.newsletter_subscribe',
                                        next=next_url)

    @patch('pybossa.view.facebook.newsletter', autospec=True)
    @patch('pybossa.view.facebook.login_user', return_value=True)
    @patch('pybossa.view.facebook.flash', return_value=True)
    @patch('pybossa.view.facebook.url_for', return_value=True)
    @patch('pybossa.view.facebook.redirect', return_value=True)
    def test_manage_login_user_already_asked(self, redirect,
                                             url_for, flash,
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
