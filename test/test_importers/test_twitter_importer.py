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


from mock import patch, Mock
from nose.tools import assert_raises
from twitter import TwitterHTTPError
from pybossa.importers import BulkImportException
from pybossa.importers.twitterapi import BulkTaskTwitterImport
from default import with_context


def create_importer_with_form_data(**form_data):
    with patch('pybossa.importers.twitterapi.oauth2_dance'):
        form_data['consumer_key'] = 'consumer_key'
        form_data['consumer_secret'] = 'consumer_secret'
        importer = BulkTaskTwitterImport(**form_data)
    importer.client.api = Mock()
    return importer

@with_context
def create_status(_id):
    return {
        'created_at': 'created',
        'favorite_count': 77,
        'coordinates': 'coords',
        'id_str': str(_id),
        'id': _id,
        'retweet_count': 44,
        'user': {'screen_name': 'fulanito'},
        'text': 'this is a tweet #match'
    }


class TestBulkTaskTwitterImportSearch(object):

    no_results = {
        'statuses': []
    }

    one_status = {
        'statuses': [
            create_status(0)
        ]
    }

    five_statuses = {
        'statuses': [create_status(i+1) for i in range(5)]
    }

    @with_context
    def test_count_tasks_returns_number_of_tweets_requested(self):
        max_tweets = 10
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets.return_value = self.one_status

        number_of_tasks = importer.count_tasks()

        assert number_of_tasks == number_of_tasks, number_of_tasks

    @with_context
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

    @with_context
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

    @with_context
    def test_tasks_does_not_return_more_than_requested_even_if_api_do(self):
        max_tweets = 2
        form_data = {'source': '#match', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.search.tweets.return_value = self.five_statuses

        tasks = importer.tasks()

        assert len(tasks) == max_tweets, len(tasks)

    @with_context
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

    @with_context
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

    @with_context
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

    @with_context
    @patch('pybossa.importers.twitterapi.OAuth')
    @patch('pybossa.importers.twitterapi.OAuth2')
    def test_app_credentials_are_used_when_no_user_ones_provided(self, oauth2, oauth):
        form_data = {'source': '#hashtag'}

        importer = create_importer_with_form_data(**form_data)

        oauth.assert_not_called()
        assert oauth2.called

    @with_context
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

    @with_context
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

    @with_context
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
            assert str(e) == "Rate limit for Twitter API reached. Please, try again in 15 minutes.", e.message

    @with_context
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

    @with_context
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

    @with_context
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


def create_status_alt(_id):
    return {
        'contributors': None,
        'truncated': False,
        'text': 'Burning news! PYBOSSA v1.2.1 released! This version gets all new @PYBOSSA releases in your admin page! https://t.co/WkOXc3YL6s',
        'is_quote_status': False,
        'in_reply_to_status_id': None,
        'id': _id,
        'favorite_count': 0,
        'source': '<a href="https://about.twitter.com/products/tweetdeck" rel="nofollow">TweetDeck</a>',
        'retweeted': False,
        'coordinates': None,
        'entities': {},
        'in_reply_to_screen_name': None,
        'id_str': str(_id),
        'retweet_count': 0,
        'in_reply_to_user_id': None,
        'favorited': False,
        'user': {
            'follow_request_sent': False,
            'has_extended_profile': False,
            'profile_use_background_image': True,
            'default_profile_image': False,
            'id': 497181885,
            'profile_background_image_url_https': 'https://abs.twimg.com/images/themes/theme1/bg.png',
            'verified': False,
            'profile_text_color': '333333',
            'profile_image_url_https': 'https://pbs.twimg.com/profile_images/446669937927389184/vkDC_c3s_normal.png',
            'profile_sidebar_fill_color': 'DDEEF6',
            'entities': {},
            'followers_count': 700,
            'profile_sidebar_border_color': 'C0DEED',
            'id_str': '497181885',
            'profile_background_color': 'C0DEED',
            'listed_count': 41,
            'is_translation_enabled': False,
            'utc_offset': 3600,
            'statuses_count': 887,
            'description': 'The open source crowdsourcing platform for research built by @Scifabric',
            'friends_count': 731,
            'location': 'Madrid, Spain',
            'profile_link_color': 'EE7147',
            'profile_image_url': 'http://pbs.twimg.com/profile_images/446669937927389184/vkDC_c3s_normal.png',
            'following': True,
            'geo_enabled': True,
            'profile_banner_url': 'https://pbs.twimg.com/profile_banners/497181885/1401885123',
            'profile_background_image_url': 'http://abs.twimg.com/images/themes/theme1/bg.png',
            'screen_name': 'PYBOSSA',
            'lang': 'en',
            'profile_background_tile': False,
            'favourites_count': 185,
            'name': 'PYBOSSA',
            'notifications': False,
            'url': 'http://t.co/ASSBcIRZjY',
            'created_at': 'Sun Feb 19 18:17:39 +0000 2012',
            'contributors_enabled': False,
            'time_zone': 'Amsterdam',
            'protected': False,
            'default_profile': False,
            'is_translator': False
        },
        'geo': None,
        'in_reply_to_user_id_str': None,
        'possibly_sensitive': False,
        'lang': 'en',
        'created_at': 'Thu Dec 03 15:09:07 +0000 2015',
        'in_reply_to_status_id_str': None,
        'place': None,
        'extended_entities': {}
    }


class TestBulkTaskTwitterImportFromAccount(object):


    no_results = []

    one_status = [create_status_alt(0)]

    five_statuses = [create_status_alt(i+1) for i in range(5)]

    @with_context
    def test_count_tasks_returns_number_of_tweets_requested(self):
        max_tweets = 10
        form_data = {'source': '@pybossa', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline.return_value = self.no_results

        number_of_tasks = importer.count_tasks()

        assert number_of_tasks == number_of_tasks, number_of_tasks

    @with_context
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

    @with_context
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

    @with_context
    def test_task_does_not_return_more_than_requested_even_if_api_do(self):
        max_tweets = 2
        form_data = {'source': '@pybossa', 'max_tweets': max_tweets}
        importer = create_importer_with_form_data(**form_data)
        importer.client.api.statuses.user_timeline.return_value = self.five_statuses

        tasks = importer.tasks()

        assert len(tasks) == max_tweets, len(tasks)

    @with_context
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

    @with_context
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

    @with_context
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

        assert 'since_id' not in list(calls[0]['kwargs'].keys()), calls[0]['kwargs']
