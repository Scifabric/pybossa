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
from flask_babel import gettext

class BulkImportException(Exception):

    """Generic Bulk Importer Exception Error."""

    pass


class BulkTaskImport(object):

    """Class to import tasks in bulk."""

    def __init__(self):
        self._headers = None

    importer_id = None

    def tasks(self):
        """Return a generator with all the tasks imported."""
        raise NotImplementedError

    def count_tasks(self):
        """Return amount of tasks to be imported."""
        return len([task for task in self.tasks()])

    def headers(self):
        return self._headers

    def fields(self):
        return set(self.headers() or [])

    def import_metadata(self):
        return None


class BulkUserImport(object):

    """Class to import users in bulk."""

    importer_id = None
    default_vals = dict(
        user_pref={}, metadata={}, project_slugs=[], data_access=[])
    reqd_headers = ["name", "fullname", "email_addr", "metadata"]
    def users(self):
        """Return a generator with all the users imported."""
        raise NotImplementedError

    def count_users(self):
        """Return number of users to be imported."""
        return len([user for user in self.users()])

    def import_metadata(self):
        return None

    def _check_valid_headers(self, headers):
        valid_headers = ["name", "fullname", "email_addr", "password",
                         "project_slugs", "user_pref", "metadata",
                         "data_access"]
        invalid_headers = [h for h in headers if h not in valid_headers]
        if invalid_headers:
            msg = 'The file you uploaded has incorrect header(s): {0}'.format(','.join(invalid_headers))
            raise BulkImportException(msg)

        missing_reqd_headers = set(self.reqd_headers) - set(headers)
        if missing_reqd_headers:
            msg = 'The file you uploaded has missing header(s): {0}' \
                    .format(', '.join(missing_reqd_headers))
            raise BulkImportException(msg)

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
                          "column %(pos)s.", pos=(position+1))
            raise BulkImportException(msg)

    def _check_row_values(self, row, row_number, headers, field_header_index):
        errors = []
        if len(headers) != len(row):
            msg = gettext("The file you uploaded has an extra value on "
                          "row %s." % (row_number+1))
            raise BulkImportException(msg)

        for idx, cell in enumerate(row):
            col_header = headers[idx]
            cell = cell.strip()
            if not cell and col_header in self.reqd_headers:
                errors.append('Missing {} value'.format(col_header))
            elif col_header == 'metadata' and 'user_type' not in cell:
                errors.append('Missing user_type in metadata')
            elif cell and col_header in self.default_vals:
                try:
                    json.loads(cell)
                except ValueError:
                    errors.append('{} value error'.format(col_header))
        if errors:
            msg = ', '.join(errors)
            raise BulkImportException(msg)
