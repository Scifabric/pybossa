# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
class TestImporterValidation(Test):
    importer = Importer()

    @with_context
    def test_invalid_n_answer(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question1'}, 'n_answers': ''},
                                            {'info': {'question': 'question2'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='gdocs', googledocs_url='http://ggl.com')
        result = self.importer.create_tasks(task_repo, project, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 1, len(tasks)
        assert '1 task import failed due to invalid n_answers' in result.message, result.message
        importer_factory.assert_called_with(**form_data)

    @with_context
    def test_invalid_priority_0(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'question1'}, 'priority_0': ''},
                                            {'info': {'question': 'question2'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='gdocs', googledocs_url='http://ggl.com')
        result = self.importer.create_tasks(task_repo, project, **form_data)
        tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 1, len(tasks)
        assert '1 task import failed due to invalid priority' in result.message, result.message
        importer_factory.assert_called_with(**form_data)

    @with_context
    def test_invalid_bucket(self, importer_factory):
        mock_importer = Mock()
        mock_importer.tasks.return_value = [{'info': {'question': 'https://s3.amazonaws.com/invalid/hey'}},
                                            {'info': {'question': 'question2'}}]
        importer_factory.return_value = mock_importer
        project = ProjectFactory.create()
        form_data = dict(type='gdocs', googledocs_url='http://ggl.com')
        with patch.dict(self.flask_app.config, { 'ALLOWED_S3_BUCKETS': ['valid'] }):
            result = self.importer.create_tasks(task_repo, project, **form_data)
            tasks = task_repo.filter_tasks_by(project_id=project.id)

        assert len(tasks) == 1, len(tasks)
        assert '1 task import failed due to invalid s3 bucket' in result.message, result.message
        importer_factory.assert_called_with(**form_data)
