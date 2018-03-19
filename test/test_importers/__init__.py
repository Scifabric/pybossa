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
        self.importer.create_tasks(task_repo, project.id, **form_data)
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
        result = self.importer.create_tasks(task_repo, project.id, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 2, len(tasks)
        assert result.message == '2 new tasks were imported successfully', result
        importer_factory.assert_called_with(**form_data)

    @with_context
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
        assert result.message == 'It looks like there were no new records to import', result
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

        result = self.importer.create_tasks(task_repo, project.id, **form_data)

        assert result.message == '1 new task was imported successfully', result.message
        assert result.total == 1, result.total
        assert result.metadata == metadata, result.metadata

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
