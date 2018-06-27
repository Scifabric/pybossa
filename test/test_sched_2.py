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

from helper import sched
from default import with_context
import json
from mock import patch


class TestSched(sched.Helper):
    def setUp(self):
        super(TestSched, self).setUp()
        self.endpoints = ['project', 'task', 'taskrun']

    # Tests
    @with_context
    @patch('pybossa.api.task_run.request')
    def test_incremental_tasks(self, mock_request):
        """ Test incremental SCHED strategy - second TaskRun receives first given answer"""
        self.create_2(sched='incremental')
        mock_request.remote_addr = '127.0.0.0'

        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register(fullname="John Doe", name="johndoe", password="p4ssw0rd")
        self.signout()
        self.register(fullname="Marie Doe", name="mariedoe", password="dr0wss4p")
        self.signout()
        self.signin()

        # Get the only task with no runs!
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)
        print("Task:%s" % data['id'])
        # Check that we received a clean Task
        assert data.get('info'), data
        assert not data.get('info').get('last_answer')

        # Submit an Answer for the assigned task
        tr = dict(project_id=data['project_id'], task_id=data['id'], info={'answer': 'No'})
        tr = json.dumps(tr)

        res = self.app.post('/api/taskrun', data=tr)

        # No more tasks available for this user!
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)
        assert not data, data

        #### Get the only task now with an answer as Anonimous!
        self.signout()
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)

        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No'

        # Submit a second Answer as Anonimous
        tr = dict(project_id=data['project_id'], task_id=data['id'],
                  info={'answer': 'No No'})
        tr = json.dumps(tr)

        self.app.post('/api/taskrun', data=tr)

        #### Get the only task now with an answer as User2!
        self.signin(email="mariedoe@example.com", password="dr0wss4p")
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)

        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No No'
