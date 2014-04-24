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

import hashlib
from default import Test, db, with_context
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.cache import apps as cached_apps


class TestAppsCache(Test):

    @with_context
    def setUp(self):
        super(TestAppsCache, self).setUp()
        self.root, self.user1, self.user2 = self.create_users()
        db.session.add_all([self.root, self.user1, self.user2])
        db.session.commit()

    def create_app_with_tasks(self, owner, completed_tasks, ongoing_tasks):
        app = App(name='my_app',
                  short_name='my_app_shortname',
                  description=u'description')
        app.owner = owner
        db.session.add(app)
        for i in range(completed_tasks):
            task = Task(app_id = 1, state = 'completed', n_answers=3)
            db.session.add(task)
        for i in range(ongoing_tasks):
            task = Task(app_id = 1, state = 'ongoing', n_answers=3)
            db.session.add(task)
        db.session.commit()
        return app


    @with_context
    def test_n_completed_tasks_no_completed_tasks(self):
        """Test CACHE APPS n_completed_tasks returns 0 if no completed tasks"""

        app = self.create_app_with_tasks(self.root, completed_tasks=0, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 0" % completed_tasks
        assert completed_tasks == 0, err_msg


    @with_context
    def test_n_completed_tasks_with_completed_tasks(self):
        """Test CACHE APPS n_completed_tasks returns number of completed tasks
        if there are any"""

        app = self.create_app_with_tasks(self.root, completed_tasks=5, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 5" % completed_tasks
        assert completed_tasks == 5, err_msg


    @with_context
    def test_n_completed_tasks_with_all_tasks_completed(self):
        """Test CACHE APPS n_completed_tasks returns number of tasks if all
        tasks are completed"""

        app = self.create_app_with_tasks(self.root, completed_tasks=5, ongoing_tasks=0)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 5" % completed_tasks
        assert completed_tasks == 5, err_msg


    @with_context
    def test_n_registered_volunteers(self):
        """Test CACHE APPS number of registered users contributed to a given app"""


    @with_context
    def test_n_anonymous_volunteers(self):
        """Test CACHE APPS number of anonymous users contributed to a given app"""


    @with_context
    def test_n_volunteers(self):
        """Test CACHE APPS total number of users contributed to a given app"""
