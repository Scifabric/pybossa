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

import requests
from io import StringIO
from flask_babel import gettext
import pandas as pd

from .base import BulkTaskImport, BulkImportException
from werkzeug.datastructures import FileStorage
import io, time

class BulkTaskCSVImport(BulkTaskImport):

    """Class to import CSV tasks in bulk."""

    importer_id = "csv"

    def __init__(self, csv_url, last_import_meta=None):
        self.url = csv_url
        self.last_import_meta = last_import_meta

    def tasks(self):
        """Get tasks from a given URL."""
        dataurl = self._get_data_url()
        r = requests.get(dataurl)
        return self._get_csv_data_from_request(r)

    def _get_data_url(self):
        """Get data from URL."""
        return self.url

    def _import_csv_tasks(self, csv_df):
        """Import CSV tasks."""
        headers = []
        fields = set(['state', 'quorum', 'calibration', 'priority_0',
                      'n_answers'])
        field_header_index = []
        row_number = 0

        headers = list(csv_df.columns)
        self._check_no_duplicated_headers(headers)
        self._check_no_empty_headers(headers)
        field_headers = set(headers) & fields
        for field in field_headers:
            field_header_index.append(headers.index(field))

        self._check_valid_row_length(csv_df)

        for index, row in csv_df.iterrows():
            row_number += 1
            task_data = {"info": {}}
            for idx, cell in enumerate(list(row)):
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
        for h in stripped_headers:
            if "Unnamed" in h:
                position = stripped_headers.index(h)
                msg = "The file you uploaded has an empty header on column {}.".format(position+1)
                raise BulkImportException(msg)

    def _check_valid_row_length(self, df):
        if type(df.index) is not pd.RangeIndex:
            msg = "The file you uploaded is a malformed CSV."
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
        csv_df = pd.read_csv(csvcontent)
        csv_df.fillna('')
        return self._import_csv_tasks(csv_df)


class BulkTaskGDImport(BulkTaskCSVImport):

    """Class to import tasks from Google Drive in bulk."""

    importer_id = "gdocs"

    def __init__(self, googledocs_url):
        self.url = googledocs_url

    def _get_data_url(self, **form_data):
        """Get data from URL."""
        # For old data links of Google Spreadsheets
        if 'ccc?key' in self.url:
            return ''.join([self.url, '&output=csv'])
        # New data format for Google Drive import is like this:
        # https://docs.google.com/spreadsheets/d/key/edit?usp=sharing
        else:
            return ''.join([self.url.split('edit')[0],
                            'export?format=csv'])


class BulkTaskLocalCSVImport(BulkTaskCSVImport):

    """Class to import CSV tasks in bulk from local file."""

    importer_id = "localCSV"

    def __init__(self, **form_data):
       self.form_data = form_data

    def _get_data(self):
        """Get data."""
        return self.form_data['csv_filename']

    def count_tasks(self):
        return len([task for task in self.tasks()])

    def _get_csv_data_from_request(self, csv_filename):
        if csv_filename is None:
            msg = ("Not a valid csv file for import")
            raise BulkImportException(gettext(msg), 'error')

        retry = 0
        csv_file = None
        while retry < 10:
            try:
                csv_file = FileStorage(io.open(csv_filename, encoding='utf-8-sig'))
                break
            except IOError as e:
                time.sleep(2)
                retry += 1

        if csv_file is None or csv_file.stream is None:
            msg = ("Unable to load csv file for import, file {0}".format(csv_filename))
            raise BulkImportException(gettext(msg), 'error')

        csv_file.stream.seek(0)
        csvcontent = io.StringIO(csv_file.stream.read())
        csv_df = pd.read_csv(csvcontent)
        csv_df.fillna('')
        return list(self._import_csv_tasks(csv_df))

    def tasks(self):
        """Get tasks from a given URL."""
        csv_filename = self._get_data()
        return self._get_csv_data_from_request(csv_filename)
