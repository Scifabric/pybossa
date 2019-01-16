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
from mock import patch
from nose.tools import assert_raises
from pybossa.importers import BulkImportException
from pybossa.importers.epicollect import BulkTaskEpiCollectPlusImport
from default import FakeResponse, with_context


@patch('pybossa.importers.epicollect.requests.get')
class TestBulkTaskEpiCollectPlusImport(object):

    epicollect = {'epicollect_project': 'fakeproject',
                  'epicollect_form': 'fakeform'}
    importer = BulkTaskEpiCollectPlusImport(**epicollect)

    @with_context
    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/json'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"

        assert_raises(BulkImportException, self.importer.count_tasks)
        try:
            self.importer.count_tasks()
        except BulkImportException as e:
            assert e.message == msg, e

    @with_context
    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/json'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"

        assert_raises(BulkImportException, self.importer.tasks)
        try:
            self.importer.tasks()
        except BulkImportException as e:
            assert e.message == msg, e

    @with_context
    def test_count_tasks_raises_exception_if_not_json(self, request):
        html_request = FakeResponse(text='Not an application/json',
                                    status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That project and form do not look like the right one."

        assert_raises(BulkImportException, self.importer.count_tasks)
        try:
            self.importer.count_tasks()
        except BulkImportException as e:
            assert e.message == msg, e

    @with_context
    def test_tasks_raises_exception_if_not_json(self, request):
        html_request = FakeResponse(text='Not an application/json',
                                    status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That project and form do not look like the right one."

        assert_raises(BulkImportException, self.importer.tasks)
        try:
            self.importer.tasks()
        except BulkImportException as e:
            assert e.message == msg, e

    @with_context
    def test_count_tasks_returns_number_of_tasks_in_project(self, request):
        data = [dict(DeviceID=23), dict(DeviceID=24)]
        response = FakeResponse(text=json.dumps(data), status_code=200,
                                headers={'content-type': 'application/json'},
                                encoding='utf-8')
        request.return_value = response

        number_of_tasks = self.importer.count_tasks()

        assert number_of_tasks is 2, number_of_tasks

    @with_context
    def test_tasks_returns_tasks_in_project(self, request):
        data = [dict(DeviceID=23), dict(DeviceID=24)]
        response = FakeResponse(text=json.dumps(data), status_code=200,
                                headers={'content-type': 'application/json'},
                                encoding='utf-8')
        request.return_value = response

        task = next(self.importer.tasks())

        assert task == {'info': {'DeviceID': 23}}, task
