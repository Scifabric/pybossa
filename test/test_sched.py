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

import json
import random

from mock import patch

from helper import sched
from default import Test, db, with_context
from pybossa.model.task import Task
from pybossa.model.project import Project
from pybossa.model.user import User
from pybossa.model.task_run import TaskRun
from pybossa.model.category import Category
from pybossa.core import task_repo, project_repo
from factories import TaskFactory, ProjectFactory, TaskRunFactory, UserFactory
from factories import AnonymousTaskRunFactory, ExternalUidTaskRunFactory
from factories import reset_all_pk_sequences
import pybossa


class TestSched(sched.Helper):
    def setUp(self):
        super(TestSched, self).setUp()
        self.endpoints = ['project', 'task', 'taskrun']
        with self.flask_app.app_context():
            db.create_all()
            self.redis_flushall()


    def tearDown(self):
        with self.flask_app.app_context():
            db.drop_all()
            self.redis_flushall()
            #reset_all_pk_sequences()


    def get_headers_jwt(self, project):
        """Return headesr JWT token."""
        # Get JWT token
        url = 'api/auth/project/%s/token' % project.short_name

        res = self.app.get(url, headers={'Authorization': project.secret_key})

        authorization_token = 'Bearer %s' % res.data

        return {'Authorization': authorization_token}

    # Tests
    @with_context
    def test_anonymous_01_newtask(self):
        """ Test SCHED newtask returns a Task for the Anonymous User"""
        project = ProjectFactory.create()
        TaskFactory.create_batch(2, project=project, info='hola')

        res = self.app.get('api/project/%s/newtask' %project.id)
        data = json.loads(res.data)
        task_id = data['id']
        assert data['info'] == 'hola', data

        taskrun = dict(project_id=data['project_id'], task_id=data['id'], info="hola")
        res = self.app.post('api/taskrun', data=json.dumps(taskrun))

        res = self.app.get('api/project/%s/newtask' %project.id)
        data = json.loads(res.data)
        assert data['info'] == 'hola', data
        assert data['id'] != task_id, data

    @with_context
    def test_anonymous_01_newtask_limits(self):
        """ Test SCHED newtask returns a list of Tasks for the Anonymous User"""
        project = ProjectFactory.create()
        TaskFactory.create_batch(100, project=project, info='hola')

        url = 'api/project/%s/newtask?limit=100' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 100
        for t in data:
            assert t['info'] == 'hola', t
        task_ids = [task['id'] for task in data]
        task_ids = set(task_ids)
        assert len(task_ids) == 100, task_ids

        url = 'api/project/%s/newtask?limit=200' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 100
        for t in data:
            assert t['info'] == 'hola', t
        task_ids = [task['id'] for task in data]
        task_ids = set(task_ids)
        assert len(task_ids) == 100, task_ids


    @with_context
    def test_anonymous_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks for the Anonymous User"""
        assigned_tasks = []
        # Get a Task until scheduler returns None
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(3, project=project, info={})
        res = self.app.get('api/project/%s/newtask' % project.id)
        data = json.loads(res.data)
        while data.get('info') is not None:
            # Save the assigned task
            assigned_tasks.append(data)

            task = db.session.query(Task).get(data['id'])
            # Submit an Answer for the assigned task
            tr = AnonymousTaskRunFactory.create(project=project, task=task)
            res = self.app.get('api/project/%s/newtask' %project.id)
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        assert len(assigned_tasks) == len(tasks), len(assigned_tasks)
        # Check if all the assigned Task.id are equal to the available ones
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg

    @with_context
    def test_anonymous_02_gets_different_tasks_limits(self):
        """ Test SCHED newtask returns N different list of Tasks for the Anonymous User"""
        assigned_tasks = []
        # Get a Task until scheduler returns None
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(10, project=project, info={})
        res = self.app.get('api/project/%s/newtask?limit=5' % project.id)
        data = json.loads(res.data)
        while len(data) > 0:
            # Save the assigned task
            for t in data:
                assigned_tasks.append(t)
                task = db.session.query(Task).get(t['id'])
                # Submit an Answer for the assigned task
                tr = AnonymousTaskRunFactory.create(project=project, task=task)
                res = self.app.get('api/project/%s/newtask?limit=5' % project.id)
                data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        assert len(assigned_tasks) == len(tasks), len(assigned_tasks)
        # Check if all the assigned Task.id are equal to the available ones
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg

    @with_context
    def test_external_uid_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks
        for a external User ID."""
        assigned_tasks = []
        # Get a Task until scheduler returns None
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(3, project=project, info={})

        headers = self.get_headers_jwt(project)

        url = 'api/project/%s/newtask?external_uid=%s' % (project.id, '1xa')

        res = self.app.get(url, headers=headers)
        data = json.loads(res.data)
        while data.get('info') is not None:
            # Save the assigned task
            assigned_tasks.append(data)

            task = db.session.query(Task).get(data['id'])
            # Submit an Answer for the assigned task
            tr = ExternalUidTaskRunFactory.create(project=project, task=task)
            res = self.app.get(url, headers=headers)
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        assert len(assigned_tasks) == len(tasks), len(assigned_tasks)
        # Check if all the assigned Task.id are equal to the available ones
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg
        # Check that there are task runs saved with the external UID
        answers = task_repo.filter_task_runs_by(external_uid='1xa')
        print(answers)
        err_msg = "There should be the same amount of task_runs than tasks"
        assert len(answers) == len(assigned_tasks), err_msg
        assigned_tasks_ids = sorted([at['id'] for at in assigned_tasks])
        task_run_ids = sorted([a.task_id for a in answers])
        err_msg = "There should be an answer for each assigned task"
        assert assigned_tasks_ids == task_run_ids, err_msg

    @with_context
    def test_external_uid_02_gets_different_tasks_limits(self):
        """ Test SCHED newtask returns N different list of Tasks
        for a external User ID."""
        assigned_tasks = []
        # Get a Task until scheduler returns None
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(10, project=project, info={})

        headers = self.get_headers_jwt(project)

        url = 'api/project/%s/newtask?limit=5&external_uid=%s' % (project.id, '1xa')

        res = self.app.get(url, headers=headers)
        data = json.loads(res.data)
        while len(data) > 0 :
            # Save the assigned task
            for t in data:
                assigned_tasks.append(t)
                task = db.session.query(Task).get(t['id'])
                # Submit an Answer for the assigned task
                tr = ExternalUidTaskRunFactory.create(project=project, task=task)
                res = self.app.get(url, headers=headers)
                data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        assert len(assigned_tasks) == len(tasks), len(assigned_tasks)
        # Check if all the assigned Task.id are equal to the available ones
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg
        # Check that there are task runs saved with the external UID
        answers = task_repo.filter_task_runs_by(external_uid='1xa')
        print answers
        err_msg = "There should be the same amount of task_runs than tasks"
        assert len(answers) == len(assigned_tasks), err_msg
        assigned_tasks_ids = sorted([at['id'] for at in assigned_tasks])
        task_run_ids = sorted([a.task_id for a in answers])
        err_msg = "There should be an answer for each assigned task"
        assert assigned_tasks_ids == task_run_ids, err_msg


    @with_context
    def test_anonymous_03_respects_limit_tasks(self):
        """ Test SCHED newtask respects the limit of 30 TaskRuns per Task"""
        assigned_tasks = []
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(1, project=project, n_answers=10)

        # Get Task until scheduler returns None
        for i in range(10):
            res = self.app.get('api/project/%s/newtask' % project.id)
            data = json.loads(res.data)

            while data.get('id') is not None:
                # Check that we received a Task
                assert data.get('id'), data

                # Save the assigned task
                assigned_tasks.append(data)

                # Submit an Answer for the assigned task
                tr = TaskRun(project_id=data['project_id'], task_id=data['id'],
                             user_ip="127.0.0." + str(i),
                             info={'answer': 'Yes'})
                db.session.add(tr)
                db.session.commit()
                res = self.app.get('api/project/%s/newtask' % project.id)
                data = json.loads(res.data)

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        for t in tasks:
            assert len(t.task_runs) == 10, len(t.task_runs)
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same IP"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.user_ip, t.task_runs), err_msg

    @with_context
    def test_anonymous_03_respects_limit_tasks_limits(self):
        """ Test SCHED newtask limit respects the limit of 30 TaskRuns per Task using limits"""
        assigned_tasks = []
        # Get Task until scheduler returns None
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project, n_answers=5)
        for i in range(5):
            url = 'api/project/%s/newtask?limit=2' % tasks[0].project_id
            res = self.app.get(url)
            data = json.loads(res.data)

            while len(data) > 0:
                # Check that we received a Task
                for t in data:
                    assert t.get('id'), t
                    # Save the assigned task
                    assigned_tasks.append(t)

                    # Submit an Answer for the assigned task
                    tr = TaskRun(project_id=t['project_id'], task_id=t['id'],
                                 user_ip="127.0.0." + str(i),
                                 info={'answer': 'Yes'})
                    db.session.add(tr)
                    db.session.commit()
                    res = self.app.get(url)
                    data = json.loads(res.data)

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 5, len(t.task_runs)
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same IP"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.user_ip, t.task_runs), err_msg


    @with_context
    def test_external_uid_03_respects_limit_tasks(self):
        """ Test SCHED newtask external uid respects the limit of 30 TaskRuns per Task for
        external user id"""
        assigned_tasks = []
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(1, project=project, n_answers=10)
        # Get Task until scheduler returns None
        url = 'api/project/%s/newtask?external_uid=%s' % (project.id, '1xa')
        headers = self.get_headers_jwt(project)
        for i in range(10):
            res = self.app.get(url, headers=headers)
            data = json.loads(res.data)

            while data.get('id') is not None:
                # Check that we received a Task
                assert data.get('id'),  data

                # Save the assigned task
                assigned_tasks.append(data)

                # Submit an Answer for the assigned task
                tr = TaskRun(project_id=data['project_id'], task_id=data['id'],
                             user_ip="127.0.0.1",
                             external_uid='newUser' + str(i),
                             info={'answer': 'Yes'})
                db.session.add(tr)
                db.session.commit()
                res = self.app.get(url, headers=headers)
                data = json.loads(res.data)

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 10, len(t.task_runs)
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same IP"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.external_uid, t.task_runs), err_msg

    @with_context
    def test_external_uid_03_respects_limit_tasks_limits(self):
        """ Test SCHED newtask external uid limits respects the limit of 30 TaskRuns per list of Tasks for
        external user id"""


        assigned_tasks = []
        # Get Task until scheduler returns None
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project, n_answers=5)
        url = 'api/project/%s/newtask?external_uid=%s&limit=2' % (project.id, '1xa')

        headers = self.get_headers_jwt(project)


        for i in range(5):
            res = self.app.get(url, headers=headers)
            data = json.loads(res.data)
            print data

            while len(data) > 0:
                # Check that we received a Task
                for t in data:
                    assert t.get('id'), t
                    # Save the assigned task
                    assigned_tasks.append(t)

                    # Submit an Answer for the assigned task
                    tr = TaskRun(project_id=t['project_id'], task_id=t['id'],
                                 user_ip="127.0.0.1",
                                 external_uid='newUser' + str(i),
                                 info={'answer': 'Yes'})
                    db.session.add(tr)
                    db.session.commit()
                    res = self.app.get(url, headers=headers)
                    data = json.loads(res.data)
                    print data

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 5, len(t.task_runs)
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same IP"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.external_uid, t.task_runs), err_msg



    @with_context
    def test_user_01_newtask(self):
        """ Test SCHED newtask returns a Task for John Doe User"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(2, project=project, n_answers=2)

        # Register
        self.register()
        self.signin()
        url = 'api/project/%s/newtask' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)
        task_id = data['id']
        assert data['id'], data

        taskrun = dict(project_id=data['project_id'], task_id=data['id'], info="hola")
        res = self.app.post('api/taskrun', data=json.dumps(taskrun))

        res = self.app.get(url)
        data = json.loads(res.data)
        assert data['id'], data
        assert data['id'] != task_id, data
        
        self.signout()

    @with_context
    def test_user_01_newtask_limits(self):
        """ Test SCHED newtask returns a Task for John Doe User with limits"""
        self.register()
        self.signin()
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        tasks = TaskFactory.create_batch(10, project=project, info=dict(foo=1))

        # Register
        url = 'api/project/%s/newtask?limit=2' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 2, data
        for t in data:
            assert t['info']['foo'] == 1, t
        self.signout()

    @with_context
    def test_user_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks for John Doe User"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        # Register
        self.register()
        self.signin()

        assigned_tasks = []
        # Get Task until scheduler returns None
        url = 'api/project/%s/newtask' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)
        while data.get('id') is not None:
            # Check that we received a Task
            assert data.get('id'),  data

            # Save the assigned task
            assigned_tasks.append(data)

            # Submit an Answer for the assigned task
            tr = dict(project_id=data['project_id'], task_id=data['id'],
                      info={'answer': 'No'})
            tr = json.dumps(tr)

            self.app.post('/api/taskrun', data=tr)
            res = self.app.get(url)
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        assert len(assigned_tasks) == len(tasks), assigned_tasks
        # Check if all the assigned Task.id are equal to the available ones
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg

    @with_context
    def test_user_02_gets_different_tasks_limit(self):
        """ Test SCHED newtask returns N different list of Tasks for John Doe User"""
        # Register
        self.register()
        self.signin()

        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        assigned_tasks = []
        # Get Task until scheduler returns None
        url = 'api/project/%s/newtask?limit=5' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)
        while len(data) > 0: 
            # Check that we received a Task
            for t in data:
                assert t.get('id'), t

                # Save the assigned task
                assigned_tasks.append(t)

                # Submit an Answer for the assigned task
                tr = dict(project_id=t['project_id'], task_id=t['id'],
                          info={'answer': 'No'})
                tr = json.dumps(tr)

                self.app.post('/api/taskrun', data=tr)
                res = self.app.get(url)
                data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        assert len(assigned_tasks) == len(tasks), assigned_tasks
        # Check if all the assigned Task.id are equal to the available ones
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg


    @with_context
    def test_user_03_respects_limit_tasks(self):
        """ Test SCHED newtask respects the limit of 30 TaskRuns per Task"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(1, project=project, n_answers=10)

        url = 'api/project/%s/newtask' % project.id
        assigned_tasks = []
        # We need one extra loop to allow the scheduler to mark a task as completed
        for i in range(11):
            self.register(fullname="John Doe" + str(i),
                          name="johndoe" + str(i),
                          password="1234" + str(i))
            self.signin()
            # Get Task until scheduler returns None
            res = self.app.get(url)
            data = json.loads(res.data)

            # Check that we received a Task
            if data.get('id'):
                assert data.get('id'),  data

                # Save the assigned task
                assigned_tasks.append(data)

                # Submit an Answer for the assigned task
                tr = dict(project_id=data['project_id'], task_id=data['id'],
                          info={'answer': 'No'})
                tr = json.dumps(tr)
                self.app.post('/api/taskrun', data=tr)
                #self.redis_flushall()
                #res = self.app.get(url)
                #data = json.loads(res.data)
            self.signout()

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 10, t.task_runs
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same User"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.user_id, t.task_runs), err_msg
        # Check that task.state is updated to completed
        for t in tasks:
            assert t.state == "completed", t.state


    @with_context
    def test_user_03_respects_limit_tasks_limit(self):
        """ Test SCHED limit arg newtask respects the limit of 30 TaskRuns per list of Tasks"""
        # Del previous TaskRuns
        assigned_tasks = []
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(2, project=project, n_answers=10)
        # We need one extra loop to allow the scheduler to mark a task as completed
        url = 'api/project/%s/newtask?limit=2' % project.id
        for i in range(11):
            self.register(fullname="John Doe" + str(i),
                          name="johndoe" + str(i),
                          password="1234" + str(i))
            self.signin()
            # Get Task until scheduler returns None
            res = self.app.get(url)
            data = json.loads(res.data)
            
            # Check that we received a Task
            for t in data:
                assert t.get('id'),  data

                # Save the assigned task
                assigned_tasks.append(t)

                # Submit an Answer for the assigned task
                tr = dict(project_id=t['project_id'], task_id=t['id'],
                          info={'answer': 'No'})
                tr = json.dumps(tr)
                self.app.post('/api/taskrun', data=tr)
            self.signout()

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 10, t.task_runs
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same User"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.user_id, t.task_runs), err_msg
        # Check that task.state is updated to completed
        for t in tasks:
            assert t.state == "completed", t.state


    @with_context
    def test_task_preloading(self):
        """Test TASK Pre-loading works"""
        # Del previous TaskRuns
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        # Register
        self.register()
        self.signin()

        assigned_tasks = []
        # Get Task until scheduler returns None
        url = 'api/project/%s/newtask' % project.id
        res = self.app.get(url)
        task1 = json.loads(res.data)
        # Check that we received a Task
        assert task1.get('id'),  task1
        # Pre-load the next task for the user
        res = self.app.get(url + '?offset=1')
        task2 = json.loads(res.data)
        # Check that we received a Task
        assert task2.get('id'),  task2
        # Check that both tasks are different
        assert task1.get('id') != task2.get('id'), "Tasks should be different"
        ## Save the assigned task
        assigned_tasks.append(task1)
        assigned_tasks.append(task2)

        # Submit an Answer for the assigned and pre-loaded task
        for t in assigned_tasks:
            tr = dict(project_id=t['project_id'], task_id=t['id'], info={'answer': 'No'})
            tr = json.dumps(tr)

            self.app.post('/api/taskrun', data=tr)
        # Get two tasks again
        res = self.app.get(url)
        task3 = json.loads(res.data)
        # Check that we received a Task
        assert task3.get('id'),  task1
        # Pre-load the next task for the user
        res = self.app.get(url + '?offset=1')
        task4 = json.loads(res.data)
        # Check that we received a Task
        assert task4.get('id'),  task2
        # Check that both tasks are different
        assert task3.get('id') != task4.get('id'), "Tasks should be different"
        assert task1.get('id') != task3.get('id'), "Tasks should be different"
        assert task2.get('id') != task4.get('id'), "Tasks should be different"
        # Check that a big offset returns None
        res = self.app.get(url + '?offset=11')
        assert json.loads(res.data) == {}, res.data

    @with_context
    def test_task_preloading_limit(self):
        """Test TASK Pre-loading with limit works"""
        # Register
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)
        self.register()
        self.signin()

        assigned_tasks = []
        url = 'api/project/%s/newtask?limit=2' % project.id
        res = self.app.get(url)
        tasks1 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks1:
            assert t.get('id'),  t
        # Pre-load the next tasks for the user
        res = self.app.get(url + '&offset=2')
        tasks2 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks2:
            assert t.get('id'),  t
        # Check that both tasks are different
        tasks1_ids = set([t['id'] for t in tasks1])
        tasks2_ids = set([t['id'] for t in tasks2])
        assert len(tasks1_ids.union(tasks2_ids)) == 4, "Tasks should be different"
        ## Save the assigned task
        for t in tasks1:
            assigned_tasks.append(t)
        for t in tasks2:
            assigned_tasks.append(t)

        # Submit an Answer for the assigned and pre-loaded task
        for t in assigned_tasks:
            tr = dict(project_id=t['project_id'], task_id=t['id'], info={'answer': 'No'})
            tr = json.dumps(tr)

            self.app.post('/api/taskrun', data=tr)
        # Get two tasks again
        res = self.app.get(url)
        tasks3 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks3:
            assert t.get('id'),  t
        # Pre-load the next task for the user
        res = self.app.get(url + '&offset=2')
        tasks4 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks4:
            assert t.get('id'),  t
        # Check that both tasks are different
        tasks3_ids = set([t['id'] for t in tasks3])
        tasks4_ids = set([t['id'] for t in tasks4])
        assert len(tasks3_ids.union(tasks4_ids)) == 4, "Tasks should be different"

        # Check that a big offset returns None
        res = self.app.get(url + '&offset=11')
        assert json.loads(res.data) == {}, res.data


    @with_context
    def test_task_preloading_external_uid(self):
        """Test TASK Pre-loading for external user IDs works"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        assigned_tasks = []
        # Get Task until scheduler returns None
        project = project_repo.get(1)
        headers = self.get_headers_jwt(project)
        url = 'api/project/%s/newtask?external_uid=2xb' % project.id
        res = self.app.get(url, headers=headers)
        task1 = json.loads(res.data)
        # Check that we received a Task
        assert task1.get('id'),  task1
        # Pre-load the next task for the user
        res = self.app.get(url + '&offset=1', headers=headers)
        task2 = json.loads(res.data)
        # Check that we received a Task
        assert task2.get('id'),  task2
        # Check that both tasks are different
        assert task1.get('id') != task2.get('id'), "Tasks should be different"
        ## Save the assigned task
        assigned_tasks.append(task1)
        assigned_tasks.append(task2)

        # Submit an Answer for the assigned and pre-loaded task
        for t in assigned_tasks:
            tr = dict(project_id=t['project_id'],
                      task_id=t['id'], info={'answer': 'No'},
                      external_uid='2xb')
            tr = json.dumps(tr)

            res = self.app.post('/api/taskrun', data=tr, headers=headers)
        # Get two tasks again
        res = self.app.get(url, headers=headers)
        task3 = json.loads(res.data)
        # Check that we received a Task
        assert task3.get('id'),  task1
        # Pre-load the next task for the user
        res = self.app.get(url + '&offset=1', headers=headers)
        task4 = json.loads(res.data)
        # Check that we received a Task
        assert task4.get('id'),  task2
        # Check that both tasks are different
        assert task3.get('id') != task4.get('id'), "Tasks should be different"
        assert task1.get('id') != task3.get('id'), "Tasks should be different"
        assert task2.get('id') != task4.get('id'), "Tasks should be different"
        # Check that a big offset returns None
        res = self.app.get(url + '&offset=11', headers=headers)
        assert json.loads(res.data) == {}, res.data

    @with_context
    def test_task_preloading_external_uid_limit(self):
        """Test TASK Pre-loading for external user IDs works with limit"""
        # Del previous TaskRuns
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        assigned_tasks = []
        # Get Task until scheduler returns None
        headers = self.get_headers_jwt(project)
        url = 'api/project/%s/newtask?external_uid=2xb&limit=2' % project.id
        res = self.app.get(url, headers=headers)
        tasks1 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks1:
            assert t.get('id'),  task1
        # Pre-load the next task for the user
        res = self.app.get(url + '&offset=2', headers=headers)
        tasks2 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks2:
            assert t.get('id'),  t
        # Check that both tasks are different
        tasks1_ids = set([task['id'] for task in tasks1])
        tasks2_ids = set([task['id'] for task in tasks2])
        assert len(tasks1_ids.union(tasks2_ids)) == 4, "Tasks should be different"
        ## Save the assigned task
        for t in tasks1:
            assigned_tasks.append(t)
        for t in tasks2:
            assigned_tasks.append(t)

        # Submit an Answer for the assigned and pre-loaded task
        for t in assigned_tasks:
            tr = dict(project_id=t['project_id'],
                      task_id=t['id'], info={'answer': 'No'},
                      external_uid='2xb')
            tr = json.dumps(tr)

            res = self.app.post('/api/taskrun', data=tr, headers=headers)
        # Get two tasks again
        res = self.app.get(url, headers=headers)
        tasks3 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks3:
            assert t.get('id'),  t
        # Pre-load the next task for the user
        res = self.app.get(url + '&offset=2', headers=headers)
        tasks4 = json.loads(res.data)
        # Check that we received a Task
        for t in tasks4:
            assert t.get('id'),  t
        # Check that both tasks are different
        tasks3_ids = set([task['id'] for task in tasks3])
        tasks4_ids = set([task['id'] for task in tasks4])
        assert len(tasks3_ids.union(tasks4_ids)) == 4, "Tasks should be different"
        # Check that a big offset returns None
        res = self.app.get(url + '&offset=11', headers=headers)
        assert json.loads(res.data) == {}, res.data


    @with_context
    def test_task_priority(self):
        """Test SCHED respects priority_0 field"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        # Register
        self.register()
        self.signin()

        # By default, tasks without priority should be ordered by task.id (FIFO)
        tasks = db.session.query(Task).filter_by(project_id=1).order_by('id').all()
        url = 'api/project/%s/newtask' % project.id
        res = self.app.get(url)
        task1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert task1.get('id') == tasks[0].id, err_msg

        # Now let's change the priority to a random task
        import random
        t = random.choice(tasks)
        # Increase priority to maximum
        t.priority_0 = 1
        db.session.add(t)
        db.session.commit()
        # Request again a new task
        res = self.app.get(url + '?orderby=priority_0&desc=true')
        task1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert task1.get('id') == t.id, err_msg
        err_msg = "Task.priority_0 should be the 1"
        assert task1.get('priority_0') == 1, err_msg

    @with_context
    def test_task_priority_limit(self):
        """Test SCHED respects priority_0 field with limit"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        # Register
        self.register()
        self.signin()

        # By default, tasks without priority should be ordered by task.id (FIFO)
        tasks = db.session.query(Task).filter_by(project_id=project.id).order_by('id').all()
        url = 'api/project/%s/newtask?limit=2' % project.id
        res = self.app.get(url)
        tasks1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert tasks1[0].get('id') == tasks[0].id, err_msg

        # Now let's change the priority to a random task
        import random
        t = random.choice(tasks)
        # Increase priority to maximum
        t.priority_0 = 1
        db.session.add(t)
        db.session.commit()
        # Request again a new task
        res = self.app.get(url + '&orderby=priority_0&desc=true')
        tasks1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert tasks1[0].get('id') == t.id, (err_msg, tasks1[0])
        err_msg = "Task.priority_0 should be the 1"
        assert tasks1[0].get('priority_0') == 1, err_msg


    @with_context
    def test_task_priority_external_uid(self):
        """Test SCHED respects priority_0 field for externa uid"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        # By default, tasks without priority should be ordered by task.id (FIFO)
        tasks = db.session.query(Task).filter_by(project_id=1).order_by('id').all()
        project = project_repo.get(1)
        headers = self.get_headers_jwt(project)
        url = 'api/project/%s/newtask?external_uid=342' % project.id
        res = self.app.get(url, headers=headers)
        task1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert task1.get('id') == tasks[0].id, err_msg

        # Now let's change the priority to a random task
        import random
        t = random.choice(tasks)
        # Increase priority to maximum
        t.priority_0 = 1
        db.session.add(t)
        db.session.commit()
        # Request again a new task
        res = self.app.get(url + '&orderby=priority_0&desc=true', headers=headers)
        task1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert task1.get('id') == t.id, (err_msg, task1, t)
        err_msg = "Task.priority_0 should be the 1"
        assert task1.get('priority_0') == 1, err_msg

    @with_context
    def test_task_priority_external_uid_limit(self):
        """Test SCHED respects priority_0 field for externa uid with limit"""
        project = ProjectFactory.create(owner=UserFactory.create(id=500))
        TaskFactory.create_batch(10, project=project)

        # By default, tasks without priority should be ordered by task.id (FIFO)
        tasks = db.session.query(Task).filter_by(project_id=project.id).order_by('id').all()
        headers = self.get_headers_jwt(project)
        url = 'api/project/%s/newtask?external_uid=342&limit=2' % project.id
        res = self.app.get(url, headers=headers)
        tasks1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert tasks1[0].get('id') == tasks[0].id, err_msg

        # Now let's change the priority to a random task
        import random
        t = random.choice(tasks)
        # Increase priority to maximum
        t.priority_0 = 1
        db.session.add(t)
        db.session.commit()
        # Request again a new task
        res = self.app.get(url + '&orderby=priority_0&desc=true', headers=headers)
        tasks1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert tasks1[0].get('id') == t.id, err_msg
        err_msg = "Task.priority_0 should be the 1"
        assert tasks1[0].get('priority_0') == 1, err_msg


    def _add_task_run(self, app, task, user=None):
        tr = AnonymousTaskRunFactory.create(project=app, task=task)

    @with_context
    def test_no_more_tasks(self):
        """Test that a users gets always tasks"""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner, short_name='egil', name='egil',
                  description='egil')

        project_id = project.id

        tasks = TaskFactory.create_batch(20, project=project, n_answers=10)

        for t in tasks[0:10]:
            TaskRunFactory.create_batch(10, task=t, project=project)

        tasks = db.session.query(Task).filter_by(project_id=project.id, state='ongoing').all()
        assert tasks[0].n_answers == 10

        url = 'api/project/%s/newtask' % project.id
        res = self.app.get(url)
        data = json.loads(res.data)

        err_msg = "User should get a task"
        assert 'project_id' in data.keys(), err_msg
        assert data['project_id'] == project_id, err_msg
        assert data['id'] == tasks[0].id, err_msg

    @with_context
    def test_no_more_tasks_limit(self):
        """Test that a users gets always tasks with limit"""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner, short_name='egil', name='egil',
                  description='egil')

        project_id = project.id

        tasks = TaskFactory.create_batch(20, project=project, n_answers=10)

        for t in tasks[0:10]:
            TaskRunFactory.create_batch(10, task=t, project=project)

        tasks = db.session.query(Task).filter_by(project_id=project.id, state='ongoing').all()
        assert tasks[0].n_answers == 10

        url = 'api/project/%s/newtask?limit=2&orderby=id' % project_id
        res = self.app.get(url)
        data = json.loads(res.data)

        err_msg = "User should get a task"
        i = 0
        for t in data:
            print t['id']
            assert 'project_id' in t.keys(), err_msg
            assert t['project_id'] == project_id, err_msg
            assert t['id'] == tasks[i].id, (err_msg, t, tasks[i].id)
            i += 1


class TestGetBreadthFirst(Test):
    def setUp(self):
        super(TestGetBreadthFirst, self).setUp()
        with self.flask_app.app_context():
            self.create()


    def del_task_runs(self, project_id=1):
        """Deletes all TaskRuns for a given project_id"""
        db.session.query(TaskRun).filter_by(project_id=1).delete()
        db.session.commit()
        db.session.remove()

    @with_context
    def test_get_default_task_anonymous(self):
        self._test_get_breadth_first_task()

    @with_context
    def test_get_breadth_first_task_user(self):
        user = self.create_users()[0]
        self._test_get_breadth_first_task(user=user)

    @with_context
    def test_get_breadth_first_task_external_user(self):
        self._test_get_breadth_first_task(external_uid='234')


    @with_context
    def test_get_default_task_anonymous_limit(self):
        self._test_get_breadth_first_task_limit()

    @with_context
    def test_get_breadth_first_task_user_limit(self):
        user = self.create_users()[0]
        self._test_get_breadth_first_task_limit(user=user)

    @with_context
    def test_get_breadth_first_task_external_user_limit(self):
        self._test_get_breadth_first_task_limit(external_uid='234')


    def _test_get_breadth_first_task(self, user=None, external_uid=None):
        self.del_task_runs()
        if user:
            short_name = 'xyzuser'
        else:
            short_name = 'xyznouser'

        category = db.session.query(Category).get(1)
        project = Project(short_name=short_name, name=short_name,
              description=short_name, category=category)
        owner = db.session.query(User).get(1)

        project.owner = owner
        task = Task(project=project, state='0', info={})
        task2 = Task(project=project, state='0', info={})
        task.project = project
        task2.project = project
        db.session.add(project)
        db.session.add(task)
        db.session.add(task2)
        db.session.commit()
        taskid = task.id
        projectid = project.id
        # give task2 a bunch of runs
        for idx in range(2):
            self._add_task_run(project, task2)

        # now check we get task without task runs as anonymous user
        out = pybossa.sched.get_breadth_first_task(projectid)
        assert len(out) == 1, out
        out = out[0]
        assert out.id == taskid, out

        # now check we get task without task runs as a user
        owner = db.session.query(User).get(1)
        out = pybossa.sched.get_breadth_first_task(projectid, owner.id)
        assert len(out) == 1, out
        out = out[0]
        assert out.id == taskid, out

        # now check we get task without task runs as a external uid
        out = pybossa.sched.get_breadth_first_task(projectid,
                                                   external_uid=external_uid)
        assert len(out) == 1, out
        out = out[0]
        assert out.id == taskid, out


        # now check that offset works
        out1 = pybossa.sched.get_breadth_first_task(projectid)
        out2 = pybossa.sched.get_breadth_first_task(projectid, offset=1)
        assert len(out1) == 1, out1
        assert len(out2) == 1, out2
        assert out1[0].id != out2[0].id, (out1, out2)

        # asking for a bigger offset (max 10)
        out2 = pybossa.sched.get_breadth_first_task(projectid, offset=11)
        assert out2 == [], out2

        self._add_task_run(project, task)
        out = pybossa.sched.get_breadth_first_task(projectid)
        assert len(out) == 1, out
        out = out[0]
        assert out.id == taskid, out

        # now add 2 more taskruns. We now have 3 and 2 task runs per task
        self._add_task_run(project, task)
        self._add_task_run(project, task)
        out = pybossa.sched.get_breadth_first_task(projectid)
        assert len(out) == 1, out
        out = out[0]
        assert out.id == task2.id, out

    def _test_get_breadth_first_task_limit(self, user=None, external_uid=None):
        self.del_task_runs()
        if user:
            short_name = 'xyzuser'
        else:
            short_name = 'xyznouser'

        category = db.session.query(Category).get(1)
        project = Project(short_name=short_name, name=short_name,
              description=short_name, category=category)
        owner = db.session.query(User).get(1)

        project.owner = owner
        task = Task(project=project, state='0', info={})
        task2 = Task(project=project, state='0', info={})
        task3 = Task(project=project, state='0', info={})
        task.project = project
        task2.project = project
        task3.project = project
        db.session.add(project)
        db.session.add(task)
        db.session.add(task2)
        db.session.add(task3)
        db.session.commit()
        taskid = task.id
        projectid = project.id
        # give task2 a bunch of runs
        for idx in range(2):
            self._add_task_run(project, task2)

        # now check we get task without task runs as anonymous user
        out = pybossa.sched.get_breadth_first_task(projectid, limit=2)
        assert len(out) == 2, out
        out = out[0]
        assert out.id == taskid, out

        # now check we get task without task runs as a user
        owner = db.session.query(User).get(1)
        out = pybossa.sched.get_breadth_first_task(projectid, owner.id, limit=2)
        assert len(out) == 2, out
        out = out[0]
        assert out.id == taskid, out

        # now check we get task without task runs as a external uid
        out = pybossa.sched.get_breadth_first_task(projectid,
                                                   external_uid=external_uid,
                                                   limit=2)
        assert len(out) == 2, out
        out = out[0]
        assert out.id == taskid, out


        # now check that offset works
        out1 = pybossa.sched.get_breadth_first_task(projectid, limit=2)
        out2 = pybossa.sched.get_breadth_first_task(projectid, offset=1, limit=2)
        assert len(out1) == 2, out1
        assert len(out2) == 2, out2
        assert out1[0].id != out2[0].id, (out1, out2)

        # asking for a bigger offset (max 10)
        out2 = pybossa.sched.get_breadth_first_task(projectid, offset=11, limit=2)
        assert out2 == [], out2

        self._add_task_run(project, task)
        out = pybossa.sched.get_breadth_first_task(projectid, limit=2)
        assert len(out) == 2, out
        out = out[0]
        assert out.id == taskid, out

        # now add 2 more taskruns. We now have 3 and 2 task runs per task
        self._add_task_run(project, task)
        self._add_task_run(project, task)
        out = pybossa.sched.get_breadth_first_task(projectid, limit=2)
        assert len(out) == 2, out
        out = out[0]
        assert out.id == task2.id, out


    def _add_task_run(self, project, task, user=None):
        tr = TaskRun(project=project, task=task, user=user)
        db.session.add(tr)
        db.session.commit()
