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

from default import with_context
from helper import web
from mock import patch
from collections import namedtuple
from pybossa.core import user_repo
from bs4 import BeautifulSoup

FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestNewsletter(web.Helper):
    #pkg_json_not_found = {
    #    "help": "Return ...",
    #    "success": False,
    #    "error": {
    #        "message": "Not found",
    #        "__type": "Not Found Error"}}

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_new_user_gets_newsletter(self, newsletter):
        """Test NEWSLETTER new user works."""
        newsletter.app = True
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
        newsletter.app = True
        res = self.register()
        dom = BeautifulSoup(res.data)
        user = user_repo.get(1)
        err_msg = "There should be a newsletter page."
        assert dom.find(id='newsletter') is not None, err_msg
        assert dom.find(id='signmeup') is not None, err_msg
        assert dom.find(id='notinterested') is not None, err_msg
        assert user.newsletter_prompted is True, err_msg

        self.signout()
        res = self.signin()
        dom = BeautifulSoup(res.data)
        assert dom.find(id='newsletter') is None, err_msg
        assert dom.find(id='signmeup') is None, err_msg
        assert dom.find(id='notinterested') is None, err_msg

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    def test_newsletter_subscribe_returns_404(self, newsletter):
        """Test NEWSLETTER view returns 404 works."""
        newsletter.app = None
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
        newsletter.app = True
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
        newsletter.app = True
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
        newsletter.app = True
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
        newsletter.app = True
        self.register()
        next_url = '%2Faccount%2Fjohndoe%2Fupdate'
        url ='/account/newsletter?subscribe=False&next=%s' % next_url
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should not be subscribed"
        assert "You are subscribed" not in res.data, err_msg
        assert newsletter.subscribe_user.called is False, err_msg
        assert "Update" in res.data, res.data
