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

from mock import patch
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.youtubeapi import BulkTaskYoutubeImport

@patch('pybossa.importers.youtubeapi.build')
class TestBulkYoutubeImport(object):

    form_data = {
        'playlist_url': 'https://www.youtube.com/playlist?list=playlistid',
        'youtube_api_server_key': 'apikey'
    }

    short_playlist_response = {
      u'items': [
        {
          u'snippet': {
            u'playlistId': u'youtubeplaylistid1',
            u'thumbnails': {
              u'default': {
                u'url': u'https://i.ytimg.com/vi/youtubeid2/default.jpg',
                u'width': 120,
                u'height': 90
              },
              u'high': {
                u'url': u'https://i.ytimg.com/vi/youtubeid2/hqdefault.jpg',
                u'width': 480,
                u'height': 360
              },
              u'medium': {
                u'url': u'https://i.ytimg.com/vi/youtubeid2/mqdefault.jpg',
                u'width': 320,
                u'height': 180
              },
              u'maxres': {
                u'url': u'https://i.ytimg.com/vi/youtubeid2/maxresdefault.jpg',
                u'width': 1280,
                u'height': 720
              },
              u'standard': {
                u'url': u'https://i.ytimg.com/vi/youtubeid2/sddefault.jpg',
                u'width': 640,
                u'height': 480
              }
            },
            u'title': u'Best of Test Videos',
            u'resourceId': {
              u'kind': u'youtube#video',
              u'videoId': u'youtubeid2'
            },
            u'channelId': u'SomeChannelID',
            u'publishedAt': u'2016-03-11T18:58:52.000Z',
            u'channelTitle': u'Some Youtube Channel',
            u'position': 2,
            u'description': u'Another long text describing the video here'
          },
          u'kind': u'youtube#playlistItem',
          u'etag': u'\'somelongetaghere1\'',
          u'id': u'somelongidhere2'
        }
      ]
    }

    long_playlist_response = {
      u'items': [
        {
          u'snippet': {
            u'playlistId': u'youtubeplaylistid0',
            u'thumbnails': {
              u'default': {
                u'url': u'https://i.ytimg.com/vi/youtubeid0/default.jpg',
                u'width': 120,
                u'height': 90
              },
              u'high': {
                u'url': u'https://i.ytimg.com/vi/youtubeid0/hqdefault.jpg',
                u'width': 480,
                u'height': 360
              },
              u'medium': {
                u'url': u'https://i.ytimg.com/vi/youtubeid0/mqdefault.jpg',
                u'width': 320,
                u'height': 180
              },
              u'maxres': {
                u'url': u'https://i.ytimg.com/vi/youtubeid0/maxresdefault.jpg',
                u'width': 1280,
                u'height': 720
              },
              u'standard': {
                u'url': u'https://i.ytimg.com/vi/youtubeid0/sddefault.jpg',
                u'width': 640,
                u'height': 480
              }
            },
            u'title': u'First video',
            u'resourceId': {
              u'kind': u'youtube#video',
              u'videoId': u'youtubeid0'
            },
            u'channelId': u'SomeChannelID',
            u'publishedAt': u'2016-03-11T18:58:52.000Z',
            u'channelTitle': u'Some Youtube Channel',
            u'position': 0,
            u'description': u'Very first video in a long playlist'
          },
          u'kind': u'youtube#playlistItem',
          u'etag': u'\'somelongetaghere0\'',
          u'id': u'somelongidher0'
        },
        {
          u'snippet': {
            u'playlistId': u'youtubeplaylistid1',
            u'thumbnails': {
              u'default': {
                u'url': u'https://i.ytimg.com/vi/youtubeid1/default.jpg',
                u'width': 120,
                u'height': 90
              },
              u'high': {
                u'url': u'https://i.ytimg.com/vi/youtubeid1/hqdefault.jpg',
                u'width': 480,
                u'height': 360
              },
              u'medium': {
                u'url': u'https://i.ytimg.com/vi/youtubeid1/mqdefault.jpg',
                u'width': 320,
                u'height': 180
              },
              u'maxres': {
                u'url': u'https://i.ytimg.com/vi/youtubeid1/maxresdefault.jpg',
                u'width': 1280,
                u'height': 720
              },
              u'standard': {
                u'url': u'https://i.ytimg.com/vi/youtubeid1/sddefault.jpg',
                u'width': 640,
                u'height': 480
              }
            },
            u'title': u'Cool Video 1',
            u'resourceId': {
              u'kind': u'youtube#video',
              u'videoId': u'youtubeid1'
            },
            u'channelId': u'SomeChannelID',
            u'publishedAt': u'2016-03-15T05:47:01.000Z',
            u'channelTitle': u'Some Youtube Channel',
            u'position': 1,
            u'description': u'A long text describing the video here'
          },
          u'kind': u'youtube#playlistItem',
          u'etag': u'\'somelongetaghere2\'',
          u'id': u'somelongidhere1'
        },
      ],
      u'nextPageToken': 'someTokenId'
    }


    def test_tasks_return_emtpy_list_if_no_video_to_import(self, build):
        form_data = {
            'playlist_url': '',
            'youtube_api_server_key': 'apikey'
        }
        number_of_tasks = BulkTaskYoutubeImport(**form_data).count_tasks()

        assert number_of_tasks == 0, number_of_tasks

    def test_call_to_youtube_api_endpoint(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.return_value = self.short_playlist_response
        importer = BulkTaskYoutubeImport(**self.form_data)
        importer._fetch_all_youtube_videos('fakeId')
        
        build.assert_called_with('youtube', 'v3', developerKey=self.form_data['youtube_api_server_key'])

    def test_call_to_youtube_api_short_playlist(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.return_value = self.short_playlist_response
        importer = BulkTaskYoutubeImport(**self.form_data)
        playlist = importer._fetch_all_youtube_videos('fakeId')

        assert playlist == self.short_playlist_response, playlist

    def test_call_to_youtube_api_long_playlist(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.side_effect = [self.long_playlist_response, self.long_playlist_response, self.short_playlist_response]
        importer = BulkTaskYoutubeImport(**self.form_data)
        expected_playlist = {'items': ''}
        expected_playlist['items'] = self.long_playlist_response['items'] + self.long_playlist_response['items'] + self.short_playlist_response['items']
        playlist = importer._fetch_all_youtube_videos('fakeId')

        assert playlist == expected_playlist, playlist

    def test_extract_video_info_one_item(self, build):
        importer = BulkTaskYoutubeImport(**self.form_data)
        info = importer._extract_video_info(self.short_playlist_response['items'][0])

        assert info['info']['video_url'] == 'https://www.youtube.com/watch?v=youtubeid2'

    def test_parse_playlist_id(self, build):
        importer = BulkTaskYoutubeImport(**self.form_data)
        id = importer._get_playlist_id('https://www.youtube.com/playlist?list=goodplaylist')
        assert id == 'goodplaylist'
        id = importer._get_playlist_id('https://www.youtube.com/watch?v=youtubeid&list=anotherplaylist&option=2')
        assert id == 'anotherplaylist'
        # no playlist
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://www.youtube.com/watch?v=youtubeid')
        # malformed url
        assert_raises(BulkImportException, importer._get_playlist_id, 'www.youtube.com/watch?v=youtubeid&list=anotherplaylist&option=2')

    def test_non_youtube_url_raises_exception(self, build):
        importer = BulkTaskYoutubeImport(**self.form_data)
        id = importer._get_playlist_id('https://www.youtu.be/playlist?list=goodplaylist')
        assert id == 'goodplaylist'
        id = importer._get_playlist_id('https://youtu.be/playlist?list=goodplaylist')
        assert id == 'goodplaylist'
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://youtubee.com/playlist?list=goodplaylist')
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://api.youtube.com/playlist?list=goodplaylist')
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://otherdomain.com/playlist?list=goodplaylist')

    def test_all_coverage_tasks_extraction(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.return_value = self.short_playlist_response
        importer = BulkTaskYoutubeImport(**self.form_data)
        tasks = importer.tasks()

        assert tasks == [{u'info': {u'oembed': '<iframe width="512" height="512" src="https://www.youtube.com/embed/youtubeid2" frameborder="0" allowfullscreen></iframe>',
            'video_url': u'https://www.youtube.com/watch?v=youtubeid2'}}]
