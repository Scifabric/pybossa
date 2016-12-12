# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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
from default import db, with_context
from nose.tools import assert_equal
from test_api import TestAPI
from mock import patch, call

from factories import ProjectFactory, TaskFactory, TaskRunFactory, UserFactory

from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
from pybossa.repositories import ResultRepository

project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestCompletedTaskAPI(TestAPI):

    @with_context
    def test_completedtask_completedtaskrun_with_params(self):
        """Test API query for completedtask and completedtaskrun with params works"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2,
                                  state='ongoing')
        admin = UserFactory.create()                                    
        # Test no completedtask yet
        url = '/api/completedtask?project_id=1&api_key=api-key1'
        res = self.app.get(url)
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 0, data

        # mark task as completed
        task_runs = TaskRunFactory.create_batch(2, task=task)
        task.state = 'completed'
        task_repo.update(task)
        
        #  test task is completed
        url = '/api/completedtask?project_id=1&api_key=api-key1'
        res = self.app.get(url)
        data = json.loads(res.data)

        # correct result
        assert data[0]['project_id'] == 1, data
        assert data[0]['state'] == u'completed', data

        # call completedtask but with wrong project_id
        url = '/api/completedtask?project_id=99999999&api_key=api-key1'
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data
        
        # get completed task runs
        url = '/api/completedtaskrun?project_id=1&api_key=api-key1'
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 2, data
        
