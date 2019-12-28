# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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

from mock import patch
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.youtubeapi import BulkTaskYoutubeImport
from default import with_context

@patch('pybossa.importers.youtubeapi.build')
class TestBulkYoutubeImport(object):

    form_data = {
        'playlist_url': 'https://www.youtube.com/playlist?list=playlistid',
        'youtube_api_server_key': 'apikey'
    }

    short_playlist_response = {
      'items': [
        {
          'snippet': {
            'playlistId': 'youtubeplaylistid1',
            'thumbnails': {
              'default': {
                'url': 'https://i.ytimg.com/vi/youtubeid2/default.jpg',
                'width': 120,
                'height': 90
              },
              'high': {
                'url': 'https://i.ytimg.com/vi/youtubeid2/hqdefault.jpg',
                'width': 480,
                'height': 360
              },
              'medium': {
                'url': 'https://i.ytimg.com/vi/youtubeid2/mqdefault.jpg',
                'width': 320,
                'height': 180
              },
              'maxres': {
                'url': 'https://i.ytimg.com/vi/youtubeid2/maxresdefault.jpg',
                'width': 1280,
                'height': 720
              },
              'standard': {
                'url': 'https://i.ytimg.com/vi/youtubeid2/sddefault.jpg',
                'width': 640,
                'height': 480
              }
            },
            'title': 'Best of Test Videos',
            'resourceId': {
              'kind': 'youtube#video',
              'videoId': 'youtubeid2'
            },
            'channelId': 'SomeChannelID',
            'publishedAt': '2016-03-11T18:58:52.000Z',
            'channelTitle': 'Some Youtube Channel',
            'position': 2,
            'description': 'Another long text describing the video here'
          },
          'kind': 'youtube#playlistItem',
          'etag': '\'somelongetaghere1\'',
          'id': 'somelongidhere2'
        }
      ]
    }

    long_playlist_response = {
      'items': [
        {
          'snippet': {
            'playlistId': 'youtubeplaylistid0',
            'thumbnails': {
              'default': {
                'url': 'https://i.ytimg.com/vi/youtubeid0/default.jpg',
                'width': 120,
                'height': 90
              },
              'high': {
                'url': 'https://i.ytimg.com/vi/youtubeid0/hqdefault.jpg',
                'width': 480,
                'height': 360
              },
              'medium': {
                'url': 'https://i.ytimg.com/vi/youtubeid0/mqdefault.jpg',
                'width': 320,
                'height': 180
              },
              'maxres': {
                'url': 'https://i.ytimg.com/vi/youtubeid0/maxresdefault.jpg',
                'width': 1280,
                'height': 720
              },
              'standard': {
                'url': 'https://i.ytimg.com/vi/youtubeid0/sddefault.jpg',
                'width': 640,
                'height': 480
              }
            },
            'title': 'First video',
            'resourceId': {
              'kind': 'youtube#video',
              'videoId': 'youtubeid0'
            },
            'channelId': 'SomeChannelID',
            'publishedAt': '2016-03-11T18:58:52.000Z',
            'channelTitle': 'Some Youtube Channel',
            'position': 0,
            'description': 'Very first video in a long playlist'
          },
          'kind': 'youtube#playlistItem',
          'etag': '\'somelongetaghere0\'',
          'id': 'somelongidher0'
        },
        {
          'snippet': {
            'playlistId': 'youtubeplaylistid1',
            'thumbnails': {
              'default': {
                'url': 'https://i.ytimg.com/vi/youtubeid1/default.jpg',
                'width': 120,
                'height': 90
              },
              'high': {
                'url': 'https://i.ytimg.com/vi/youtubeid1/hqdefault.jpg',
                'width': 480,
                'height': 360
              },
              'medium': {
                'url': 'https://i.ytimg.com/vi/youtubeid1/mqdefault.jpg',
                'width': 320,
                'height': 180
              },
              'maxres': {
                'url': 'https://i.ytimg.com/vi/youtubeid1/maxresdefault.jpg',
                'width': 1280,
                'height': 720
              },
              'standard': {
                'url': 'https://i.ytimg.com/vi/youtubeid1/sddefault.jpg',
                'width': 640,
                'height': 480
              }
            },
            'title': 'Cool Video 1',
            'resourceId': {
              'kind': 'youtube#video',
              'videoId': 'youtubeid1'
            },
            'channelId': 'SomeChannelID',
            'publishedAt': '2016-03-15T05:47:01.000Z',
            'channelTitle': 'Some Youtube Channel',
            'position': 1,
            'description': 'A long text describing the video here'
          },
          'kind': 'youtube#playlistItem',
          'etag': '\'somelongetaghere2\'',
          'id': 'somelongidhere1'
        },
      ],
      'nextPageToken': 'someTokenId'
    }


    @with_context
    def test_tasks_return_emtpy_list_if_no_video_to_import(self, build):
        form_data = {
            'playlist_url': '',
            'youtube_api_server_key': 'apikey'
        }
        number_of_tasks = BulkTaskYoutubeImport(**form_data).count_tasks()

        assert number_of_tasks == 0, number_of_tasks

    @with_context
    def test_call_to_youtube_api_endpoint(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.return_value = self.short_playlist_response
        importer = BulkTaskYoutubeImport(**self.form_data)
        importer._fetch_all_youtube_videos('fakeId')

        build.assert_called_with('youtube', 'v3', developerKey=self.form_data['youtube_api_server_key'])

    @with_context
    def test_call_to_youtube_api_short_playlist(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.return_value = self.short_playlist_response
        importer = BulkTaskYoutubeImport(**self.form_data)
        playlist = importer._fetch_all_youtube_videos('fakeId')

        assert playlist == self.short_playlist_response, playlist

    @with_context
    def test_call_to_youtube_api_long_playlist(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.side_effect = [self.long_playlist_response, self.long_playlist_response, self.short_playlist_response]
        importer = BulkTaskYoutubeImport(**self.form_data)
        expected_playlist = {'items': ''}
        expected_playlist['items'] = self.long_playlist_response['items'] + self.long_playlist_response['items'] + self.short_playlist_response['items']
        playlist = importer._fetch_all_youtube_videos('fakeId')

        assert playlist == expected_playlist, playlist

    @with_context
    def test_extract_video_info_one_item(self, build):
        importer = BulkTaskYoutubeImport(**self.form_data)
        info = importer._extract_video_info(self.short_playlist_response['items'][0])

        assert info['info']['video_url'] == 'https://www.youtube.com/watch?v=youtubeid2'

    @with_context
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

    @with_context
    def test_non_youtube_url_raises_exception(self, build):
        importer = BulkTaskYoutubeImport(**self.form_data)
        id = importer._get_playlist_id('https://www.youtu.be/playlist?list=goodplaylist')
        assert id == 'goodplaylist'
        id = importer._get_playlist_id('https://youtu.be/playlist?list=goodplaylist')
        assert id == 'goodplaylist'
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://youtubee.com/playlist?list=goodplaylist')
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://api.youtube.com/playlist?list=goodplaylist')
        assert_raises(BulkImportException, importer._get_playlist_id, 'https://otherdomain.com/playlist?list=goodplaylist')

    @with_context
    def test_all_coverage_tasks_extraction(self, build):
        build.return_value.playlistItems.return_value.list.\
            return_value.execute.return_value = self.short_playlist_response
        importer = BulkTaskYoutubeImport(**self.form_data)
        tasks = importer.tasks()

        assert tasks == [{'info': {'oembed': '<iframe width="512" height="512" src="https://www.youtube.com/embed/youtubeid2" frameborder="0" allowfullscreen></iframe>',
            'video_url': 'https://www.youtube.com/watch?v=youtubeid2'}}]
