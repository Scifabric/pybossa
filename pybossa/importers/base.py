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

class BulkImportException(Exception):

    """Generic Bulk Importer Exception Error."""

    pass


class BulkTaskImport(object):

    """Class to import tasks in bulk."""

    importer_id = None
    _headers = None

    def tasks(self):
        """Return a generator with all the tasks imported."""
        raise NotImplementedError

    def count_tasks(self):
        """Return amount of tasks to be imported."""
        return len([task for task in self.tasks()])

    def headers(self):
        return self._headers

    def import_metadata(self):
        return None


class BulkUserImport(object):

    """Class to import users in bulk."""

    importer_id = None

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
                         "project_slugs", "user_pref", "metadata"]
        res = [h in valid_headers for h in headers]
        if False in res:
            invalid_headers = []
            [invalid_headers.append(headers[i]) for i, r in enumerate(res) if r == False]
            msg = 'The file you uploaded has incorrect header(s): {0}'.format(','.join(invalid_headers))
            raise BulkImportException(msg)


    def _import_csv_users(self, csvreader):
        """Import users from CSV."""
        headers = []
        field_header_index = []
        row_number = 0
        default_vals = dict(
            user_pref={}, metadata={}, project_slugs=[])
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
                self._check_valid_row_length(row, row_number, headers)
                user_data = {"info": {}}
                for idx, cell in enumerate(row):
                    col_header = headers[idx]
                    cell = cell.strip()
                    if idx in field_header_index:
                        if col_header in default_vals:
                            user_data[col_header] = json.loads(cell) \
                                if cell else \
                                default_vals[col_header]
                        else:
                            user_data[col_header] = cell
                    else:
                        user_data["info"][col_header] = cell
                yield user_data

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

    def _check_valid_row_length(self, row, row_number, headers):
        if len(headers) != len(row):
            msg = gettext("The file you uploaded has an extra value on "
                          "row %s." % (row_number+1))
            raise BulkImportException(msg)
