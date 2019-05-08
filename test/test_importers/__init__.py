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
from mock import patch, Mock
from pybossa.importers import Importer

from default import Test, with_context
from factories import ProjectFactory, TaskFactory
from pybossa.repositories import TaskRepository
from pybossa.core import db
from pybossa.cloud_store_api.s3 import s3_upload_from_string
task_repo = TaskRepository(db)


@patch.object(Importer, '_create_importer_for')
class TestImporterPublicMethods(Test):
    importer = Importer()

    @with_context
    def test_create_tasks_creates_them_correctly(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question',
                                                     'url': 'url'},
                                            'n_answers': 20}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='csv', csv_url='http://fakecsv.com')
        self.importer.create_tasks(task_repo, project, **form_data)
        task = task_repo.get_task(1)

        assert task is not None
        assert task.project_id == project.id, task.project_id
        assert task.n_answers == 20, task.n_answers
        assert task.info == {'question': 'question', 'url': 'url'}, task.info
        importer_factory.assert_called_with(**form_data)
        mock_importer.tasks.assert_called_with()

    @with_context
    def test_create_tasks_creates_many_tasks(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question1'}},
                                            {'info': {'question': 'question2'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='gdocs', googledocs_url='http://ggl.com')
        result = self.importer.create_tasks(task_repo, project, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 2, len(tasks)
        assert result.message == '2 new tasks were imported successfully ', result
        importer_factory.assert_called_with(**form_data)

    @with_context
    def test_create_tasks_not_creates_duplicated_tasks(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        TaskFactory.create(project=project, info={'question': 'question'})
        form_data = dict(type='flickr', album_id='1234')

        result = self.importer.create_tasks(task_repo, project, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 1, len(tasks)
        assert result.message == 'It looks like there were no new records to import. ', result.message
        importer_factory.assert_called_with(**form_data)

    @with_context
    def test_create_tasks_returns_task_report(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question'}}]
        metadata = {"metadata": 123}
        mock_importer.import_metadata.return_value = metadata
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='flickr', album_id='1234')

        result = self.importer.create_tasks(task_repo, project, **form_data)

        assert result.message == '1 new task was imported successfully ', result.message
        assert result.total == 1, result.total
        assert result.metadata == metadata, result.metadata

    @with_context
    def test_create_tasks_save_exception(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question'}}]
        metadata = {"metadata": 123}
        mock_importer.import_metadata.return_value = metadata
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='flickr', album_id='1234')
        with patch.object(task_repo, 'save', side_effect=Exception('a')):
            result = self.importer.create_tasks(task_repo, project, **form_data)
        assert '1 task import failed due to a' in result.message, result.message

    @with_context
    def test_count_tasks_to_import_returns_number_of_tasks_to_import(self, importer_factory):
        mock_importer = Mock()
        mock_importer.count_tasks.return_value = 2
        importer_factory.return_value = mock_importer
        form_data = dict(type='epicollect', epicollect_project='project',
                         epicollect_form='form')

        number_of_tasks = self.importer.count_tasks_to_import(**form_data)

        assert number_of_tasks == 2, number_of_tasks
        importer_factory.assert_called_with(**form_data)

    @with_context
    def test_get_all_importer_names_returns_default_importer_names(self, create):
        importers = self.importer.get_all_importer_names()
        expected_importers = ['csv', 'gdocs', 'epicollect', 's3', 'localCSV',
                              'iiif']

        assert set(importers) == set(expected_importers)

    @with_context
    def test_get_all_importers_returns_configured_importers(self, create):
        flickr_params = {'api_key': self.flask_app.config['FLICKR_API_KEY']}
        twitter_params = {}
        youtube_params = {'youtube_api_server_key': self.flask_app.config['YOUTUBE_API_SERVER_KEY']}
        importer = Importer()
        importer.register_flickr_importer(flickr_params)
        importer.register_dropbox_importer()
        importer.register_twitter_importer(twitter_params)
        importer.register_youtube_importer(youtube_params)

        assert 'flickr' in importer.get_all_importer_names()
        assert 'dropbox' in importer.get_all_importer_names()
        assert 'twitter' in importer.get_all_importer_names()
        assert 'youtube' in importer.get_all_importer_names()

    @with_context
    def test_get_autoimporter_names_returns_default_autoimporter_names(self, create):
        importers = self.importer.get_autoimporter_names()
        expected_importers = ['csv', 'gdocs', 'epicollect', 'localCSV', 'iiif']

        assert set(importers) == set(expected_importers)

    @with_context
    def test_get_autoimporter_names_returns_configured_autoimporters(self, create):
        flickr_params = {'api_key': self.flask_app.config['FLICKR_API_KEY']}
        twitter_params = {}
        importer = Importer()
        importer.register_flickr_importer(flickr_params)
        importer.register_dropbox_importer()
        importer.register_twitter_importer(twitter_params)

        assert 'flickr' in importer.get_autoimporter_names()
        assert 'twitter' in importer.get_autoimporter_names()
        assert 'dropbox' not in importer.get_autoimporter_names()

    @with_context
    @patch('pybossa.cloud_store_api.s3.s3_upload_from_string', return_value='https:/s3/task.json')
    @patch('pybossa.importers.importer.delete_import_csv_file', return_value=None)
    @patch('pybossa.importers.csv.data_access_levels')
    @patch('pybossa.task_creator_helper.data_access_levels')
    def test_create_tasks_creates_private_regular_and_gold_fields(self,
        mock_data_access, mock_data_access_task_creator, mock_del, upload_from_string, importer_factory):
        mock_importer = Mock()
        mock_data_access = True
        mock_data_access_task_creator = True
        mock_importer.tasks.return_value = [{'info': {u'Foo': u'a'}, 'private_fields': {u'Bar2': u'd', u'Bar': u'c'},
            'gold_answers': {u'ans2': u'e', u'ans': u'b'}, 'calibration': 1, 'exported': True}]

        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='localCSV', csv_filename='fakefile.csv')

        with patch.dict(self.flask_app.config, { 'S3_REQUEST_BUCKET': 'mybucket', 'S3_CONN_TYPE': 'dev' }):
            result = self.importer.create_tasks(task_repo, project, **form_data)
            importer_factory.assert_called_with(**form_data)
            upload_from_string.assert_called()
            assert result.message == '1 new task was imported successfully ', result

            # validate task created has private fields url, gold_answers url
            # calibration and exported flag set
            tasks = task_repo.filter_tasks_by(project_id=project.id)
            assert len(tasks) == 1, len(tasks)
            task = tasks[0]
            private_json_url = task.info['private_json__upload_url']

            localhost, fileproxy, encrypted, env, bucket, project_id, hash_key, filename = private_json_url.split('/', 2)[2].split('/')
            assert localhost == 'localhost', localhost
            assert fileproxy == 'fileproxy', fileproxy
            assert encrypted == 'encrypted', encrypted
            assert env == 'dev', env
            assert bucket == 'mybucket', bucket
            assert project_id == '1', project_id
            assert filename == 'task_private_data.json', filename

            gold_ans__upload_url = task.gold_answers['gold_ans__upload_url']
            localhost, fileproxy, encrypted, env, bucket, project_id, hash_key, filename = gold_ans__upload_url.split('/', 2)[2].split('/')
            assert localhost == 'localhost', localhost
            assert fileproxy == 'fileproxy', fileproxy
            assert encrypted == 'encrypted', encrypted
            assert env == 'dev', env
            assert bucket == 'mybucket', bucket
            assert project_id == '1', project_id
            assert filename == 'task_private_gold_answer.json', filename
            assert task.calibration and task.exported
            assert task.state == 'ongoing', task.state
