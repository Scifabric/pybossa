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
from pybossa.importers.csv import BulkTaskLocalCSVImport, BulkTaskGDImport
from pybossa.encryption import AESWithGCM
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from default import with_context, Test
from nose.tools import assert_equal


class TestBulkTaskLocalCSVImport(Test):

    def setUp(self):
        form_data = {'type': 'localCSV', 'csv_filename': 'fakefile.csv'}
        self.importer = BulkTaskLocalCSVImport(**form_data)
        super(TestBulkTaskLocalCSVImport, self).setUp()

    def test_importer_type_local_csv(self):
        assert isinstance(self.importer, BulkTaskLocalCSVImport) is True
        # confirm object is not of type other than BulkTaskLocalCSVImport
        assert isinstance(self.importer, BulkTaskGDImport) is False

    def test_importer_form_data_csv_filename(self):
        csv_file = self.importer._get_data()
        assert csv_file == 'fakefile.csv'

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    def test_count_tasks_returns_0_row(self, s3_get):
        with patch('pybossa.importers.csv.io.open', mock_open(read_data=u'Foo,Bar\n'), create=True):
            number_of_tasks = self.importer.count_tasks()
            assert number_of_tasks is 0, number_of_tasks

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    def test_count_tasks_returns_1_row(self, s3_get):
        with patch('pybossa.importers.csv.io.open', mock_open(read_data=u'Foo,Bar\n1,2\n'), create=True):
            number_of_tasks = self.importer.count_tasks()
            assert number_of_tasks is 1, number_of_tasks

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    def test_count_tasks_returns_2_rows(self, s3_get):
        with patch('pybossa.importers.csv.io.open', mock_open(read_data=u'Foo,Bar\n1,2\naaa,bbb\n'), create=True):
            number_of_tasks = self.importer.count_tasks()
            assert number_of_tasks is 2, number_of_tasks

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    def test_gold_answers_import(self, s3_get):
        expected_t1_gold_ans = {u'ans': u'3', u'ans2': u'4', u'ans3': u'5'}
        expected_t2_gold_ans = {u'ans': u'a1', u'ans2': u'a2', u'ans3': u'a3'}
        with patch('pybossa.importers.csv.io.open', mock_open(read_data=u'Foo,Bar,ans_gold,ans2_gold,ans3_priv_gold\n1,2,3,4,5\naaa,bbb,a1,a2,a3\n'), create=True):
            [t1, t2] = self.importer.tasks()
            assert_equal(t1['gold_answers'], expected_t1_gold_ans), t1
            assert_equal(t2['gold_answers'], expected_t2_gold_ans), t2

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    @patch('pybossa.importers.csv.data_access_levels')
    def test_priv_fields_import(self, mock_data_access, s3_get):
        mock_data_access = True
        expected_t1_priv_field = {u'Bar2': u'4', u'Bar': u'3'}
        expected_t1_priv_gold_ans = {u'ans2': u'5', u'ans': u'2'}
        expected_t2_priv_field = {u'Bar2': u'd', u'Bar': u'c'}
        expected_t2_priv_gold_ans = {u'ans2': u'e', u'ans': u'b'}

        with patch('pybossa.importers.csv.io.open', mock_open(
            read_data=u'Foo,ans_priv_gold,Bar_priv,Bar2_priv,ans2_priv_gold\n1,2,3,4,5\na,b,c,d,e\n'), create=True):
            [t1, t2] = self.importer.tasks()
            assert_equal(t1['private_fields'], expected_t1_priv_field), t1
            assert_equal(t1['private_gold_answers'], expected_t1_priv_gold_ans), t1
            assert_equal(t2['private_fields'], expected_t2_priv_field), t2
            assert_equal(t2['private_gold_answers'], expected_t2_priv_gold_ans), t2
            assert_equal(t1['calibration'], 1)
            assert_equal(t2['calibration'], 1)
            assert_equal(t1['exported'], True)
            assert_equal(t2['exported'], True)

    @with_context
    @patch('pybossa.cloud_store_api.s3.get_s3_bucket_key')
    def test_count_tasks_encrypted(self, s3_get):
        k = Mock()
        s3_get.return_value = '', k
        cont = 'req\n1'
        cipher = AESWithGCM('abcd')
        k.get_contents_as_string.return_value = cipher.encrypt(cont)
        config = {
            'S3_IMPORT_BUCKET': 'aadf',
            'FILE_ENCRYPTION_KEY': 'abcd',
            'ENABLE_ENCRYPTION': True
        }
        with patch.dict(self.flask_app.config, config):
            number_of_tasks = self.importer.count_tasks()
            assert number_of_tasks is 1, number_of_tasks
