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
from twitter import Twitter, OAuth2, oauth2_dance, OAuth
from .base import BulkTaskImport


class BulkTaskTwitterImport(BulkTaskImport):

    importer_id = "twitter"
    DEFAULT_TWEETS = 200

    def __init__(self, consumer_key, consumer_secret, source, max_tweets=None, user_credentials=None):
        if user_credentials:
            self.client = UserCredentialsClient(consumer_key, consumer_secret, user_credentials)
        else:
            self.client = AppCredentialsClient(consumer_key, consumer_secret)
        self.source = source
        self.count = self.DEFAULT_TWEETS if max_tweets is None else max_tweets

    def tasks(self):
        statuses = self._get_statuses()
        tasks = [self._create_task_from_status(status) for status in statuses]
        return tasks[0:self.count]

    def count_tasks(self):
        return self.count

    def _get_statuses(self):
        if self._is_source_a_user_account():
            fetcher = self.client.fetch_statuses_from_account
        else:
            fetcher = self.client.fetch_statuses_from_search
        max_id = None
        partial_results = fetcher(q=self.source, count=self.count)
        if not self._using_user_credentials():
            return partial_results
        results = []
        while len(results) < self.count and len(partial_results) > 0:
            results += partial_results
            remaining = self.count - len(results)
            max_id = min([status['id'] for status in partial_results]) - 1
            partial_results = fetcher(q=self.source, count=remaining, max_id=max_id)
        return results or partial_results

    def _is_source_a_user_account(self):
        return self.source and self.source.startswith('@')

    def _using_user_credentials(self):
        return type(self.client) is UserCredentialsClient

    def _create_task_from_status(self, status):
        user_screen_name = status.get('user').get('screen_name')
        info = dict(status, user_screen_name=user_screen_name)
        return {'info': info}


class TwitterClient(object):

    NO_RETWEETS = '-filter:retweets'

    def fetch_statuses_from_search(self, **kwargs):
        kwargs['q'] = kwargs['q'] + self.NO_RETWEETS
        return self.api.search.tweets(**kwargs).get('statuses')

    def fetch_statuses_from_account(self, **kwargs):
        kwargs['screen_name'] = kwargs['q']
        del kwargs['q']
        return self.api.statuses.user_timeline(**kwargs)


class UserCredentialsClient(TwitterClient):

    def __init__(self, consumer_key, consumer_secret, user_credentials):
        credentials = json.loads(user_credentials)
        auth = OAuth(credentials['oauth_token'],
                     credentials['oauth_token_secret'],
                     consumer_key,
                     consumer_secret)
        self.api = Twitter(auth=auth)


class AppCredentialsClient(TwitterClient):

    def __init__(self, consumer_key, consumer_secret):
        bearer_token = oauth2_dance(consumer_key, consumer_secret)
        auth = OAuth2(bearer_token=bearer_token)
        self.api = Twitter(auth=auth)
