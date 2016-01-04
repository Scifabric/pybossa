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

import copy
import json
import string
from mock import patch, Mock
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.flickr import BulkTaskFlickrImport


@patch('pybossa.importers.flickr.requests')
class TestBulkTaskFlickrImport(object):

    invalid_response = {u'stat': u'fail',
                        u'code': 1, u'message': u'Photoset not found'}
    response = {
        u'stat': u'ok',
        u'photoset': {
            u'perpage': 500,
            u'title': u'Science Hack Day Balloon Mapping Workshop',
            u'photo': [
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 6,
                 u'ispublic': 1, u'server': u'5441', u'isfriend': 0,
                 u'secret': u'00e2301a0d', u'isprimary': u'0', u'id': u'8947115130'},
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 4,
                 u'ispublic': 1, u'server': u'3763', u'isfriend': 0,
                 u'secret': u'70d482fc68', u'isprimary': u'0', u'id': u'8946490553'},
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 3,
                 u'ispublic': 1, u'server': u'2810', u'isfriend': 0,
                 u'secret': u'99cae13d87', u'isprimary': u'0', u'id': u'8947113960'}],
            u'pages': 1,
            u'primary': u'8947113500',
            u'id': u'72157633923521788',
            u'ownername': u'Teleyinex',
            u'owner': u'32985084@N00',
            u'per_page': 500,
            u'total': u'3',
            u'page': 1}}
    photo = {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 6,
             u'ispublic': 1, u'server': u'5441', u'isfriend': 0,
             u'secret': u'00e2301a0d', u'isprimary': u'0', u'id': u'8947115130'}
    importer = BulkTaskFlickrImport(api_key='fake-key', album_id='72157633923521788')


    def make_response(self, text, status_code=200):
        fake_response = Mock()
        fake_response.text = text
        fake_response.status_code = status_code
        return fake_response

    def test_call_to_flickr_api_endpoint(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        self.importer._get_album_info()
        url = 'https://api.flickr.com/services/rest/'
        payload = {'method': 'flickr.photosets.getPhotos',
                   'api_key': 'fake-key',
                   'photoset_id': '72157633923521788',
                   'format': 'json',
                   'nojsoncallback': '1'}
        requests.get.assert_called_with(url, params=payload)

    def test_call_to_flickr_api_uses_no_credentials(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        self.importer._get_album_info()

        # The request MUST NOT include user credentials, to avoid private photos
        url_call_params = requests.get.call_args_list[0][1]['params'].keys()
        assert 'auth_token' not in url_call_params

    def test_count_tasks_returns_number_of_photos_in_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))

        number_of_tasks = self.importer.count_tasks()

        assert number_of_tasks is 3, number_of_tasks

    def test_count_tasks_raises_exception_if_invalid_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.invalid_response))
        importer = BulkTaskFlickrImport(api_key='fake-key', album_id='bad')

        assert_raises(BulkImportException, importer.count_tasks)

    def test_count_tasks_raises_exception_on_non_200_flickr_response(self, requests):
        requests.get.return_value = self.make_response('Not Found', 404)

        assert_raises(BulkImportException, self.importer.count_tasks)

    def test_tasks_returns_list_of_all_photos(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))

        photos = self.importer.tasks()

        assert len(photos) == 3, len(photos)

    def test_tasks_returns_tasks_with_title_and_url_info_fields(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        url = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d.jpg'
        url_m = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_m.jpg'
        url_b = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_b.jpg'
        link = 'https://www.flickr.com/photos/32985084@N00/8947115130'
        title = self.response['photoset']['photo'][0]['title']
        photo = self.importer.tasks()[0]

        assert photo['info'].get('title') == title
        assert photo['info'].get('url') == url, photo['info'].get('url')
        assert photo['info'].get('url_m') == url_m, photo['info'].get('url_m')
        assert photo['info'].get('url_b') == url_b, photo['info'].get('url_b')
        assert photo['info'].get('link') == link, photo['info'].get('link')

    def test_tasks_raises_exception_if_invalid_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.invalid_response))
        importer = BulkTaskFlickrImport(api_key='fake-key', album_id='bad')

        assert_raises(BulkImportException, importer.tasks)

    def test_tasks_raises_exception_on_non_200_flickr_response(self, requests):
        requests.get.return_value = self.make_response('Not Found', 404)

        assert_raises(BulkImportException, self.importer.tasks)

    def test_tasks_returns_all_for_sets_with_more_than_500_photos(self, requests):
        # Deep-copy the object, as we will be modifying it and we don't want
        # these modifications to affect other tests
        first_response = copy.deepcopy(self.response)
        first_response['photoset']['pages'] = 2
        first_response['photoset']['total'] = u'600'
        first_response['photoset']['page'] = 1
        first_response['photoset']['photo'] = [self.photo for i in range(500)]
        second_response = copy.deepcopy(self.response)
        second_response['photoset']['pages'] = 2
        second_response['photoset']['total'] = u'600'
        second_response['photoset']['page'] = 2
        second_response['photoset']['photo'] = [self.photo for i in range(100)]
        fake_first_response = self.make_response(json.dumps(first_response))
        fake_second_response = self.make_response(json.dumps(second_response))
        responses = [fake_first_response, fake_second_response]
        requests.get.side_effect = lambda *args, **kwargs: responses.pop(0)

        photos = self.importer.tasks()

        assert len(photos) == 600, len(photos)

    def test_tasks_returns_all_for_sets_with_more_than_1000_photos(self, requests):
        # Deep-copy the object, as we will be modifying it and we don't want
        # these modifications to affect other tests
        first_response = copy.deepcopy(self.response)
        first_response['photoset']['pages'] = 3
        first_response['photoset']['total'] = u'1100'
        first_response['photoset']['page'] = 1
        first_response['photoset']['photo'] = [self.photo for i in range(500)]
        second_response = copy.deepcopy(self.response)
        second_response['photoset']['pages'] = 3
        second_response['photoset']['total'] = u'1100'
        second_response['photoset']['page'] = 2
        second_response['photoset']['photo'] = [self.photo for i in range(500)]
        third_response = copy.deepcopy(self.response)
        third_response['photoset']['pages'] = 3
        third_response['photoset']['total'] = u'1100'
        third_response['photoset']['page'] = 3
        third_response['photoset']['photo'] = [self.photo for i in range(100)]
        fake_first_response = self.make_response(json.dumps(first_response))
        fake_second_response = self.make_response(json.dumps(second_response))
        fake_third_response = self.make_response(json.dumps(third_response))
        responses = [fake_first_response, fake_second_response, fake_third_response]
        requests.get.side_effect = lambda *args, **kwargs: responses.pop(0)

        photos = self.importer.tasks()

        assert len(photos) == 1100, len(photos)
