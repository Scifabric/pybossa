# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from helper import sched
from base import Fixtures, redis_flushall, model
import json


class TestSched(sched.Helper):
    def setUp(self):
        super(TestSched, self).setUp()
        self.endpoints = ['app', 'task', 'taskrun']

    def tearDown(self):
        model.rebuild_db()
        redis_flushall()

    # Tests
    def test_incremental_tasks(self):
        """ Test incremental SCHED strategy - second TaskRun receives first gaven answer"""
        redis_flushall()
        Fixtures.create_2(sched='incremental')

        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register(fullname=self.user.fullname, username=self.user.username,
                      password=self.user.password)
        self.register(fullname="Marie Doe", username="mariedoe", password="dr0wss4p")
        self.signin()

        # Get the only task with no runs!
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        # Check that we received a clean Task
        assert data.get('info'), data
        assert not data.get('info').get('last_answer')

        # Submit an Answer for the assigned task
        tr = dict(app_id=data['app_id'], task_id=data['id'], info={'answer': 'No'})
        tr = json.dumps(tr)

        self.app.post('/api/taskrun', data=tr)
        # No more tasks available for this user!
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        assert not data

        #### Get the only task now with an answer as Anonimous!
        self.signout()
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)

        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No'

        # Submit a second Answer as Anonimous
        tr = dict(app_id=data['app_id'], task_id=data['id'],
                  info={'answer': 'No No'})
        tr = json.dumps(tr)

        self.app.post('/api/taskrun', data=tr)

        #### Get the only task now with an answer as User2!
        self.signin(email="mariedoe@example.com", password="dr0wss4p")
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)

        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No No'
