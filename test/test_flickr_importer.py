# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
import json
from mock import patch, Mock
from nose.tools import assert_raises
from pybossa.importers import _BulkTaskFlickrImport, BulkImportException


@patch('pybossa.importers.requests')
class Test_BulkTaskFlickrImport(object):

    invalid_photoset_response = { "stat": "fail",
                                       "code": 1,
                                       "message": "Photoset not found" }
    photoset_response = {
        "photoset": {
            "id": "72157633923521788",
            "primary": "8947113500",
            "owner": "32985084@N00",
            "ownername": "Teleyinex", 
            "photo": [
                { "id": "8947115130", "secret": "00e2301a0d", "server": "5441", "farm": 6, "title": "Inflating the balloon", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946490553", "secret": "70d482fc68", "server": "3763", "farm": 4, "title": "Inflating the balloon", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947113960", "secret": "99cae13d87", "server": "2810", "farm": 3, "title": "Inflating the balloon", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947113500", "secret": "10aca4ac5e", "server": "8120", "farm": 9, "title": "Best balloon ever", "isprimary": 1, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946487679", "secret": "9cfebaaa17", "server": "7393", "farm": 8, "title": "Tying the balloon", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946487131", "secret": "a058869bc9", "server": "7367", "farm": 8, "title": "Adding a ring", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947109952", "secret": "da953ecc07", "server": "2820", "farm": 3, "title": "Attaching the balloon to the string", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946484353", "secret": "f8303887ec", "server": "8267", "farm": 9, "title": "Checking the balloon connections", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947107094", "secret": "71ff58689b", "server": "3803", "farm": 4, "title": "Setting up the camera", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946482659", "secret": "b4175399b7", "server": "5338", "farm": 6, "title": "Securing the camera", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946480363", "secret": "f99745f017", "server": "5456", "farm": 6, "title": "Attaching the bottle rig to the balloon", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947103528", "secret": "3447659c65", "server": "2833", "farm": 3, "title": "Infragram camera from Public Laboratory", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8946479121", "secret": "2e65b7b453", "server": "5350", "farm": 6, "title": "Balloon Mapping", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947102174", "secret": "cc70885ab8", "server": "3714", "farm": 4, "title": "Balloon Mapping", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 },
                { "id": "8947101672", "secret": "9a8f52c9f2", "server": "2810", "farm": 3, "title": "Balloon Mapping", "isprimary": 0, "ispublic": 1, "isfriend": 0, "isfamily": 0 }],
            "page": 1,
            "per_page": "500",
            "perpage": "500",
            "pages": 1,
            "total": 15,
            "title": "Science Hack Day Balloon Mapping Workshop" },
        "stat": "ok" }


    def test_count_tasks_returns_number_of_photos_in_album(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.photoset_response)
        requests.get.return_value = fake_response
        importer = _BulkTaskFlickrImport()

        number_of_tasks = importer.count_tasks(album_id='72157633923521788')

        assert number_of_tasks is 15, number_of_tasks


    def test_count_tasks_raises_exception_if_invalid_album(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.invalid_photoset_response)
        requests.get.return_value = fake_response
        importer = _BulkTaskFlickrImport()

        assert_raises(BulkImportException, importer.count_tasks, album_id='bad')


    def test_tasks_returns_list_of_all_photos(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.photoset_response)
        requests.get.return_value = fake_response
        importer = _BulkTaskFlickrImport()

        photos = importer.tasks(album_id='72157633923521788')

        assert len(photos) == 15, len(photos)


    def test_tasks_returns_tasks_with_title_and_url_info_fields(self, requests):
        task_data_info_fields = ['url', 'title']
        fake_response = Mock()
        fake_response.text = json.dumps(self.photoset_response)
        requests.get.return_value = fake_response
        importer = _BulkTaskFlickrImport()

        photo_url = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d.jpg'
        photo_title = self.photoset_response['photoset']['photo'][0]['title']
        photo = importer.tasks(album_id='72157633923521788')[0]

        assert photo['info'].get('title') == photo_title
        assert photo['info'].get('url') == photo_url, photo['info'].get('url')


    def test_tasks_raises_exception_if_invalid_album(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.invalid_photoset_response)
        requests.get.return_value = fake_response
        importer = _BulkTaskFlickrImport()

        assert_raises(BulkImportException, importer.tasks, album_id='bad')
