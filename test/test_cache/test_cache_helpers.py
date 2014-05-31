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

from default import Test, db, with_context
from factories import (AppFactory, TaskFactory, TaskRunFactory,
                      AnonymousTaskRunFactory, UserFactory)
from pybossa.cache import helpers


class TestHelpersCache(Test):

    def test_n_available_tasks_no_tasks_authenticated_user(self):
        """Test n_available_tasks returns 0 for authenticated user if the project
        has no tasks"""
        app = AppFactory.create()

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=1)

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_no_tasks_anonymous_user(self):
        """Test n_available_tasks returns 0 for anonymous user if the project
        has no tasks"""
        app = AppFactory.create()

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip='127.0.0.1')

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_no_taskruns_authenticated_user(self):
        """Test n_available_tasks returns 1 for authenticated user
        if there are no taskruns"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app)

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=1)

        assert n_available_tasks == 1, n_available_tasks


    def test_n_available_tasks_no_taskruns_anonymous_user(self):
        """Test n_available_tasks returns 1 for anonymous user
        if there are no taskruns"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app)

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip='127.0.0.1')

        assert n_available_tasks == 1, n_available_tasks


    def test_n_available_tasks_all_tasks_completed_authenticated_user(self):
        """Test n_available_tasks returns 0 for authenticated user if all the
        tasks are completed"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, state='completed')

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=1)

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_all_tasks_completed_anonymous_user(self):
        """Test n_available_tasks returns 0 for anonymous user if all the
        tasks are completed"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, state='completed')

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip='127.0.0.1')

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_all_tasks_answered_by_authenticated_user(self):
        """Test n_available_tasks returns 0 for authenticated user if he has
        submitted taskruns for all the tasks"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=2)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=task, user=user)

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=user.id)

        assert task.state != 'completed', task.state
        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_all_tasks_answered_by_anonymous_user(self):
        """Test n_available_tasks returns 0 for anonymous user if he has
        submitted taskruns for all the tasks"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=2)
        taskrun = AnonymousTaskRunFactory.create(task=task)

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip=taskrun.user_ip)

        assert task.state != 'completed', task.state
        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_some_tasks_answered_by_authenticated_user(self):
        """Test n_available_tasks returns 1 for authenticated user if he has
        submitted taskruns for one of the tasks but there is still another task"""
        app = AppFactory.create()
        answered_task = TaskFactory.create(app=app)
        available_task = TaskFactory.create(app=app)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=answered_task, user=user)

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=user.id)
        assert n_available_tasks == 1, n_available_tasks


    def test_n_available_some_all_tasks_answered_by_anonymous_user(self):
        """Test n_available_tasks returns 1 for anonymous user if he has
        submitted taskruns for one of the tasks but there is still another task"""
        app = AppFactory.create()
        answered_task = TaskFactory.create(app=app)
        available_task = TaskFactory.create(app=app)
        taskrun = AnonymousTaskRunFactory.create(task=answered_task)

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip=taskrun.user_ip)

        assert n_available_tasks == 1, n_available_tasks


    def test_n_available_tasks_task_answered_by_another_user(self):
        """Test n_available_tasks returns 1 for a user if another
        user has submitted taskruns for the task but he hasn't"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=task)

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=user.id)
        assert n_available_tasks == 1, n_available_tasks


    def test_check_contributing_state_completed(self):
        """Test check_contributing_state returns 'completed' for a project with all
        tasks completed and user that has contributed to it"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=1)
        user = UserFactory.create()
        TaskRunFactory.create_batch(1, task=task, user=user)

        contributing_state = helpers.check_contributing_state(app_id=app.id,
                                                              user_id=user.id)

        assert task.state == 'completed', task.state
        assert contributing_state == 'completed', contributing_state


    def test_check_contributing_state_completed_user_not_contributed(self):
        """Test check_contributing_state returns 'completed' for a project with all
        tasks completed even if the user has not contributed to it"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=2)
        TaskRunFactory.create_batch(2, task=task)
        user = UserFactory.create()

        contributing_state = helpers.check_contributing_state(app_id=app.id,
                                                              user_id=user.id)

        assert task.state == 'completed', task.state
        assert contributing_state == 'completed', contributing_state


    def test_check_contributing_state_ongoing_tasks_not_contributed(self):
        """Test check_contributing_state returns 'can_contribute' for a project
        with ongoing tasks a user has not contributed to"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app)
        user = UserFactory.create()

        contributing_state = helpers.check_contributing_state(app_id=app.id,
                                                              user_id=user.id)

        assert contributing_state == 'can_contribute', contributing_state


    def test_check_contributing_state_ongoing_tasks_contributed(self):
        """Test check_contributing_state returns 'cannot_contribute' for a project
        with ongoing tasks to which the user has already contributed"""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=3)
        user = UserFactory.create()
        TaskRunFactory.create(task=task, user=user)
        contributing_state = helpers.check_contributing_state(app_id=app.id,
                                                              user_id=user.id)

        assert contributing_state == 'cannot_contribute', contributing_state
