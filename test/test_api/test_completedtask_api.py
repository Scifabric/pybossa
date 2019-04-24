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
from helper.gig_helper import make_admin
from datetime import datetime, timedelta


project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestCompletedTaskAPI(TestAPI):

    @with_context
    def test_completedtask_completedtaskrun_with_params(self):
        """Test API query for completedtask and completedtaskrun with params works"""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=2,
                                  state='ongoing', exported=False)
        admin = UserFactory.create()
        # Test no completedtask yet
        url = '/api/completedtask?project_id=1&api_key=api-key1'
        res = self.app.get(url)
        data = json.loads(res.data)
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

    @with_context
    def test_completedtask_api(self):
        """Test API query for completedtask works"""
        project = ProjectFactory.create()
        admin = UserFactory.create()
        make_admin(admin)

        # create 2 tasks to be completed, 1 gold task, remaining 2 would be ongoing
        otask, ctask, gtask, ctask2, _ = TaskFactory.create_batch(5, project=project,
            n_answers=2,state='ongoing')
        gtask.calibration = 1
        task_repo.update(gtask)

        # submit task runs
        otask_runs = TaskRunFactory.create_batch(1, task=otask)     # ongoing taskrun
        ctask_runs = TaskRunFactory.create_batch(2, task=ctask)     # completed taskruns
        ctask_runs2 = TaskRunFactory.create_batch(2, task=ctask2)   # completed taskruns 2
        gtask_runs = TaskRunFactory.create_batch(5, task=gtask)     # gold taskruns
        all_expected_taskruns = ctask_runs + ctask_runs2 + gtask_runs
        all_expected_taskruns_ids = [taskruns.id for taskruns in all_expected_taskruns]

        gtask.calibration = 1
        gtask.gold_answers = dict(somefield='g ans')
        task_repo.update(gtask)

        # get all tasks; confirm tasks 2,4 are complete and 3 is gold task
        url = '/api/task?project_id=1&api_key={}&all=1'.format(admin.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, 'There should be total 5 tasks'
        assert data[1]['state'] == 'completed' and data[1]['calibration'] == 0, \
            'Task should have been completed and not a gold task'
        assert data[3]['state'] == 'completed' and data[3]['calibration'] == 0, \
            'Task should have been completed and not a gold task'
        assert data[2]['state'] == 'ongoing' and data[2]['calibration'] == 1, \
            'Task should have been ongoing and a gold task'
        assert data[1]['id'] == ctask.id and data[2]['id'] == gtask.id and \
            data[3]['id'] == ctask2.id, 'Task ids for completed and gold tasks should match'

        # get completed tasks and gold tasks
        expected_tasks = [ctask, gtask, ctask2]
        url = '/api/completedtask?project_id=1&api_key={}&exported=False'.format(admin.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == len(expected_tasks), \
            'Completedtask api should have returned {} tasks'.format(len(expected_tasks))
        for i, task in enumerate(expected_tasks):
            assert data[i]['id'] == task.id, \
                'completedtask api should have returned task {}, state {}, calibration {}' \
                    .format(task.id, task.state, task.calibration)

        # mark expected_tasks as exported, add 3 more gold tasks
        # completedtask api should return new 3 gold tasks
        for task in expected_tasks:
            task.exported = True
            task_repo.save(task)
        new_gold_tasks = TaskFactory.create_batch(3, project=project,
            n_answers=2,state='ongoing', calibration=1, gold_answers=dict(somefield='g ans'))
        url = '/api/completedtask?project_id=1&api_key={}&exported=False'.format(admin.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)

        assert len(data) == len(new_gold_tasks), \
            'completedtasks api should have returned {} tasks'.format(len(new_gold_tasks))
        for i, task in enumerate(new_gold_tasks):
            assert data[i]['id'] == task.id, \
                'completedtask api should have returned new gold tasks {}, state {}, calibration {}' \
                    .format(task.id, task.state, task.calibration)

        # set exported to false to all 8 tasks
        all_expected_tasks = expected_tasks + new_gold_tasks
        all_expected_tasks_ids = [task.id for task in all_expected_tasks]
        for task in all_expected_tasks:
            task.exported = False
            task_repo.save(task)
        url = '/api/completedtask?project_id=1&api_key={}&exported=False'.format(admin.api_key)
        res = self.app.get(url)
        tasks = json.loads(res.data)
        for task in tasks:
            assert task['id'] in all_expected_tasks_ids, \
                'completedtask api should have returned task {}'.format(task['id'])

        # perform api call with last_id
        url = '/api/completedtask?project_id=1&api_key={}&exported=False&last_id={}' \
            .format(admin.api_key, all_expected_tasks[2].id)
        res = self.app.get(url)
        tasks = json.loads(res.data)
        for task in tasks:
            # last id set to all_expected_tasks[2].id. hence returned task ids to be from index 3 onwards
            assert task['id'] in all_expected_tasks_ids[3:], \
                'completedtask api with last_id should not have returned task {}'.format(task['id'])

        # get all completed and gold taskruns
        url = '/api/completedtaskrun?project_id=1&api_key={}&exported=False'.format(admin.api_key)
        res = self.app.get(url)
        taskruns = json.loads(res.data)
        assert len(taskruns) == len(all_expected_taskruns)
        for taskrun in taskruns:
            assert taskrun['id'] in all_expected_taskruns_ids, \
                'completedtaskrun api should have returned taskrun {}'.format(taskrun['id'])

        # perform api call with last_id
        url = '/api/completedtaskrun?project_id=1&api_key={}&exported=False&last_id={}' \
            .format(admin.api_key, all_expected_taskruns_ids[2])
        res = self.app.get(url)
        taskruns = json.loads(res.data)
        for taskrun in taskruns:
            # last id set to all_expected_tasks[2].id. hence returned task ids to be from index 3 onwards
            assert taskrun['id'] in all_expected_taskruns_ids[3:], \
                'completedtaskrun api with last_id should not have returned taskrun {}'.format(taskrun['id'])

        # perform api call with finish_time
        today = datetime.today().strftime('%Y-%m-%d')
        tomorrow = (datetime.today() + timedelta(1)).strftime('%Y-%m-%d')
        url = '/api/completedtaskrun?project_id=1&api_key={}&exported=False&finish_time={}' \
            .format(admin.api_key, today)
        res = self.app.get(url)
        taskruns = json.loads(res.data)
        assert len(taskruns) == 9, 'there should be total 9 completed taskruns returned'

        url = '/api/completedtaskrun?project_id=1&api_key={}&exported=False&finish_time={}' \
            .format(admin.api_key, tomorrow)
        res = self.app.get(url)
        taskruns = json.loads(res.data)
        assert not len(taskruns), 'no completed taskruns for future date'