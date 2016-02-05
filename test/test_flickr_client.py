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

from mock import patch, MagicMock
from flask import Response, session
from pybossa.flickr_client import FlickrClient


class TestFlickrClient(object):
    class Res(object):
        def __init__(self, status, data):
            self.status_code = status
            self.json = lambda: data

    def setUp(self):
        self.token = {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        self.user = {'username': u'palotespaco', 'user_nsid': u'user'}
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
            u'stat': u'ok',
            u'photosets': {
                u'total': 2,
                u'perpage': 2,
                u'photoset':
                [{u'date_update': u'1421313791',
                  u'visibility_can_see_set': 1,
                  u'description': {u'_content': u'mis mejores vacaciones'},
                  u'videos': 0, u'title': {u'_content': u'vacaciones'},
                  u'farm': 9, u'needs_interstitial': 0,
                  u'primary': u'16284868505',
                  u'primary_photo_extras': {
                      u'height_t': u'63',
                      u'width_t': u'100',
                      u'url_q': u'https://farm9.staticflickr.com/8597/16284868505_c4a032a62e_t.jpg'},
                  u'server': u'8597',
                  u'date_create': u'1421313790',
                  u'photos': u'3',
                  u'secret': u'c4a032a62e',
                  u'count_comments': u'0',
                  u'count_views': u'1',
                  u'can_comment': 0,
                  u'id': u'72157649886540037'}],
                u'page': 1,
                u'pages': 1}}
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
