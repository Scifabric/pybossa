# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
"""Importers module for PyBossa."""
import string
import json
import requests
from StringIO import StringIO
from flask.ext.babel import gettext
from pybossa.util import unicode_csv_reader


class BulkImportException(Exception):

    """Generic Bulk Importer Exception Error."""

    pass


class _BulkTaskImport(object):

    """Class to import tasks in bulk."""

    importer_id = None

    def tasks(self, **form_data):
        """Return a generator with all the tasks imported."""
        pass

    def count_tasks(self, **form_data):
        """Return amount of tasks to be imported."""
        return len([task for task in self.tasks(**form_data)])


class _BulkTaskCSVImport(_BulkTaskImport):

    """Class to import CSV tasks in bulk."""

    importer_id = "csv"

    def tasks(self, **form_data):
        """Get tasks from a given URL."""
        dataurl = self._get_data_url(**form_data)
        r = requests.get(dataurl)
        return self._get_csv_data_from_request(r)

    def _get_data_url(self, **form_data):
        """Get data from URL."""
        return form_data['csv_url']

    def _import_csv_tasks(self, csvreader):
        """Import CSV tasks."""
        headers = []
        fields = set(['state', 'quorum', 'calibration', 'priority_0',
                      'n_answers'])
        field_header_index = []
        row_number = 0
        for row in csvreader:
            if not headers:
                headers = row
                self._check_no_duplicated_headers(headers)
                self._check_no_empty_headers(headers)
                field_headers = set(headers) & fields
                for field in field_headers:
                    field_header_index.append(headers.index(field))
            else:
                row_number += 1
                self._check_valid_row_length(row, row_number, headers)
                task_data = {"info": {}}
                for idx, cell in enumerate(row):
                    if idx in field_header_index:
                        task_data[headers[idx]] = cell
                    else:
                        task_data["info"][headers[idx]] = cell
                yield task_data

    def _check_no_duplicated_headers(self, headers):
        if len(headers) != len(set(headers)):
            msg = gettext('The file you uploaded has '
                          'two headers with the same name.')
            raise BulkImportException(msg)

    def _check_no_empty_headers(self, headers):
        stripped_headers = [header.strip() for header in headers]
        if "" in stripped_headers:
            position = stripped_headers.index("")
            msg = gettext("The file you uploaded has an empty header on "
                          "column %s." % (position+1))
            raise BulkImportException(msg)

    def _check_valid_row_length(self, row, row_number, headers):
        if len(headers) != len(row):
            msg = gettext("The file you uploaded has an extra value on "
                          "row %s." % (row_number+1))
            raise BulkImportException(msg)

    def _get_csv_data_from_request(self, r):
        """Get CSV data from a request."""
        if r.status_code == 403:
            msg = ("Oops! It looks like you don't have permission to access"
                   " that file")
            raise BulkImportException(gettext(msg), 'error')
        if (('text/plain' not in r.headers['content-type']) and
                ('text/csv' not in r.headers['content-type'])):
            msg = gettext("Oops! That file doesn't look like the right file.")
            raise BulkImportException(msg, 'error')

        r.encoding = 'utf-8'
        csvcontent = StringIO(r.text)
        csvreader = unicode_csv_reader(csvcontent)
        return self._import_csv_tasks(csvreader)


class _BulkTaskGDImport(_BulkTaskCSVImport):

    """Class to import tasks from Google Drive in bulk."""

    importer_id = "gdocs"

    def _get_data_url(self, **form_data):
        """Get data from URL."""
        # For old data links of Google Spreadsheets
        if 'ccc?key' in form_data['googledocs_url']:
            return ''.join([form_data['googledocs_url'], '&output=csv'])
        # New data format for Google Drive import is like this:
        # https://docs.google.com/spreadsheets/d/key/edit?usp=sharing
        else:
            return ''.join([form_data['googledocs_url'].split('edit')[0],
                            'export?format=csv'])


class _BulkTaskEpiCollectPlusImport(_BulkTaskImport):

    """Class to import tasks in bulk from an EpiCollect+ project."""

    importer_id = "epicollect"

    def tasks(self, **form_data):
        """Get tasks."""
        dataurl = self._get_data_url(**form_data)
        r = requests.get(dataurl)
        return self._get_epicollect_data_from_request(r)

    def _import_epicollect_tasks(self, data):
        """Import epicollect tasks."""
        for d in data:
            yield {"info": d}

    def _get_data_url(self, **form_data):
        """Get data url."""
        return 'http://plus.epicollect.net/%s/%s.json' % \
            (form_data['epicollect_project'], form_data['epicollect_form'])

    def _get_epicollect_data_from_request(self, r):
        """Get epicollect data from request."""
        if r.status_code == 403:
            msg = ("Oops! It looks like you don't have permission to access"
                   " the EpiCollect Plus project")
            raise BulkImportException(gettext(msg), 'error')
        if 'application/json' not in r.headers['content-type']:
            msg = "Oops! That project and form do not look like the right one."
            raise BulkImportException(gettext(msg), 'error')
        return self._import_epicollect_tasks(json.loads(r.text))


class _BulkTaskFlickrImport(_BulkTaskImport):

    """Class to import tasks from Flickr in bulk."""

    importer_id = "flickr"

    def __init__(self, api_key):
        """Init method."""
        self.api_key = api_key

    def tasks(self, **form_data):
        """Get tasks."""
        album_info = self._get_album_info(form_data['album_id'])
        return self._get_tasks_data_from_request(album_info)

    def count_tasks(self, **form_data):
        """Count tasks."""
        album_info = self._get_album_info(form_data['album_id'])
        return int(album_info['total'])

    def _get_album_info(self, album_id):
        """Get album info."""
        url = 'https://api.flickr.com/services/rest/'
        payload = {'method': 'flickr.photosets.getPhotos',
                   'api_key': self.api_key,
                   'photoset_id': album_id,
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


class _BulkTaskDropboxImport(_BulkTaskImport):

    """Class to import tasks from Dropbox in bulk."""

    importer_id = 'dropbox'

    def tasks(self, **form_data):
        """Get tasks."""
        return [self._extract_file_info(_file) for _file in form_data['files']]

    def count_tasks(self, **form_data):
        """Count number of tasks."""
        return len(self.tasks(**form_data))

    def _extract_file_info(self, _file):
        """Extract file information."""
        _file = json.loads(_file)
        info = {'filename': _file['name'],
                'link_raw': string.replace(_file['link'], 'dl=0', 'raw=1'),
                'link': _file['link']}
        if self._is_image_file(_file['name']):
            extra_fields = {'url_m': info['link_raw'],
                            'url_b': info['link_raw'],
                            'title': info['filename']}
            info.update(extra_fields)
        if self._is_video_file(_file['name']):
            url = self._create_raw_cors_link(_file['link'])
            extra_fields = {'video_url': url}
            info.update(extra_fields)
        if self._is_audio_file(_file['name']):
            url = self._create_raw_cors_link(_file['link'])
            extra_fields = {'audio_url': url}
            info.update(extra_fields)
        if self._is_pdf_file(_file['name']):
            url = self._create_raw_cors_link(_file['link'])
            extra_fields = {'pdf_url': url}
            info.update(extra_fields)
        return {'info': info}

    def _is_image_file(self, filename):
        """Check if it is an image."""
        return (filename.endswith('.png') or filename.endswith('.jpg') or
                filename.endswith('.jpeg') or filename.endswith('.gif'))

    def _is_video_file(self, filename):
        """Check if it is a video."""
        return (filename.endswith('.mp4') or filename.endswith('.m4v') or
                filename.endswith('.ogg') or filename.endswith('.ogv') or
                filename.endswith('.webm') or filename.endswith('.avi'))

    def _is_audio_file(self, filename):
        """Check if it is an audio."""
        return (filename.endswith('.mp4') or filename.endswith('.m4a') or
                filename.endswith('.ogg') or filename.endswith('.oga') or
                filename.endswith('.webm') or filename.endswith('.wav') or
                filename.endswith('.mp3'))

    def _is_pdf_file(self, filename):
        """Check if it is a PDF file."""
        return filename.endswith('.pdf')

    def _create_raw_cors_link(self, url):
        """Create RAW CORS link."""
        new_url = string.replace(url, 'www.dropbox.com',
                                 'dl.dropboxusercontent.com')
        if new_url.endswith('?dl=0'):
            new_url = new_url[:-5]
        return new_url


class Importer(object):

    """Class to import data."""

    def __init__(self):
        """Init method."""
        self._importers = {'csv': _BulkTaskCSVImport,
                           'gdocs': _BulkTaskGDImport,
                           'epicollect': _BulkTaskEpiCollectPlusImport}
        self._importer_constructor_params = {}

    def register_flickr_importer(self, flickr_params):
        """Register Flickr importer."""
        self._importers['flickr'] = _BulkTaskFlickrImport
        self._importer_constructor_params['flickr'] = flickr_params

    def register_dropbox_importer(self):
        """Register Dropbox importer."""
        self._importers['dropbox'] = _BulkTaskDropboxImport

    def create_tasks(self, task_repo, project_id, **form_data):
        """Create tasks."""
        from pybossa.model.task import Task
        """Create tasks from a remote source using an importer object and
        avoiding the creation of repeated tasks"""
        importer_id = form_data.get('type')
        empty = True
        n = 0
        importer = self._create_importer_for(importer_id)
        for task_data in importer.tasks(**form_data):
            task = Task(project_id=project_id)
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            found = task_repo.get_task_by(project_id=project_id, info=task.info)
            if found is None:
                task_repo.save(task)
                n += 1
                empty = False
        if empty:
            msg = gettext('It looks like there were no new records to import')
            return msg
        msg = str(n) + " " + gettext('new tasks were imported successfully')
        if n == 1:
            msg = str(n) + " " + gettext('new task was imported successfully')
        return msg

    def count_tasks_to_import(self, **form_data):
        """Count tasks to import."""
        importer_id = form_data.get('type')
        return self._create_importer_for(importer_id).count_tasks(**form_data)

    def _create_importer_for(self, importer_id):
        """Create importer."""
        params = self._importer_constructor_params.get(importer_id) or {}
        return self._importers[importer_id](**params)

    def get_all_importer_names(self):
        """Get all importer names."""
        return self._importers.keys()

    def get_autoimporter_names(self):
        """Get autoimporter names."""
        return [name for name in self._importers.keys() if name != 'dropbox']
