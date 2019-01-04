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
from pybossa.sched import (
    get_task_users_key,
    acquire_lock,
    has_lock,
    get_locked_task
)
from pybossa.core import sentinel
from pybossa.contributions_guard import ContributionsGuard
from default import with_context
import json

from mock import patch


class TestLockedSched(sched.Helper):

    @with_context
    def test_get_locked_task(self):
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        t1 = get_locked_task(project.id)
        t2 = get_locked_task(project.id, 1)
        assert t1[0].id == task1.id
        assert t2[0].id == task1.id
        t3 = get_locked_task(project.id, 2)
        t4 = get_locked_task(project.id, 3)
        assert t3[0].id == task2.id
        assert t4[0].id == task2.id

        t5 = get_locked_task(project.id)
        assert t5[0].id == task1.id

        t6 = get_locked_task(project.id, 4)
        assert not t6

    @with_context
    def test_get_locked_task_offset(self):
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=2)
        task3 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        t1 = get_locked_task(project.id, 1)
        assert t1[0].id == task1.id
        t2 = get_locked_task(project.id, 1, offset=1)
        assert t2[0].id == task2.id
        t3 = get_locked_task(project.id, 1, offset=2)
        assert not t3

    @with_context
    def test_taskrun_submission(self):
        owner = UserFactory.create(id=500)
        user = UserFactory.create(id=501)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=1)

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
    def test_anonymous_taskrun_submission(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=1)

        res = self.app.get('api/project/{}/newtask'.format(project.id))
        rec_task1 = json.loads(res.data)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        rec_task2 = json.loads(res.data)

        # users get different tasks
        assert rec_task1['info'] != rec_task2['info']

        tr = {
            'project_id': project.id,
            'task_id': task1.id,
            'info': 'hello'
        }

        # submit answer for the right task
        res = self.app.post('api/taskrun', data=json.dumps(tr))
        assert res.status_code == 200, res.status_code

    @with_context
    def test_anonymous_taskrun_submission_external_uid(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=1)

        headers = self.get_headers_jwt(project)

        res = self.app.get('api/project/{}/newtask?external_uid={}'
                           .format(project.id, '1xa'), headers=headers)
        rec_task1 = json.loads(res.data)

        res = self.app.get('api/project/{}/newtask?external_uid={}'
                           .format(project.id, '2xa'), headers=headers)
        rec_task2 = json.loads(res.data)

        # users get different tasks
        print(rec_task1)
        print(rec_task2)
        assert rec_task1['info'] != rec_task2['info']

        tr = {
            'project_id': project.id,
            'task_id': task1.id,
            'info': 'hello'
        }

        # submit answer for the right task
        res = self.app.post('api/taskrun?external_uid=1xa', data=json.dumps(tr),
                            headers=headers)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_one_task(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)

        res = self.app.get('api/project/{}/newtask'.format(project.id))
        rec_task1 = json.loads(res.data)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        rec_task2 = json.loads(res.data)
        assert not rec_task2

    @with_context
    def test_lock_expiration(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task1 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        # fake expired user lock
        acquire_lock(task1.id, 1000, 2, -10)

        res = self.app.get('api/project/{}/newtask'.format(project.id))
        rec_task1 = json.loads(res.data)

        assert rec_task1['info'] == 'task 1'

    @with_context
    def test_invalid_offset(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = 'locked'
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task1 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        res = self.app.get('api/project/{}/newtask?api_key={}&offset=3'
                           .format(project.id, owner.api_key))

        assert res.status_code == 400, res.data

    @with_context
    def test_acquire_lock_no_pipeline(self):
        task_id = 1
        user_id = 1
        limit = 1
        timeout = 100
        acquire_lock(task_id, user_id, limit, timeout)
        assert has_lock(task_id, user_id, limit)
