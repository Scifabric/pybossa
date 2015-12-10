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

TWITTER_CONSUMER_KEY = 'hJTTkwD5jJze9TFvfHX4HC69z'
TWITTER_CONSUMER_SECRET = 'BD5MVfao6Mb7mJDGf9AqJ1sAaTt7U5jfhOvCGuaCo7n2lzNsLS'
TWITTER_ACCESS_TOKEN = '2163950446-okkpWxsi25vj594NR49bUfgaXobn3e915eeWRqX'
TWITTER_TOKEN_SECRET = 'kyC3NdPqZFkcQ35CxaaDEUmr5zR7VZuGejZtQjGtOoaGf'


class _BulkTaskTwitterImport(object):

    importer_id = "twitter"
    client = Twitter(auth=OAuth(
        TWITTER_ACCESS_TOKEN,
        TWITTER_TOKEN_SECRET,
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET))

    def tasks(self, **form_data):
        if form_data.get('hashtag'):
            pass
        return self._get_tasks_data_from_request(album_info)

    def count_tasks(self, **form_data):
        album_info = self._get_album_info(form_data['album_id'])
        return int(album_info['total'])
