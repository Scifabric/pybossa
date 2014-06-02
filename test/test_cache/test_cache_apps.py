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
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from pybossa.model.featured import Featured
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

    def create_app_with_contributors(self, anonymous, registered, two_tasks=False, name='my_app'):
        app = App(name=name,
                  short_name='%s_shortname' % name,
                  description=u'description')
        app.owner = self.user
        db.session.add(app)
        task = Task(app=app)
        db.session.add(task)
        if two_tasks:
            task2 = Task(app=app)
            db.session.add(task2)
        db.session.commit()
        for i in range(anonymous):
            task_run = TaskRun(app_id = app.id,
                               task_id = 1,
                               user_ip = '127.0.0.%s' % i)
            db.session.add(task_run)
            if two_tasks:
                task_run2 = TaskRun(app_id = app.id,
                               task_id = 2,
                               user_ip = '127.0.0.%s' % i)
                db.session.add(task_run2)
        for i in range(registered):
            user = User(email_addr = "%s@a.com" % i,
                        name = "user%s" % i,
                        passwd_hash = "1234%s" % i,
                        fullname = "user_fullname%s" % i)
            db.session.add(user)
            task_run = TaskRun(app_id = app.id,
                               task_id = 1,
                               user = user)
            db.session.add(task_run)
            if two_tasks:
                task_run2 = TaskRun(app_id = app.id,
                               task_id = 2,
                               user = user)
                db.session.add(task_run2)
        db.session.commit()
        return app


    @with_context
    def test_get_featured_front_page(self):
        """Test CACHE PROJECTS get_featured_front_page returns featured projects"""

        app = self.create_app(None)
        app.owner = self.user
        db.session.add(app)
        featured = Featured(app=app)
        db.session.add(featured)
        db.session.commit()

        featured = cached_apps.get_featured_front_page()

        assert len(featured) is 1, featured


    @with_context
    def test_get_featured_front_page_only_returns_featured(self):
        """Test CACHE PROJECTS get_featured_front_page returns only featured projects"""

        featured_app = self.create_app(None)
        non_featured_app = self.create_app(None)
        non_featured_app.name = 'other_app'
        non_featured_app.short_name = 'other_app'
        featured_app.owner = self.user
        non_featured_app.owner = self.user
        db.session.add(featured_app)
        db.session.add(non_featured_app)
        featured = Featured(app=featured_app)
        db.session.add(featured)
        db.session.commit()

        featured = cached_apps.get_featured_front_page()

        assert len(featured) is 1, featured


    @with_context
    def test_get_featured_front_page_not_returns_hidden_apps(self):
        """Test CACHE PROJECTS get_featured_front_page does not return hidden projects"""

        featured_app = self.create_app(None)
        featured_app.owner = self.user
        featured_app.hidden = 1
        db.session.add(featured_app)
        featured = Featured(app=featured_app)
        db.session.add(featured)
        db.session.commit()

        featured = cached_apps.get_featured_front_page()

        assert len(featured) is 0, featured


    @with_context
    def test_get_featured_front_page_returns_required_fields(self):
        """Test CACHE PROJECTS get_featured_front_page returns the required info
        about each featured project"""

        app = self.create_app(None)
        app.owner = self.user
        db.session.add(app)
        featured = Featured(app=app)
        db.session.add(featured)
        db.session.commit()
        fields = ('id', 'name', 'short_name', 'info', 'n_volunteers', 'n_completed_tasks')

        featured = cached_apps.get_featured_front_page()[0]

        for field in fields:
            assert featured.has_key(field), "%s not in app info" % field


    @with_context
    def test_get_top_returns_apps_with_most_taskruns(self):
        """Test CACHE PROJECTS get_top returns the projects with most taskruns in order"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        ranked_4_app = self.create_app_with_contributors(7, 0, name='four')

        top_apps = cached_apps.get_top()

        assert top_apps[0]['name'] == 'one', top_apps
        assert top_apps[1]['name'] == 'two', top_apps
        assert top_apps[2]['name'] == 'three', top_apps
        assert top_apps[3]['name'] == 'four', top_apps


    @with_context
    def test_get_top_respects_limit(self):
        """Test CACHE PROJECTS get_top returns only the top n projects"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        ranked_4_app = self.create_app_with_contributors(7, 0, name='four')

        top_apps = cached_apps.get_top(n=2)

        assert len(top_apps) is 2, len(top_apps)


    @with_context
    def test_get_top_returns_four_apps_by_default(self):
        """Test CACHE PROJECTS get_top returns the top 4 projects by default"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        ranked_4_app = self.create_app_with_contributors(7, 0, name='four')
        ranked_5_app = self.create_app_with_contributors(7, 0, name='five')

        top_apps = cached_apps.get_top()

        assert len(top_apps) is 4, len(top_apps)


    @with_context
    def test_get_top_doesnt_return_hidden_apps(self):
        """Test CACHE PROJECTS get_top does not return projects that are hidden"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        hidden_app = self.create_app_with_contributors(11, 0, name='hidden')
        hidden_app.hidden = 1
        db.session.add(hidden_app)
        db.session.commit()

        top_apps = cached_apps.get_top()

        assert len(top_apps) is 3, len(top_apps)
        for app in top_apps:
            assert app['name'] != 'hidden', app['name']

    @with_context
    def test_n_completed_tasks_no_completed_tasks(self):
        """Test CACHE PROJECTS n_completed_tasks returns 0 if no completed tasks"""

        app = self.create_app_with_tasks(completed_tasks=0, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 0" % completed_tasks
        assert completed_tasks == 0, err_msg


    @with_context
    def test_n_completed_tasks_with_completed_tasks(self):
        """Test CACHE PROJECTS n_completed_tasks returns number of completed tasks
        if there are any"""

        app = self.create_app_with_tasks(completed_tasks=5, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 5" % completed_tasks
        assert completed_tasks == 5, err_msg


    @with_context
    def test_n_completed_tasks_with_all_tasks_completed(self):
        """Test CACHE PROJECTS n_completed_tasks returns number of tasks if all
        tasks are completed"""

        app = self.create_app_with_tasks(completed_tasks=4, ongoing_tasks=0)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 4" % completed_tasks
        assert completed_tasks == 4, err_msg


    @with_context
    def test_n_registered_volunteers(self):
        """Test CACHE PROJECTS n_registered_volunteers returns number of volunteers
        that contributed to a project when each only submited one task run"""

        app = self.create_app_with_contributors(anonymous=0, registered=3)
        registered_volunteers = cached_apps.n_registered_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 3" % registered_volunteers
        assert registered_volunteers == 3, err_msg


    @with_context
    def test_n_registered_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE PROJECTS n_registered_volunteers returns number of volunteers
        that contributed to a project when any submited more than one task run"""

        app = self.create_app_with_contributors(anonymous=0, registered=2, two_tasks=True)
        registered_volunteers = cached_apps.n_registered_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 2" % registered_volunteers
        assert registered_volunteers == 2, err_msg


    @with_context
    def test_n_anonymous_volunteers(self):
        """Test CACHE PROJECTS n_anonymous_volunteers returns number of volunteers
        that contributed to a project when each only submited one task run"""

        app = self.create_app_with_contributors(anonymous=3, registered=0)
        anonymous_volunteers = cached_apps.n_anonymous_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 3" % anonymous_volunteers
        assert anonymous_volunteers == 3, err_msg


    @with_context
    def test_n_anonymous_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE PROJECTS n_anonymous_volunteers returns number of volunteers
        that contributed to a project when any submited more than one task run"""

        app = self.create_app_with_contributors(anonymous=2, registered=0, two_tasks=True)
        anonymous_volunteers = cached_apps.n_anonymous_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 2" % anonymous_volunteers
        assert anonymous_volunteers == 2, err_msg


    @with_context
    def test_n_volunteers(self):
        """Test CACHE PROJECTS n_volunteers returns the sum of the anonymous 
        plus registered volunteers that contributed to a project"""

        app = self.create_app_with_contributors(anonymous=2, registered=3, two_tasks=True)
        total_volunteers = cached_apps.n_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 5" % total_volunteers
        assert total_volunteers == 5, err_msg
