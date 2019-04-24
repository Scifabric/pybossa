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
    Schedulers,
    get_task_users_key,
    acquire_lock,
    has_lock,
    get_task_id_and_duration_for_project_user,
    get_task_id_project_id_key,
    get_locked_task
)
from pybossa.core import sentinel
from pybossa.contributions_guard import ContributionsGuard
from default import with_context, flask_app
import json
from mock import patch
from helper.gig_helper import make_admin, make_subadmin


class TestLockedSched(sched.Helper):

    patch_data_access_levels = dict(
        valid_access_levels=[("L1", "L1"), ("L2", "L2"),("L3", "L3"), ("L4", "L4")],
        valid_user_levels_for_project_task_level=dict(
            L1=[], L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"]),
        valid_task_levels_for_user_level=dict(
            L1=["L2", "L3", "L4"], L2=["L3", "L4"], L3=["L4"], L4=[]),
        valid_project_levels_for_task_level=dict(
            L1=["L1"], L2=["L1", "L2"], L3=["L1", "L2", "L3"], L4=["L1", "L2", "L3", "L4"]),
        valid_task_levels_for_project_level=dict(
            L1=["L1", "L2", "L3", "L4"], L2=["L2", "L3", "L4"], L3=["L3", "L4"], L4=["L4"])
    )

    @with_context
    def test_get_locked_task(self):
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        t1 = get_locked_task(project.id, 11)
        t2 = get_locked_task(project.id, 1)
        assert t1[0].id == task1.id
        assert t2[0].id == task1.id
        t3 = get_locked_task(project.id, 2)
        t4 = get_locked_task(project.id, 3)
        assert t3[0].id == task2.id
        assert t4[0].id == task2.id

        t5 = get_locked_task(project.id, 11)
        assert t5[0].id == task1.id

        t6 = get_locked_task(project.id, 4)
        assert not t6

    @with_context
    def test_get_locked_task_offset(self):
        owner = UserFactory.create(id=500)
        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task2 = TaskFactory.create(project=project, info='task 2', n_answers=2)
        task3 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        t1 = get_locked_task(project.id, 1)
        assert t1[0].id == task1.id
        t2 = get_locked_task(project.id, 1, offset=1)
        assert t2 is None
        t3 = get_locked_task(project.id, 1, offset=2)
        assert t3 is None

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
        user_rec_task = json.loads(res.data)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        owner_rec_task = json.loads(res.data)

        # users get different tasks
        assert user_rec_task['info'] != owner_rec_task['info']

        user_task = task1 if task1.id == user_rec_task['id'] else task2
        owner_task = task1 if task1.id == owner_rec_task['id'] else task2

        # submit answer for the wrong task
        # stamp contribution guard first
        guard = ContributionsGuard(sentinel.master)
        guard._remove_task_stamped(owner_task, {'user_id': owner.id})

        tr = {
            'project_id': project.id,
            'task_id': owner_task.id,
            'info': 'hello'
        }
        res = self.app.post('api/taskrun?api_key={}'.format(owner.api_key),
                            data=json.dumps(tr))
        assert res.status_code == 403, (res.status_code, res.data)

        # submit answer for the right task
        guard.stamp(owner_task, {'user_id': owner.id})
        tr['task_id'] = owner_task.id
        res = self.app.post('api/taskrun?api_key={}'.format(owner.api_key),
                            data=json.dumps(tr))
        assert res.status_code == 200, res.status_code

        tr['task_id'] = user_task.id
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
        assert get_task_users_key(task1.id) in key_args
        assert get_task_users_key(task2.id) in key_args

    @with_context
    def test_acquire_lock_no_pipeline(self):
        task_id = 1
        user_id = 1
        limit = 1
        timeout = 100
        acquire_lock(task_id, user_id, limit, timeout)
        assert has_lock(task_id, user_id, limit)

    @with_context
    def test_get_task_id_and_duration_for_project_user_missing(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user, short_name='egil', name='egil',
                  description='egil')
        task = TaskFactory.create_batch(1, project=project, n_answers=1)[0]
        limit = 1
        timeout = 100
        acquire_lock(task.id, user.id, limit, timeout)
        task_id, _ = get_task_id_and_duration_for_project_user(project.id, user.id)
        assert get_task_id_project_id_key(task.id) in sentinel.master.keys()
        assert task.id == task_id

    @with_context
    def test_tasks_assigned_as_per_user_access_levels_l1(self):
        """ Test tasks assigned by locked scheduler are as per access levels set for user, task and project"""

        from pybossa import data_access
        from test_api import get_pwd_cookie

        owner = UserFactory.create(id=500)
        user_l1 = UserFactory.create(id=501, info=dict(data_access=["L1"]))
        project = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        project2 = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project2.info['sched'] = Schedulers.user_pref
        project_repo.save(project2)

        task1 = TaskFactory.create(project=project, info=dict(question='q1', data_access=["L1"]), n_answers=1)
        task2 = TaskFactory.create(project=project, info=dict(question='q2', data_access=["L2"]), n_answers=1)
        task3 = TaskFactory.create(project=project2, info=dict(question='q3', data_access=["L1"]), n_answers=1)
        task4 = TaskFactory.create(project=project2, info=dict(question='q4', data_access=["L2"]), n_answers=1)

        self.set_proj_passwd_cookie(project, user_l1)
        with patch.object(data_access, 'data_access_levels', self.patch_data_access_levels):
            res = self.app.get('api/project/{}/newtask?api_key={}'
                               .format(project.id, user_l1.api_key))
            assert res.status_code == 200, res.status_code
            data = json.loads(res.data)
            assert data['id'] == task1.id, 'user_l1 should have obtained task {}'.format(task1.id)
            assert data['info']['data_access'] == task1.info['data_access'], \
                'user_l1 should have obtained task with level {}'.format(task1.info['data_access'])

            self.set_proj_passwd_cookie(project2, user_l1)
            res = self.app.get('api/project/{}/newtask?api_key={}'
                               .format(project2.id, user_l1.api_key))
            assert res.status_code == 200, res.status_code
            data = json.loads(res.data)
            assert data['id'] == task3.id, 'user_l1 should have obtained task {}'.format(task3.id)
            assert data['info']['data_access'] == task3.info['data_access'], \
                'user_l1 should have obtained task with level {}'.format(task3.info['data_access'])


    @with_context
    def test_tasks_assigned_as_per_user_access_levels_l2(self):
        """ Test tasks assigned by locked scheduler are as per access levels set for user, task and project"""

        from pybossa import data_access
        from test_api import get_pwd_cookie

        owner = UserFactory.create(id=500)
        user_l2 = UserFactory.create(id=502, info=dict(data_access=["L2"]))

        project = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        project2 = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project2.info['sched'] = Schedulers.user_pref
        project_repo.save(project2)

        task1 = TaskFactory.create(project=project, info=dict(question='q1', data_access=["L1"]), n_answers=1)
        task2 = TaskFactory.create(project=project, info=dict(question='q2', data_access=["L2"]), n_answers=1)
        task3 = TaskFactory.create(project=project2, info=dict(question='q3', data_access=["L1"]), n_answers=1)
        task4 = TaskFactory.create(project=project2, info=dict(question='q4', data_access=["L2"]), n_answers=1)

        self.set_proj_passwd_cookie(project, user_l2)
        with patch.dict(data_access.data_access_levels, self.patch_data_access_levels):
            res = self.app.get('api/project/{}/newtask?api_key={}'
                               .format(project.id, user_l2.api_key))
            assert res.status_code == 200, res.status_code

            data = json.loads(res.data)
            assert data['id'] == task2.id, 'user_l2 should have obtained task {}'.format(task2.id)
            assert data['info']['data_access'] == task2.info['data_access'], \
                'user_l2 should have obtained task with level {}'.format(task1.info['data_access'])

            self.set_proj_passwd_cookie(project2, user_l2)
            res = self.app.get('api/project/{}/newtask?api_key={}'
                               .format(project2.id, user_l2.api_key))
            assert res.status_code == 200, res.status_code
            data = json.loads(res.data)
            assert data['id'] == task4.id, 'user_l2 should have obtained task {}'.format(task4.id)
            assert data['info']['data_access'] == task4.info['data_access'], \
                'user_l1 should have obtained task with level {}'.format(task4.info['data_access'])

    @with_context
    def test_tasks_assigned_as_per_user_access_levels_l4(self):
        """ Test tasks assigned by locked scheduler are as per access levels set for user, task and project"""

        from pybossa import data_access
        from test_api import get_pwd_cookie

        owner = UserFactory.create(id=500)
        user_l4 = UserFactory.create(id=502, info=dict(data_access=["L4"]))

        project = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        project2 = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project2.info['sched'] = Schedulers.user_pref
        project_repo.save(project2)

        task1 = TaskFactory.create(project=project, info=dict(question='q1', data_access=["L1"]), n_answers=1)
        task2 = TaskFactory.create(project=project, info=dict(question='q2', data_access=["L2"]), n_answers=1)
        task3 = TaskFactory.create(project=project, info=dict(question='q3', data_access=["L2"]), n_answers=1)
        task4 = TaskFactory.create(project=project, info=dict(question='q4', data_access=["L2"]), n_answers=1)

        self.set_proj_passwd_cookie(project, user_l4)
        with patch.dict(data_access.data_access_levels, self.patch_data_access_levels):
            res = self.app.get('api/project/{}/newtask?api_key={}'
                               .format(project.id, user_l4.api_key))
            assert res.status_code == 200, res.status_code
            data = json.loads(res.data)
            assert not data, 'user_l4 with L4 access should not have obtained any task under locked scheduler'

            self.set_proj_passwd_cookie(project2, user_l4)
            res = self.app.get('api/project/{}/newtask?api_key={}'
                               .format(project2.id, user_l4.api_key))
            assert res.status_code == 200, res.status_code
            data = json.loads(res.data)
            assert not data, 'user_l4 with L4 access should not have obtained any task under user pref scheduler'

    @with_context
    @patch('pybossa.sched.random.randint')
    def test_locked_sched_gold_task(self, mock_random):
        """ Test gold tasks presented with locked scheduler """

        [admin, owner, user] = UserFactory.create_batch(3)
        make_admin(admin)
        make_subadmin(owner)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        tasks = TaskFactory.create_batch(4, project=project, n_answers=1)
        gold_task = tasks[3]
        gold_task.calibration = 1; gold_task.gold_answers = dict(field_3='someans')

        # gold task to be presented to the user when available with randomness
        # set to a value (to zero) that means gold task to be presented
        mock_random.return_value = 0
        # user #1
        self.set_proj_passwd_cookie(project, user)
        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, user.api_key))
        assert res.status_code == 200, res.status_code
        resp = json.loads(res.data)
        assert resp['id'] == gold_task.id, \
            'task presented to regular user under locked sched should be gold task'
        # submit answer for gold task
        task_run = dict(project_id=project.id, task_id=gold_task.id, info='hi there!')
        res = self.app.post('api/taskrun?api_key={}'.format(user.api_key),
                            data=json.dumps(task_run))
        assert res.status_code == 200, res.status_code

        # user #2 also gets gold_task even when redundancy was set to 1
        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        assert res.status_code == 200, res.status_code
        resp = json.loads(res.data)
        assert resp['id'] == gold_task.id, \
            'task presented to owner under locked sched should be gold task'

        # after two task run submissions for gold task, state is unchanged to ongoing
        task_run = dict(project_id=project.id, task_id=gold_task.id, info='hi there!')
        res = self.app.post('api/taskrun?api_key={}'.format(owner.api_key),
                            data=json.dumps(task_run))
        assert res.status_code == 200, res.status_code
        res = self.app.get('api/task/{}?api_key={}'
                           .format(gold_task.id, admin.api_key))
        assert res.status_code == 200, res.status_code
        resp = json.loads(res.data)
        assert resp['id'] == gold_task.id and resp['state'] == 'ongoing', \
            'gold task state should be unchanged to ongoing'

        # user #3 don't receive gold_task when randomness is not zero
        mock_random.return_value = 1
        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, admin.api_key))
        assert res.status_code == 200, res.status_code
        resp = json.loads(res.data)
        assert resp['id'] == tasks[0].id, \
            'task presented should not be gold task'

    # @with_context
    # def test_anonymous_taskrun_submission(self):
    #     owner = UserFactory.create(id=500)

    #     project = ProjectFactory.create(owner=owner)
    #     project.info['sched'] = Schedulers.locked
    #     project_repo.save(project)

    #     task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)
    #     task2 = TaskFactory.create(project=project, info='task 2', n_answers=1)

    #     res = self.app.get('api/project/{}/newtask'.format(project.id))
    #     rec_task1 = json.loads(res.data)

    #     res = self.app.get('api/project/{}/newtask?api_key={}'
    #                        .format(project.id, owner.api_key))
    #     rec_task2 = json.loads(res.data)

    #     # users get different tasks
    #     assert rec_task1['info'] != rec_task2['info']

    #     tr = {
    #         'project_id': project.id,
    #         'task_id': task1.id,
    #         'info': 'hello'
    #     }

    #     # submit answer for the right task
    #     res = self.app.post('api/taskrun', data=json.dumps(tr))
    #     assert res.status_code == 200, res.status_code

    # @with_context
    # def test_anonymous_taskrun_submission_external_uid(self):
    #     owner = UserFactory.create(id=500)

    #     project = ProjectFactory.create(owner=owner)
    #     project.info['sched'] = Schedulers.locked
    #     project_repo.save(project)

    #     task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)
    #     task2 = TaskFactory.create(project=project, info='task 2', n_answers=1)

    #     headers = self.get_headers_jwt(project)

    #     res = self.app.get('api/project/{}/newtask?external_uid={}'
    #                        .format(project.id, '1xa'), headers=headers)
    #     rec_task1 = json.loads(res.data)

    #     res = self.app.get('api/project/{}/newtask?external_uid={}'
    #                        .format(project.id, '2xa'), headers=headers)
    #     rec_task2 = json.loads(res.data)

    #     # users get different tasks
    #     assert rec_task1['info'] != rec_task2['info']

    #     tr = {
    #         'project_id': project.id,
    #         'task_id': task1.id,
    #         'info': 'hello'
    #     }

    #     # submit answer for the right task
    #     res = self.app.post('api/taskrun?external_uid=1xa', data=json.dumps(tr),
    #                         headers=headers)
    #     assert res.status_code == 200, (res.status_code, res.body)

    @with_context
    def test_one_task(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=1)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        rec_task1 = json.loads(res.data)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        rec_task2 = json.loads(res.data)
        assert rec_task1['id'] == task1.id
        assert rec_task2['id'] == rec_task1['id']

    @with_context
    def test_lock_expiration(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task1 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        # fake expired user lock
        acquire_lock(task1.id, 1000, 2, -10)

        res = self.app.get('api/project/{}/newtask?api_key={}'
                           .format(project.id, owner.api_key))
        rec_task1 = json.loads(res.data)

        assert rec_task1['info'] == 'task 1', rec_task1

    @with_context
    def test_invalid_offset(self):
        owner = UserFactory.create(id=500)

        project = ProjectFactory.create(owner=owner)
        project.info['sched'] = Schedulers.locked
        project_repo.save(project)

        task1 = TaskFactory.create(project=project, info='task 1', n_answers=2)
        task1 = TaskFactory.create(project=project, info='task 2', n_answers=2)

        res = self.app.get('api/project/{}/newtask?api_key={}&offset=3'
                           .format(project.id, owner.api_key))

        assert res.status_code == 400, res.data
