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
"""This module tests the TaskCsvExporter class."""

from default import Test, with_context
from pybossa.exporter.task_csv_export import TaskCsvExporter
from mock import patch
from codecs import encode
from pybossa.exporter.csv_export import CsvExporter
from pybossa.exporter.json_export import JsonExporter
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from werkzeug.datastructures import FileStorage
from pybossa.uploader.local import LocalUploader

class TestTaskCsvExporter(Test):

    """Test PyBossa TaskCsvExporter module."""

    @with_context
    def test_task_csv_exporter_init(self):
        """Test that TaskCsvExporter init method works."""
        exporter = TaskCsvExporter()
        assert isinstance(exporter, TaskCsvExporter)

    @with_context
    def test_task_csv_exporter_get_keys(self):
        """Test that TaskCsvExporter get_keys method works."""
        exporter = TaskCsvExporter()

        row = {'a': {'nested_x': 'N'},
               'b': 1,
               'c': {
                 'nested_y': {'double_nested': 'www.example.com'},
                 'nested_z': True}}
        keys = sorted(exporter.get_keys(row, 'taskrun'))

        expected_keys = ['taskrun__a',
                         'taskrun__a__nested_x',
                         'taskrun__b',
                         'taskrun__c',
                         'taskrun__c__nested_y',
                         'taskrun__c__nested_y__double_nested',
                         'taskrun__c__nested_z']

        assert keys == expected_keys

    @with_context
    def test_task_csv_exporter_get_values(self):
        """Test that TaskCsvExporter get_values method works."""
        exporter = TaskCsvExporter()

        row = {'a': {'nested_x': 'N'},
               'b': 1,
               'c': {
                 'nested_y': {'double_nested': 'www.example.com'},
                 'nested_z': True}}

        value = exporter.get_value(row, 'c__nested_y__double_nested')

        assert value == 'www.example.com'

        unicode_text = {'german': u'Straße auslösen zerstören',
                        'french': u'français américaine épais',
                        'chinese': u'中國的 英語 美國人',
                        'smart_quotes': u'“Hello”'}

        german_value = exporter.get_value(unicode_text, 'german')
        french_value = exporter.get_value(unicode_text, 'french')
        chinese_value = exporter.get_value(unicode_text, 'chinese')
        smart_quotes_value = exporter.get_value(unicode_text, 'smart_quotes')

        assert german_value == u'Stra\u00DFe ausl\u00F6sen zerst\u00F6ren'
        assert french_value == u'fran\u00E7ais am\u00E9ricaine \u00E9pais'
        assert chinese_value == u'\u4E2D\u570B\u7684 \u82F1\u8A9E \u7F8E\u570B\u4EBA'
        assert smart_quotes_value == u'\u201CHello\u201D'


class TestExporters(Test):

    """Test PyBossa Csv and Json Exporter module."""

    @staticmethod
    def _check_func_called_with_params(call_params, expected_params):
        params = set([param[0][0].filename for param in call_params])
        return not len(params - expected_params)

    @with_context
    @patch('pybossa.exporter.csv_export.uploader')
    @patch('pybossa.exporter.json_export.uploader')
    def test_exporters_generates_zip(self, json_uploader, csv_uploader):
        """Test that CsvExporter and JsonExporter generate zip works."""

        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)
        csv_exporter = CsvExporter()
        json_exporter = JsonExporter()
        csv_exporter.pregenerate_zip_files(project)
        call_csv_params = csv_uploader.upload_file.call_args_list
        expected_csv_params = set(['1_project1_task_run_csv.zip', '1_project1_result_csv.zip', '1_project1_task_csv.zip'])
        assert self._check_func_called_with_params(call_csv_params, expected_csv_params)

        json_exporter.pregenerate_zip_files(project)
        call_json_params = json_uploader.upload_file.call_args_list
        expected_json_params = set(['1_project1_task_run_json.zip', '1_project1_result_json.zip', '1_project1_task_json.zip'])
        assert self._check_func_called_with_params(call_json_params, expected_json_params)
