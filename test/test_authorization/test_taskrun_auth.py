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

from default import Test, assert_not_raises, with_context
from pybossa.auth import ensure_authorized_to
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import (ProjectFactory, AnonymousTaskRunFactory,
                       TaskFactory, TaskRunFactory, UserFactory)



class TestTaskrunAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_first_taskrun(self):
        """Test anonymous user can create a taskrun for a given task if he
        hasn't already done it"""
        task = TaskFactory.create()
        taskrun = AnonymousTaskRunFactory.build(task=task)

        assert_not_raises(Exception, ensure_authorized_to, 'create', taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_repeated_taskrun(self):
        """Test anonymous user cannot create two taskruns for the same task"""
        task = TaskFactory.create()
        taskrun1 = AnonymousTaskRunFactory.create(task=task)
        taskrun2 = AnonymousTaskRunFactory.build(task=task)

        assert_raises(Forbidden, ensure_authorized_to, 'create', taskrun2)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_taskrun(self):
        """Test anonymous user can create a taskrun for a task even though
        he has posted taskruns for different tasks in the same project"""
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project)
        taskrun1 = AnonymousTaskRunFactory.create(task=tasks[0])
        taskrun2 = AnonymousTaskRunFactory.build(task_id=tasks[1].id,
                                                 project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to, 'create', taskrun2)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_create_taskrun_non_allow_anonymous_contrib(self):
        """Test anonymous user cannot create a taskrun for a project that does
        not allow for anonymous contributors"""
        project = ProjectFactory.create(allow_anonymous_contributors=False)
        task = TaskFactory.create(project=project)
        taskrun = AnonymousTaskRunFactory.build(task=task)

        assert_raises(Unauthorized, ensure_authorized_to, 'create', taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_can_create_taskrun_for_draft_project(self):
        """Test anonymous users can create a taskrun for a project that
        is a draft"""
        project = ProjectFactory.create(published=False)
        task = TaskFactory.create(project=project)
        taskrun = AnonymousTaskRunFactory.build(task_id=task.id,
                                                project_id=project.id)

        assert_not_raises(Forbidden, ensure_authorized_to, 'create', taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_create_first_taskrun(self):
        """Test authenticated user can create a taskrun for a given task if he
        hasn't already done it"""
        task = TaskFactory.create()
        taskrun = TaskRunFactory.build(task_id=task.id,
                                       project_id=task.project_id,
                                       user_id=self.mock_authenticated.id)

        assert self.mock_authenticated.id == taskrun.user_id, taskrun
        assert_not_raises(Exception, ensure_authorized_to, 'create', taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_create_repeated_taskrun(self):
        """Test authenticated user cannot create two taskruns for the same task"""
        task = TaskFactory.create()
        taskrun1 = TaskRunFactory.create(task=task)
        taskrun2 = TaskRunFactory.build(task=task, user=taskrun1.user)

        assert self.mock_authenticated.id == taskrun1.user.id
        assert_raises(Forbidden, ensure_authorized_to, 'create', taskrun2)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_create_taskrun(self):
        """Test authenticated user can create a taskrun for a task even though
        he has posted taskruns for different tasks in the same project"""
        user = UserFactory.create_batch(2)[1]
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project)
        taskrun1 = TaskRunFactory.create(task=tasks[0], user=user)
        taskrun2 = TaskRunFactory.build(task_id=tasks[1].id, user_id=user.id,
                                        project_id=tasks[1].project_id)

        assert self.mock_authenticated.id == taskrun2.user_id
        assert_not_raises(Exception, ensure_authorized_to, 'create', taskrun2)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_create_taskrun_non_allow_anonymous_contrib(self):
        """Test authenticated user can create a taskrun for a project that does
        not allow for anonymous contributors"""
        project = ProjectFactory.create(allow_anonymous_contributors=False)
        task = TaskFactory.create(project=project)
        taskrun = TaskRunFactory.build(task_id=task.id, project_id=project.id)

        assert_not_raises(Exception, ensure_authorized_to, 'create', taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_create_taskrun_for_draft_project(self):
        """Test authenticated users can create a taskrun for a project that
        is a draft"""
        project = ProjectFactory.create(published=False)
        task = TaskFactory.create(project=project)
        taskrun = TaskRunFactory.build(task_id=task.id, project_id=project.id)

        assert_not_raises(Forbidden, ensure_authorized_to, 'create', taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_read(self):
        """Test anonymous user can read any taskrun"""
        anonymous_taskrun = AnonymousTaskRunFactory.create()
        user_taskrun = TaskRunFactory.create()

        assert_not_raises(Exception,
                          ensure_authorized_to, 'read', anonymous_taskrun)
        assert_not_raises(Exception, ensure_authorized_to, 'read', user_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_read(self):
        """Test authenticated user can read any taskrun"""
        own_taskrun = TaskRunFactory.create()
        anonymous_taskrun = AnonymousTaskRunFactory.create()
        other_users_taskrun = TaskRunFactory.create()

        assert self.mock_authenticated.id == own_taskrun.user.id
        assert self.mock_authenticated.id != other_users_taskrun.user.id
        assert_not_raises(Exception,
                          ensure_authorized_to, 'read', anonymous_taskrun)
        assert_not_raises(Exception,
                          ensure_authorized_to, 'read', other_users_taskrun)
        assert_not_raises(Exception, ensure_authorized_to, 'read', own_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_update_anoymous_taskrun_result(self):
        """Test anonymous users cannot update an anonymously posted taskrun
        with result"""
        task = TaskFactory.create(n_answers=1)
        anonymous_taskrun = AnonymousTaskRunFactory.create(task=task)

        assert_raises(Unauthorized,
                      ensure_authorized_to, 'update', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_update_anoymous_taskrun(self):
        """Test anonymous users cannot update an anonymously posted taskrun"""
        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Unauthorized,
                      ensure_authorized_to, 'update', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_update_anonymous_taskrun(self):
        """Test authenticated users cannot update an anonymously
        posted taskrun"""
        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Forbidden,
                      ensure_authorized_to, 'update', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_update_anonymous_taskrun_result(self):
        """Test admins cannot update anonymously posted taskruns
        when there is a result associated."""
        task = TaskFactory.create(n_answers=1)
        anonymous_taskrun = AnonymousTaskRunFactory.create(task=task)

        assert_raises(Forbidden,
                      ensure_authorized_to, 'update', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_update_anonymous_taskrun(self):
        """Test admins can update anonymously posted taskruns
        when no result is associated."""
        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_not_raises(Exception,
                          ensure_authorized_to, 'update', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_update_user_taskrun(self):
        """Test anonymous user cannot update taskruns posted by authenticated users"""
        user_taskrun = TaskRunFactory.create()

        assert_raises(Unauthorized,
                      ensure_authorized_to, 'update', user_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_update_other_users_taskrun(self):
        """Test authenticated user cannot update any user taskrun
        except own."""
        own_taskrun = TaskRunFactory.create()
        other_users_taskrun = TaskRunFactory.create()

        assert self.mock_authenticated.id == own_taskrun.user.id
        assert self.mock_authenticated.id != other_users_taskrun.user.id
        assert_not_raises(Exception, ensure_authorized_to,
                          'update', own_taskrun)
        assert_raises(Forbidden,
                      ensure_authorized_to, 'update', other_users_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_update_other_users_taskrun_result(self):
        """Test authenticated user cannot update any user taskrun
        when task runs have associated results."""
        task = TaskFactory.create(n_answers=1)
        own_taskrun = TaskRunFactory.create(task=task)
        task2 = TaskFactory.create(n_answers=1)
        other_users_taskrun = TaskRunFactory.create(task=task2)

        assert self.mock_authenticated.id == own_taskrun.user.id
        assert self.mock_authenticated.id != other_users_taskrun.user.id
        assert_raises(Forbidden, ensure_authorized_to, 'update', own_taskrun)
        assert_raises(Forbidden,
                      ensure_authorized_to, 'update', other_users_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_update_user_taskrun(self):
        """Test admins can update taskruns posted by authenticated
        when there is no result associated."""
        user_taskrun = TaskRunFactory.create()

        assert self.mock_admin.id != user_taskrun.user.id
        assert_not_raises(Exception, ensure_authorized_to,
                          'update', user_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_update_user_taskrun_with_result(self):
        """Test admins cannot update taskruns posted by authenticated
        when there is a result associated."""
        task = TaskFactory.create(n_answers=1)
        user_taskrun = TaskRunFactory.create(task=task)

        assert self.mock_admin.id != user_taskrun.user.id
        assert_raises(Forbidden, ensure_authorized_to,
                      'update', user_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_anonymous_taskrun(self):
        """Test anonymous users cannot delete an anonymously posted taskrun"""
        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Unauthorized,
                      ensure_authorized_to, 'delete', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_anonymous_taskrun(self):
        """Test authenticated users cannot delete an anonymously posted taskrun"""
        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_raises(Forbidden,
                      ensure_authorized_to, 'delete', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_delete_anonymous_taskrun(self):
        """Test admins can delete anonymously posted taskruns"""
        anonymous_taskrun = AnonymousTaskRunFactory.create()

        assert_not_raises(Exception,
                          ensure_authorized_to, 'delete', anonymous_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_delete_user_taskrun(self):
        """Test anonymous user cannot delete taskruns posted by authenticated users"""
        user_taskrun = TaskRunFactory.create()

        assert_raises(Unauthorized,
                      ensure_authorized_to, 'delete', user_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_delete_other_users_taskrun(self):
        """Test authenticated user cannot delete a taskrun if it was created
        by another authenticated user, but can delete his own taskruns"""
        own_taskrun = TaskRunFactory.create()
        other_users_taskrun = TaskRunFactory.create()

        assert self.mock_authenticated.id == own_taskrun.user.id
        assert self.mock_authenticated.id != other_users_taskrun.user.id
        assert_not_raises(Exception,
                          ensure_authorized_to, 'delete', own_taskrun)
        assert_raises(Forbidden,
                      ensure_authorized_to, 'delete', other_users_taskrun)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_delete_user_taskrun(self):
        """Test admins can delete taskruns posted by authenticated users"""
        user_taskrun = TaskRunFactory.create()

        assert self.mock_admin.id != user_taskrun.user.id, user_taskrun.user.id
        assert_not_raises(Exception,
                          ensure_authorized_to, 'delete', user_taskrun)
