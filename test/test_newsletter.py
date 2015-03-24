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

from default import with_context, Test
from helper import web
from mock import patch, MagicMock
from collections import namedtuple
from pybossa.core import user_repo
from pybossa.newsletter import Newsletter
from factories import UserFactory
from bs4 import BeautifulSoup
from nose.tools import assert_raises
from mailchimp import Error

FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestNewsletterClass(Test):

    @patch('pybossa.newsletter.mailchimp')
    def test_init_app(self, mailchimp):
        """Test Newsletter init_app method works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            nw = Newsletter()
            assert nw.app is None
            nw.init_app(self.flask_app)
            assert nw.app == self.flask_app
            assert nw.client, nw.client
            assert nw.list_id == 1

    @patch('pybossa.newsletter.mailchimp')
    def test_is_user_subscribed_false(self, mailchimp):
        """Test is_user_subscribed returns False."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            email = 'john@john.com'
            nw = Newsletter()
            nw.init_app(self.flask_app)
            res = nw.is_user_subscribed(email)
            nw.client.lists.member_info.assert_called_with(1,
                                                           [{'email': email}])
            assert res is False

    @patch('pybossa.newsletter.mailchimp')
    def test_is_user_subscribed_true(self, mailchimp):
        """Test is_user_subscribed returns True."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            email = 'john@john.com'
            nw = Newsletter()
            nw.init_app(self.flask_app)
            tmp = {'data': [{'email': email}],
                   'success_count': 1}
            nw.client.lists.member_info.return_value = tmp
            res = nw.is_user_subscribed(email)
            nw.client.lists.member_info.assert_called_with(1,
                                                           [{'email': email}])
            assert res is True

    @patch('pybossa.newsletter.mailchimp')
    def test_is_user_subscribed_exception(self, mp):
        """Test is_user_subscribed exception works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            email = 'john@john.com'
            nw = Newsletter()
            nw.init_app(self.flask_app)
            nw.client.lists.member_info.side_effect = Error
            assert_raises(Error, nw.is_user_subscribed, email)

    @patch('pybossa.newsletter.mailchimp')
    def test_subscribe_user_exception(self, mp):
        """Test subscribe_user exception works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            nw = Newsletter()
            nw.init_app(self.flask_app)
            nw.client.lists.subscribe.side_effect = Error
            tmp = {'data': [{'email': user.email_addr}],
                   'success_count': 1}
            nw.client.lists.member_info.return_value = tmp
            assert_raises(Error, nw.subscribe_user, user)


    @patch('pybossa.newsletter.mailchimp')
    def test_subscribe_user(self, mailchimp):
        """Test subscribe user works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            nw = Newsletter()
            nw.init_app(self.flask_app)

            nw.subscribe_user(user)

            email = {'email': user.email_addr}
            merge_vars = {'FNAME': user.fullname}
            nw.client.lists.subscribe.assert_called_with(1, email, merge_vars,
                                                         update_existing=False)

    @patch('pybossa.newsletter.mailchimp')
    def test_subscribe_user_update_existing(self, mailchimp):
        """Test subscribe user update existing works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            nw = Newsletter()
            nw.init_app(self.flask_app)

            old_email = 'old@email.com'

            tmp = {'data': [{'email': old_email}],
                   'success_count': 1}
            nw.client.lists.member_info.return_value = tmp

            nw.subscribe_user(user, old_email=old_email)

            email = {'email': old_email}
            merge_vars = {'FNAME': user.fullname,
                          'new-email': user.email_addr}
            nw.client.lists.subscribe.assert_called_with(1, email, merge_vars,
                                                         update_existing=True)

    @patch('pybossa.newsletter.mailchimp')
    def test_is_initialized_returns_false_before_calling_init_app(self, mailchimp):
        nw = Newsletter()
        app = MagicMock()

        assert nw.is_initialized() is False

    @patch('pybossa.newsletter.mailchimp')
    def test_is_initialized_returns_true_after_calling_init_app(self, mailchimp):
        nw = Newsletter()
        app = MagicMock()
        nw.init_app(app)

        assert nw.is_initialized() is True

    def test_ask_user_to_subscribe_returns_false_if_not_initialized(self):
        nw = Newsletter()
        user = UserFactory.build()

        assert nw.ask_user_to_subscribe(user) is False

    @patch('pybossa.newsletter.mailchimp')
    def test_ask_user_to_subscribe_returns_false_if_newsletter_prompted(self, mailchimp):
        nw = Newsletter()
        app = MagicMock()
        nw.init_app(app)
        user = UserFactory.build(newsletter_prompted=True)

        assert nw.ask_user_to_subscribe(user) is False

    @patch('pybossa.newsletter.mailchimp')
    def test_ask_user_to_subscribe_returns_false_if_user_subscribed(self, mailchimp):
        user = UserFactory.build(newsletter_prompted=False)
        app = MagicMock()
        fake_client = MagicMock()
        fake_client.lists.member_info.return_value = {
            'success_count': 1, 'data': [{'email':user.email_addr}]}
        mailchimp.Mailchimp.return_value = fake_client
        nw = Newsletter()
        nw.init_app(app)

        assert nw.ask_user_to_subscribe(user) is False

    @patch('pybossa.newsletter.mailchimp')
    def test_ask_user_to_subscribe_returns_true_if_user_not_subscribed(self, mailchimp):
        user = UserFactory.build(newsletter_prompted=False)
        app = MagicMock()
        fake_client = MagicMock()
        fake_client.lists.member_info.return_value = {
            'success_count': 0, 'data': [{'email':'anotheruser@a.com'}]}
        mailchimp.Mailchimp.return_value = fake_client
        nw = Newsletter()
        nw.init_app(app)

        assert nw.ask_user_to_subscribe(user) is True


class TestNewsletterViewFuntions(web.Helper):

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_new_user_gets_newsletter(self, newsletter):
        """Test NEWSLETTER new user works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        res = self.register()
        dom = BeautifulSoup(res.data)
        err_msg = "There should be a newsletter page."
        assert dom.find(id='newsletter') is not None, err_msg
        assert dom.find(id='signmeup') is not None, err_msg
        assert dom.find(id='notinterested') is not None, err_msg


    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_new_user_gets_newsletter_only_once(self, newsletter):
        """Test NEWSLETTER user gets newsletter only once works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        res = self.register()
        dom = BeautifulSoup(res.data)
        user = user_repo.get(1)
        err_msg = "There should be a newsletter page."
        assert dom.find(id='newsletter') is not None, err_msg
        assert dom.find(id='signmeup') is not None, err_msg
        assert dom.find(id='notinterested') is not None, err_msg
        assert user.newsletter_prompted is True, err_msg

        self.signout()
        newsletter.ask_user_to_subscribe.return_value = False
        res = self.signin()
        dom = BeautifulSoup(res.data)
        assert dom.find(id='newsletter') is None, err_msg
        assert dom.find(id='signmeup') is None, err_msg
        assert dom.find(id='notinterested') is None, err_msg

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_subscribe_returns_404(self, newsletter):
        """Test NEWSLETTER view returns 404 works."""
        newsletter.is_initialized.return_value = False
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        res = self.app.get('/account/newsletter', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "It should return 404"
        assert dom.find(id='newsletter') is None, err_msg
        assert res.status_code == 404, err_msg

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_subscribe(self, newsletter):
        """Test NEWSLETTER view subcribe works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        res = self.app.get('/account/newsletter?subscribe=True',
                           follow_redirects=True)
        err_msg = "User should be subscribed"
        user = user_repo.get(1)
        assert "You are subscribed" in res.data, err_msg
        assert newsletter.subscribe_user.called, err_msg
        newsletter.subscribe_user.assert_called_with(user)


    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_subscribe_next(self, newsletter):
        """Test NEWSLETTER view subscribe next works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        next_url = '%2Faccount%2Fjohndoe%2Fupdate'
        url ='/account/newsletter?subscribe=True&next=%s' % next_url
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should be subscribed"
        user = user_repo.get(1)
        assert "You are subscribed" in res.data, err_msg
        assert newsletter.subscribe_user.called, err_msg
        newsletter.subscribe_user.assert_called_with(user)
        assert "Update" in res.data, res.data

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_not_subscribe(self, newsletter):
        """Test NEWSLETTER view not subcribe works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        res = self.app.get('/account/newsletter?subscribe=False',
                           follow_redirects=True)
        err_msg = "User should not be subscribed"
        assert "You are subscribed" not in res.data, err_msg
        assert newsletter.subscribe_user.called is False, err_msg

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_not_subscribe_next(self, newsletter):
        """Test NEWSLETTER view subscribe next works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        next_url = '%2Faccount%2Fjohndoe%2Fupdate'
        url ='/account/newsletter?subscribe=False&next=%s' % next_url
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should not be subscribed"
        assert "You are subscribed" not in res.data, err_msg
        assert newsletter.subscribe_user.called is False, err_msg
        assert "Update" in res.data, res.data

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_with_any_argument(self, newsletter):
        """Test NEWSLETTER view with any argument works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        res = self.app.get('/account/newsletter?subscribe=something',
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should not be subscribed"
        assert "You are subscribed" not in res.data, err_msg
        assert newsletter.subscribe_user.called is False, err_msg
        assert dom.find(id='newsletter') is not None, err_msg

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_with_any_argument_variation(self, newsletter):
        """Test NEWSLETTER view with any argument variation works."""
        newsletter.is_initialized.return_value = True
        newsletter.ask_user_to_subscribe.return_value = True
        self.register()
        res = self.app.get('/account/newsletter?myarg=something',
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should not be subscribed"
        assert "You are subscribed" not in res.data, err_msg
        assert newsletter.subscribe_user.called is False, err_msg
        assert dom.find(id='newsletter') is not None, err_msg
