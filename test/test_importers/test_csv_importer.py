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

from mock import patch
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.csv import BulkTaskCSVImport
from default import FakeResponse, with_context


@patch('pybossa.importers.csv.requests.get')
class TestBulkTaskCSVImport(object):

    def setUp(self):
        url = 'http://myfakecsvurl.com'
        self.importer = BulkTaskCSVImport(csv_url=url)


    @with_context
    def test_count_tasks_returns_0_if_no_rows_other_than_header(self, request):
        empty_file = FakeResponse(text='CSV,with,no,content\n', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = empty_file

        try:
            number_of_tasks = self.importer.count_tasks()
        except BulkImportException as e:
            msg = "The file you uploaded is a malformed CSV."
            assert msg == str(e), str(e)

    def test_count_tasks_returns_1_for_CSV_with_one_valid_row(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = csv_file

        number_of_tasks = self.importer.count_tasks()

        assert number_of_tasks is 1, number_of_tasks

    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/csv'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.count_tasks)
        try:
            self.importer.count_tasks()
        except BulkImportException as e:
            assert msg in str(e), msg

    def test_count_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = FakeResponse(text='Not a CSV', status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.count_tasks)
        try:
            self.importer.count_tasks()
        except BulkImportException as e:
            assert msg in str(e), e

    # def test_count_tasks_raises_exception_if_dup_header(self, request):
    #     csv_file = FakeResponse(text='Foo,Bar,Foo\n1,2,3', status_code=200,
    #                               headers={'content-type': 'text/plain'},
    #                               encoding='utf-8')
    #     request.return_value = csv_file
    #     msg = "The file you uploaded has two headers with the same name."

    #     assert_raises(BulkImportException, self.importer.count_tasks)
    #     try:
    #         self.importer.count_tasks()
    #     except BulkImportException as e:
    #         assert msg in str(e), e

    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/csv'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.tasks)
        try:
            self.importer.tasks()
        except BulkImportException as e:
            assert msg in str(e), e

    def test_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = FakeResponse(text='Not a CSV', status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.tasks)
        try:
            self.importer.tasks()
        except BulkImportException as e:
            assert msg in str(e), e

    # def test_tasks_raises_exception_if_dup_header(self, request):
    #     csv_file = FakeResponse(text='Foo,Bar,Foo\n1,2,3', status_code=200,
    #                             headers={'content-type': 'text/plain'},
    #                             encoding='utf-8')
    #     request.return_value = csv_file
    #     msg = "The file you uploaded has two headers with the same name."

    #     raised = False
    #     try:
    #         next(self.importer.tasks())
    #     except BulkImportException as e:
    #         assert msg in str(e), e
    #         raised = True
    #     finally:
    #         assert raised, "Exception not raised"

    def test_tasks_raises_exception_if_empty_headers(self, request):
        csv_file = FakeResponse(text='Foo,Bar,\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
        msg = "The file you uploaded has an empty header on column 3."

        raised = False
        try:
            next(self.importer.tasks())
        except BulkImportException as e:
            raised = True
            assert msg in str(e), e
        finally:
            assert raised, "Exception not raised"

    def test_tasks_raises_exception_if_headers_row_mismatch(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3,4', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
        msg = "The file you uploaded is a malformed CSV."

        raised = False
        try:
            next(self.importer.tasks())
        except BulkImportException as e:
            raised = True
            assert msg in str(e), e
        finally:
            assert raised, "Exception not raised"

    def test_tasks_return_tasks_with_only_info_fields(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file

        tasks = self.importer.tasks()
        task = next(tasks)

        assert task == {"info": {'Bar': 2, 'Foo': 1, 'Baz': 3}}, task

    def test_tasks_return_tasks_with_non_info_fields_too(self, request):
        csv_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3',
                                status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file

        tasks = self.importer.tasks()
        task = next(tasks)

        assert task == {'info': {'Foo': 1, 'Bar': 2},
                        'priority_0': 3}, task

    def test_tasks_works_with_encodings_other_than_utf8(self, request):
        csv_file = FakeResponse(text='Foo\nM\xc3\xbcnchen', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='ISO-8859-1')
        request.return_value = csv_file

        tasks = self.importer.tasks()
        task = next(tasks)

        assert csv_file.encoding == 'utf-8'
