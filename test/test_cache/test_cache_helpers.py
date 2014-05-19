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
        """Test n_available_tasks returns 0 for authenticated user if the app
        has no tasks"""
        app = AppFactory.create()

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=1)

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_no_tasks_anonymous_user(self):
        """Test n_available_tasks returns 0  for anonymous user if the app
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
        app = AppFactory.create()
        task = TaskFactory.create(app=app, state='completed')

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=1)

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_all_tasks_completed_anonymous_user(self):
        app = AppFactory.create()
        task = TaskFactory.create(app=app, state='completed')

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip='127.0.0.1')

        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_all_tasks_answered_by_authenticated_user(self):
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=2)
        user = UserFactory.create()
        taskrun = TaskRunFactory.create(task=task, user=user)

        n_available_tasks = helpers.n_available_tasks(app.id, user_id=user.id)

        assert task.state != 'completed', task.state
        assert n_available_tasks == 0, n_available_tasks


    def test_n_available_tasks_all_tasks_answered_by_anonymous_user(self):
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=2)
        taskrun = TaskRunFactory.create(task=task)

        n_available_tasks = helpers.n_available_tasks(app.id, user_ip=taskrun.user_ip)

        assert task.state != 'completed', task.state
        assert n_available_tasks == 0, n_available_tasks
