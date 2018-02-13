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

from helper import sched
from pybossa.core import project_repo
from factories import TaskFactory, ProjectFactory, UserFactory
from pybossa.sched import Schedulers, get_key
from pybossa.core import sentinel
from pybossa.contributions_guard import ContributionsGuard
from default import with_context
import json

from mock import patch


class TestLockedSched(sched.Helper):

    @with_context
    def test_taskrun_submission(self):
        """ Test submissions with locked scheduler """
        owner = UserFactory.create(id=500)
        user = UserFactory.create(id=501)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=1)

        self.set_proj_passwd_cookie(project, user)
        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, user.api_key))
        rec_task1 = json.loads(res.data)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        rec_task2 = json.loads(res.data)

        # users get different tasks
        assert rec_task1['info'] != rec_task2['info']

        # submit answer for the wrong task
        # stamp contribution guard first
        guard = ContributionsGuard(sentinel.master)
        guard.stamp(task1, {'user_id': owner.id})

        tr = {
            'project_id': project.id,
            'task_id': task1.id,
            'info': 'hello'
        }
        res = self.app.post('api/taskrun?api_key={}'.format(owner.api_key),
                            data=json.dumps(tr))
        assert res.status_code == 403, res.status_code

        # submit answer for the right task
        tr['task_id'] = task2.id
        res = self.app.post('api/taskrun?api_key={}'.format(owner.api_key),
                            data=json.dumps(tr))
        assert res.status_code == 200, res.status_code

        tr['task_id'] = task1.id
        res = self.app.post('api/taskrun?api_key={}'.format(user.api_key),
                            data=json.dumps(tr))
        assert res.status_code == 200, res.status_code

    @with_context
    @patch('pybossa.redis_lock.LockManager.release_lock')
    def test_user_logout_unlocks_locked_tasks(self, release_lock):
        """ Test user logout unlocks/expires all locks locked by user """
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='project 1', n_answers=1)

        project2 = ProjectFactory.create(owner=owner)
        project2.info['sched'] = Schedulers.locked

        task2 = TaskFactory.create(project=project2, info='project 2', n_answers=1)

        self.register(name='johndoe')
        self.signin(email='johndoe@example.com')

        self.set_proj_passwd_cookie(project, user=None, username='johndoe')
        res = self.app.get('api/project/1/newtask')
        data = json.loads(res.data)
        assert data.get('info'), data

        self.set_proj_passwd_cookie(project2, user=None, username='johndoe')
        res = self.app.get('api/project/2/newtask')
        data = json.loads(res.data)
        assert data.get('info'), data
        self.signout()

        key_args = [args[0] for args, kwargs in release_lock.call_args_list]
        assert get_key(task1.id) in key_args
        assert get_key(task2.id) in key_args
