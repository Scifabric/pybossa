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
from nose.tools import assert_raises
from twitter import TwitterHTTPError
from pybossa.importers import BulkImportException
from pybossa.importers.twitterapi import BulkTaskTwitterImport


def create_importer_with_form_data(**form_data):
    with patch('pybossa.importers.twitterapi.oauth2_dance'):
        form_data['consumer_key'] = 'consumer_key'
        form_data['consumer_secret'] = 'consumer_secret'
        importer = BulkTaskTwitterImport(**form_data)
    importer.client.api = Mock()
    return importer


class TestBulkTaskTwitterImportSearch(object):

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

    def test_count_tasks_returns_number_of_tweets_requested(self):
        max_tweets = 10
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets.return_value = self.one_status

        number_of_tasks = importer.count_tasks()

        assert number_of_tasks == number_of_tasks, number_of_tasks

    def test_tasks_return_task_dict_with_info_from_query_result(self):
        form_data = {'source': '#match', 'max_tweets': 1}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets.return_value = self.one_status
        expected_task_data = self.one_status['statuses'][0]

        tasks = importer.tasks()

        assert len(tasks) == 1, tasks
        info = tasks[0]['info']
        assert info['created_at'] == expected_task_data['created_at']
        assert info['favorite_count'] == expected_task_data['favorite_count']
        assert info['coordinates'] == expected_task_data['coordinates']
        assert info['id'] == expected_task_data['id']
        assert info['retweet_count'] == expected_task_data['retweet_count']
        assert info['user_screen_name'] == expected_task_data['user']['screen_name']
        assert info['user'] == expected_task_data['user']
        assert info['text'] == expected_task_data['text']

    def test_tasks_can_return_more_than_returned_by_single_api_call(self):
        responses = [self.no_results, self.one_status, self.five_statuses]
        def multiple_responses(*args, **kwargs):
            return responses.pop()

        max_tweets = 10
        form_data = {
            'source': '#hashtag',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = multiple_responses

        tasks = importer.tasks()

        assert len(tasks) == 6, len(tasks)

    def test_tasks_does_not_return_more_than_requested_even_if_api_do(self):
        max_tweets = 2
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets.return_value = self.five_statuses

        tasks = importer.tasks()

        assert len(tasks) == max_tweets, len(tasks)

    def test_api_calls_with_max_id_pagination(self):
        responses = [self.no_results, self.one_status, self.five_statuses]
        calls = []
        def multiple_responses(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return responses.pop()

        max_tweets = 6
        form_data = {
            'source': '#hashtag',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = multiple_responses

        tasks = importer.tasks()

        assert calls[0]['kwargs']['count'] == 6, calls[0]['kwargs']
        assert calls[0]['kwargs']['q'] == form_data['source'] + '-filter:retweets', calls[0]['kwargs']
        assert calls[1]['kwargs']['count'] == 1, calls[1]['kwargs']
        assert calls[1]['kwargs']['max_id'] == 0, calls[1]['kwargs']
        assert calls[2]['kwargs']['count'] == 0, calls[2]['kwargs']
        assert calls[2]['kwargs']['max_id'] == -1, calls[2]['kwargs']

    def test_max_tweets_gets_a_default_value_of_200(self):
        calls = []
        def response(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return self.five_statuses

        form_data = {'source': '#match'}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = response

        tasks = importer.tasks()

        assert calls[0]['kwargs']['count'] == 200, calls[0]['kwargs']['count']

    @patch('pybossa.importers.twitterapi.OAuth')
    @patch('pybossa.importers.twitterapi.OAuth2')
    def test_user_credentials_are_used_when_provided(self, oauth2, oauth):
        form_data = {
            'source': '#hashtag',
            'max_tweets': 500,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }

        importer = create_importer_with_form_data(**form_data)

        oauth.assert_called_with('token', 'secret', 'consumer_key', 'consumer_secret')
        oauth2.assert_not_called()

    @patch('pybossa.importers.twitterapi.OAuth')
    @patch('pybossa.importers.twitterapi.OAuth2')
    def test_app_credentials_are_used_when_no_user_ones_provided(self, oauth2, oauth):
        form_data = {'source': '#hashtag'}

        importer = create_importer_with_form_data(**form_data)

        oauth.assert_not_called()
        assert oauth2.called

    def test_only_one_api_call_is_made_when_using_app_credentials(self):
        responses = [self.no_results, self.five_statuses]
        api_calls = []
        def multiple_responses(*args, **kwargs):
            api_calls.append({'args': args, 'kwargs': kwargs})
            return responses.pop()

        max_tweets = 10
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = multiple_responses

        tasks = importer.tasks()

        assert len(api_calls) == 1, api_calls

    def test_tasks_raises_exception_on_twitter_client_error(self):
        def response(*args, **kwargs):
            class HTTPError(object):
                code = 401
                headers = {}
                fp = Mock()
                fp.read.return_value = []
            raise TwitterHTTPError(HTTPError, "api.twitter.com", None, None)

        max_tweets = 10
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = response

        assert_raises(BulkImportException, importer.tasks)

    def test_tasks_raises_exception_on_rate_limit_error(self):
        def response(*args, **kwargs):
            class HTTPError(object):
                code = 429
                headers = {}
                fp = Mock()
                fp.read.return_value = []
            raise TwitterHTTPError(HTTPError, "api.twitter.com", None, None)

        max_tweets = 10
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = response

        assert_raises(BulkImportException, importer.tasks)

        try:
            importer.tasks()
        except BulkImportException as e:
            assert e.message == "Rate limit for Twitter API reached. Please, try again in 15 minutes.", e.message

    def test_metadata_is_used_for_twitter_api_call_if_present(self):
        form_data = {
            'source': '#hashtag',
            'max_tweets': 500,
            'last_import_meta': {'last_id': 3},
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets.return_value = {'statuses': []}

        tasks = importer.tasks()

        importer.client.api.search.tweets.assert_called_with(
            count=500,
            q='#hashtag-filter:retweets',
            since_id=3)

    def test_import_metadata_returns_None_before_fetching_tasks(self):
        responses = [self.no_results, self.five_statuses]
        def multiple_responses(*args, **kwargs):
            return responses.pop()

        max_tweets = 10
        form_data = {
            'source': '#hashtag',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = multiple_responses

        assert importer.import_metadata() == None, importer.import_metadata()

    def test_import_metadata_returns_greatest_id_of_imported_tweets(self):
        responses = [self.no_results, self.five_statuses]
        def multiple_responses(*args, **kwargs):
            return responses.pop()

        max_tweets = 10
        form_data = {
            'source': '#hashtag',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets = multiple_responses
        expected_metadata = {'last_id': 5}

        tasks = importer.tasks()
        metadata = importer.import_metadata()
        assert metadata == expected_metadata, metadata


class TestBulkTaskTwitterImportFromAccount(object):

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

    def test_count_tasks_returns_number_of_tweets_requested(self):
        max_tweets = 10
        form_data = {'source': '@pybossa', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline.return_value = self.no_results

        number_of_tasks = importer.count_tasks()

        assert number_of_tasks == number_of_tasks, number_of_tasks

    def test_tasks_return_task_dict_with_info_from_query_result(self):
        form_data = {'source': '@pybossa', 'max_tweets': 1}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline.return_value = self.one_status
        expected_task_data = self.one_status[0]

        tasks = importer.tasks()

        assert len(tasks) == 1, tasks
        info = tasks[0]['info']
        assert info['created_at'] == expected_task_data['created_at']
        assert info['favorite_count'] == expected_task_data['favorite_count']
        assert info['coordinates'] == expected_task_data['coordinates']
        assert info['id'] == expected_task_data['id']
        assert info['retweet_count'] == expected_task_data['retweet_count']
        assert info['user_screen_name'] == expected_task_data['user']['screen_name']
        assert info['user'] == expected_task_data['user']
        assert info['text'] == expected_task_data['text']

    def test_task_can_return_more_than_returned_by_single_api_call(self):
        responses = [self.no_results, self.one_status, self.five_statuses]
        def multiple_responses(*args, **kwargs):
            return responses.pop()

        max_tweets = 10
        form_data = {
            'source': '@pybossa',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline = multiple_responses

        tasks = importer.tasks()

        assert len(tasks) == 6, len(tasks)

    def test_task_does_not_return_more_than_requested_even_if_api_do(self):
        max_tweets = 2
        form_data = {'source': '@pybossa', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline.return_value = self.five_statuses

        tasks = importer.tasks()

        assert len(tasks) == max_tweets, len(tasks)

    def test_api_calls_with_max_id_pagination(self):
        responses = [self.no_results, self.one_status, self.five_statuses]
        calls = []
        def multiple_responses(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return responses.pop()

        max_tweets = 6
        form_data = {
            'source': '@pybossa',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline = multiple_responses

        tasks = importer.tasks()

        assert calls[0]['kwargs']['count'] == 6, calls[0]['kwargs']
        assert calls[0]['kwargs'].get('q') is None, calls[0]['kwargs']
        assert calls[0]['kwargs']['screen_name'] == form_data['source']
        assert calls[1]['kwargs']['count'] == 1, calls[1]['kwargs']
        assert calls[1]['kwargs']['max_id'] == 0, calls[1]['kwargs']
        assert calls[2]['kwargs']['count'] == 0, calls[2]['kwargs']
        assert calls[2]['kwargs']['max_id'] == -1, calls[2]['kwargs']

    def test_tasks_raises_exception_on_twitter_client_error(self):
        def response(*args, **kwargs):
            class HTTPError(object):
                code = 401
                headers = {}
                fp = Mock()
                fp.read.return_value = []
            raise TwitterHTTPError(HTTPError, "api.twitter.com", None, None)

        max_tweets = 10
        form_data = {'source': '@pybossa', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline = response

        assert_raises(BulkImportException, importer.tasks)

    def test_if_last_import_meta_is_None_since_id_is_not_passed_to_twitter_client(self):
        responses = [self.no_results, self.five_statuses]
        calls = []
        def multiple_responses(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return responses.pop()

        max_tweets = 3
        form_data = {
            'source': '@pybossa',
            'max_tweets': max_tweets,
            'user_credentials': '{"oauth_token_secret": "secret", "oauth_token": "token"}'
        }
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline = multiple_responses

        tasks = importer.tasks()

        assert 'since_id' not in calls[0]['kwargs'].keys(), calls[0]['kwargs']
