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

from default import Test, db, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import (AppFactory, AnonymousTaskRunFactory,
                       TaskFactory, TaskRunFactory, UserFactory)
from factories import reset_all_pk_sequences



class TestTaskrunAuthorization(Test):

    def setUp(self):
        super(TestTaskrunAuthorization, self).setUp()
        reset_all_pk_sequences()


    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)


    def configure_fixtures(self):
        self.app = db.session.query(App).first()
        self.root = db.session.query(User).first()
        self.user1 = db.session.query(User).get(2)
        self.user2 = db.session.query(User).get(3)
        self.task = Task(app_id=self.app.id, state='0', n_answers=10)
        self.task.app = self.app
        db.session.add(self.task)
        db.session.commit()


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_first_taskrun(self):
        """Test anonymous user can create a taskrun for a given task if he
        hasn't already done it"""

        with self.flask_app.test_request_context('/'):
            taskrun = AnonymousTaskRunFactory.build()

            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_repeated_taskrun(self):
        """Test anonymous user cannot create a taskrun for a task to which
        he has previously posted a taskrun"""

        with self.flask_app.test_request_context('/'):
            task = TaskFactory.create()
            taskrun1 = AnonymousTaskRunFactory.create(task=task)
            taskrun2 = AnonymousTaskRunFactory.build(task=task)
            assert_raises(Forbidden,
                        getattr(require, 'taskrun').create,
                        taskrun2)

            # But the user can still create taskruns for different tasks
            task2 = TaskFactory.create(app=task.app)
            taskrun3 = AnonymousTaskRunFactory.build(task=task2)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun3)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_first_taskrun(self):
        """Test authenticated user can create a taskrun for a given task if he
        hasn't already done it"""

        with self.flask_app.test_request_context('/'):
            taskrun = TaskRunFactory.build()

            err_msg ="The user id should be the same: self.mock_authenticated.id -> %s != taskrun.user.id -> %s" % (self.mock_authenticated.id, taskrun.user.id)
            assert self.mock_authenticated.id == taskrun.user.id, err_msg
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_repeated_taskrun(self):
        """Test authenticated user cannot create a taskrun for a task to which
        he has previously posted a taskrun"""

        with self.flask_app.test_request_context('/'):
            task = TaskFactory.create()
            taskrun1 = TaskRunFactory.create(task=task)
            taskrun2 = TaskRunFactory.build(task=task, user=taskrun1.user)

            assert self.mock_authenticated.id == taskrun1.user.id
            assert_raises(Forbidden, getattr(require, 'taskrun').create, taskrun2)

            # But the user can still create taskruns for different tasks
            task2 = TaskFactory.create(app=task.app)
            taskrun3 = TaskRunFactory.build(task=task2, user=taskrun1.user)

            assert self.mock_authenticated.id == taskrun3.user.id
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').create,
                          taskrun3)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_read(self):
        """Test anonymous user can read any taskrun"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()
            user_taskrun = TaskRunFactory.create()

            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          anonymous_taskrun)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_read(self):
        """Test authenticated user can read any taskrun"""

        with self.flask_app.test_request_context('/'):
            own_taskrun = TaskRunFactory.create()
            anonymous_taskrun = AnonymousTaskRunFactory.create()
            other_users_taskrun = TaskRunFactory.create()

            assert self.mock_authenticated.id == own_taskrun.user.id
            assert self.mock_authenticated.id != other_users_taskrun.user.id
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          anonymous_taskrun)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          other_users_taskrun)
            assert_not_raises(Exception,
                          getattr(require, 'taskrun').read,
                          own_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update_anoymous_taskrun(self):
        """Test anonymous users cannot update an anonymously posted taskrun"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()

            assert_raises(Unauthorized,
                          getattr(require, 'taskrun').update,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update_anonymous_taskrun(self):
        """Test authenticated users cannot update an anonymously posted taskrun"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()

            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_update_anonymous_taskrun(self):
        """Test admins cannot update anonymously posted taskruns"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()

            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update_user_taskrun(self):
        """Test anonymous user cannot update taskruns posted by authenticated users"""
        with self.flask_app.test_request_context('/'):
            user_taskrun = TaskRunFactory.create()

            assert_raises(Unauthorized,
                          getattr(require, 'taskrun').update,
                          user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot update any user taskrun"""

        with self.flask_app.test_request_context('/'):
            own_taskrun = TaskRunFactory.create()
            other_users_taskrun = TaskRunFactory.create()

            assert self.mock_authenticated.id == own_taskrun.user.id
            assert self.mock_authenticated.id != other_users_taskrun.user.id
            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          own_taskrun)
            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          other_users_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_update_user_taskrun(self):
        """Test admins cannot update taskruns posted by authenticated users"""

        with self.flask_app.test_request_context('/'):
            user_taskrun = TaskRunFactory.create()

            assert self.mock_admin.id != user_taskrun.user.id
            assert_raises(Forbidden,
                          getattr(require, 'taskrun').update,
                          user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_anonymous_taskrun(self):
        """Test anonymous users cannot delete an anonymously posted taskrun"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()

            assert_raises(Unauthorized,
                          getattr(require, 'taskrun').delete,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_anonymous_taskrun(self):
        """Test authenticated users cannot delete an anonymously posted taskrun"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()

            assert_raises(Forbidden,
                          getattr(require, 'taskrun').delete,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_delete_anonymous_taskrun(self):
        """Test admins can delete anonymously posted taskruns"""

        with self.flask_app.test_request_context('/'):
            anonymous_taskrun = AnonymousTaskRunFactory.create()

            assert_not_raises(Exception,
                          getattr(require, 'taskrun').delete,
                          anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_user_taskrun(self):
        """Test anonymous user cannot delete taskruns posted by authenticated users"""

        with self.flask_app.test_request_context('/'):
            user_taskrun = TaskRunFactory.create()

            assert_raises(Unauthorized,
                      getattr(require, 'taskrun').delete,
                      user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_other_users_taskrun(self):
        """Test authenticated user cannot delete a taskrun if it was created
        by another authenticated user, but can delete his own taskruns"""

        with self.flask_app.test_request_context('/'):
            own_taskrun = TaskRunFactory.create()
            other_users_taskrun = TaskRunFactory.create()

            assert self.mock_authenticated.id == own_taskrun.user.id
            assert self.mock_authenticated.id != other_users_taskrun.user.id
            assert_not_raises(Exception,
                      getattr(require, 'taskrun').delete,
                      own_taskrun)
            assert_raises(Forbidden,
                      getattr(require, 'taskrun').delete,
                      other_users_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_delete_user_taskrun(self):
        """Test admins can delete taskruns posted by authenticated users"""

        with self.flask_app.test_request_context('/'):
            user_taskrun = TaskRunFactory.create()

            assert self.mock_admin.id != user_taskrun.user_id, user_taskrun.user_id
            assert_not_raises(Exception,
                      getattr(require, 'taskrun').delete,
                      user_taskrun)
