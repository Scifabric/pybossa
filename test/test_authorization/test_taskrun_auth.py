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

from default import Test, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import (AppFactory, AnonymousTaskRunFactory,
                       TaskFactory, TaskRunFactory, UserFactory)
from factories import reset_all_pk_sequences



class TestTaskrunAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_first_taskrun(self):
        """Test anonymous user can create a taskrun for a given task if he
        hasn't already done it"""

        taskrun = AnonymousTaskRunFactory.build()

        assert_not_raises(Exception,
                        getattr(require, 'taskrun').create,
                        taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_repeated_taskrun(self):
        """Test anonymous user cannot create a taskrun for a task to which
        he has previously posted a taskrun"""

        task = TaskFactory.create()
        taskrun1 = AnonymousTaskRunFactory.create(task=task)
        taskrun2 = AnonymousTaskRunFactory.build(task=task)
        assert_raises(Forbidden,
                    getattr(require, 'taskrun').create,
                    taskrun2)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_create_taskrun(self):
        """Test anonymous user can create a taskrun for a task even though
        he has posted taskruns for different tasks in the same project"""

        tasks = TaskFactory.create_batch(2)
        taskrun1 = AnonymousTaskRunFactory.create(task=tasks[0])
        taskrun2 = AnonymousTaskRunFactory.build(task_id=tasks[1].id)

        assert_not_raises(Exception,
                      getattr(require, 'taskrun').create,
                      taskrun2)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_first_taskrun(self):
        """Test authenticated user can create a taskrun for a given task if he
        hasn't already done it"""

        taskrun = TaskRunFactory.build()

        assert self.mock_authenticated.id == taskrun.user.id
        assert_not_raises(Exception,
                      getattr(require, 'taskrun').create,
                      taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_repeated_taskrun(self):
        """Test authenticated user cannot create a taskrun for a task to which
        he has previously posted a taskrun"""

        task = TaskFactory.create()
        taskrun1 = TaskRunFactory.create(task=task)
        taskrun2 = TaskRunFactory.build(task=task, user=taskrun1.user)

        assert self.mock_authenticated.id == taskrun1.user.id
        assert_raises(Forbidden, getattr(require, 'taskrun').create, taskrun2)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_create_taskrun(self):
        """Test authenticated user can create a taskrun for a task even though
        he has posted taskruns for different tasks in the same project"""

        user = UserFactory.create_batch(2)[1]
        tasks = TaskFactory.create_batch(2)
        taskrun1 = TaskRunFactory.create(task=tasks[0], user=user)
        taskrun2 = TaskRunFactory.build(task_id=tasks[1].id, user=user)

        assert self.mock_authenticated.id == taskrun2.user.id
        assert_not_raises(Exception,
                      getattr(require, 'taskrun').create,
                      taskrun2)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_read(self):
        """Test anonymous user can read any taskrun"""

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

        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Unauthorized,
                      getattr(require, 'taskrun').update,
                      anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update_anonymous_taskrun(self):
        """Test authenticated users cannot update an anonymously posted taskrun"""

        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Forbidden,
                      getattr(require, 'taskrun').update,
                      anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_update_anonymous_taskrun(self):
        """Test admins cannot update anonymously posted taskruns"""

        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Forbidden,
                      getattr(require, 'taskrun').update,
                      anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_update_user_taskrun(self):
        """Test anonymous user cannot update taskruns posted by authenticated users"""

        user_taskrun = TaskRunFactory.create()

        assert_raises(Unauthorized,
                      getattr(require, 'taskrun').update,
                      user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot update any user taskrun"""

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

        user_taskrun = TaskRunFactory.create()

        assert self.mock_admin.id != user_taskrun.user.id
        assert_raises(Forbidden,
                      getattr(require, 'taskrun').update,
                      user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_anonymous_taskrun(self):
        """Test anonymous users cannot delete an anonymously posted taskrun"""

        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Unauthorized,
                      getattr(require, 'taskrun').delete,
                      anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_anonymous_taskrun(self):
        """Test authenticated users cannot delete an anonymously posted taskrun"""

        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Forbidden,
                      getattr(require, 'taskrun').delete,
                      anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.taskrun.current_user', new=mock_admin)
    def test_admin_delete_anonymous_taskrun(self):
        """Test admins can delete anonymously posted taskruns"""

        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_not_raises(Exception,
                      getattr(require, 'taskrun').delete,
                      anonymous_taskrun)


    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.taskrun.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_user_taskrun(self):
        """Test anonymous user cannot delete taskruns posted by authenticated users"""

        user_taskrun = TaskRunFactory.create()

        assert_raises(Unauthorized,
                  getattr(require, 'taskrun').delete,
                  user_taskrun)


    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.taskrun.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_other_users_taskrun(self):
        """Test authenticated user cannot delete a taskrun if it was created
        by another authenticated user, but can delete his own taskruns"""

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

        user_taskrun = TaskRunFactory.create()

        assert self.mock_admin.id != user_taskrun.user.id, user_taskrun.user.id
        assert_not_raises(Exception,
                  getattr(require, 'taskrun').delete,
                  user_taskrun)
