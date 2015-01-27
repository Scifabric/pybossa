# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from StringIO import StringIO
import json
import requests
from flask.ext.babel import gettext
from pybossa.util import unicode_csv_reader


class BulkImportException(Exception):
    pass


class _BulkTaskImport(object):
    importer_id = None

    def tasks(self, **form_data):
        """Returns a generator with all the tasks imported"""
        pass

    def count_tasks(self, **form_data):
        """Returns amount of tasks to be imported"""
        return len([task for task in self.tasks(**form_data)])


class _BulkTaskCSVImport(_BulkTaskImport):
    importer_id = "csv"

    def tasks(self, **form_data):
        dataurl = self._get_data_url(**form_data)
        r = requests.get(dataurl)
        return self._get_csv_data_from_request(r)

    def _get_data_url(self, **form_data):
        return form_data['csv_url']

    def _import_csv_tasks(self, csvreader):
        headers = []
        fields = set(['state', 'quorum', 'calibration', 'priority_0',
                      'n_answers'])
        field_header_index = []

        for row in csvreader:
            if not headers:
                headers = row
                if len(headers) != len(set(headers)):
                    msg = gettext('The file you uploaded has '
                                  'two headers with the same name.')
                    raise BulkImportException(msg)
                field_headers = set(headers) & fields
                for field in field_headers:
                    field_header_index.append(headers.index(field))
            else:
                task_data = {"info": {}}
                for idx, cell in enumerate(row):
                    if idx in field_header_index:
                        task_data[headers[idx]] = cell
                    else:
                        task_data["info"][headers[idx]] = cell
                yield task_data

    def _get_csv_data_from_request(self, r):
        if r.status_code == 403:
            msg = "Oops! It looks like you don't have permission to access" \
                " that file"
            raise BulkImportException(gettext(msg), 'error')
        if (('text/plain' not in r.headers['content-type']) and
                ('text/csv' not in r.headers['content-type'])):
            msg = gettext("Oops! That file doesn't look like the right file.")
            raise BulkImportException(msg, 'error')

        csvcontent = StringIO(r.text)
        csvreader = unicode_csv_reader(csvcontent)
        return self._import_csv_tasks(csvreader)


class _BulkTaskGDImport(_BulkTaskCSVImport):
    importer_id = "gdocs"

    def _get_data_url(self, **form_data):
        # For old data links of Google Spreadsheets
        if 'ccc?key' in form_data['googledocs_url']:
            return ''.join([form_data['googledocs_url'], '&output=csv'])
        # New data format for Google Drive import is like this:
        # https://docs.google.com/spreadsheets/d/key/edit?usp=sharing
        else:
            return ''.join([form_data['googledocs_url'].split('edit')[0],
                            'export?format=csv'])


class _BulkTaskEpiCollectPlusImport(_BulkTaskImport):
    importer_id = "epicollect"

    def tasks(self, **form_data):
        dataurl = self._get_data_url(**form_data)
        r = requests.get(dataurl)
        return self._get_epicollect_data_from_request(r)

    def _import_epicollect_tasks(self, data):
        for d in data:
            yield {"info": d}

    def _get_data_url(self, **form_data):
        return 'http://plus.epicollect.net/%s/%s.json' % \
            (form_data['epicollect_project'], form_data['epicollect_form'])

    def _get_epicollect_data_from_request(self, r):
        if r.status_code == 403:
            msg = "Oops! It looks like you don't have permission to access" \
                " the EpiCollect Plus project"
            raise BulkImportException(gettext(msg), 'error')
        if 'application/json' not in r.headers['content-type']:
            msg = "Oops! That project and form do not look like the right one."
            raise BulkImportException(gettext(msg), 'error')
        return self._import_epicollect_tasks(json.loads(r.text))


class _BulkTaskFlickrImport(_BulkTaskImport):
    importer_id = "flickr"

    def __init__(self, api_key):
        self.api_key = api_key

    def tasks(self, **form_data):
        album_info = self._get_album_info(form_data['album_id'])
        return self._get_tasks_data_from_request(album_info)

    def count_tasks(self, **form_data):
        album_info = self._get_album_info(form_data['album_id'])
        return int(album_info['total'])

    def _get_album_info(self, album_id):
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
        if type(res.tex) is dict:
            error_message = json.loads(res.text).get('message')
        else:
            error_message = res.text
        raise BulkImportException(error_message)

    def _is_valid_response(self, response):
        return (response.status_code == 200
                and json.loads(response.text).get('stat') == 'ok')

    def _remaining_photos(self, url, payload, total_pages):
        photo_lists = [self._photos_from_page(url, payload, page)
            for page in range(2, total_pages+1)]
        return [item for sublist in photo_lists for item in sublist]

    def _photos_from_page(self, url, payload, page):
        payload['page'] = page
        res = requests.get(url, params=payload)
        if self._is_valid_response(res):
            return json.loads(res.text)['photoset']['photo']
        return []

    def _get_tasks_data_from_request(self, album_info):
        photo_list = album_info['photo']
        return [self._extract_photo_info(photo) for photo in photo_list]

    def _extract_photo_info(self, photo):
        base_url = 'https://farm%s.staticflickr.com/%s/%s_%s' % (
            photo['farm'], photo['server'], photo['id'], photo['secret'])
        title = photo['title']
        url = ''.join([base_url, '.jpg'])
        url_m = ''.join([base_url, '_m.jpg'])
        url_b = ''.join([base_url, '_b.jpg'])
        return {"info": {'title': title, 'url': url,
                         'url_b': url_b, 'url_m': url_m}}


class Importer(object):

    def __init__(self):
        self._importers = {'csv': _BulkTaskCSVImport,
                           'gdocs': _BulkTaskGDImport,
                           'epicollect': _BulkTaskEpiCollectPlusImport}
        self._importer_constructor_params = {}

    def register_flickr_importer(self, flickr_params):
        self._importers['flickr'] = _BulkTaskFlickrImport
        self._importer_constructor_params['flickr'] = flickr_params

    def create_tasks(self, task_repo, project_id, **form_data):
        from pybossa.cache import apps as cached_apps
        from pybossa.model.task import Task
        """Create tasks from a remote source using an importer object and
        avoiding the creation of repeated tasks"""
        importer_id = form_data.get('type')
        empty = True
        n = 0
        importer = self._create_importer_for(importer_id)
        for task_data in importer.tasks(**form_data):
            task = Task(app_id=project_id)
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            found = task_repo.get_task_by(app_id=project_id, info=task.info)
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
        cached_apps.delete_n_tasks(project_id)
        cached_apps.delete_n_task_runs(project_id)
        cached_apps.delete_overall_progress(project_id)
        cached_apps.delete_last_activity(project_id)
        return msg

    def count_tasks_to_import(self, **form_data):
        importer_id = form_data.get('type')
        return self._create_importer_for(importer_id).count_tasks(**form_data)

    def _create_importer_for(self, importer_id):
        constructor_params = self._importer_constructor_params.get(importer_id)
        return self._importers[importer_id](**constructor_params)

    def get_all_importer_names(self):
        return self._importers.keys()
