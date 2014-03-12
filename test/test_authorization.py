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

from base import web, model, Fixtures, db
from pybossa.auth import taskrun as taskrun_authorization
from pybossa.model import User, TaskRun, Task, App
from nose.tools import assert_equal, assert_raises
from werkzeug.exceptions import Forbidden


class FakeCurrentUser:
    def __init__(self, user=None):
        if user:
            self.id = user.id
            self.admin = user.admin
        self.anonymous = user is None

    def is_anonymous(self):
        return self.anonymous



def setup_module():
    model.rebuild_db()


def teardown_module():
    db.session.remove()
    model.rebuild_db()

class TestTaskrunCreateAuthorization:

    def setUp(self):
        model.rebuild_db()
        self.root, self.user1, self.user2 = Fixtures.create_users()

    def tearDown(self):
        db.session.remove()


    def test_anonymous_user_create_first_taskrun(self):
        """Test anonymous user can create a taskrun for a given task if it
        is the first taskrun posted to that particular task"""
        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser()

        taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        assert taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.create(taskrun)


    def test_anonymous_user_create_repeated_taskrun(self):
        """Test anonymous user cannot create a taskrun for a task to which 
        he has previously posted a taskrun"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser()

        taskrun1 = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        db.session.add(taskrun1)
        db.session.commit()
        taskrun2 = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="a different taskrun info")
        assert taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.create, taskrun2)

        # But the user can still create taskruns for different tasks
        task2 = model.Task(app_id=app.id, state='0', n_answers=10)
        task2.app = app
        db.session.add(task2)
        db.session.commit()
        taskrun3 = model.TaskRun(app_id=app.id,
                                task_id=task2.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        assert taskrun_authorization.create(taskrun3)


    def test_authenticated_user_create_first_taskrun(self):
        """Test authenticated user can create a taskrun for a given task if it
        is the first taskrun posted to that particular task"""
        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="some taskrun info")
        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.create(taskrun)


    def test_authenticated_user_create_repeated_taskrun(self):
        """Test authenticated user cannot create a taskrun for a task to which 
        he has previously posted a taskrun"""
        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        taskrun1 = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="some taskrun info")
        db.session.add(taskrun1)
        db.session.commit()
        taskrun2 = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="a different taskrun info")
        assert not taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.create, taskrun2)

        # But the user can still create taskruns for different tasks
        task2 = model.Task(app_id=app.id, state='0', n_answers=10)
        task2.app = app
        db.session.add(task2)
        db.session.commit()
        taskrun3 = model.TaskRun(app_id=app.id,
                                task_id=task2.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="some taskrun info")
        assert taskrun_authorization.create(taskrun3)


    def test_anonymous_user_read(self):
        """Test anonymous user can read any taskrun"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser()
        anonymous_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        user_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=self.root.id,
                                info="another taskrun info")
        assert taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.read(anonymous_taskrun)
        assert taskrun_authorization.read(user_taskrun)


    def test_authenticated_user_read(self):
        """Test authenticated user can read any taskrun"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        anonymous_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        other_users_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=self.root.id,
                                info="a different taskrun info")
        own_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="another taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.read(anonymous_taskrun)
        assert taskrun_authorization.read(other_users_taskrun)
        assert taskrun_authorization.read(own_taskrun)


    def test_anonymous_user_update_anoymous_taskrun(self):
        """Test anonymous users cannot update an anonymously posted taskrun"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser()

        anonymous_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.update, anonymous_taskrun)


    def test_authenticated_user_update_anonymous_taskrun(self):
        """Test authenticated users cannot update an anonymously posted taskrun"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        anonymous_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.update, anonymous_taskrun)


    def test_admin_update_anonymous_taskrun(self):
        """Test admins cannot update anonymously posted taskruns"""

        app = Fixtures.create_app('')
        app.owner = self.user1
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        self.root.admin = True
        taskrun_authorization.current_user = FakeCurrentUser(self.root)

        anonymous_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert taskrun_authorization.current_user.admin
        assert_raises(Forbidden, taskrun_authorization.update, anonymous_taskrun)


    def test_anonymous_user_update_user_taskrun(self):
        """Test anonymous user cannot update taskruns posted by authenticated users"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser()

        user_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user_id=self.root.id,
                                info="some taskrun info")

        assert taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.update, user_taskrun)


    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot update a taskrun if it was created
        by another authenticated user, but can update its own taskruns"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        user_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user=self.user1,
                                info="some taskrun info")
        other_users_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user=self.root,
                                info="a different taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.update(user_taskrun)
        assert not taskrun_authorization.update(other_users_taskrun)


    def test_admin_update_user_taskrun(self):
        """Test admins can update taskruns posted by authenticated users"""

        app = Fixtures.create_app('')
        app.owner = self.root
        db.session.add(app)
        db.session.commit()
        task = model.Task(app_id=app.id, state='0', n_answers=10)
        task.app = app
        db.session.add(task)
        db.session.commit()
        self.root.admin = True
        taskrun_authorization.current_user = FakeCurrentUser(self.root)

        user_taskrun = model.TaskRun(app_id=app.id,
                                task_id=task.id,
                                user=self.user1,
                                info="some taskrun info")

        assert taskrun_authorization.current_user.admin
        assert taskrun_authorization.update(user_taskrun)





