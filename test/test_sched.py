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

import json
import random

from helper import sched
from base import model, Fixtures, db, redis_flushall
import pybossa


class TestSched(sched.Helper):
    def setUp(self):
        super(TestSched, self).setUp()
        model.rebuild_db()
        Fixtures.create()
        self.endpoints = ['app', 'task', 'taskrun']

    def tearDown(self):
        db.session.remove()
        redis_flushall()


    # Tests
    def test_anonymous_01_newtask(self):
        """ Test SCHED newtask returns a Task for the Anonymous User"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        assert data['info'], data

    def test_anonymous_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks for the Anonymous User"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        assigned_tasks = []
        # Get a Task until scheduler returns None
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        while data.get('info') is not None:
            # Check that we have received a Task
            assert data.get('info'),  data

            # Save the assigned task
            assigned_tasks.append(data)

            # Submit an Answer for the assigned task
            tr = model.task_run.TaskRun(app_id=data['app_id'], task_id=data['id'],
                               user_ip="127.0.0.1",
                               info={'answer': 'Yes'})
            db.session.add(tr)
            db.session.commit()
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
        assert len(assigned_tasks) == len(tasks), len(assigned_tasks)
        # Check if all the assigned Task.id are equal to the available ones
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg

    def test_anonymous_03_respects_limit_tasks(self):
        """ Test SCHED newtask respects the limit of 30 TaskRuns per Task"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        assigned_tasks = []
        # Get Task until scheduler returns None
        for i in range(10):
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

            while data.get('info') is not None:
                # Check that we received a Task
                assert data.get('info'),  data

                # Save the assigned task
                assigned_tasks.append(data)

                # Submit an Answer for the assigned task
                tr = model.task_run.TaskRun(app_id=data['app_id'], task_id=data['id'],
                                   user_ip="127.0.0." + str(i),
                                   info={'answer': 'Yes'})
                db.session.add(tr)
                db.session.commit()
                res = self.app.get('api/app/1/newtask')
                data = json.loads(res.data)

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 10, len(t.task_runs)
        # Check that all the answers are from different IPs
        err_msg = "There are two or more Answers from same IP"
        for t in tasks:
            for tr in t.task_runs:
                assert self.is_unique(tr.user_ip, t.task_runs), err_msg

    def test_user_01_newtask(self):
        """ Test SCHED newtask returns a Task for John Doe User"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register()
        self.signin()
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        assert data['info'], data
        self.signout()

    def test_user_02_gets_different_tasks(self):
        """ Test SCHED newtask returns N different Tasks for John Doe User"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register()
        self.signin()

        assigned_tasks = []
        # Get Task until scheduler returns None
        res = self.app.get('api/app/1/newtask')
        data = json.loads(res.data)
        while data.get('info') is not None:
            # Check that we received a Task
            assert data.get('info'),  data

            # Save the assigned task
            assigned_tasks.append(data)

            # Submit an Answer for the assigned task
            tr = dict(app_id=data['app_id'], task_id=data['id'],
                      info={'answer': 'No'})
            tr = json.dumps(tr)

            self.app.post('/api/taskrun', data=tr)
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

        # Check if we received the same number of tasks that the available ones
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
        assert len(assigned_tasks) == len(tasks), assigned_tasks
        # Check if all the assigned Task.id are equal to the available ones
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
        err_msg = "Assigned Task not found in DB Tasks"
        for at in assigned_tasks:
            assert self.is_task(at['id'], tasks), err_msg
        # Check that there are no duplicated tasks
        err_msg = "One Assigned Task is duplicated"
        for at in assigned_tasks:
            assert self.is_unique(at['id'], assigned_tasks), err_msg

    def test_user_03_respects_limit_tasks(self):
        """ Test SCHED newtask respects the limit of 30 TaskRuns per Task"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        assigned_tasks = []
        # We need one extra loop to allow the scheduler to mark a task as completed
        for i in range(11):
            self.register(fullname=self.user.username + str(i),
                          username=self.user.username + str(i),
                          password=self.user.username + str(i))
            self.signin()
            # Get Task until scheduler returns None
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

            while data.get('info') is not None:
                # Check that we received a Task
                assert data.get('info'),  data

                # Save the assigned task
                assigned_tasks.append(data)

                # Submit an Answer for the assigned task
                tr = dict(app_id=data['app_id'], task_id=data['id'],
                          info={'answer': 'No'})
                tr = json.dumps(tr)
                self.app.post('/api/taskrun', data=tr)

                res = self.app.get('api/app/1/newtask')
                data = json.loads(res.data)
            self.signout()

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
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

    def test_tasks_for_user_ip_id(self):
        """ Test SCHED newtask to see if sends the same ammount of Task to
            user_id and user_ip
        """
        redis_flushall()
        # Del Fixture Task
        self.del_task_runs()

        assigned_tasks = []
        for i in range(10):
            signin = False
            if random.random >= 0.5:
                signin = True
                self.register(fullname=self.user.username + str(i),
                              username=self.user.username + str(i),
                              password=self.user.username + str(i))

            if signin:
                self.signin()
            # Get Task until scheduler returns None
            res = self.app.get('api/app/1/newtask')
            data = json.loads(res.data)

            while data.get('info') is not None:
                # Check that we received a Task
                assert data.get('info'),  data

                # Save the assigned task
                assigned_tasks.append(data)

                # Submit an Answer for the assigned task
                if signin:
                    tr = dict(app_id=data['app_id'], task_id=data['id'],
                              info={'answer': 'No'})
                    tr = json.dumps(tr)
                    self.app.post('/api/taskrun', data=tr)
                else:
                    tr = model.task_run.TaskRun(app_id=data['app_id'], task_id=data['id'],
                                       user_ip="127.0.0." + str(i),
                                       info={'answer': 'Yes'})
                    db.session.add(tr)
                    db.session.commit()

                res = self.app.get('api/app/1/newtask')
                data = json.loads(res.data)
            if signin:
                self.signout()

        # Check if there are 30 TaskRuns per Task
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).all()
        for t in tasks:
            assert len(t.task_runs) == 10, t.task_runs
        # Check that all the answers are from different IPs and IDs
        err_msg1 = "There are two or more Answers from same User ID"
        err_msg2 = "There are two or more Answers from same User IP"
        for t in tasks:
            for tr in t.task_runs:
                if tr.user_id:
                    assert self.is_unique(tr.user_id, t.task_runs), err_msg1
                else:
                    assert self.is_unique(tr.user_ip, t.task_runs), err_msg2

    def test_task_preloading(self):
        """Test TASK Pre-loading works"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register()
        self.signin()

        assigned_tasks = []
        # Get Task until scheduler returns None
        res = self.app.get('api/app/1/newtask')
        task1 = json.loads(res.data)
        # Check that we received a Task
        assert task1.get('info'),  task1
        # Pre-load the next task for the user
        res = self.app.get('api/app/1/newtask?offset=1')
        task2 = json.loads(res.data)
        # Check that we received a Task
        assert task2.get('info'),  task2
        # Check that both tasks are different
        assert task1.get('id') != task2.get('id'), "Tasks should be different"
        ## Save the assigned task
        assigned_tasks.append(task1)
        assigned_tasks.append(task2)

        # Submit an Answer for the assigned and pre-loaded task
        for t in assigned_tasks:
            tr = dict(app_id=t['app_id'], task_id=t['id'], info={'answer': 'No'})
            tr = json.dumps(tr)

            self.app.post('/api/taskrun', data=tr)
        # Get two tasks again
        res = self.app.get('api/app/1/newtask')
        task3 = json.loads(res.data)
        # Check that we received a Task
        assert task3.get('info'),  task1
        # Pre-load the next task for the user
        res = self.app.get('api/app/1/newtask?offset=1')
        task4 = json.loads(res.data)
        # Check that we received a Task
        assert task4.get('info'),  task2
        # Check that both tasks are different
        assert task3.get('id') != task4.get('id'), "Tasks should be different"
        assert task1.get('id') != task3.get('id'), "Tasks should be different"
        assert task2.get('id') != task4.get('id'), "Tasks should be different"
        # Check that a big offset returns None
        res = self.app.get('api/app/1/newtask?offset=11')
        assert json.loads(res.data) == {}, res.data

    def test_task_priority(self):
        """Test SCHED respects priority_0 field"""
        redis_flushall()
        # Del previous TaskRuns
        self.del_task_runs()

        # Register
        self.register()
        self.signin()

        # By default, tasks without priority should be ordered by task.id (FIFO)
        tasks = db.session.query(model.task.Task).filter_by(app_id=1).order_by('id').all()
        res = self.app.get('api/app/1/newtask')
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
        res = self.app.get('api/app/1/newtask')
        task1 = json.loads(res.data)
        # Check that we received a Task
        err_msg = "Task.id should be the same"
        assert task1.get('id') == t.id, err_msg
        err_msg = "Task.priority_0 should be the 1"
        assert task1.get('priority_0') == 1, err_msg

    def _add_task_run(self, app, task, user=None):
        tr = model.task_run.TaskRun(app=app, task=task, user=user)
        db.session.add(tr)
        db.session.commit()

    def test_no_more_tasks(self):
        """Test that a users gets always tasks"""
        app = model.app.App(short_name='egil', name='egil',
                        description='egil')
        owner = db.session.query(model.user.User).get(1)
        app.owner_id = owner.id
        db.session.add(app)
        db.session.commit()

        app_id = app.id

        for i in range(20):
            task = model.task.Task(app=app, info={'i': i}, n_answers=10)
            db.session.add(task)
            db.session.commit()

        tasks = db.session.query(model.task.Task).filter_by(app_id=app.id).limit(11).all()
        for t in tasks[0:10]:
            for x in range(10):
                self._add_task_run(app, t)

        assert tasks[0].n_answers == 10

        url = 'api/app/%s/newtask' % app_id
        res = self.app.get(url)
        data = json.loads(res.data)

        err_msg = "User should get a task"
        assert 'app_id' in data.keys(), err_msg
        assert data['app_id'] == app_id, err_msg
        assert data['id'] == tasks[10].id, err_msg


class TestGetBreadthFirst:
    def setUp(self):
        model.rebuild_db()
        Fixtures.create()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def tearDown(self):
        db.session.remove()
        redis_flushall()

    def del_task_runs(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        db.session.query(model.task_run.TaskRun).filter_by(app_id=1).delete()
        db.session.commit()
        db.session.remove()

    def test_get_default_task_anonymous(self):
        self._test_get_breadth_first_task()

    def test_get_breadth_first_task_user(self):
        user = Fixtures.create_users()[0]
        self._test_get_breadth_first_task(user)

    def test_get_random_task(self):
        self._test_get_random_task()

    def _test_get_random_task(self, user=None):
        task = pybossa.sched.get_random_task(app_id=1)
        assert task is not None, task

        tasks = db.session.query(model.task.Task).all()
        for t in tasks:
            db.session.delete(t)
        db.session.commit()
        task = pybossa.sched.get_random_task(app_id=1)
        assert task is None, task

    def _test_get_breadth_first_task(self, user=None):
        self.del_task_runs()
        if user:
            short_name = 'xyzuser'
        else:
            short_name = 'xyznouser'

        app = model.app.App(short_name=short_name, name=short_name,
                        description=short_name)
        owner = db.session.query(model.user.User).get(1)

        app.owner = owner
        task = model.task.Task(app=app, state='0', info={})
        task2 = model.task.Task(app=app, state='0', info={})
        task.app = app
        task2.app = app
        db.session.add(app)
        db.session.add(task)
        db.session.add(task2)
        db.session.commit()
        taskid = task.id
        appid = app.id
        # give task2 a bunch of runs
        for idx in range(2):
            self._add_task_run(app, task2)

        # now check we get task without task runs as anonymous user
        out = pybossa.sched.get_breadth_first_task(appid)
        assert out.id == taskid, out

        # now check we get task without task runs as a user
        out = pybossa.sched.get_breadth_first_task(appid, owner.id)
        assert out.id == taskid, out


        # now check that offset works
        out1 = pybossa.sched.get_breadth_first_task(appid)
        out2 = pybossa.sched.get_breadth_first_task(appid, offset=1)
        assert out1.id != out2.id, out

        # asking for a bigger offset (max 10)
        out2 = pybossa.sched.get_breadth_first_task(appid, offset=11)
        assert out2 is None, out

        self._add_task_run(app, task)
        out = pybossa.sched.get_breadth_first_task(appid)
        assert out.id == taskid, out

        # now add 2 more taskruns. We now have 3 and 2 task runs per task
        self._add_task_run(app, task)
        self._add_task_run(app, task)
        out = pybossa.sched.get_breadth_first_task(appid)
        assert out.id == task2.id, out

    def _add_task_run(self, app, task, user=None):
        tr = model.task_run.TaskRun(app=app, task=task, user=user)
        db.session.add(tr)
        db.session.commit()
