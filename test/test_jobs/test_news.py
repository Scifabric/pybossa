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

import json
from pybossa.jobs import news
from pybossa.news import get_news
from default import Test, with_context, FakeResponse, db
from factories import ProjectFactory
from factories import TaskFactory
from factories import TaskRunFactory
from redis import StrictRedis
from mock import patch, MagicMock


class TestNews(Test):

    d = MagicMock()
    d.entries = [dict(updated='2015-01-01')]

    def setUp(self):
        super(TestNews, self).setUp()
        self.connection = StrictRedis()
        self.connection.flushall()

    @with_context
    @patch('feedparser.parse')
    def test_webhooks(self, feedparser_mock):
        """Test NEWS works."""
        feedparser_mock.return_value = self.d
        news()
        tmp = get_news()
        assert len(tmp) == 1, len(tmp)

    @with_context
    @patch('feedparser.parse')
    def test_webhooks_no_new_items(self, feedparser_mock):
        """Test NEWS no new items works."""
        feedparser_mock.return_value = self.d
        news()
        feedparser_mock.return_value = self.d
        news()
        tmp = get_news()
        assert len(tmp) == 1, len(tmp)
