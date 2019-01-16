# -*- coding: utf8 -*-
# This file is part of PyBossa.
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

from mock import patch, Mock, mock_open
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.csv import BulkTaskLocalCSVImport, BulkTaskGDImport

class TestBulkTaskLocalCSVImport(object):

    def setUp(self):
        form_data = {'type': 'localCSV', 'csv_filename': 'fakefile.csv'}
        self.importer = BulkTaskLocalCSVImport(**form_data)

    def test_importer_type_local_csv(self):
        assert isinstance(self.importer, BulkTaskLocalCSVImport) is True
        # confirm object is not of type other than BulkTaskLocalCSVImport
        assert isinstance(self.importer, BulkTaskGDImport) is False

    def test_importer_form_data_csv_filename(self):
        csv_file = self.importer._get_data()
        assert csv_file == 'fakefile.csv'

    def test_count_tasks_returns_0_row(self):
        with patch('pybossa.importers.csv.io.open', mock_open(read_data='Foo,Bar\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_tasks)

    def test_count_tasks_returns_1_row(self):
        with patch('pybossa.importers.csv.io.open', mock_open(read_data='Foo,Bar\n1,2\n'), create=True):
            number_of_tasks = self.importer.count_tasks()
            assert number_of_tasks is 1, number_of_tasks

    def test_count_tasks_returns_2_rows(self):
        with patch('pybossa.importers.csv.io.open', mock_open(read_data='Foo,Bar\n1,2\naaa,bbb\n'), create=True):
            number_of_tasks = self.importer.count_tasks()
            assert number_of_tasks is 2, number_of_tasks
