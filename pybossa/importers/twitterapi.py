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
from twitter import Twitter, OAuth


class _BulkTaskTwitterImport(object):

    importer_id = "twitter"

    def __init__(self, access_token, token_secret, consumer_key, consumer_secret):
        self.client = Twitter(auth=OAuth(
            access_token,
            token_secret,
            consumer_key,
            consumer_secret))

    def tasks(self, **form_data):
        if form_data.get('hashtag'):
            statuses = self._get_statuses(form_data.get('hashtag'))
            tasks = [self._create_task_from_status(status) for status in statuses]
            return tasks
        if form_data.get('user'):
            statuses = self._get_statuses_from_account(form_data.get('user'))
            tasks = [self._create_task_from_status(status) for status in statuses]
            return tasks
        return []

    def count_tasks(self, **form_data):
        if form_data.get('hashtag'):
            return len(self._get_statuses(form_data.get('hashtag')))
        if form_data.get('user'):
            return len(self._get_statuses_from_account(form_data.get('user')))
        return 0

    def _get_statuses_from_account(self, query):
        query_result = self.client.statuses.user_timeline(screen_name=query)
        return query_result

    def _get_statuses(self, query):
        search_result = self.client.search.tweets(q=query)
        return search_result.get('statuses')

    def _create_task_from_status(self, status):
        info = {
            'created_at': status.get('created_at'),
            'favorite_count': status.get('favorite_count'),
            'coordinates': status.get('coordinates'),
            'tweet_id': status.get('id_str'),
            'retweet_count': status.get('retweet_count'),
            'user_screen_name': status.get('user').get('screen_name'),
            'text': status.get('text')
        }
        return {'info': info}
