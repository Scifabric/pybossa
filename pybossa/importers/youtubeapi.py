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
from .base import BulkTaskImport, BulkImportException

# TODO: therealmarv

class BulkTaskYoutubeImport(BulkTaskImport):

    importer_id = "youtube"

    def __init__(self, consumer_key, consumer_secret, source,
                 max_tweets=None, last_import_meta=None, user_credentials=None):
        pass
        # if user_credentials:
        #     self.client = UserCredentialsClient(consumer_key, consumer_secret,
        #                                         user_credentials)
        # else:
        #     self.client = AppCredentialsClient(consumer_key, consumer_secret)
        # self.source = source
        # self.count = self.DEFAULT_TWEETS if max_tweets is None else max_tweets
        # self.last_import_meta = last_import_meta
        # self._tasks = None

    def tasks(self):
        # if self._tasks is None:
        #     statuses = self._get_statuses()
        #     tasks = [self._create_task_from_status(status) for status in statuses]
        #     self._tasks = tasks[0:self.count]
        return self._tasks

    def count_tasks(self):
        return self.count

    def import_metadata(self):
        return None if self._tasks is None else self._extract_metadata()

    def _extract_metadata(self):
        return {'last_id': max(t['info']['id'] for t in self._tasks)}

    def _get_statuses(self):
        meta = self.last_import_meta
        last_id = None if meta is None else meta.get('last_id')
        return self.client.fetch_all_statuses(source=self.source,
                                              count=self.count,
                                              since_id=last_id)

    def _create_task_from_status(self, status):
        user_screen_name = status.get('user').get('screen_name')
        info = dict(status, user_screen_name=user_screen_name)
        return {'info': info}