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
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from pybossa.cache import apps as cached_apps


class TestAppsCache(Test):

    @with_context
    def setUp(self):
        super(TestAppsCache, self).setUp()
        self.user = self.create_users()[0]
        db.session.add(self.user)
        db.session.commit()

    def create_app_with_tasks(self, completed_tasks, ongoing_tasks):
        app = App(name='my_app',
                  short_name='my_app_shortname',
                  description=u'description')
        app.owner = self.user
        db.session.add(app)
        for i in range(completed_tasks):
            task = Task(app_id = 1, state = 'completed', n_answers=3)
            db.session.add(task)
        for i in range(ongoing_tasks):
            task = Task(app_id = 1, state = 'ongoing', n_answers=3)
            db.session.add(task)
        db.session.commit()
        return app

    def create_app_with_contributors(self, anonymous, registered, two_tasks=False):
        app = App(name='my_app',
                  short_name='my_app_shortname',
                  description=u'description')
        app.owner = self.user
        db.session.add(app)
        task = Task(app=app)
        db.session.add(task)
        if two_tasks:
            task2 = Task(app=app)
            db.session.add(task2)
        for i in range(anonymous):
            task_run = TaskRun(app_id = 1,
                               task_id = 1,
                               user_ip = '127.0.0.%s' % i)
            db.session.add(task_run)
            if two_tasks:
                task_run2 = TaskRun(app_id = 1,
                               task_id = 2,
                               user_ip = '127.0.0.%s' % i)
                db.session.add(task_run2)
        for i in range(registered):
            user = User(email_addr = "%s@a.com" % i,
                        name = "user%s" % i,
                        passwd_hash = "1234%s" % i,
                        fullname = "user_fullname%s" % i)
            db.session.add(user)
            task_run = TaskRun(app_id = 1,
                               task_id = 1,
                               user = user)
            db.session.add(task_run)
            if two_tasks:
                task_run2 = TaskRun(app_id = 1,
                               task_id = 2,
                               user = user)
                db.session.add(task_run2)
        db.session.commit()
        return app


    @with_context
    def test_n_completed_tasks_no_completed_tasks(self):
        """Test CACHE APPS n_completed_tasks returns 0 if no completed tasks"""

        app = self.create_app_with_tasks(completed_tasks=0, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 0" % completed_tasks
        assert completed_tasks == 0, err_msg


    @with_context
    def test_n_completed_tasks_with_completed_tasks(self):
        """Test CACHE APPS n_completed_tasks returns number of completed tasks
        if there are any"""

        app = self.create_app_with_tasks(completed_tasks=5, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 5" % completed_tasks
        assert completed_tasks == 5, err_msg


    @with_context
    def test_n_completed_tasks_with_all_tasks_completed(self):
        """Test CACHE APPS n_completed_tasks returns number of tasks if all
        tasks are completed"""

        app = self.create_app_with_tasks(completed_tasks=4, ongoing_tasks=0)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 4" % completed_tasks
        assert completed_tasks == 4, err_msg


    @with_context
    def test_n_registered_volunteers(self):
        """Test CACHE APPS n_registered_volunteers returns number of volunteers
        that contributed to an app when each only submited one task run"""

        app = self.create_app_with_contributors(anonymous=0, registered=3)
        registered_volunteers = cached_apps.n_registered_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 3" % registered_volunteers
        assert registered_volunteers == 3, err_msg


    @with_context
    def test_n_registered_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE APPS n_registered_volunteers returns number of volunteers
        that contributed to an app when any submited more than one task run"""

        app = self.create_app_with_contributors(anonymous=0, registered=2, two_tasks=True)
        registered_volunteers = cached_apps.n_registered_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 2" % registered_volunteers
        assert registered_volunteers == 2, err_msg


    @with_context
    def test_n_anonymous_volunteers(self):
        """Test CACHE APPS n_anonymous_volunteers returns number of volunteers
        that contributed to an app when each only submited one task run"""


    @with_context
    def test_n_anonymous_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE APPS n_anonymous_volunteers returns number of volunteers
        that contributed to an app when any submited more than one task run"""


    @with_context
    def test_n_volunteers(self):
        """Test CACHE APPS total number of users contributed to a given app"""
