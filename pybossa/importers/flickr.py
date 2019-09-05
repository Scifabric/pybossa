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

import json
import requests

from .base import BulkTaskImport, BulkImportException


class BulkTaskFlickrImport(BulkTaskImport):

    """Class to import tasks from Flickr in bulk."""

    importer_id = "flickr"

    def __init__(self, api_key, album_id, last_import_meta=None):
        """Init method."""
        BulkTaskImport.__init__(self)
        self.api_key = api_key
        self.album_id = album_id
        self.last_import_meta = last_import_meta

    def tasks(self):
        """Get tasks."""
        album_info = self._get_album_info()
        return self._get_tasks_data_from_request(album_info)

    def count_tasks(self):
        """Count tasks."""
        album_info = self._get_album_info()
        return int(album_info['total'])

    def _get_album_info(self):
        """Get album info."""
        url = 'https://api.flickr.com/services/rest/'
        payload = {'method': 'flickr.photosets.getPhotos',
                   'api_key': self.api_key,
                   'photoset_id': self.album_id,
                   'format': 'json',
                   'nojsoncallback': '1'}
        res = requests.get(url, params=payload)
        if self._is_valid_response(res):
            content = json.loads(res.text)['photoset']
            total_pages = content.get('pages')
            rest_photos = self._remaining_photos(url, payload, total_pages)
            content['photo'] += rest_photos
            return content

    def _is_valid_response(self, response):
        """Check if it's a valid response."""
        if type(response.text) is dict:
            error_message = json.loads(response.text).get('message')
        else:
            error_message = response.text
        valid = (response.status_code == 200
                 and json.loads(response.text).get('stat') == 'ok')
        if not valid:
            raise BulkImportException(error_message)
        return valid

    def _remaining_photos(self, url, payload, total_pages):
        """Return the remainin photos."""
        photo_lists = [self._photos_from_page(url, payload, page)
                       for page in range(2, total_pages+1)]
        return [item for sublist in photo_lists for item in sublist]

    def _photos_from_page(self, url, payload, page):
        """Return photos from page."""
        payload['page'] = page
        res = requests.get(url, params=payload)
        if self._is_valid_response(res):
            return json.loads(res.text)['photoset']['photo']
        return []

    def _get_tasks_data_from_request(self, album_info):
        """Get tasks data from request."""
        photo_list = album_info['photo']
        owner = album_info['owner']
        return [self._extract_photo_info(photo, owner) for photo in photo_list]

    def _extract_photo_info(self, photo, owner):
        """Extract photo info."""
        base_url = 'https://farm%s.staticflickr.com/%s/%s_%s' % (
            photo['farm'], photo['server'], photo['id'], photo['secret'])
        title = photo['title']
        url = ''.join([base_url, '.jpg'])
        url_m = ''.join([base_url, '_m.jpg'])
        url_b = ''.join([base_url, '_b.jpg'])
        link = 'https://www.flickr.com/photos/%s/%s' % (owner, photo['id'])
        return {"info": {'title': title, 'url': url,
                         'url_b': url_b, 'url_m': url_m, 'link': link}}
