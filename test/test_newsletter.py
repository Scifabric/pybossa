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

import json
from default import with_context, Test, FakeResponse
from helper import web
from mock import patch, MagicMock
from collections import namedtuple
from pybossa.core import user_repo
from pybossa.newsletter import Newsletter
from factories import UserFactory
from bs4 import BeautifulSoup
from nose.tools import assert_raises

FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestNewsletterClass(Test):

    @with_context
    def test_init_app(self):
        """Test Newsletter init_app method works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            nw = Newsletter()
            assert nw.app is None
            nw.init_app(self.flask_app)
            assert nw.app == self.flask_app
            assert nw.list_id == 1
            assert nw.root == 'https://3.api.mailchimp.com/3.0'

    @with_context
    @patch('pybossa.newsletter.requests.get')
    def test_is_user_subscribed_false(self, req_mock):
        """Test is_user_subscribed returns False."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            email = 'john@john.com'
            nw = Newsletter()
            nw.init_app(self.flask_app)
            req_mock.side_effect = [FakeResponse(text=json.dumps(dict(status=404)),
                                                 json=lambda : dict(status=404),
                                               status_code=200)]

            res = nw.is_user_subscribed(email)[0]
            assert res is False

    @with_context
    @patch('requests.get')
    def test_is_user_subscribed_true(self, req_mock):
        """Test is_user_subscribed returns True."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            email = 'john@john.com'
            nw = Newsletter()
            nw.init_app(self.flask_app)
            req_mock.side_effect = [FakeResponse(text=json.dumps(dict(status='200')),
                                               json=lambda : dict(status=200),
                                               status_code=200)]
            res, err = nw.is_user_subscribed(email)
            assert res is True, (res, err)

    @with_context
    @patch('requests.post')
    def test_subscribe_user(self, mailchimp):
        """Test subscribe user works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            nw = Newsletter()
            nw.init_app(self.flask_app)

            nw.subscribe_user(user)

            url = "%s/lists/1/members/" % (nw.root)
            data = dict(email_address=user.email_addr,
                        status='pending',
                        merge_fields=dict(FNAME=user.fullname))
            mailchimp.assert_called_with(url, data=json.dumps(data),
                                         headers={'content-type':
                                                  'application/json'},
                                         auth=nw.auth)

    @with_context
    @patch('requests.put')
    def test_subscribe_user_update_existing(self, mailchimp):
        """Test subscribe user update existing works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            nw = Newsletter()
            nw.init_app(self.flask_app)

            nw.subscribe_user(user, update=True)

            email = {'email': user.email_addr}
            merge_vars = {'FNAME': user.fullname}
            url = "%s/lists/1/members/%s" % (nw.root,
                                             nw.get_email_hash(user.email_addr))
            data = dict(email_address=user.email_addr,
                        status='pending',
                        merge_fields=dict(FNAME=user.fullname),
                        status_if_new='pending'
                        )
            mailchimp.assert_called_with(url, data=json.dumps(data),
                                         headers={'content-type':
                                                  'application/json'},
                                         auth=nw.auth)

    @with_context
    @patch('requests.delete')
    def test_delete_user(self, mailchimp):
        """Test delete user from mailchimp."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            nw = Newsletter()
            nw.init_app(self.flask_app)

            mailchimp.side_effect = [FakeResponse(text=json.dumps(dict(status=204)),
                                                 json=lambda : '',
                                               status_code=204)]

            res = nw.delete_user('email')

            url = "%s/lists/1/members/%s" % (nw.root,
                                             nw.get_email_hash('email'))
            mailchimp.assert_called_with(url, auth=nw.auth)
            assert res is True, res

    @with_context
    @patch('requests.delete')
    def test_delete_user_returns_false(self, mailchimp):
        """Test delete user from mailchimp returns false."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            nw = Newsletter()
            nw.init_app(self.flask_app)

            mailchimp.side_effect = [FakeResponse(text=json.dumps(dict(status=404)),
                                                 json=lambda : '',
                                               status_code=404)]

            res = nw.delete_user('email')

            url = "%s/lists/1/members/%s" % (nw.root,
                                             nw.get_email_hash('email'))
            mailchimp.assert_called_with(url, auth=nw.auth)
            assert res is False, res


    @with_context
    def test_is_initialized_returns_false_before_calling_init_app(self):
        nw = Newsletter()
        app = MagicMock()

        assert nw.is_initialized() is False

    @with_context
    def test_is_initialized_returns_true_after_calling_init_app(self):
        nw = Newsletter()
        app = MagicMock()
        nw.init_app(app)

        assert nw.is_initialized() is True

    @with_context
    def test_ask_user_to_subscribe_returns_false_if_not_initialized(self):
        nw = Newsletter()
        user = UserFactory.build()

        assert nw.ask_user_to_subscribe(user) is False

    @with_context
    def test_ask_user_to_subscribe_returns_false_if_newsletter_prompted(self):
        nw = Newsletter()
        app = MagicMock()
        nw.init_app(app)
        user = UserFactory.build(newsletter_prompted=True)

        assert nw.ask_user_to_subscribe(user) is False

    @with_context
    @patch('requests.get')
    def test_ask_user_to_subscribe_returns_false_if_user_subscribed(self,
                                                                    req_mock):
        user = UserFactory.build(newsletter_prompted=False)
        app = MagicMock()
        nw = Newsletter()
        nw.init_app(app)
        req_mock.side_effect = [FakeResponse(text=json.dumps(dict(foo='bar')),
                                             json=lambda: dict(status=200),
                                             status_code=200)]
        assert nw.ask_user_to_subscribe(user) is False

    @with_context
    @patch('requests.get')
    def test_ask_user_to_subscribe_returns_true_if_user_not_subscribed(self,
                                                                       req_mock):
        user = UserFactory.build(newsletter_prompted=False)
        app = MagicMock()
        nw = Newsletter()
        nw.init_app(app)
        req_mock.side_effect = [FakeResponse(text=json.dumps(dict(foo='bar')),
                                             json=lambda: dict(status=404),
                                             status_code=200)]

        assert nw.ask_user_to_subscribe(user) is True


class TestNewsletterViewFunctions(web.Helper):

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_new_user_gets_newsletter(self, newsletter):
        """Test NEWSLETTER new user works."""
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'key'}):
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
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'key'}):
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
        assert "You are subscribed" in str(res.data), err_msg
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
        assert "You are subscribed" in str(res.data), err_msg
        assert newsletter.subscribe_user.called, err_msg
        newsletter.subscribe_user.assert_called_with(user)
        assert "Update" in str(res.data), res.data

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
        assert "You are subscribed" not in str(res.data), err_msg
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
        assert "You are subscribed" not in str(res.data), err_msg
        assert newsletter.subscribe_user.called is False, err_msg
        assert "Update" in str(res.data), res.data

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
        assert "You are subscribed" not in str(res.data), err_msg
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
        assert "You are subscribed" not in str(res.data), err_msg
        assert newsletter.subscribe_user.called is False, err_msg
        assert dom.find(id='newsletter') is not None, err_msg
