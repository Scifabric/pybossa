# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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
from pybossa.importers.youtubeapi import BulkTaskYoutubeImport

def create_importer_with_form_data(**form_data):
    with patch('pybossa.importers.youtubeapi.build'):
        form_data['youtube_api_server_key'] = 'apikey'
        importer = BulkTaskYoutubeImport(**form_data)
    importer.client.api = Mock()
    return importer


class TestBulkYoutubeImport(object):

    form_data = {
        'playlist_url': 'https://www.youtube.com/playlist?list=playlistid',
        'youtube_api_server_key': 'apikey'
    }

    def test_tasks_return_emtpy_list_if_no_video_to_import(self):
        form_data = {
            'playlist_url': '',
            'youtube_api_server_key': 'apikey'
        }
        number_of_tasks = BulkTaskYoutubeImport(**form_data).count_tasks()

        assert number_of_tasks == 0, number_of_tasks
