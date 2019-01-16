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

from pybossa.core import sentinel
from pybossa.jobs import news
from pybossa.news import get_news
from default import Test, with_context, FakeResponse, db
from factories import UserFactory
from mock import patch, MagicMock, call


class TestNews(Test):

    d = MagicMock()
    d.entries = [dict(updated='2015-01-01')]

    def get_notify_users(self, user):
        key = "notify:admin:%s" % user.id
        return sentinel.master.get(key)

    def delete_notify(self, user):
        key = "notify:admin:%s" % user.id
        return sentinel.master.delete(key)

    @with_context
    @patch('feedparser.parse')
    def test_news(self, feedparser_mock):
        """Test NEWS works."""
        user = UserFactory.create(admin=True)
        feedparser_mock.return_value = self.d
        news()
        tmp = get_news()
        assert len(tmp) == 1, len(tmp)
        err_msg = "Notify user should be notified"
        assert self.get_notify_users(user) == b'1', err_msg

    @with_context
    @patch('feedparser.parse')
    def test_news_no_new_items(self, feedparser_mock):
        """Test NEWS no new items works."""
        user = UserFactory.create(admin=True)
        feedparser_mock.return_value = self.d
        news()
        feedparser_mock.return_value = self.d
        news()
        tmp = get_news()
        assert len(tmp) == 1, len(tmp)
        err_msg = "Notify user should be notified"
        assert self.get_notify_users(user) == b'1', err_msg

    @with_context
    @patch('feedparser.parse')
    def test_news_no_new_items_no_notification(self, feedparser_mock):
        """Test NEWS no new items no notificaton works."""
        user = UserFactory.create(admin=True)
        feedparser_mock.return_value = self.d
        news()
        self.delete_notify(user)
        feedparser_mock.return_value = self.d
        news()
        tmp = get_news()
        assert len(tmp) == 1, len(tmp)
        err_msg = "Notify user should NOT be notified"
        assert self.get_notify_users(user) == None, err_msg

    @with_context
    @patch('feedparser.parse')
    def test_news_check_config_urls(self, feedparser_mock):
        """Test NEWS adds config URLs."""
        urls = ['https://github.com/Scifabric/pybossa/releases.atom',
                'http://scifabric.com/blog/all.atom.xml',
                'http://url']

        feedparser_mock.return_value = self.d
        with patch.dict(self.flask_app.config, {'NEWS_URL': ['http://url']}):
            news()
            calls = []
            for url in urls:
                calls.append(call(url))
            feedparser_mock.assert_has_calls(calls, any_order=True)
