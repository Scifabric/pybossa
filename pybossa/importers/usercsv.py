#
# Copyright (C) 2017 SciFabric LTD.
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
import os

import requests
from StringIO import StringIO
from flask.ext.babel import gettext
from pybossa.util import unicode_csv_reader

from .base import BulkUserImport, BulkImportException
from flask import request
from werkzeug.datastructures import FileStorage
import io
import time

class BulkUserCSVImport(BulkUserImport):

    """Class to import users from CSV in bulk."""

    importer_id = "userimport"

    def __init__(self, **form_data):
       self.form_data = form_data

    def _get_data(self):
        """Get data."""
        return self.form_data['csv_filename']

    def count_users(self):
        return len([user for user in self.users()])

    def users(self):
        """Get users from a given URL."""
        csv_filename = self._get_data()
        return self._get_csv_data_from_request(csv_filename)

    def _get_csv_data_from_request(self, csv_filename):
        if csv_filename is None:
            msg = ("Not a valid csv file for import")
            raise BulkImportException(gettext(msg), 'error')
        retry = 0
        csv_file = None
        while retry < 5:
            try:
                csv_file = FileStorage(io.open(csv_filename, encoding='utf-8-sig'))    #utf-8-sig to ignore BOM
                break
            except IOError, e:
                time.sleep(1)
                retry += 1

        if csv_file is None:
           if (('text/plain' not in request.headers['content-type']) and
                   ('text/csv' not in request.headers['content-type']) and
                   ('multipart/form-data' not in request.headers['content-type'])):
               msg = gettext("Oops! That file doesn't look like the right file.")
               raise BulkImportException(msg, 'error')

           request.encoding = 'utf-8'
           csv_file = request.files['file']
           if csv_file is None or csv_file.stream is None:
               msg = ("Not a valid csv file for import")
               raise BulkImportException(gettext(msg), 'error')

        csv_file.stream.seek(0)
        csvcontent = io.StringIO(csv_file.stream.read().decode("UTF8"))
        csvreader = unicode_csv_reader(csvcontent)
        return self._import_csv_users(csvreader)

    def _import_csv_users(self, csvreader):
        """Import users from CSV."""
        headers = []
        field_header_index = []
        row_number = 0

        for row in csvreader:
            if not headers:
                headers = row
                self._check_no_duplicated_headers(headers)
                self._check_no_empty_headers(headers)
                headers = [header.strip() for header in headers]
                self._check_valid_headers(headers)

                field_headers = set(headers)
                for field in field_headers:
                    field_header_index.append(headers.index(field))
            else:
                row_number += 1
                self._check_row_values(row, row_number, headers, field_header_index)
                user_data = {"info": {}}
                for idx, cell in enumerate(row):
                    col_header = headers[idx]
                    cell = cell.strip()
                    if idx in field_header_index:
                        if col_header in self.default_vals:
                            user_data[col_header] = json.loads(cell) \
                                if cell else \
                                self.default_vals[col_header]
                        else:
                            user_data[col_header] = cell
                    else:
                        user_data["info"][col_header] = cell
                yield user_data
