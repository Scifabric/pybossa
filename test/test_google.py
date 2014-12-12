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
from pybossa.view.google import manage_user, manage_user_login
from mock import patch
from factories import UserFactory


class TestGoogle(Test):

    def test_manage_user(self):
        """Test GOOGLE manage_user works."""
        # First with a new user
        user_data = dict(id='1', name='google',
                         email='g@g.com')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user

        # Second with the same user
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user

        # Finally with a user that already is in the system
        user_data = dict(id='10', name=self.name,
                         email=self.email_addr)
        token = 'tA'
        user = manage_user(token, user_data, None)
        err_msg = "User should be the same"
        assert user.google_user_id == '10', err_msg

    @patch('pybossa.view.google.newsletter', autospec=True)
    def test_manage_user_with_newsletter(self, newsletter):
        """Test GOOGLE manage_user with newsletter works."""
        # First with a new user
        newsletter.app = True
        user_data = dict(id='1', name='google',
                         email='g@g.com')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user
        newsletter.subscribe_user.assert_called_once_with(user)

    @patch('pybossa.view.google.newsletter', autospec=True)
    def test_manage_user_with_newsletter_only_once(self, newsletter):
        """Test GOOGLE manage_user with newsletter only once works."""
        # Second with the same user
        token = 't'
        user = UserFactory.create(fullname='john', name='john',
                                  google_user_id='1')
        user_data = dict(id=str(user.id), name=user.name, email=user.email_addr)
        r_user = manage_user(token, user_data, None)
        assert r_user.email_addr == user_data['email'], user
        assert r_user.name == user_data['name'], user
        assert r_user.fullname == user_data['name'], user
        assert r_user.google_user_id == user_data['id'], user
        assert newsletter.subscribe_user.called is False, newsletter.subscribe_user.called

    @patch('pybossa.view.google.newsletter', autospec=True)
    @patch('pybossa.view.google.login_user', return_value=True)
    @patch('pybossa.view.google.flash', return_value=True)
    @patch('pybossa.view.google.url_for', return_value=True)
    @patch('pybossa.view.google.redirect', return_value=True)
    def test_manage_user_with_oauth_newsletter(self, redirect,
                                               url_for, flash,
                                               login_user,
                                               newsletter):
        """Test GOOGLE manage_user_login shows newsletter works."""
        user = UserFactory.create(fullname='john', name='john',
                                  google_user_id='1')
        next_url = '/'
        manage_user_login(user, next_url=next_url)
        login_user.assert_called_with(user, remember=True)
        assert user.newsletter_prompted is False
        url_for.assert_called_with('account.newsletter_subscribe',
                                   next=next_url)

    @patch('pybossa.view.google.newsletter', autospec=True)
    @patch('pybossa.view.google.login_user', return_value=True)
    @patch('pybossa.view.google.flash', return_value=True)
    @patch('pybossa.view.google.url_for', return_value=True)
    @patch('pybossa.view.google.redirect', return_value=True)
    def test_manage_user_is_not_asked_twice(self, redirect,
                                            url_for, flash,
                                            login_user,
                                            newsletter):
        """Test GOOGLE manage_user_login shows newsletter only once works."""
        user = UserFactory.create(fullname='john', name='john',
                                  google_user_id='1',
                                  newsletter_prompted=True)
        next_url = '/'
        manage_user_login(user, next_url=next_url)
        login_user.assert_called_with(user, remember=True)
        assert user.newsletter_prompted is True
        assert url_for.called is False
