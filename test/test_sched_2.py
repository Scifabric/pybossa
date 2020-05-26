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
import time
from mock import patch
from factories import TaskFactory, ProjectFactory, TaskRunFactory, UserFactory
from pybossa.redis_lock import get_active_user_count, register_active_user, unregister_active_user, EXPIRE_LOCK_DELAY
from pybossa.core import sentinel

class TestSched(sched.Helper):
    def setUp(self):
        super(TestSched, self).setUp()
        self.endpoints = ['project', 'task', 'taskrun']

    @with_context
    def test_get_active_users_lock(self):
        """ Test number of locked tasks"""
        user = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=user,info={'sched':'default'})
        TaskFactory.create_batch(2, project=project, n_answers=2)

        # Register the active user as a locked task.
        register_active_user(project.id, user.id, sentinel.master)
        # Verify the count of locked tasks for this project equals 1.
        count = get_active_user_count(project.id, sentinel.master)
        assert count == 1

        # Unregister the active user as a locked task.
        unregister_active_user(project.id, user.id, sentinel.master)
        # Verify the count of locked tasks for this project equals 1.
        # There is a delay before the lock is released.
        count = get_active_user_count(project.id, sentinel.master)
        assert count == 1

        # Confirm lock released after a delay.
        time.sleep(EXPIRE_LOCK_DELAY + 1)
        count = get_active_user_count(project.id, sentinel.master)
        assert not count


    # Tests
    @with_context
    @patch('pybossa.api.pwd_manager.ProjectPasswdManager.password_needed')
    @patch('pybossa.api.task_run.request')
    def test_incremental_tasks(self, mock_request, passwd_needed):
        """ Test incremental SCHED strategy - second TaskRun receives first given answer"""
        passwd_needed.return_value = False
        self.create_2(sched='incremental')
        mock_request.remote_addr = '127.0.0.0'

        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register(fullname="John Doe", name="johndoe", password="p4ssw0rd")
        self.signout()
        self.register(fullname="Marie Doe", name="mariedoe", password="dr0wss4p")
        self.signout()
        self.register(fullname="Mario Doe", name="mariodoe", password="dr0wss4p")
        self.signout()
        self.signin()

        # Get the only task with no runs!
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)
        print "Task:%s" % data['id']
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

        #### Get the only task now with an answer as Mario!
        self.signout()
        self.signin(email="mariodoe@example.com", password="dr0wss4p")
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)

        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No'

        # Submit a second Answer as Mario
        tr = dict(project_id=data['project_id'], task_id=data['id'],
                  info={'answer': 'No No'})
        tr = json.dumps(tr)

        res = self.app.post('/api/taskrun', data=tr)
        # no anonymous contributions
        assert res.status_code == 200
        self.signout()

        #### Get the only task now with an answer as User2!
        self.signin(email="mariedoe@example.com", password="dr0wss4p")
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)

        # Check that we received a Task with answer
        assert data.get('info'), data
        assert data.get('info').get('last_answer').get('answer') == 'No No'
