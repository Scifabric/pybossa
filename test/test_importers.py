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
import copy
import json
import string
from collections import namedtuple
from mock import patch, Mock
from nose.tools import assert_raises
from pybossa.importers import (_BulkTaskDropboxImport, _BulkTaskFlickrImport,
    _BulkTaskCSVImport, _BulkTaskGDImport, _BulkTaskEpiCollectPlusImport,
    BulkImportException, Importer)

from default import Test, FakeResponse
from factories import ProjectFactory, TaskFactory
from pybossa.repositories import TaskRepository
from pybossa.core import db
task_repo = TaskRepository(db)



@patch.object(Importer, '_create_importer_for')
class TestImporterPublicMethods(Test):
    importer = Importer()

    def test_create_tasks_creates_them_correctly(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question',
                                                     'url': 'url'},
                                            'n_answers': 20}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='csv', csv_url='http://fakecsv.com')
        self.importer.create_tasks(task_repo, project.id, **form_data)
        task = task_repo.get_task(1)

        assert task is not None
        assert task.project_id == project.id, task.project_id
        assert task.n_answers == 20, task.n_answers
        assert task.info == {'question': 'question', 'url': 'url'}, task.info
        importer_factory.assert_called_with('csv')
        mock_importer.tasks.assert_called_with(**form_data)

    def test_create_tasks_creates_many_tasks(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question1'}},
                                            {'info': {'question': 'question2'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='gdocs', googledocs_url='http://ggl.com')
        result = self.importer.create_tasks(task_repo, project.id, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 2, len(tasks)
        assert result == '2 new tasks were imported successfully', result
        importer_factory.assert_called_with('gdocs')

    def test_create_tasks_not_creates_duplicated_tasks(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        TaskFactory.create(project=project, info={'question': 'question'})
        form_data = dict(type='flickr', album_id='1234')

        result = self.importer.create_tasks(task_repo, project.id, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 1, len(tasks)
        assert result == 'It looks like there were no new records to import', result
        importer_factory.assert_called_with('flickr')

    def test_count_tasks_to_import_returns_what_expected(self, importer_factory):
        mock_importer = Mock()
        mock_importer.count_tasks.return_value = 2
        importer_factory.return_value = mock_importer
        form_data = dict(type='epicollect', epicollect_project='project',
                         epicollect_form='form')

        number_of_tasks = self.importer.count_tasks_to_import(**form_data)

        assert number_of_tasks == 2, number_of_tasks
        importer_factory.assert_called_with('epicollect')

    def test_get_all_importer_names_returns_default_importer_names(self, create):
        importers = self.importer.get_all_importer_names()
        expected_importers = ['csv', 'gdocs', 'epicollect']

        assert set(importers) == set(expected_importers)

    def test_get_all_importers_returns_configured_importers(self, create):
        importer_params = {'api_key': self.flask_app.config['FLICKR_API_KEY']}
        importer = Importer()
        importer.register_flickr_importer(importer_params)
        importer.register_dropbox_importer()

        assert 'flickr' in importer.get_all_importer_names()
        assert 'dropbox' in importer.get_all_importer_names()

    def test_get_autoimporter_names_returns_default_autoimporter_names(self, create):
        importers = self.importer.get_autoimporter_names()
        expected_importers = ['csv', 'gdocs', 'epicollect']

        assert set(importers) == set(expected_importers)

    def test_get_autoimporter_names_returns_configured_autoimporters(self, create):
        importer_params = {'api_key': self.flask_app.config['FLICKR_API_KEY']}
        importer = Importer()
        importer.register_flickr_importer(importer_params)

        assert 'flickr' in importer.get_autoimporter_names()


class Test_BulkTaskDropboxImport(object):

    dropbox_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0",'
        u'"name":"test.txt",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')
    importer = _BulkTaskDropboxImport()

    def test_count_tasks_returns_0_if_no_files_to_import(self):
        form_data = {'files': [], 'type': 'dropbox'}
        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 0, number_of_tasks

    def test_count_tasks_returns_1_if_1_file_to_import(self):
        form_data = {'files': [self.dropbox_file_data],
                     'type': 'dropbox'}
        number_of_tasks = self.importer.count_tasks(**form_data)

        assert number_of_tasks == 1, number_of_tasks

    def test_tasks_return_emtpy_list_if_no_files_to_import(self):
        form_data = {'files': [], 'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks == [], tasks

    def test_tasks_returns_list_with_1_file_data_if_1_file_to_import(self):
        form_data = {'files': [self.dropbox_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert len(tasks) == 1, tasks

    def test_tasks_returns_tasks_with_fields_for_generic_files(self):
        #For generic file extensions: link, filename, link_raw
        form_data = {'files': [self.dropbox_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.txt"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?raw=1"

    def test_tasks_attributes_for_png_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        png_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?dl=0",'
        u'"name":"test.png",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [png_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.png"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.png?raw=1"
        assert tasks[0]['info']['title'] == "test.png"

    def test_tasks_attributes_for_jpg_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        jpg_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?dl=0",'
        u'"name":"test.jpg",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [jpg_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.jpg"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpg?raw=1"
        assert tasks[0]['info']['title'] == "test.jpg"

    def test_tasks_attributes_for_jpeg_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        jpeg_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?dl=0",'
        u'"name":"test.jpeg",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [jpeg_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.jpeg"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.jpeg?raw=1"
        assert tasks[0]['info']['title'] == "test.jpeg"

    def test_tasks_attributes_for_gif_image_files(self):
        #For image file extensions: link, filename, link_raw, url_m, url_b, title
        gif_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?dl=0",'
        u'"name":"test.gif",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [gif_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.gif"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?raw=1"
        assert tasks[0]['info']['url_m'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?raw=1"
        assert tasks[0]['info']['url_b'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.gif?raw=1"
        assert tasks[0]['info']['title'] == "test.gif"

    def test_tasks_attributes_for_pdf_files(self):
        #For pdf file extension: link, filename, link_raw, pdf_url
        pdf_file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?dl=0",'
        u'"name":"test.pdf",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        form_data = {'files': [pdf_file_data],
                     'type': 'dropbox'}
        tasks = self.importer.tasks(**form_data)

        assert tasks[0]['info']['filename'] == "test.pdf"
        assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?dl=0"
        assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.pdf?raw=1"
        assert tasks[0]['info']['pdf_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.pdf"

    def test_tasks_attributes_for_video_files(self):
        #For video file extension: link, filename, link_raw, video_url
        video_ext = ['mp4', 'm4v', 'ogg', 'ogv', 'webm', 'avi']
        file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        u'"name":"test.extension",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        for ext in video_ext:
            data = string.replace(file_data,'extension', ext)
            form_data = {'files': [data],
                         'type': 'dropbox'}
            tasks = self.importer.tasks(**form_data)

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['video_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.%s" % ext

    def test_tasks_attributes_for_audio_files(self):
        #For audio file extension: link, filename, link_raw, audio_url
        audio_ext = ['mp4', 'm4a', 'mp3', 'ogg', 'oga', 'webm', 'wav']
        file_data = (u'{"bytes":286,'
        u'"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.extension?dl=0",'
        u'"name":"test.extension",'
        u'"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')

        for ext in audio_ext:
            data = string.replace(file_data,'extension', ext)
            form_data = {'files': [data],
                         'type': 'dropbox'}
            tasks = self.importer.tasks(**form_data)

            assert tasks[0]['info']['filename'] == "test.%s" % ext
            assert tasks[0]['info']['link'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?dl=0" % ext
            assert tasks[0]['info']['link_raw'] == "https://www.dropbox.com/s/l2b77qvlrequ6gl/test.%s?raw=1" % ext
            assert tasks[0]['info']['audio_url'] == "https://dl.dropboxusercontent.com/s/l2b77qvlrequ6gl/test.%s" % ext


@patch('pybossa.importers.requests')
class Test_BulkTaskFlickrImport(object):

    invalid_response = {u'stat': u'fail',
                        u'code': 1, u'message': u'Photoset not found'}
    response = {
        u'stat': u'ok',
        u'photoset': {
            u'perpage': 500,
            u'title': u'Science Hack Day Balloon Mapping Workshop',
            u'photo': [
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 6,
                 u'ispublic': 1, u'server': u'5441', u'isfriend': 0,
                 u'secret': u'00e2301a0d', u'isprimary': u'0', u'id': u'8947115130'},
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 4,
                 u'ispublic': 1, u'server': u'3763', u'isfriend': 0,
                 u'secret': u'70d482fc68', u'isprimary': u'0', u'id': u'8946490553'},
                {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 3,
                 u'ispublic': 1, u'server': u'2810', u'isfriend': 0,
                 u'secret': u'99cae13d87', u'isprimary': u'0', u'id': u'8947113960'}],
            u'pages': 1,
            u'primary': u'8947113500',
            u'id': u'72157633923521788',
            u'ownername': u'Teleyinex',
            u'owner': u'32985084@N00',
            u'per_page': 500,
            u'total': u'3',
            u'page': 1}}
    photo = {u'isfamily': 0, u'title': u'Inflating the balloon', u'farm': 6,
             u'ispublic': 1, u'server': u'5441', u'isfriend': 0,
             u'secret': u'00e2301a0d', u'isprimary': u'0', u'id': u'8947115130'}
    importer = _BulkTaskFlickrImport(api_key='fake-key')


    def make_response(self, text, status_code=200):
        fake_response = Mock()
        fake_response.text = text
        fake_response.status_code = status_code
        return fake_response

    def test_call_to_flickr_api_endpoint(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        self.importer._get_album_info('72157633923521788')
        url = 'https://api.flickr.com/services/rest/'
        payload = {'method': 'flickr.photosets.getPhotos',
                   'api_key': 'fake-key',
                   'photoset_id': '72157633923521788',
                   'format': 'json',
                   'nojsoncallback': '1'}
        requests.get.assert_called_with(url, params=payload)

    def test_call_to_flickr_api_uses_no_credentials(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        self.importer._get_album_info('72157633923521788')

        # The request MUST NOT include user credentials, to avoid private photos
        url_call_params = requests.get.call_args_list[0][1]['params'].keys()
        assert 'auth_token' not in url_call_params

    def test_count_tasks_returns_number_of_photos_in_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))

        number_of_tasks = self.importer.count_tasks(album_id='72157633923521788')

        assert number_of_tasks is 3, number_of_tasks

    def test_count_tasks_raises_exception_if_invalid_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.invalid_response))

        assert_raises(BulkImportException, self.importer.count_tasks, album_id='bad')

    def test_count_tasks_raises_exception_on_non_200_flickr_response(self, requests):
        requests.get.return_value = self.make_response('Not Found', 404)

        assert_raises(BulkImportException, self.importer.count_tasks,
                      album_id='72157633923521788')

    def test_tasks_returns_list_of_all_photos(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))

        photos = self.importer.tasks(album_id='72157633923521788')

        assert len(photos) == 3, len(photos)

    def test_tasks_returns_tasks_with_title_and_url_info_fields(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.response))
        url = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d.jpg'
        url_m = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_m.jpg'
        url_b = 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_b.jpg'
        link = 'https://www.flickr.com/photos/32985084@N00/8947115130'
        title = self.response['photoset']['photo'][0]['title']
        photo = self.importer.tasks(album_id='72157633923521788')[0]

        assert photo['info'].get('title') == title
        assert photo['info'].get('url') == url, photo['info'].get('url')
        assert photo['info'].get('url_m') == url_m, photo['info'].get('url_m')
        assert photo['info'].get('url_b') == url_b, photo['info'].get('url_b')
        assert photo['info'].get('link') == link, photo['info'].get('link')

    def test_tasks_raises_exception_if_invalid_album(self, requests):
        requests.get.return_value = self.make_response(json.dumps(self.invalid_response))

        assert_raises(BulkImportException, self.importer.tasks, album_id='bad')

    def test_tasks_raises_exception_on_non_200_flickr_response(self, requests):
        requests.get.return_value = self.make_response('Not Found', 404)

        assert_raises(BulkImportException, self.importer.tasks,
                      album_id='72157633923521788')

    def test_tasks_returns_all_for_sets_with_more_than_500_photos(self, requests):
        # Deep-copy the object, as we will be modifying it and we don't want
        # these modifications to affect other tests
        first_response = copy.deepcopy(self.response)
        first_response['photoset']['pages'] = 2
        first_response['photoset']['total'] = u'600'
        first_response['photoset']['page'] = 1
        first_response['photoset']['photo'] = [self.photo for i in range(500)]
        second_response = copy.deepcopy(self.response)
        second_response['photoset']['pages'] = 2
        second_response['photoset']['total'] = u'600'
        second_response['photoset']['page'] = 2
        second_response['photoset']['photo'] = [self.photo for i in range(100)]
        fake_first_response = self.make_response(json.dumps(first_response))
        fake_second_response = self.make_response(json.dumps(second_response))
        responses = [fake_first_response, fake_second_response]
        requests.get.side_effect = lambda *args, **kwargs: responses.pop(0)

        photos = self.importer.tasks(album_id='72157633923521788')

        assert len(photos) == 600, len(photos)

    def test_tasks_returns_all_for_sets_with_more_than_1000_photos(self, requests):
        # Deep-copy the object, as we will be modifying it and we don't want
        # these modifications to affect other tests
        first_response = copy.deepcopy(self.response)
        first_response['photoset']['pages'] = 3
        first_response['photoset']['total'] = u'1100'
        first_response['photoset']['page'] = 1
        first_response['photoset']['photo'] = [self.photo for i in range(500)]
        second_response = copy.deepcopy(self.response)
        second_response['photoset']['pages'] = 3
        second_response['photoset']['total'] = u'1100'
        second_response['photoset']['page'] = 2
        second_response['photoset']['photo'] = [self.photo for i in range(500)]
        third_response = copy.deepcopy(self.response)
        third_response['photoset']['pages'] = 3
        third_response['photoset']['total'] = u'1100'
        third_response['photoset']['page'] = 3
        third_response['photoset']['photo'] = [self.photo for i in range(100)]
        fake_first_response = self.make_response(json.dumps(first_response))
        fake_second_response = self.make_response(json.dumps(second_response))
        fake_third_response = self.make_response(json.dumps(third_response))
        responses = [fake_first_response, fake_second_response, fake_third_response]
        requests.get.side_effect = lambda *args, **kwargs: responses.pop(0)

        photos = self.importer.tasks(album_id='72157633923521788')

        assert len(photos) == 1100, len(photos)



@patch('pybossa.importers.requests.get')
class Test_BulkTaskCSVImport(object):

    url = 'http://myfakecsvurl.com'
    importer = _BulkTaskCSVImport()


    def test_count_tasks_returns_0_if_no_rows_other_than_header(self, request):
        empty_file = FakeResponse(text='CSV,with,no,content\n', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = empty_file

        number_of_tasks = self.importer.count_tasks(csv_url=self.url)

        assert number_of_tasks is 0, number_of_tasks

    def test_count_tasks_returns_1_for_CSV_with_one_valid_row(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = csv_file

        number_of_tasks = self.importer.count_tasks(csv_url=self.url)

        assert number_of_tasks is 1, number_of_tasks

    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/csv'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.count_tasks, csv_url=self.url)
        try:
            self.importer.count_tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_count_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = FakeResponse(text='Not a CSV', status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.count_tasks, csv_url=self.url)
        try:
            self.importer.count_tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_count_tasks_raises_exception_if_dup_header(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Foo\n1,2,3', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = csv_file
        msg = "The file you uploaded has two headers with the same name."

        assert_raises(BulkImportException, self.importer.count_tasks, csv_url=self.url)
        try:
            self.importer.count_tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/csv'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.tasks, csv_url=self.url)
        try:
            self.importer.tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = FakeResponse(text='Not a CSV', status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.tasks, csv_url=self.url)
        try:
            self.importer.tasks(csv_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_dup_header(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Foo\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
        msg = "The file you uploaded has two headers with the same name."

        raised = False
        try:
            self.importer.tasks(csv_url=self.url).next()
        except BulkImportException as e:
            assert e[0] == msg, e
            raised = True
        finally:
            assert raised, "Exception not raised"

    def test_tasks_raises_exception_if_empty_headers(self, request):
        csv_file = FakeResponse(text='Foo,Bar,\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
        msg = "The file you uploaded has an empty header on column 3."

        raised = False
        try:
            self.importer.tasks(csv_url=self.url).next()
        except BulkImportException as e:
            raised = True
            assert e[0] == msg, e
        finally:
            assert raised, "Exception not raised"

    def test_tasks_raises_exception_if_headers_row_mismatch(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3,4', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
        msg = "The file you uploaded has an extra value on row 2."

        raised = False
        try:
            self.importer.tasks(csv_url=self.url).next()
        except BulkImportException as e:
            raised = True
            assert e[0] == msg, e
        finally:
            assert raised, "Exception not raised"

    def test_tasks_return_tasks_with_only_info_fields(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file

        tasks = self.importer.tasks(csv_url=self.url)
        task = tasks.next()

        assert task == {"info": {u'Bar': u'2', u'Foo': u'1', u'Baz': u'3'}}, task

    def test_tasks_return_tasks_with_non_info_fields_too(self, request):
        csv_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3',
                                status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file

        tasks = self.importer.tasks(csv_url=self.url)
        task = tasks.next()

        assert task == {'info': {u'Foo': u'1', u'Bar': u'2'},
                        u'priority_0': u'3'}, task

    def test_tasks_works_with_encodings_other_than_utf8(self, request):
        csv_file = FakeResponse(text=u'Foo\nM\xc3\xbcnchen', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='ISO-8859-1')
        request.return_value = csv_file

        tasks = self.importer.tasks(csv_url=self.url)
        task = tasks.next()

        assert csv_file.encoding == 'utf-8'



@patch('pybossa.importers.requests.get')
class Test_BulkTaskGDImport(object):

    url = 'http://drive.google.com'
    importer = _BulkTaskGDImport()

    def test_count_tasks_returns_0_if_no_rows_other_than_header(self, request):
        empty_file = FakeResponse(text='CSV,with,no,content\n', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = empty_file

        number_of_tasks = self.importer.count_tasks(googledocs_url=self.url)

        assert number_of_tasks is 0, number_of_tasks

    def test_count_tasks_returns_1_for_CSV_with_one_valid_row(self, request):
        valid_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = valid_file

        number_of_tasks = self.importer.count_tasks(googledocs_url=self.url)

        assert number_of_tasks is 1, number_of_tasks

    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/plain'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.count_tasks, googledocs_url=self.url)
        try:
            self.importer.count_tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_count_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = FakeResponse(text='Not a CSV', status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.count_tasks, googledocs_url=self.url)
        try:
            self.importer.count_tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_count_tasks_raises_exception_if_dup_header(self, request):
        empty_file = FakeResponse(text='Foo,Bar,Foo\n1,2,3', status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        request.return_value = empty_file
        msg = "The file you uploaded has two headers with the same name."

        assert_raises(BulkImportException, self.importer.count_tasks, googledocs_url=self.url)
        try:
            self.importer.count_tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/plain'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access that file"

        assert_raises(BulkImportException, self.importer.tasks, googledocs_url=self.url)
        try:
            self.importer.tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_not_CSV_file(self, request):
        html_request = FakeResponse(text='Not a CSV', status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That file doesn't look like the right file."

        assert_raises(BulkImportException, self.importer.tasks, googledocs_url=self.url)
        try:
            self.importer.tasks(googledocs_url=self.url)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_dup_header(self, request):
        csv_file = FakeResponse(text='Foo,Bar,Foo\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
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
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file

        tasks = self.importer.tasks(googledocs_url=self.url)
        task = tasks.next()

        assert task == {"info": {u'Bar': u'2', u'Foo': u'1', u'Baz': u'3'}}, task

    def test_tasks_return_tasks_with_non_info_fields_too(self, request):
        csv_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3',
                                status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file

        tasks = self.importer.tasks(googledocs_url=self.url)
        task = tasks.next()

        assert task == {'info': {u'Foo': u'1', u'Bar': u'2'},
                        u'priority_0': u'3'}, task

    def test_tasks_works_with_encodings_other_than_utf8(self, request):
        csv_file = FakeResponse(text=u'Foo\nM\xc3\xbcnchen', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='ISO-8859-1')
        request.return_value = csv_file

        tasks = self.importer.tasks(googledocs_url=self.url)
        task = tasks.next()

        assert csv_file.encoding == 'utf-8'



@patch('pybossa.importers.requests.get')
class Test_BulkTaskEpiCollectPlusImport(object):

    epicollect = {'epicollect_project': 'fakeproject',
                  'epicollect_form': 'fakeform'}
    importer = _BulkTaskEpiCollectPlusImport()

    def test_count_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/json'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"

        assert_raises(BulkImportException, self.importer.count_tasks, **self.epicollect)
        try:
            self.importer.count_tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_file_forbidden(self, request):
        forbidden_request = FakeResponse(text='Forbidden', status_code=403,
                                         headers={'content-type': 'text/json'},
                                         encoding='utf-8')
        request.return_value = forbidden_request
        msg = "Oops! It looks like you don't have permission to access the " \
              "EpiCollect Plus project"

        assert_raises(BulkImportException, self.importer.tasks, **self.epicollect)
        try:
            self.importer.tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_count_tasks_raises_exception_if_not_json(self, request):
        html_request = FakeResponse(text='Not an application/json',
                                    status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That project and form do not look like the right one."

        assert_raises(BulkImportException, self.importer.count_tasks, **self.epicollect)
        try:
            self.importer.count_tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_tasks_raises_exception_if_not_json(self, request):
        html_request = FakeResponse(text='Not an application/json',
                                    status_code=200,
                                    headers={'content-type': 'text/html'},
                                    encoding='utf-8')
        request.return_value = html_request
        msg = "Oops! That project and form do not look like the right one."

        assert_raises(BulkImportException, self.importer.tasks, **self.epicollect)
        try:
            self.importer.tasks(**self.epicollect)
        except BulkImportException as e:
            assert e[0] == msg, e

    def test_count_tasks_returns_number_of_tasks_in_project(self, request):
        data = [dict(DeviceID=23), dict(DeviceID=24)]
        response = FakeResponse(text=json.dumps(data), status_code=200,
                                headers={'content-type': 'application/json'},
                                encoding='utf-8')
        request.return_value = response

        number_of_tasks = self.importer.count_tasks(**self.epicollect)

        assert number_of_tasks is 2, number_of_tasks

    def test_tasks_returns_tasks_in_project(self, request):
        data = [dict(DeviceID=23), dict(DeviceID=24)]
        response = FakeResponse(text=json.dumps(data), status_code=200,
                                headers={'content-type': 'application/json'},
                                encoding='utf-8')
        request.return_value = response

        task = self.importer.tasks(**self.epicollect).next()

        assert task == {'info': {u'DeviceID': 23}}, task
