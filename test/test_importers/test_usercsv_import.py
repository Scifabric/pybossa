# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2018 SciFabric LTD.
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
from pybossa.importers.usercsv import BulkUserCSVImport
from pybossa.importers.csv import BulkTaskLocalCSVImport
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from default import with_context, FakeResponse, assert_not_raises

class TestBulkTaskLocalCSVImport(object):

    def setUp(self):
        form_data = {'type': 'usercsvimport', 'csv_filename': 'fakefile.csv'}
        self.importer = BulkUserCSVImport(**form_data)

    def test_importer_type_usercsv(self):
        """Test BulkUserCSVImport is a valid importer"""
        assert isinstance(self.importer, BulkUserCSVImport) is True
        assert isinstance(self.importer, BulkTaskLocalCSVImport) is False

    def test_importer_form_data_csv_filename(self):
        """Test user csv file for import is attached"""
        csv_file = self.importer._get_data()
        assert csv_file == 'fakefile.csv'

    @with_context
    def test_import_users_with_incorrect_headers_returns_error(self):
        """Test user csv file for import has incorrect headers"""
        with patch('pybossa.importers.usercsv.io.open', mock_open(read_data=u'Foo,Bar\n1,2\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'The file you uploaded has incorrect header(s): Foo,Bar'
            try:
                self.importer.count_users()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_with_missing_required_header_name_returns_error(self):
        """Test user csv file for import has missing required header name"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'fullname,email_addr,password,metadata\na,a@a.com,a,a\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'The file you uploaded has missing header(s): name'
            try:
                self.importer.count_users()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_with_missing_required_header_fullname_returns_error(self):
        """Test user csv file for import has missing required header fullname"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'name,email_addr,password,metadata\na,a@a.com,a,a\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'The file you uploaded has missing header(s): fullname'
            try:
                self.importer.count_users()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_with_missing_required_header_metadata_returns_error(self):
        """Test user csv file for import has missing required header metadata"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'name,fullname,email_addr,password\na,a,a@a.com,a\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'The file you uploaded has missing header(s): metadata'
            try:
                self.importer.count_users()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_with_missing_required_header_fullname_password_metadata_returns_error(self):
        """Test user csv file for import has missing required headers fullname, metadata"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'name,email_addr\na,a@a.com\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'The file you uploaded has missing header(s): fullname, metadata'
            try:
                self.importer.count_users()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_with_missing_password_and_user_type_values(self):
        """Test user csv file import having missing password and user_type values"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'name,fullname,email_addr,password,metadata\na,a,a@a.com,,a\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'Missing user_type in metadata'
            try:
                self.importer.count_users()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_raises_exception_for_extra_column(self):
        """Test user csv file import raises exception when there is extra columns"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'name,fullname,email_addr,password,metadata\na,a,a@a.com,a,"{""user_type"":""a""}",extracol\n'), create=True):
            assert_raises(BulkImportException, self.importer.count_users)
            msg = 'The file you uploaded has an extra value on row 2.'
            try:
                self.importer.users().next()
            except BulkImportException as e:
                assert e[0] == msg, e

    @with_context
    def test_import_users_with_correct_data(self):
        """Test user csv file import with correct data"""
        with patch('pybossa.importers.usercsv.io.open',
            mock_open(read_data=u'name,fullname,email_addr,password,metadata\na,a,a@a.com,a,"{""user_type"":""a""}"\n'), create=True):
            assert_not_raises(BulkImportException, self.importer.users)
