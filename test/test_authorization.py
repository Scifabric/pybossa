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

from base import web, model, Fixtures, db, redis_flushall
from pybossa.auth import taskrun as taskrun_authorization
from pybossa.auth import token as token_authorization
from pybossa.model import TaskRun, Task
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
    redis_flushall()



class TestTaskrunCreateAuthorization:

    def setUp(self):
        model.rebuild_db()
        self.root, self.user1, self.user2 = Fixtures.create_users()
        self.app = Fixtures.create_app('')
        self.app.owner = self.root
        db.session.add(self.app)
        db.session.commit()
        self.task = model.Task(app_id=self.app.id, state='0', n_answers=10)
        self.task.app = self.app
        db.session.add(self.task)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        redis_flushall()



    def test_anonymous_user_create_first_taskrun(self):
        """Test anonymous user can create a taskrun for a given task if it
        is the first taskrun posted to that particular task"""
        
        taskrun_authorization.current_user = FakeCurrentUser()

        taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        assert taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.create(taskrun)


    def test_anonymous_user_create_repeated_taskrun(self):
        """Test anonymous user cannot create a taskrun for a task to which 
        he has previously posted a taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser()

        taskrun1 = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        db.session.add(taskrun1)
        db.session.commit()
        taskrun2 = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="a different taskrun info")
        assert taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.create, taskrun2)

        # But the user can still create taskruns for different tasks
        task2 = model.Task(app_id=self.app.id, state='0', n_answers=10)
        task2.app = self.app
        db.session.add(task2)
        db.session.commit()
        taskrun3 = model.TaskRun(app_id=self.app.id,
                                task_id=task2.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        assert taskrun_authorization.create(taskrun3)


    def test_authenticated_user_create_first_taskrun(self):
        """Test authenticated user can create a taskrun for a given task if it
        is the first taskrun posted to that particular task"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="some taskrun info")
        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.create(taskrun)


    def test_authenticated_user_create_repeated_taskrun(self):
        """Test authenticated user cannot create a taskrun for a task to which 
        he has previously posted a taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        taskrun1 = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="some taskrun info")
        db.session.add(taskrun1)
        db.session.commit()
        taskrun2 = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="a different taskrun info")
        assert not taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.create, taskrun2)

        # But the user can still create taskruns for different tasks
        task2 = model.Task(app_id=self.app.id, state='0', n_answers=10)
        task2.app = self.app
        db.session.add(task2)
        db.session.commit()
        taskrun3 = model.TaskRun(app_id=self.app.id,
                                task_id=task2.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="some taskrun info")
        assert taskrun_authorization.create(taskrun3)


    def test_anonymous_user_read(self):
        """Test anonymous user can read any taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser()
        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        user_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=self.root.id,
                                info="another taskrun info")
        assert taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.read(anonymous_taskrun)
        assert taskrun_authorization.read(user_taskrun)


    def test_authenticated_user_read(self):
        """Test authenticated user can read any taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")
        other_users_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=self.root.id,
                                info="a different taskrun info")
        own_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=taskrun_authorization.current_user.id,
                                info="another taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.read(anonymous_taskrun)
        assert taskrun_authorization.read(other_users_taskrun)
        assert taskrun_authorization.read(own_taskrun)


    def test_anonymous_user_update_anoymous_taskrun(self):
        """Test anonymous users cannot update an anonymously posted taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser()

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.update, anonymous_taskrun)


    def test_authenticated_user_update_anonymous_taskrun(self):
        """Test authenticated users cannot update an anonymously posted taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.update, anonymous_taskrun)


    def test_admin_update_anonymous_taskrun(self):
        """Test admins cannot update anonymously posted taskruns"""

        self.root.admin = True
        taskrun_authorization.current_user = FakeCurrentUser(self.root)

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert taskrun_authorization.current_user.admin
        assert_raises(Forbidden, taskrun_authorization.update, anonymous_taskrun)


    def test_anonymous_user_update_user_taskrun(self):
        """Test anonymous user cannot update taskruns posted by authenticated users"""

        taskrun_authorization.current_user = FakeCurrentUser()

        user_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=self.root.id,
                                info="some taskrun info")

        assert taskrun_authorization.current_user.is_anonymous()
        assert_raises(Forbidden, taskrun_authorization.update, user_taskrun)


    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot update a taskrun if it was created
        by another authenticated user, but can update his own taskruns"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        user_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user=self.user1,
                                info="some taskrun info")
        own_users_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user=self.root,
                                info="a different taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.update(own_taskrun)
        assert not taskrun_authorization.update(other_users_taskrun)


    def test_admin_update_user_taskrun(self):
        """Test admins can update taskruns posted by authenticated users"""

        self.root.admin = True
        taskrun_authorization.current_user = FakeCurrentUser(self.root)

        user_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user=self.user1,
                                info="some taskrun info")

        assert taskrun_authorization.current_user.admin
        assert taskrun_authorization.update(user_taskrun)


    def test_anonymous_user_delete_anonymous_taskrun(self):
        """Test anonymous users cannot delete an anonymously posted taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser()

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert taskrun_authorization.current_user.is_anonymous()
        assert not taskrun_authorization.delete(anonymous_taskrun)


    def test_authenticated_user_delete_anonymous_taskrun(self):
        """Test authenticated users cannot delete an anonymously posted taskrun"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert not taskrun_authorization.delete(anonymous_taskrun)


    def test_admin_delete_anonymous_taskrun(self):
        """Test admins can delete anonymously posted taskruns"""

        self.root.admin = True
        taskrun_authorization.current_user = FakeCurrentUser(self.root)

        anonymous_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_ip='127.0.0.0',
                                info="some taskrun info")

        assert taskrun_authorization.current_user.admin
        assert taskrun_authorization.delete(anonymous_taskrun)


    def test_anonymous_user_delete_user_taskrun(self):
        """Test anonymous user cannot delete taskruns posted by authenticated users"""

        taskrun_authorization.current_user = FakeCurrentUser()

        user_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user_id=self.root.id,
                                info="some taskrun info")

        assert taskrun_authorization.current_user.is_anonymous()
        assert not taskrun_authorization.delete(user_taskrun)


    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot delete a taskrun if it was created
        by another authenticated user, but can delete his own taskruns"""

        taskrun_authorization.current_user = FakeCurrentUser(self.user1)

        own_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user=self.user1,
                                info="some taskrun info")
        other_users_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user=self.root,
                                info="a different taskrun info")

        assert not taskrun_authorization.current_user.is_anonymous()
        assert taskrun_authorization.delete(own_taskrun)
        assert not taskrun_authorization.delete(other_users_taskrun)


    def test_admin_update_user_taskrun(self):
        """Test admins can delete taskruns posted by authenticated users"""

        self.root.admin = True
        taskrun_authorization.current_user = FakeCurrentUser(self.root)

        user_taskrun = model.TaskRun(app_id=self.app.id,
                                task_id=self.task.id,
                                user=self.user1,
                                info="some taskrun info")

        assert taskrun_authorization.current_user.admin
        assert taskrun_authorization.delete(user_taskrun)


class TestTokenAuthorization:

    auth_providers = ('twitter', 'facebook', 'google')
    root, user1, user2 = Fixtures.create_users()


    def test_anonymous_user_delete(self):
        """Test anonymous user is not allowed to delete an oauth token"""
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.delete(token)

    def test_authenticated_user_delete(self):
        """Test authenticated user is not allowed to delete an oauth token"""
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert not token_authorization.delete(token)

    def test_anonymous_user_create(self):
        """Test anonymous user is not allowed to create an oauth token"""
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.create(token)

    def test_authenticated_user_create(self):
        """Test authenticated user is not allowed to create an oauth token"""
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert not token_authorization.create(token)

    def test_anonymous_user_update(self):
        """Test anonymous user is not allowed to update an oauth token"""
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.update(token)

    def test_authenticated_user_update(self):
        """Test authenticated user is not allowed to update an oauth token"""
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert not token_authorization.update(token)

    def test_anonymous_user_read(self):
        """Test anonymous user is not allowed to read an oauth token"""
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.read(token)

    def test_authenticated_user_read(self):
        """Test authenticated user is allowed to read his own oauth tokens"""
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert token_authorization.read(token)
