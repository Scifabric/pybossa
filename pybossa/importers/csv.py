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

import numbers
import types
import requests
from StringIO import StringIO
from flask_babel import gettext
from pybossa.util import unicode_csv_reader, validate_required_fields
from pybossa.util import unicode_csv_reader

from .base import BulkTaskImport, BulkImportException
from flask import request
from werkzeug.datastructures import FileStorage
import io, time, json
from flask import current_app as app
from pybossa.util import get_import_csv_file
import re
from pybossa.data_access import data_access_levels

type_map = {
    # Python considers booleans to be numbers so we need an extra check for that.
    'number': lambda x: isinstance(x, numbers.Real) and type(x) is not bool,
    'bool': lambda x: isinstance(x, bool),
    'null': lambda x: isinstance(x, types.NoneType)
}

def get_value(header, value_string, data_type):
    def error():
        raise BulkImportException('Column {} contains a non-{} value {}'.format(header, data_type, value_string))

    if not data_type:
        return value_string

    try:
        value = json.loads(value_string)
    except ValueError:
        error()

    python_type_checker = type_map.get(data_type)
    if python_type_checker and not python_type_checker(value):
        error()

    return value

class ReservedFieldProcessor(object):
    def __init__(self, header):
        self.header = header

    reserved_fields = set([
        'state',
        'quorum',
        'calibration',
        'priority_0',
        'n_answers',
        'user_pref',
        'expiration'
    ])
    is_input = False

    @staticmethod
    def create_if_can_process(header):
        if header in ReservedFieldProcessor.reserved_fields:
            return ReservedFieldProcessor(header)

    def process(self, task_data, cell, *args):
        if self.header == 'user_pref':
            if cell:
                task_data[self.header] = json.loads(cell.lower())
            else:
                task_data[self.header] = {}
        elif cell:
            task_data[self.header] = cell

class GoldFieldProcessor(object):
    def __init__(self, data_type, field_name, header):
        self.data_type = data_type
        self.field_name = field_name
        self.header = header

    is_input = False

    @staticmethod
    def create_if_can_process(header):
        gold_match = re.match('(?P<field>.*?)(_priv)?_gold(_(?P<type>json|number|bool|null))?$', header)
        if gold_match:
            return GoldFieldProcessor(gold_match.group('type'), gold_match.group('field'), header)

    def process(self, task_data, cell, *args):
        if not cell:
            return
        task_data.setdefault('gold_answers', {})[self.field_name] = get_value(self.header, cell, self.data_type)

class PrivateFieldProcessor(object):
    def __init__(self, data_type, field_name, header):
        self.data_type = data_type
        self.field_name = field_name
        self.header = header

    is_input = True

    @staticmethod
    def create_if_can_process(header):
        priv_match = re.match('(?P<field>.*?)_priv(_(?P<type>json|number|bool|null))?$', header)
        if priv_match:
            return PrivateFieldProcessor(priv_match.group('type'), priv_match.group('field'), header)

    def process(self, task_data, cell, private_fields, *args):
        if not cell:
            return

        if data_access_levels: # This is how we check for private GIGwork.
            private_fields[self.field_name] = get_value(self.header, cell, self.data_type)
        else:
            task_data["info"][self.field_name] = get_value(self.header, cell, self.data_type)

class DataAccessFieldProcessor(object):
    def __init__(self):
        pass

    field_name = 'data_access'
    is_input = True

    @staticmethod
    def create_if_can_process(header):
        if header == DataAccessFieldProcessor.field_name and data_access_levels:
            return DataAccessFieldProcessor()

    def process(self, task_data, cell, *args):
        if not cell:
            return

        task_data["info"][self.field_name] = json.loads(cell.upper())

class PublicFieldProcessor(object):
    def __init__(self, data_type, field_name, header):
        self.data_type = data_type
        self.field_name = field_name
        self.header = header

    is_input = True

    @staticmethod
    def create_if_can_process(header):
        pub_match = re.match('(?P<field>.*?)(_(?P<type>json|number|bool|null))?$', header)
        if pub_match: # This must match since there are no other options left.
            return PublicFieldProcessor(pub_match.group('type'), pub_match.group('field'), header)

    def process(self, task_data, cell, *args):
        if not cell:
            return

        task_data["info"][self.field_name] = get_value(self.header, cell, self.data_type)

# Abstract base class
class BulkTaskCSVImportBase(BulkTaskImport):

    """Class to import CSV tasks in bulk."""

    def __init__(self):
        BulkTaskImport.__init__(self)
        self._field_processors = None
        self._input_fields = None
    
    def tasks(self):
        """Get tasks from a given URL."""
        return self._get_csv_data()

    def headers(self, csvreader=None):
        if self._headers is not None:
            return self._headers
        if not csvreader:
            csvreader = self._get_csv_reader()
        self._headers = []
        for row in csvreader:
            self._headers = row
            break
        self._check_no_duplicated_headers()
        self._check_no_empty_headers()
        self._check_required_headers()

        return self._headers

    def fields(self, csvreader=None):
        def get_field_processors():
            for header in self.headers(csvreader):
                yield (
                    ReservedFieldProcessor.create_if_can_process(header)
                    or GoldFieldProcessor.create_if_can_process(header)
                    or PrivateFieldProcessor.create_if_can_process(header)
                    or DataAccessFieldProcessor.create_if_can_process(header)
                    or PublicFieldProcessor.create_if_can_process(header)
                )

        if self._field_processors is None:
            self._field_processors = list(get_field_processors())
            self._input_fields = {field.field_name for field in self._field_processors if field.is_input}

        return self._input_fields

    def _convert_row_to_task_data(self, row, row_number):
        task_data = {"info": {}}
        private_fields = dict()

        for idx, cell in enumerate(row):
            self._field_processors[idx].process(task_data, cell, private_fields)
        if private_fields:
            task_data['private_fields'] = private_fields
        return task_data

    def _import_csv_tasks(self, csvreader):
        """Import CSV tasks."""
        # These two lines execute immediately when the function is called.
        # The rest is deferred inside the generator function until the 
        # first task is iterated.
        csviterator = iter(csvreader)
        self.fields(csvreader=csviterator)

        def task_generator():
            row_number = 0
            for row in csviterator:
                row_number += 1
                self._check_valid_row_length(row, row_number)

                # check required fields
                fvals = {self._headers[idx]: cell for idx, cell in enumerate(row)}
                invalid_fields = validate_required_fields(fvals)
                if invalid_fields:
                    msg = gettext('The file you uploaded has incorrect/missing '
                                    'values for required header(s): {0}'
                                    .format(','.join(invalid_fields)))
                    raise BulkImportException(msg)
                task_data = self._convert_row_to_task_data(row, row_number)
                yield task_data

        return task_generator()

    def _check_no_duplicated_headers(self):
        if len(self._headers) != len(set(self._headers)):
            msg = gettext('The file you uploaded has '
                          'two headers with the same name.')
            raise BulkImportException(msg)

    def _check_no_empty_headers(self):
        stripped_headers = [header.strip() for header in self._headers]
        if "" in stripped_headers:
            position = stripped_headers.index("")
            msg = gettext("The file you uploaded has an empty header on "
                          "column %(pos)s.", pos=(position+1))
            raise BulkImportException(msg)

    def _check_valid_row_length(self, row, row_number):
        if len(self._headers) != len(row):
            msg = gettext("The file you uploaded has an extra value on "
                          "row %s." % (row_number+1))
            raise BulkImportException(msg)

    def _check_required_headers(self):
        required_headers = app.config.get("TASK_REQUIRED_FIELDS", {})
        missing_headers = [r for r in required_headers if r not in self._headers]
        if missing_headers:
            msg = gettext('The file you uploaded has missing '
                          'required header(s): {0}'.format(','.join(missing_headers)))
            raise BulkImportException(msg)

    def _get_csv_reader(self):
        raise NotImplementedError()

    def _get_csv_data(self):
        return self._import_csv_tasks(self._get_csv_reader())

class BulkTaskCSVImport(BulkTaskCSVImportBase):
    importer_id = "csv"

    def __init__(self, csv_url, last_import_meta=None):
        BulkTaskCSVImportBase.__init__(self)
        self.url = csv_url
        self.last_import_meta = last_import_meta

    def _get_data_url(self):
        """Get data from URL."""
        return self.url

    def _get_csv_reader(self):
        """Get CSV data from a request."""
        r = requests.get(self._get_data_url())
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
        return unicode_csv_reader(csvcontent)

class BulkTaskGDImport(BulkTaskCSVImport):

    """Class to import tasks from Google Drive in bulk."""

    importer_id = "gdocs"

    def __init__(self, googledocs_url):
        BulkTaskCSVImport.__init__(self, googledocs_url)

    def _get_data_url(self):
        """Get data from URL."""
        # For old data links of Google Spreadsheets
        if 'ccc?key' in self.url:
            return ''.join([self.url, '&output=csv'])
        # New data format for Google Drive import is like this:
        # https://docs.google.com/spreadsheets/d/key/edit?usp=sharing
        else:
            return ''.join([self.url.split('edit')[0],
                            'export?format=csv'])


class BulkTaskLocalCSVImport(BulkTaskCSVImportBase):

    """Class to import CSV tasks in bulk from local file."""

    importer_id = "localCSV"

    def __init__(self, **form_data):
       BulkTaskCSVImportBase.__init__(self)
       self.form_data = form_data

    def _get_csv_reader(self):
        csv_filename = self.form_data['csv_filename']
        if csv_filename is None:
            msg = ("Not a valid csv file for import")
            raise BulkImportException(gettext(msg), 'error')

        datafile = get_import_csv_file(csv_filename)
        csv_file = FileStorage(io.open(datafile.name, encoding='utf-8-sig'))    #utf-8-sig to ignore BOM

        if csv_file is None or csv_file.stream is None:
            msg = ("Unable to load csv file for import, file {0}".format(csv_filename))
            raise BulkImportException(gettext(msg), 'error')

        csv_file.stream.seek(0)
        csvcontent = io.StringIO(csv_file.stream.read())
        return unicode_csv_reader(csvcontent)

    def tasks(self):
        return list(BulkTaskCSVImportBase.tasks(self))