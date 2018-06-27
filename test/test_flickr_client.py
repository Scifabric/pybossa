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

from mock import patch, MagicMock
from flask import Response, session
from pybossa.flickr_client import FlickrClient


class TestFlickrClient(object):
    class Res(object):
        def __init__(self, status, data):
            self.status_code = status
            self.json = lambda: data

    def setUp(self):
        self.token = {'oauth_token_secret': 'secret', 'oauth_token': 'token'}
        self.user = {'username': 'palotespaco', 'user_nsid': 'user'}
        self.flickr = FlickrClient('key', MagicMock())


    @patch('pybossa.flickr_client.requests')
    def test_get_user_albums_calls_flickr_api_endpoint(self, fake_requests):
        session = {'flickr_token': self.token, 'flickr_user': self.user}
        url = 'https://api.flickr.com/services/rest/'
        payload = {'method': 'flickr.photosets.getList',
                   'api_key': 'key',
                   'user_id': 'user',
                   'format': 'json',
                   'primary_photo_extras':'url_q',
                   'nojsoncallback': '1'}

        self.flickr.get_user_albums(session)

        fake_requests.get.assert_called_with(url, params=payload)


    @patch('pybossa.flickr_client.requests')
    def test_get_user_albums_return_empty_list_on_request_error(self, fake_requests):
        response = self.Res(404, 'not found')
        fake_requests.get.return_value = response

        session = {'flickr_token': self.token, 'flickr_user': self.user}

        albums = self.flickr.get_user_albums(session)

        assert albums == [], albums


    @patch('pybossa.flickr_client.requests')
    def test_get_user_albums_return_empty_list_on_request_fail(self, fake_requests):
        data = {'stat': 'fail', 'code': 1, 'message': 'User not found'}
        response = self.Res(200, data)
        fake_requests.get.return_value = response

        session = {'flickr_token': self.token, 'flickr_user': self.user}

        albums = self.flickr.get_user_albums(session)

        assert albums == [], albums


    @patch('pybossa.flickr_client.requests')
    def test_get_user_albums_log_response_on_request_fail(self, fake_requests):
        data = {'stat': 'fail', 'code': 1, 'message': 'User not found'}
        response = self.Res(200, data)
        fake_requests.get.return_value = response
        log_error_msg = ("Bad response from Flickr:\nStatus: %s, Content: %s"
            % (response.status_code, response.json()))
        session = {'flickr_token': self.token, 'flickr_user': self.user}

        albums = self.flickr.get_user_albums(session)

        self.flickr.logger.error.assert_called_with(log_error_msg)


    @patch('pybossa.flickr_client.requests')
    def test_get_user_albums_return_list_with_album_info(self, fake_requests):
        data = {
            'stat': 'ok',
            'photosets': {
                'total': 2,
                'perpage': 2,
                'photoset':
                [{'date_update': '1421313791',
                  'visibility_can_see_set': 1,
                  'description': {'_content': 'mis mejores vacaciones'},
                  'videos': 0, 'title': {'_content': 'vacaciones'},
                  'farm': 9, 'needs_interstitial': 0,
                  'primary': '16284868505',
                  'primary_photo_extras': {
                      'height_t': '63',
                      'width_t': '100',
                      'url_q': 'https://farm9.staticflickr.com/8597/16284868505_c4a032a62e_t.jpg'},
                  'server': '8597',
                  'date_create': '1421313790',
                  'photos': '3',
                  'secret': 'c4a032a62e',
                  'count_comments': '0',
                  'count_views': '1',
                  'can_comment': 0,
                  'id': '72157649886540037'}],
                'page': 1,
                'pages': 1}}
        response = self.Res(200, data)
        fake_requests.get.return_value = response
        session = {'flickr_token': self.token, 'flickr_user': self.user}

        albums = self.flickr.get_user_albums(session)

        expected_album = response.json()['photosets']['photoset'][0]
        expected_album_info = {
            'photos': expected_album['photos'],
            'thumbnail_url': expected_album['primary_photo_extras']['url_q'],
            'id': expected_album['id'],
            'title': expected_album['title']['_content']}

        assert albums == [expected_album_info], albums
