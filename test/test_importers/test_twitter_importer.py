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

    def create_status(_id):
        return {
            u'created_at': 'created',
            u'favorite_count': 77,
            u'coordinates': 'coords',
            u'id_str': unicode(_id),
            u'id': _id,
            u'retweet_count': 44,
            u'user': {'screen_name': 'fulanito'},
            u'text': 'this is a tweet #match'
        }

    no_results = {
        u'statuses': []
    }

    one_status = {
        u'statuses': [
            create_status(0)
        ]
    }

    five_statuses = {
        u'statuses': [create_status(i+1) for i in range(5)]
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

    @patch.object(importer, 'client')
    def test_task_can_return_more_than_returned_by_single_api_call(self, client):
        responses = [self.no_results, self.one_status, self.five_statuses]
        def multiple_responses(*args, **kwargs):
            return responses.pop()

        client.search.tweets = multiple_responses
        max_tweets = 10
        form_data = {'hashtag': '#match', 'max_tweets': max_tweets}

        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == 6, len(tasks)

    @patch.object(importer, 'client')
    def test_task_does_not_return_more_than_requested_even_if_api_do(self, client):
        client.search.tweets.return_value = self.five_statuses
        max_tweets = 2
        form_data = {'hashtag': '#match', 'max_tweets': max_tweets}

        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == max_tweets, len(tasks)

    @patch.object(importer, 'client')
    def test_api_calls_with_max_id_pagination(self, client):
        responses = [self.no_results, self.one_status, self.five_statuses]
        calls = []
        def multiple_responses(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return responses.pop()

        client.search.tweets = multiple_responses
        max_tweets = 6
        form_data = {'hashtag': '#match', 'max_tweets': max_tweets}

        tasks = self.importer.tasks(**form_data)

        assert calls[0]['kwargs']['count'] == 6, calls[0]['kwargs']
        assert calls[1]['kwargs']['count'] == 1, calls[1]['kwargs']
        assert calls[1]['kwargs']['max_id'] == 0, calls[1]['kwargs']
        assert calls[2]['kwargs']['count'] == 0, calls[2]['kwargs']
        assert calls[2]['kwargs']['max_id'] == -1, calls[2]['kwargs']


class Test_BulkTaskTwitterImportFromAccount(object):

    importer = _BulkTaskTwitterImport('access_token',
                                      'token_secret',
                                      'consumer_key',
                                      'consumer_secret')

    def create_status(_id):
        return {
            u'contributors': None,
            u'truncated': False,
            u'text': u'Burning news! PyBossa v1.2.1 released! This version gets all new @PyBossa releases in your admin page! https://t.co/WkOXc3YL6s',
            u'is_quote_status': False,
            u'in_reply_to_status_id': None,
            u'id': _id,
            u'favorite_count': 0,
            u'source': u'<a href="https://about.twitter.com/products/tweetdeck" rel="nofollow">TweetDeck</a>',
            u'retweeted': False,
            u'coordinates': None,
            u'entities': {},
            u'in_reply_to_screen_name': None,
            u'id_str': unicode(_id),
            u'retweet_count': 0,
            u'in_reply_to_user_id': None,
            u'favorited': False,
            u'user': {
                u'follow_request_sent': False,
                u'has_extended_profile': False,
                u'profile_use_background_image': True,
                u'default_profile_image': False,
                u'id': 497181885,
                u'profile_background_image_url_https': u'https://abs.twimg.com/images/themes/theme1/bg.png',
                u'verified': False,
                u'profile_text_color': u'333333',
                u'profile_image_url_https': u'https://pbs.twimg.com/profile_images/446669937927389184/vkDC_c3s_normal.png',
                u'profile_sidebar_fill_color': u'DDEEF6',
                u'entities': {},
                u'followers_count': 700,
                u'profile_sidebar_border_color': u'C0DEED',
                u'id_str': u'497181885',
                u'profile_background_color': u'C0DEED',
                u'listed_count': 41,
                u'is_translation_enabled': False,
                u'utc_offset': 3600,
                u'statuses_count': 887,
                u'description': u'The open source crowdsourcing platform for research built by @Scifabric',
                u'friends_count': 731,
                u'location': u'Madrid, Spain',
                u'profile_link_color': u'EE7147',
                u'profile_image_url': u'http://pbs.twimg.com/profile_images/446669937927389184/vkDC_c3s_normal.png',
                u'following': True,
                u'geo_enabled': True,
                u'profile_banner_url': u'https://pbs.twimg.com/profile_banners/497181885/1401885123',
                u'profile_background_image_url': u'http://abs.twimg.com/images/themes/theme1/bg.png',
                u'screen_name': u'PyBossa',
                u'lang': u'en',
                u'profile_background_tile': False,
                u'favourites_count': 185,
                u'name': u'PyBossa',
                u'notifications': False,
                u'url': u'http://t.co/ASSBcIRZjY',
                u'created_at': u'Sun Feb 19 18:17:39 +0000 2012',
                u'contributors_enabled': False,
                u'time_zone': u'Amsterdam',
                u'protected': False,
                u'default_profile': False,
                u'is_translator': False
            },
            u'geo': None,
            u'in_reply_to_user_id_str': None,
            u'possibly_sensitive': False,
            u'lang': u'en',
            u'created_at': u'Thu Dec 03 15:09:07 +0000 2015',
            u'in_reply_to_status_id_str': None,
            u'place': None,
            u'extended_entities': {}
        }

    no_results = []

    one_status = [create_status(0)]

    five_statuses = [create_status(i+1) for i in range(5)]

    @patch.object(importer, 'client')
    def test_count_tasks_return_0_if_no_tweets_match_search(self, client):
        client.statuses.user_timeline.return_value = self.no_results
        form_data = {'user': '@pybossa'}

        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 0, number_of_tasks

    @patch.object(importer, 'client')
    def test_count_tasks_return_1_if_1_tweet_matches_search(self, client):
        client.statuses.user_timeline.return_value = self.one_status
        form_data = {'user': '@pybossa'}

        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 1, number_of_tasks

    @patch.object(importer, 'client')
    def test_tasks_return_task_dict_with_info_from_query_result(self, client):
        client.statuses.user_timeline.return_value = self.one_status
        form_data = {'user': '@pybossa'}
        expected_task_data = self.one_status[0]

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

    @patch.object(importer, 'client')
    def test_task_can_return_more_than_returned_by_single_api_call(self, client):
        responses = [self.no_results, self.one_status, self.five_statuses]
        def multiple_responses(*args, **kwargs):
            return responses.pop()

        client.statuses.user_timeline = multiple_responses
        max_tweets = 10
        form_data = {'user': '@pybossa', 'max_tweets': max_tweets}

        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == 6, len(tasks)

    @patch.object(importer, 'client')
    def test_task_does_not_return_more_than_requested_even_if_api_do(self, client):
        client.statuses.user_timeline.return_value = self.five_statuses
        max_tweets = 2
        form_data = {'user': '@pybossa', 'max_tweets': max_tweets}

        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == max_tweets, len(tasks)

    @patch.object(importer, 'client')
    def test_api_calls_with_max_id_pagination(self, client):
        responses = [self.no_results, self.one_status, self.five_statuses]
        calls = []
        def multiple_responses(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return responses.pop()

        client.statuses.user_timeline = multiple_responses
        max_tweets = 6
        form_data = {'user': '@pybossa', 'max_tweets': max_tweets}

        tasks = self.importer.tasks(**form_data)

        assert calls[0]['kwargs']['count'] == 6, calls[0]['kwargs']
        assert calls[1]['kwargs']['count'] == 1, calls[1]['kwargs']
        assert calls[1]['kwargs']['max_id'] == 0, calls[1]['kwargs']
        assert calls[2]['kwargs']['count'] == 0, calls[2]['kwargs']
        assert calls[2]['kwargs']['max_id'] == -1, calls[2]['kwargs']
