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
from default import Test, with_context
from pybossa.news import get_news
from pybossa.core import sentinel
try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

myset = 'scifabricnews'

class TestNews(Test):

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
        sentinel.master.zadd(myset, 0, pickle.dumps(self.news))
        news = get_news()
        assert len(news) == 1, len(news)
        news[0]['updated'] == self.news['updated'], news

    @with_context
    def test_get_news_with_score(self):
        sentinel.master.zadd(myset, 0, pickle.dumps(self.news))
        news = get_news(score=1)
        assert len(news) == 0, len(news)
