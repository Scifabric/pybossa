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

import copy
import json
import string
from default import with_context
from mock import patch, Mock
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.flickr import BulkTaskFlickrImport


@patch('pybossa.importers.flickr.requests')
class TestBulkTaskFlickrImport(object):

    invalid_response = {'stat': 'fail',
                        'code': 1, 'message': 'Photoset not found'}
    response = {
        'stat': 'ok',
        'photoset': {
            'perpage': 500,
            'title': 'Science Hack Day Balloon Mapping Workshop',
            'photo': [
                {'isfamily': 0, 'title': 'Inflating the balloon', 'farm': 6,
                 'ispublic': 1, 'server': '5441', 'isfriend': 0,
                 'secret': '00e2301a0d', 'isprimary': '0', 'id': '8947115130'},
                {'isfamily': 0, 'title': 'Inflating the balloon', 'farm': 4,
                 'ispublic': 1, 'server': '3763', 'isfriend': 0,
                 'secret': '70d482fc68', 'isprimary': '0', 'id': '8946490553'},
                {'isfamily': 0, 'title': 'Inflating the balloon', 'farm': 3,
                 'ispublic': 1, 'server': '2810', 'isfriend': 0,
                 'secret': '99cae13d87', 'isprimary': '0', 'id': '8947113960'}],
            'pages': 1,
            'primary': '8947113500',
            'id': '72157633923521788',
            'ownername': 'Teleyinex',
            'owner': '32985084@N00',
            'per_page': 500,
            'total': '3',
            'page': 1}}
    photo = {'isfamily': 0, 'title': 'Inflating the balloon', 'farm': 6,
             'ispublic': 1, 'server': '5441', 'isfriend': 0,
             'secret': '00e2301a0d', 'isprimary': '0', 'id': '8947115130'}
    importer = BulkTaskFlickrImport(api_key='fake-key', album_id='72157633923521788')


    @with_context
    def make_response(self, text, status_code=200):
        fake_response = Mock()
        fake_response.text = text
        fake_response.status_code = status_code
        return fake_response

    @with_context
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

    @with_context
    def test_call_to_flickr_api_uses_no_credentials(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        self.importer._get_album_info()

        # The request MUST NOT include user credentials, to avoid private photos
        url_call_params = list(requests.get.call_args_list[0][1]['params'].keys())
        assert 'auth_token' not in url_call_params

    @with_context
    def test_count_tasks_returns_number_of_photos_in_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))

        number_of_tasks = self.importer.count_tasks()

        assert number_of_tasks is 3, number_of_tasks

    @with_context
    def test_count_tasks_raises_exception_if_invalid_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.invalid_response))
        importer = BulkTaskFlickrImport(api_key='fake-key', album_id='bad')

        assert_raises(BulkImportException, importer.count_tasks)

    @with_context
    def test_count_tasks_raises_exception_on_non_200_flickr_response(self, requests):
        requests.get.return_value = self.make_response('Not Found', 404)

        assert_raises(BulkImportException, self.importer.count_tasks)

    @with_context
    def test_tasks_returns_list_of_all_photos(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))

        photos = self.importer.tasks()

        assert len(photos) == 3, len(photos)

    @with_context
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

    @with_context
    def test_tasks_raises_exception_if_invalid_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.invalid_response))
        importer = BulkTaskFlickrImport(api_key='fake-key', album_id='bad')

        assert_raises(BulkImportException, importer.tasks)

    @with_context
    def test_tasks_raises_exception_on_non_200_flickr_response(self, requests):
        requests.get.return_value = self.make_response('Not Found', 404)

        assert_raises(BulkImportException, self.importer.tasks)

    @with_context
    def test_tasks_returns_all_for_sets_with_more_than_500_photos(self, requests):
        # Deep-copy the object, as we will be modifying it and we don't want
        # these modifications to affect other tests
        first_response = copy.deepcopy(self.response)
        first_response['photoset']['pages'] = 2
        first_response['photoset']['total'] = '600'
        first_response['photoset']['page'] = 1
        first_response['photoset']['photo'] = [self.photo for i in range(500)]
        second_response = copy.deepcopy(self.response)
        second_response['photoset']['pages'] = 2
        second_response['photoset']['total'] = '600'
        second_response['photoset']['page'] = 2
        second_response['photoset']['photo'] = [self.photo for i in range(100)]
        fake_first_response = self.make_response(json.dumps(first_response))
        fake_second_response = self.make_response(json.dumps(second_response))
        responses = [fake_first_response, fake_second_response]
        requests.get.side_effect = lambda *args, **kwargs: responses.pop(0)

        photos = self.importer.tasks()

        assert len(photos) == 600, len(photos)

    @with_context
    def test_tasks_returns_all_for_sets_with_more_than_1000_photos(self, requests):
        # Deep-copy the object, as we will be modifying it and we don't want
        # these modifications to affect other tests
        first_response = copy.deepcopy(self.response)
        first_response['photoset']['pages'] = 3
        first_response['photoset']['total'] = '1100'
        first_response['photoset']['page'] = 1
        first_response['photoset']['photo'] = [self.photo for i in range(500)]
        second_response = copy.deepcopy(self.response)
        second_response['photoset']['pages'] = 3
        second_response['photoset']['total'] = '1100'
        second_response['photoset']['page'] = 2
        second_response['photoset']['photo'] = [self.photo for i in range(500)]
        third_response = copy.deepcopy(self.response)
        third_response['photoset']['pages'] = 3
        third_response['photoset']['total'] = '1100'
        third_response['photoset']['page'] = 3
        third_response['photoset']['photo'] = [self.photo for i in range(100)]
        fake_first_response = self.make_response(json.dumps(first_response))
        fake_second_response = self.make_response(json.dumps(second_response))
        fake_third_response = self.make_response(json.dumps(third_response))
        responses = [fake_first_response, fake_second_response, fake_third_response]
        requests.get.side_effect = lambda *args, **kwargs: responses.pop(0)

        photos = self.importer.tasks()

        assert len(photos) == 1100, len(photos)
