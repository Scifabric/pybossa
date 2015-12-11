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


from mock import patch, Mock
from pybossa.importers import BulkImportException
from pybossa.importers.twitterapi import _BulkTaskTwitterImport


class Test_BulkTaskTwitterImportSearchHashtag(object):

    importer = _BulkTaskTwitterImport('access_token',
                                      'token_secret',
                                      'consumer_key',
                                      'consumer_secret')

    no_results = {
        u'search_metadata': {
            u'count': 15,
            u'completed_in': 0.018,
            u'max_id_str':u'673928446372945921',
            u'since_id_str': u'0',
            u'refresh_url': u'?since_id=673928446372945921&q=%23noMatches&include_entities=1',
            u'since_id': 0,
            u'query': u'%23noMatches',
            u'max_id': 673928446372945921L
            },
        u'statuses': []
    }
    one_status = {
        u'search_metadata': {
            u'count': 15,
            u'completed_in': 0.018,
            u'max_id_str':u'673928446372945921',
            u'since_id_str': u'0',
            u'refresh_url': u'?since_id=673928446372945921&q=%23noMatches&include_entities=1',
            u'since_id': 0,
            u'query': u'%23noMatches',
            u'max_id': 673928446372945921L
            },
        u'statuses': [
            {
                u'created_at': 'created',
                u'favorite_count': 77,
                u'coordinates': 'coords',
                u'id_str': '1234',
                u'retweet_count': 44,
                u'user': {'screen_name': 'fulanito'},
                u'text': 'this is a tweet #match'
            }
        ]
    }

    @patch.object(importer, 'client')
    def test_count_tasks_return_0_if_no_tweets_match_search(self, client):
        client.search.tweets.return_value = self.no_results
        form_data = {'hashtag': '#noMatches'}

        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 0, number_of_tasks

    @patch.object(importer, 'client')
    def test_count_tasks_return_1_if_1_tweet_matches_search(self, client):
        client.search.tweets.return_value = self.one_status
        form_data = {'hashtag': '#match'}

        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 1, number_of_tasks

    @patch.object(importer, 'client')
    def test_tasks_return_task_dict_with_info_from_query_result(self, client):
        client.search.tweets.return_value = self.one_status
        form_data = {'hashtag': '#match'}
        expected_task_data = self.one_status['statuses'][0]

        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == 1, tasks
        info = tasks[0]['info']
        assert info['created_at'] == expected_task_data['created_at']
        assert info['favorite_count'] == expected_task_data['favorite_count']
        assert info['coordinates'] == expected_task_data['coordinates']
        assert info['tweet_id'] == expected_task_data['id_str']
        assert info['retweet_count'] == expected_task_data['retweet_count']
        assert info['user_screen_name'] == expected_task_data['user']['screen_name']
        assert info['text'] == expected_task_data['text']
