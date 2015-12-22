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
from twitter import Twitter, OAuth2, oauth2_dance


class _BulkTaskTwitterImport(object):

    importer_id = "twitter"
    DEFAULT_NUMBER_OF_TWEETS = 200

    def __init__(self, consumer_key, consumer_secret, source, max_tweets=None):
        bearer_token = oauth2_dance(consumer_key, consumer_secret)
        self.client = Twitter(auth=OAuth2(bearer_token=bearer_token))
        self.source = source
        self.count = max_tweets or self.DEFAULT_NUMBER_OF_TWEETS

    def tasks(self):
        statuses = self._get_statuses()
        tasks = [self._create_task_from_status(status) for status in statuses]
        return tasks[0:self.count]

    def count_tasks(self):
        return self.count

    def _get_statuses(self):
        if self._is_source_a_user_account():
            fetcher = self._fetch_statuses_from_account
        else:
            fetcher = self._fetch_statuses_from_search
        max_id = None
        partial_results = fetcher(q=self.source, count=self.count)
        results = []
        while len(results) < self.count and len(partial_results) > 0:
            results += partial_results
            remaining = self.count - len(results)
            max_id = min([status['id'] for status in partial_results]) - 1
            partial_results = fetcher(q=self.source, count=remaining, max_id=max_id)
        return results or partial_results

    def _is_source_a_user_account(self):
        return self.source and self.source.startswith('@')

    def _fetch_statuses_from_search(self, **kwargs):
        kwargs['q'] = kwargs['q'] + '-filter:retweets'
        return self.client.search.tweets(**kwargs).get('statuses')

    def _fetch_statuses_from_account(self, **kwargs):
        kwargs['screen_name'] = kwargs['q']
        del kwargs['q']
        return self.client.statuses.user_timeline(**kwargs)

    def _create_task_from_status(self, status):
        user_screen_name = status.get('user').get('screen_name')
        info = dict(status, user_screen_name=user_screen_name)
        return {'info': info}
