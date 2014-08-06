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


_importers = {}


def register_importer(cls):
    _importers[cls.importer_id] = cls
    return cls


class BulkImportException(Exception):
    pass


class BulkTaskImportManager(object):

    def create_importer(self, importer_id):
        return _importers[importer_id]()

    def variants(self):
        """Returns all the importers and variants defined within this module"""
        variants = [cls.variants() for cls in _importers.values()]
        variants = [item for sublist in variants for item in sublist]
        return variants


googledocs_urls = {
    'spreadsheet': None,
    'image': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdHFEN29mZUF0czJWMUhIejF6dWZXdkE"
             "&usp=sharing",
    'sound': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdEczcWduOXRUb1JUc1VGMmJtc2xXaXc"
             "&usp=sharing",
    'video': "https://docs.google.com/spreadsheet/ccc"
             "?key=0AsNlt0WgPAHwdGZ2UGhxSTJjQl9YNVhfUVhGRUdoRWc"
             "&usp=sharing",
    'map': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdGZnbjdwcnhKRVNlN1dGXy0tTnNWWXc"
           "&usp=sharing",
    'pdf': "https://docs.google.com/spreadsheet/ccc"
           "?key=0AsNlt0WgPAHwdEVVamc0R0hrcjlGdXRaUXlqRXlJMEE"
           "&usp=sharing"}


class BulkTaskImport(object):
    importer_id = None

    @classmethod
    def variants(self):
        return [self.importer_id] if self.importer_id != None else []

    def tasks(self):
        pass

    def _get_data_url(self):
        pass

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
        if ((not 'text/plain' in r.headers['content-type']) and
                (not 'text/csv' in r.headers['content-type'])):
            msg = gettext("Oops! That file doesn't look like the right file.")
            raise BulkImportException(msg, 'error')

        csvcontent = StringIO(r.text)
        csvreader = unicode_csv_reader(csvcontent)
        return self._import_csv_tasks(csvreader)


@register_importer
class BulkTaskCSVImport(BulkTaskImport):
    importer_id = "csv"

    def tasks(self, form):
        dataurl = self._get_data_url(form)
        r = requests.get(dataurl)
        return self._get_csv_data_from_request(r)

    def _get_data_url(self, form):
        return form.csv_url.data


@register_importer
class BulkTaskGDImport(BulkTaskImport):
    importer_id = "gdocs"

    @classmethod
    def variants(self):
        return [("-".join([self.importer_id, mode]))
                for mode in googledocs_urls.keys()]

    def tasks(self, form):
        dataurl = self._get_data_url(form)
        r = requests.get(dataurl)
        return self._get_csv_data_from_request(r)

    def _get_data_url(self, form):
        return ''.join([form.googledocs_url.data, '&output=csv'])


@register_importer
class BulkTaskEpiCollectPlusImport(BulkTaskImport):
    importer_id = "epicollect"

    def tasks(self, form):
        dataurl = self._get_data_url(form)
        r = requests.get(dataurl)
        return self._get_epicollect_data_from_request(r)

    def _import_epicollect_tasks(self, data):
        for d in data:
            yield {"info": d}

    def _get_data_url(self, form):
        return 'http://plus.epicollect.net/%s/%s.json' % \
            (form.epicollect_project.data, form.epicollect_form.data)

    def _get_epicollect_data_from_request(self, r):
        if r.status_code == 403:
            msg = "Oops! It looks like you don't have permission to access" \
                " the EpiCollect Plus project"
            raise BulkImportException(gettext(msg), 'error')
        if not 'application/json' in r.headers['content-type']:
            msg = "Oops! That project and form do not look like the right one."
            raise BulkImportException(gettext(msg), 'error')
        return self._import_epicollect_tasks(json.loads(r.text))
