# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
import json
from collections import namedtuple
from mock import patch, Mock
from nose.tools import assert_raises
from pybossa.importers import (_BulkTaskFlickrImport, _BulkTaskCSVImport,
    _BulkTaskGDImport, _BulkTaskEpiCollectPlusImport, BulkImportException,
    create_tasks, count_tasks_to_import)

from default import Test
from factories import AppFactory, TaskFactory
from pybossa.repositories import TaskRepository
from pybossa.core import db
task_repo = TaskRepository(db)



class TestImportersPublicFunctions(Test):

    @patch('pybossa.importers._create_importer_for')
    def test_create_tasks_creates_them_correctly(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question',
                                                     'url': 'url'},
                                            'n_answers': 20}]
        importer_factory.return_value = mock_importer
        app = AppFactory.create()

        create_tasks(task_repo, app.id, 'csv', csv_url='http://fakecsv.com')
        task = task_repo.get_task(1)

        assert task is not None
        assert task.app_id == app.id, task.app_id
        assert task.n_answers == 20, task.n_answers
        assert task.info == {'question': 'question', 'url': 'url'}, task.info
        importer_factory.assert_called_with('csv')
        mock_importer.tasks.assert_called_with(csv_url='http://fakecsv.com')


    @patch('pybossa.importers._create_importer_for')
    def test_create_tasks_creates_many_tasks(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question1'}},
                                            {'info': {'question': 'question2'}}]
        importer_factory.return_value = mock_importer
        app = AppFactory.create()

        result = create_tasks(task_repo, app.id, 'gdocs', googledocs_url='http://ggl.com')
        tasks = task_repo.filter_tasks_by(app_id=app.id)

        assert len(tasks) == 2, len(tasks)
        assert result == '2 new tasks were imported successfully', result
        importer_factory.assert_called_with('gdocs')


    @patch('pybossa.importers._create_importer_for')
    def test_create_tasks_not_creates_duplicated_tasks(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question'}}]
        importer_factory.return_value = mock_importer
        app = AppFactory.create()
        TaskFactory.create(app=app, info={'question': 'question'})

        result = create_tasks(task_repo, app.id, 'flickr', album_id='1234')
        tasks = task_repo.filter_tasks_by(app_id=app.id)

        assert len(tasks) == 1, len(tasks)
        assert result == 'It looks like there were no new records to import', result
        importer_factory.assert_called_with('flickr')


    @patch('pybossa.importers._create_importer_for')
    def test_count_tasks_to_import_returns_what_expected(self, importer_factory):
        mock_importer = Mock()
        mock_importer.count_tasks.return_value = 2
        importer_factory.return_value = mock_importer

        number_of_tasks = count_tasks_to_import('epicollect',
                                                epicollect_project='project',
                                                epicollect_form='form')

        assert number_of_tasks == 2, number_of_tasks
        importer_factory.assert_called_with('epicollect')




@patch('pybossa.importers.requests')
class Test_BulkTaskFlickrImport(object):

    invalid_photoset_response = {u'stat': u'fail',
                                 u'code': 1, u'message': u'Photoset not found'}
    photoset_response = {
        u'stat': u'ok',
        u'photoset': {
            u'perpage': 500,
            u'title': u'Science Hack Day Balloon Mapping Workshop',
            u'photo': [
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 6, u'ispublic': 1, u'server': u'5441', u'isfriend': 0, u'secret': u'00e2301a0d', u'isprimary': u'0', u'id': u'8947115130'},
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 4, u'ispublic': 1, u'server': u'3763', u'isfriend': 0, u'secret': u'70d482fc68', u'isprimary': u'0', u'id': u'8946490553'},
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 3, u'ispublic': 1, u'server': u'2810', u'isfriend': 0, u'secret': u'99cae13d87', u'isprimary': u'0', u'id': u'8947113960'},
                {u'isfamily': 0, u'title': u'Best balloon ever', u'farm': 9, u'ispublic': 1, u'server': u'8120', u'isfriend': 0, u'secret': u'10aca4ac5e', u'isprimary': u'1', u'id': u'8947113500'},
                {u'isfamily': 0, u'title': u'Tying the balloon', u'farm': 8, u'ispublic': 1, u'server': u'7393', u'isfriend': 0, u'secret': u'9cfebaaa17', u'isprimary': u'0', u'id': u'8946487679'},
                {u'isfamily': 0, u'title': u'Adding a ring', u'farm': 8, u'ispublic': 1, u'server': u'7367', u'isfriend': 0, u'secret': u'a058869bc9', u'isprimary': u'0', u'id': u'8946487131'},
                {u'isfamily': 0, u'title': u'Attaching the balloon to the string', u'farm': 3, u'ispublic': 1, u'server': u'2820', u'isfriend': 0, u'secret': u'da953ecc07', u'isprimary': u'0', u'id': u'8947109952'},
                {u'isfamily': 0, u'title': u'Checking the balloon connections', u'farm': 9, u'ispublic': 1, u'server': u'8267', u'isfriend': 0, u'secret': u'f8303887ec', u'isprimary': u'0', u'id': u'8946484353'},
                {u'isfamily': 0, u'title': u'Setting up the camera', u'farm': 4, u'ispublic': 1, u'server': u'3803', u'isfriend': 0, u'secret': u'71ff58689b', u'isprimary': u'0', u'id': u'8947107094'},
                {u'isfamily': 0, u'title': u'Securing the camera', u'farm': 6, u'ispublic': 1, u'server': u'5338', u'isfriend': 0, u'secret': u'b4175399b7', u'isprimary': u'0', u'id': u'8946482659'},
                {u'isfamily': 0, u'title': u'Attaching the bottle rig to the balloon', u'farm': 6, u'ispublic': 1, u'server': u'5456', u'isfriend': 0, u'secret': u'f99745f017', u'isprimary': u'0', u'id': u'8946480363'},
                {u'isfamily': 0, u'title': u'Infragram camera from Public Laboratory', u'farm': 3, u'ispublic': 1, u'server': u'2833', u'isfriend': 0, u'secret': u'3447659c65', u'isprimary': u'0', u'id': u'8947103528'},
                {u'isfamily': 0, u'title': u'Balloon Mapping', u'farm': 6, u'ispublic': 1, u'server': u'5350', u'isfriend': 0, u'secret': u'2e65b7b453', u'isprimary': u'0', u'id': u'8946479121'},
                {u'isfamily': 0, u'title': u'Balloon Mapping', u'farm': 4, u'ispublic': 1, u'server': u'3714', u'isfriend': 0, u'secret': u'cc70885ab8', u'isprimary': u'0', u'id': u'8947102174'},
                {u'isfamily': 0, u'title': u'Balloon Mapping', u'farm': 3, u'ispublic': 1, u'server': u'2810', u'isfriend': 0, u'secret': u'9a8f52c9f2', u'isprimary': u'0', u'id': u'8947101672'}],
            u'pages': 1,
            u'primary': u'8947113500',
            u'id': u'72157633923521788',
            u'ownername': u'Teleyinex',
            u'owner': u'32985084@N00',
            u'per_page': 500,
            u'total': u'15',
            u'page': 1}}
    importer = _BulkTaskFlickrImport()


    def test_call_to_flickr_api_endpoint(self, requests):
        try:
            from settings_local import FLICKR_API_KEY as api_key
        except Exception:
            api_key = None
        fake_response = Mock()
        fake_response.text = '{}'
        requests.get.return_value = fake_response
        self.importer._get_album_info('72157633923521788')
        api_url = 'https://api.flickr.com/services/rest/?\
        method=flickr.photosets.getPhotos&api_key=%s&photoset_id=72157633923521788\
        &format=json&nojsoncallback=1' % api_key
        requests.get.assert_called_with(api_url)

    def test_count_tasks_returns_number_of_photos_in_album(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.photoset_response)
        requests.get.return_value = fake_response

        number_of_tasks = self.importer.count_tasks(album_id='72157633923521788')

        assert number_of_tasks is 15, number_of_tasks


    def test_count_tasks_raises_exception_if_invalid_album(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.invalid_photoset_response)
        requests.get.return_value = fake_response

        assert_raises(BulkImportException, self.importer.count_tasks, album_id='bad')


    def test_tasks_returns_list_of_all_photos(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.photoset_response)
        requests.get.return_value = fake_response

        photos = self.importer.tasks(album_id='72157633923521788')

        assert len(photos) == 15, len(photos)


    def test_tasks_returns_tasks_with_title_and_url_info_fields(self, requests):
        task_data_info_fields = ['url', 'title']
        fake_response = Mock()
        fake_response.text = json.dumps(self.photoset_response)
        requests.get.return_value = fake_response

        url = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d.jpg'
        url_m = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_m.jpg'
        url_b = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_b.jpg'
        title = self.photoset_response['photoset']['photo'][0]['title']
        photo = self.importer.tasks(album_id='72157633923521788')[0]

        assert photo['info'].get('title') == title
        assert photo['info'].get('url') == url, photo['info'].get('url')
        assert photo['info'].get('url_m') == url_m, photo['info'].get('url_m')
        assert photo['info'].get('url_b') == url_b, photo['info'].get('url_b')


    def test_tasks_raises_exception_if_invalid_album(self, requests):
        fake_response = Mock()
        fake_response.text = json.dumps(self.invalid_photoset_response)
        requests.get.return_value = fake_response

        assert_raises(BulkImportException, self.importer.tasks, album_id='bad')



@patch('pybossa.importers.requests.get')
class Test_BulkTaskCSVImport(object):

    FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])
    url = 'http://myfakecsvurl.com'
    importer = _BulkTaskCSVImport()


    def test_count_tasks_returns_0_if_no_rows_other_than_header(self, request):
        empty_file = self.FakeRequest('CSV,with,no,content\n', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        number_of_tasks = self.importer.count_tasks(csv_url=self.url)

        assert number_of_tasks is 0, number_of_tasks


    def test_count_tasks_returns_1_for_CSV_with_one_valid_row(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Baz\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        number_of_tasks = self.importer.count_tasks(csv_url=self.url)

        assert number_of_tasks is 1, number_of_tasks


    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = self.FakeRequest('Forbidden', 403,
                                           {'content-type': 'text/csv'})
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.count_tasks, csv_url=self.url)
        try:
            self.importer.count_tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_count_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = self.FakeRequest('Not a CSV', 200,
                                   {'content-type': 'text/html'})
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.count_tasks, csv_url=self.url)
        try:
            self.importer.count_tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_count_tasks_raises_exception_if_dup_header(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Foo\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file
        msg = "The file you uploaded has two headers with the same name."

        assert_raises(BulkImportException, self.importer.count_tasks, csv_url=self.url)
        try:
            self.importer.count_tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = self.FakeRequest('Forbidden', 403,
                                           {'content-type': 'text/csv'})
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.tasks, csv_url=self.url)
        try:
            self.importer.tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = self.FakeRequest('Not a CSV', 200,
                                   {'content-type': 'text/html'})
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.tasks, csv_url=self.url)
        try:
            self.importer.tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_dup_header(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Foo\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file
        msg = "The file you uploaded has two headers with the same name."

        raised = False
        try:
            self.importer.tasks(csv_url=self.url).next()
        except BulkImportException as e:
            assert e[0] == msg, e
            raised = True
        finally:
            assert raised, "Exception not raised"


    def test_tasks_return_tasks_with_only_info_fields(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Baz\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        tasks = self.importer.tasks(csv_url=self.url)
        task = tasks.next()

        assert task == {"info": {u'Bar': u'2', u'Foo': u'1', u'Baz': u'3'}}, task


    def test_tasks_return_tasks_with_non_info_fields_too(self, request):
        empty_file = self.FakeRequest('Foo,Bar,priority_0\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        tasks = self.importer.tasks(csv_url=self.url)
        task = tasks.next()

        assert task == {'info': {u'Foo': u'1', u'Bar': u'2'},
                        u'priority_0': u'3'}, task



@patch('pybossa.importers.requests.get')
class Test_BulkTaskGDImport(object):

    FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])
    url = 'http://drive.google.com'
    importer = _BulkTaskGDImport()


    def test_count_tasks_returns_0_if_no_rows_other_than_header(self, request):
        empty_file = self.FakeRequest('CSV,with,no,content\n', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        number_of_tasks = self.importer.count_tasks(googledocs_url=self.url)

        assert number_of_tasks is 0, number_of_tasks


    def test_count_tasks_returns_1_for_CSV_with_one_valid_row(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Baz\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        number_of_tasks = self.importer.count_tasks(googledocs_url=self.url)

        assert number_of_tasks is 1, number_of_tasks


    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = self.FakeRequest('Forbidden', 403,
                                           {'content-type': 'text/plain'})
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.count_tasks, googledocs_url=self.url)
        try:
            self.importer.count_tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_count_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = self.FakeRequest('Not a CSV', 200,
                                   {'content-type': 'text/html'})
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.count_tasks, googledocs_url=self.url)
        try:
            self.importer.count_tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_count_tasks_raises_exception_if_dup_header(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Foo\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file
        msg = "The file you uploaded has two headers with the same name."

        assert_raises(BulkImportException, self.importer.count_tasks, googledocs_url=self.url)
        try:
            self.importer.count_tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = self.FakeRequest('Forbidden', 403,
                                           {'content-type': 'text/plain'})
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.tasks, googledocs_url=self.url)
        try:
            self.importer.tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = self.FakeRequest('Not a CSV', 200,
                                   {'content-type': 'text/html'})
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.tasks, googledocs_url=self.url)
        try:
            self.importer.tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_dup_header(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Foo\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file
        msg = "The file you uploaded has two headers with the same name."

        raised = False
        try:
            self.importer.tasks(googledocs_url=self.url).next()
        except BulkImportException as e:
            assert e[0] == msg, e
            raised = True
        finally:
            assert raised, "Exception not raised"


    def test_tasks_return_tasks_with_only_info_fields(self, request):
        empty_file = self.FakeRequest('Foo,Bar,Baz\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        tasks = self.importer.tasks(googledocs_url=self.url)
        task = tasks.next()

        assert task == {"info": {u'Bar': u'2', u'Foo': u'1', u'Baz': u'3'}}, task


    def test_tasks_return_tasks_with_non_info_fields_too(self, request):
        empty_file = self.FakeRequest('Foo,Bar,priority_0\n1,2,3', 200,
                                 {'content-type': 'text/plain'})
        request.return_value = empty_file

        tasks = self.importer.tasks(googledocs_url=self.url)
        task = tasks.next()

        assert task == {'info': {u'Foo': u'1', u'Bar': u'2'},
                        u'priority_0': u'3'}, task



@patch('pybossa.importers.requests.get')
class Test_BulkTaskEpiCollectPlusImport(object):

    FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])
    epicollect = {'epicollect_project': 'fakeproject',
                  'epicollect_form': 'fakeform'}
    importer = _BulkTaskEpiCollectPlusImport()

    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        unauthorized_request = self.FakeRequest('Forbidden', 403,
                                           {'content-type': 'application/json'})
        request.return_value = unauthorized_request
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"

        assert_raises(BulkImportException, self.importer.count_tasks, **self.epicollect)
        try:
            self.importer.count_tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_file_forbidden(self, request):
        unauthorized_request = self.FakeRequest('Forbidden', 403,
                                           {'content-type': 'application/json'})
        request.return_value = unauthorized_request
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"

        assert_raises(BulkImportException, self.importer.tasks, **self.epicollect)
        try:
            self.importer.tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_count_tasks_raises_exception_if_not_json(self, request):
        html_request = self.FakeRequest('Not an application/json', 200,
                                   {'content-type': 'text/html'})
        request.return_value = html_request
        msg = "Oops! That project and form do not look like the right one."

        assert_raises(BulkImportException, self.importer.count_tasks, **self.epicollect)
        try:
            self.importer.count_tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_tasks_raises_exception_if_not_json(self, request):
        html_request = self.FakeRequest('Not an application/json', 200,
                                   {'content-type': 'text/html'})
        request.return_value = html_request
        msg = "Oops! That project and form do not look like the right one."

        assert_raises(BulkImportException, self.importer.tasks, **self.epicollect)
        try:
            self.importer.tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e


    def test_count_tasks_returns_number_of_tasks_in_project(self, request):
        data = [dict(DeviceID=23), dict(DeviceID=24)]
        html_request = self.FakeRequest(json.dumps(data), 200,
                                   {'content-type': 'application/json'})
        request.return_value = html_request

        number_of_tasks = self.importer.count_tasks(**self.epicollect)

        assert number_of_tasks is 2, number_of_tasks


    def test_tasks_returns_tasks_in_project(self, request):
        data = [dict(DeviceID=23), dict(DeviceID=24)]
        html_request = self.FakeRequest(json.dumps(data), 200,
                                   {'content-type': 'application/json'})
        request.return_value = html_request

        task = self.importer.tasks(**self.epicollect).next()

        assert task == {'info': {u'DeviceID': 23}}, task
