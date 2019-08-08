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
        with patch('pybossa.importers.csv.io.open', mock_open(read_data=u'Foo,Bar,ans_gold,ans2_gold,ans3_gold\n1,2,3,4,5\naaa,bbb,a1,a2,a3\n'), create=True):
            [t1, t2] = self.importer.tasks()
            assert_equal(t1['gold_answers'], expected_t1_gold_ans), t1
            assert_equal(t2['gold_answers'], expected_t2_gold_ans), t2

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    @patch('pybossa.importers.csv.data_access_levels')
    def test_priv_fields_import(self, mock_data_access, s3_get):
        mock_data_access = True
        expected_t1_priv_field = {u'Bar2': u'4', u'Bar': u'3'}
        expected_t1_gold_ans = {u'ans2': u'5', u'ans': u'2', u'ans3': u'6'}
        expected_t2_priv_field = {u'Bar2': u'd', u'Bar': u'c'}
        expected_t2_gold_ans = {u'ans2': u'e', u'ans': u'b', u'ans3': u'f'}

        with patch('pybossa.importers.csv.io.open', mock_open(
            read_data=u'Foo,ans_gold,Bar_priv,Bar2_priv,ans2_gold,ans3_priv_gold\n1,2,3,4,5,6\na,b,c,d,e,f\n'), create=True):
            [t1, t2] = self.importer.tasks()
            assert_equal(t1['private_fields'], expected_t1_priv_field), t1
            assert_equal(t1['gold_answers'], expected_t1_gold_ans), t1
            assert_equal(t2['private_fields'], expected_t2_priv_field), t2
            assert_equal(t2['gold_answers'], expected_t2_gold_ans), t2

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

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    @patch('pybossa.importers.csv.data_access_levels')
    def test_typed_fields_import(self, mock_data_access, s3_get):
        mock_data_access = True
        expected_t1_priv_field = {u'Bar2': u'4', u'Bar': u'3', u'ans12': [], u'ans13': 1.3, u'ans14': True, u'ans15': None}
        expected_t1_gold_ans = {u'ans2': u'5', u'ans': u'2', u'ans3': u'6', u'ans8': False, u'ans9': -2, u'ans10': True, u'ans11': None, u'ans16': [], u'ans17': 1.3, u'ans18': True, u'ans19': None}
        expected_t1_field = {u'Foo': u'1', u'ans4': {u'a':1} ,u'ans5': 1.5, u'ans6': True, u'ans7': None}
        expected_t2_priv_field = {u'Bar2': u'd', u'Bar': u'c', u'ans12': None, u'ans13': 0, u'ans14': True, u'ans15': None}
        expected_t2_gold_ans = {u'ans2': u'e', u'ans': u'b', u'ans3': u'f', u'ans8': None, u'ans9': 0, u'ans10': True, u'ans11': None, u'ans16': None, u'ans17': 0, u'ans18': True, u'ans19': None}
        expected_t2_field = {u'Foo': u'a', u'ans4': [1,2] ,u'ans5': 3, u'ans6': False, u'ans7': None}
        fields = {
            'Foo': ['1', 'a', '7', 'g', '14', 'm'],
            'ans_gold': ['2', 'b', '8', 'h', '15', 'n'],
            'Bar_priv': ['3', 'c', '9', 'i', '16', 'o'],
            'Bar2_priv': ['4', 'd', '10', 'j', '17', 'p'],
            'ans2_gold': ['5', 'e', '11', 'k', '18', 'q'],
            'ans3_priv_gold': ['6', 'f', '12', 'l', '19', 'r'],
            'ans4_json': ['"{""a"":1}"', '"[1,2]"', '13', 'true', 'null', '"""a string in JSON"""'],
            'ans5_number': ['1.5', '3', '7', '8', '9', '10'],
            'ans6_bool': ['true', 'false', 'true', 'false', 'true', 'false'],
            'ans7_null': ['null', 'null', 'null', 'null', 'null', 'null'],
            'ans8_gold_json': ['false', 'null', '"[null, true, 1]"', '"""x"""', '8', '{}'],
            'ans9_gold_number': ['-2', '0', '3.5', '1.77777777777777777', 'NaN', '7'],
            'ans10_gold_bool': ['true', 'true', 'true', 'true', 'true', 'true'],
            'ans11_gold_null': ['null', 'null', 'null', 'null', 'null', 'null'],
            'ans12_priv_json': ['[]', 'null', 'true', '1', '2', '3'],
            'ans13_priv_number': ['1.3', '0', '1', '2', '3', '4'],
            'ans14_priv_bool': ['true', 'true', 'true', 'true', 'true', 'true'],
            'ans15_priv_null': ['null', 'null', 'null', 'null', 'null', 'null'],
            'ans16_priv_gold_json': ['[]', 'null', 'true', '1', '2', '3'],
            'ans17_priv_gold_number': ['1.3', '0', '1', '2', '3', '4'],
            'ans18_priv_gold_bool': ['true', 'true', 'true', 'true', 'true', 'true'],
            'ans19_priv_gold_null': ['null', 'null', 'null', 'null', 'null', 'null']
        }
        rows = []
        rows.append(','.join(fields.iterkeys()))
        for i in range(6):
            rows.append(','.join(map(lambda x: x[i], fields.itervalues())))
        data = unicode('\n'.join(rows))
        print data
        with patch('pybossa.importers.csv.io.open', mock_open(read_data= data), create=True):
            [t1, t2, t3, t4, t5, t6] = self.importer.tasks()
            assert_equal(t1['private_fields'], expected_t1_priv_field), t1
            assert_equal(t1['gold_answers'], expected_t1_gold_ans), t1
            assert_equal(t1['info'], expected_t1_field), t1
            assert_equal(t2['private_fields'], expected_t2_priv_field), t2
            assert_equal(t2['gold_answers'], expected_t2_gold_ans), t2
            assert_equal(t2['info'], expected_t2_field), t2

    @with_context
    @patch('pybossa.importers.csv.get_import_csv_file')
    @patch('pybossa.importers.csv.data_access_levels')
    def test_invalid_typed_fields_import(self, mock_data_access, s3_get):
        invalid_fields = {
            'ans1_json': 'not json',
            'ans2_number': 'true',
            'ans3_bool': '7',
            'ans4_null': '6',
            'ans5_gold_json': 'True',
            'ans6_gold_number': 'null',
            'ans7_gold_bool': '5',
            'ans8_gold_null': 'false',
            'ans9_priv_json': "''",
            'ans10_priv_number': '[]',
            'ans11_priv_bool': '{}',
            'ans12_priv_null': '"""a string"""',
            'ans13_priv_gold_json': '"{1,2}"',
            'ans14_priv_gold_number': 'false',
            'ans15_priv_gold_bool': 'null',
            'ans16_priv_gold_null': '7'
        }

        for field, value in invalid_fields.iteritems():
            data = u"{}\n{}".format(field, value)
            with patch('pybossa.importers.csv.io.open', mock_open(read_data= data), create=True):
                with assert_raises(BulkImportException):
                    [t1] = self.importer.tasks()
