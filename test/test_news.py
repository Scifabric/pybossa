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
from default import Test, with_context
from pybossa.news import get_news, notify_news_admins
from pybossa.core import sentinel
from factories import UserFactory
try:
    import pickle as pickle
except ImportError:  # pragma: no cover
    import pickle

myset = 'scifabricnews'


class TestNews(Test):

    def setUp(self):
        super(TestNews, self).setUp()
        self.connection = sentinel.master
        self.connection.flushall()

    news = dict(updated='2015-01-01')

    @with_context
    def test_get_news_empty(self):
        news = get_news()
        assert len(news) == 0, len(news)

    @with_context
    def test_get_news_with_score_empty(self):
        news = get_news(score=1)
        assert len(news) == 0, len(news)

    @with_context
    def test_get_news(self):
        mapping = dict()
        mapping[pickle.dumps(self.news)] = 0
        sentinel.master.zadd(myset, mapping)
        news = get_news()
        assert len(news) == 1, len(news)
        news[0]['updated'] == self.news['updated'], news

    @with_context
    def test_get_news_with_score(self):
        mapping = dict()
        mapping[pickle.dumps(self.news)] = 0
        sentinel.master.zadd(myset, mapping)

        news = get_news(score=1)
        assert len(news) == 0, len(news)

    @with_context
    def test_notify_news_admins(self):
        user = UserFactory.create(admin=True)
        notify_news_admins()
        key = "notify:admin:%s" % user.id
        value = sentinel.slave.get(key)
        err_msg = "Key should exist"
        assert value == str(1), err_msg

    @with_context
    def test_notify_news_admins(self):
        user = UserFactory.create(admin=False)
        user2 = UserFactory.create(admin=False)
        notify_news_admins()
        key = "notify:admin:%s" % user2.id
        value = sentinel.slave.get(key)
        err_msg = "Key should not exist"
        assert value is None, err_msg
