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
from pybossa.cache import apps as cached_apps

from factories import UserFactory, AppFactory, TaskFactory, \
    FeaturedFactory, TaskRunFactory, AnonymousTaskRunFactory


class TestAppsCache(Test):


    def create_app_with_tasks(self, completed_tasks, ongoing_tasks):
        app = AppFactory.create()
        TaskFactory.create_batch(completed_tasks, state='completed', app=app)
        TaskFactory.create_batch(ongoing_tasks, state='ongoing', app=app)
        return app

    def create_app_with_contributors(self, anonymous, registered,
                                     two_tasks=False, name='my_app', hidden=0):
        app = AppFactory.create(name=name, hidden=hidden)
        task = TaskFactory(app=app)
        if two_tasks:
            task2 = TaskFactory(app=app)
        for i in range(anonymous):
            task_run = AnonymousTaskRunFactory(task=task,
                               user_ip='127.0.0.%s' % i)
            if two_tasks:
                task_run2 = AnonymousTaskRunFactory(task=task2,
                               user_ip='127.0.0.%s' % i)
        for i in range(registered):
            user = UserFactory.create()
            task_run = TaskRunFactory(task=task, user=user)
            if two_tasks:
                task_run2 = TaskRunFactory(task=task2, user=user)
        return app


    def test_get_featured_front_page(self):
        """Test CACHE PROJECTS get_featured_front_page returns featured projects"""

        FeaturedFactory.create()

        featured = cached_apps.get_featured_front_page()

        assert len(featured) is 1, featured


    def test_get_featured_front_page_only_returns_featured(self):
        """Test CACHE PROJECTS get_featured_front_page returns only featured projects"""

        featured_app = AppFactory.create()
        non_featured_app = AppFactory.create()
        FeaturedFactory.create(app=featured_app)

        featured = cached_apps.get_featured_front_page()

        assert len(featured) is 1, featured


    def test_get_featured_front_page_not_returns_hidden_apps(self):
        """Test CACHE PROJECTS get_featured_front_page does not return hidden projects"""

        featured_app = AppFactory.create(hidden=1)
        FeaturedFactory.create(app=featured_app)

        featured = cached_apps.get_featured_front_page()

        assert len(featured) is 0, featured


    def test_get_featured_front_page_returns_required_fields(self):
        """Test CACHE PROJECTS get_featured_front_page returns the required info
        about each featured project"""

        fields = ('id', 'name', 'short_name', 'info', 'n_volunteers', 'n_completed_tasks')

        FeaturedFactory.create()

        featured = cached_apps.get_featured_front_page()[0]

        for field in fields:
            assert featured.has_key(field), "%s not in app info" % field


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


    def test_get_top_respects_limit(self):
        """Test CACHE PROJECTS get_top returns only the top n projects"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        ranked_4_app = self.create_app_with_contributors(7, 0, name='four')

        top_apps = cached_apps.get_top(n=2)

        assert len(top_apps) is 2, len(top_apps)


    def test_get_top_returns_four_apps_by_default(self):
        """Test CACHE PROJECTS get_top returns the top 4 projects by default"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        ranked_4_app = self.create_app_with_contributors(7, 0, name='four')
        ranked_5_app = self.create_app_with_contributors(7, 0, name='five')

        top_apps = cached_apps.get_top()

        assert len(top_apps) is 4, len(top_apps)


    def test_get_top_doesnt_return_hidden_apps(self):
        """Test CACHE PROJECTS get_top does not return projects that are hidden"""

        ranked_3_app = self.create_app_with_contributors(8, 0, name='three')
        ranked_2_app = self.create_app_with_contributors(9, 0, name='two')
        ranked_1_app = self.create_app_with_contributors(10, 0, name='one')
        hidden_app = self.create_app_with_contributors(11, 0, name='hidden', hidden=1)

        top_apps = cached_apps.get_top()

        assert len(top_apps) is 3, len(top_apps)
        for app in top_apps:
            assert app['name'] != 'hidden', app['name']

    def test_n_completed_tasks_no_completed_tasks(self):
        """Test CACHE PROJECTS n_completed_tasks returns 0 if no completed tasks"""

        app = self.create_app_with_tasks(completed_tasks=0, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 0" % completed_tasks
        assert completed_tasks == 0, err_msg


    def test_n_completed_tasks_with_completed_tasks(self):
        """Test CACHE PROJECTS n_completed_tasks returns number of completed tasks
        if there are any"""

        app = self.create_app_with_tasks(completed_tasks=5, ongoing_tasks=5)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 5" % completed_tasks
        assert completed_tasks == 5, err_msg


    def test_n_completed_tasks_with_all_tasks_completed(self):
        """Test CACHE PROJECTS n_completed_tasks returns number of tasks if all
        tasks are completed"""

        app = self.create_app_with_tasks(completed_tasks=4, ongoing_tasks=0)
        completed_tasks = cached_apps.n_completed_tasks(app.id)

        err_msg = "Completed tasks is %s, it should be 4" % completed_tasks
        assert completed_tasks == 4, err_msg


    def test_n_registered_volunteers(self):
        """Test CACHE PROJECTS n_registered_volunteers returns number of volunteers
        that contributed to a project when each only submited one task run"""

        app = self.create_app_with_contributors(anonymous=0, registered=3)
        registered_volunteers = cached_apps.n_registered_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 3" % registered_volunteers
        assert registered_volunteers == 3, err_msg


    def test_n_registered_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE PROJECTS n_registered_volunteers returns number of volunteers
        that contributed to a project when any submited more than one task run"""

        app = self.create_app_with_contributors(anonymous=0, registered=2, two_tasks=True)
        registered_volunteers = cached_apps.n_registered_volunteers(app.id)
        for tr in app.task_runs:
            print tr.user

        err_msg = "Volunteers is %s, it should be 2" % registered_volunteers
        assert registered_volunteers == 2, err_msg


    def test_n_anonymous_volunteers(self):
        """Test CACHE PROJECTS n_anonymous_volunteers returns number of volunteers
        that contributed to a project when each only submited one task run"""

        app = self.create_app_with_contributors(anonymous=3, registered=0)
        anonymous_volunteers = cached_apps.n_anonymous_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 3" % anonymous_volunteers
        assert anonymous_volunteers == 3, err_msg


    def test_n_anonymous_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE PROJECTS n_anonymous_volunteers returns number of volunteers
        that contributed to a project when any submited more than one task run"""

        app = self.create_app_with_contributors(anonymous=2, registered=0, two_tasks=True)
        anonymous_volunteers = cached_apps.n_anonymous_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 2" % anonymous_volunteers
        assert anonymous_volunteers == 2, err_msg


    def test_n_volunteers(self):
        """Test CACHE PROJECTS n_volunteers returns the sum of the anonymous
        plus registered volunteers that contributed to a project"""

        app = self.create_app_with_contributors(anonymous=2, registered=3, two_tasks=True)
        total_volunteers = cached_apps.n_volunteers(app.id)

        err_msg = "Volunteers is %s, it should be 5" % total_volunteers
        assert total_volunteers == 5, err_msg


    def test_n_draft_no_drafts(self):
        """Test CACHE PROJECTS n_draft returns 0 if there are no draft projects"""
        # Here, we are suposing that a project is draft iff has no presenter AND has no tasks

        app = AppFactory.create(info={})
        TaskFactory.create_batch(2, app=app)

        number_of_drafts = cached_apps.n_draft()

        assert number_of_drafts == 0, number_of_drafts


    def test_n_draft_with_drafts(self):
        """Test CACHE PROJECTS n_draft returns 2 if there are 2 draft projects"""
        # Here, we are suposing that a project is draft iff has no presenter AND has no tasks

        AppFactory.create_batch(2, info={})

        number_of_drafts = cached_apps.n_draft()

        assert number_of_drafts == 2, number_of_drafts


    def test_project_tasks_returns_no_tasks(self):
        """Test CACHE PROJECTS project_tasks returns an empty list if a project
        has no tasks"""

        project = AppFactory.create()

        project_tasks = cached_apps.project_tasks(project.id)

        assert project_tasks == [], project_tasks


    def test_project_tasks_returns_all_tasks(self):
        """Test CACHE PROJECTS project_tasks returns a list with all the tasks
        from a given project"""

        project = AppFactory.create()
        TaskFactory.create_batch(2, app=project)

        project_tasks = cached_apps.project_tasks(project.id)

        assert len(project_tasks) == 2, project_tasks


    def test_project_tasks_returns_tasks(self):
        """Test CACHE PROJECTS project_tasks returns a list with objects
        with the required task attributes"""

        project = AppFactory.create()
        task = TaskFactory.create( app=project, info={})
        attributes = ('id', 'created', 'app_id', 'state',
                      'priority_0', 'info', 'n_answers')

        cached_task = cached_apps.project_tasks(project.id)[0]

        for attr in attributes:
            assert cached_task.get(attr) == getattr(task, attr), attr


    def test_project_tasks_returns_pct_status(self):
        """Test CACHE PROJECTS project_tasks returns also the completion
        percentage of each task"""

        project = AppFactory.create()
        task = TaskFactory.create( app=project, info={}, n_answers=4)

        cached_task = cached_apps.project_tasks(project.id)[0]

        assert cached_task.get('pct_status') == 0, cached_task.get('pct_status')

        TaskRunFactory.create(task=task)
        cached_task = cached_apps.project_tasks(project.id)[0]

        assert cached_task.get('pct_status') == 0.25, cached_task.get('pct_status')

        TaskRunFactory.create(task=task)
        cached_task = cached_apps.project_tasks(project.id)[0]

        assert cached_task.get('pct_status') == 0.5, cached_task.get('pct_status')


    def test_n_task_taskruns_returns_0_no_taskruns(self):
        """Test CACHE PROJECTS n_task_taskruns returns 0 for a task with no
        contributions"""

        project = AppFactory.create()
        task = TaskFactory.create(app=project)

        n_taskruns = cached_apps.n_task_taskruns(task.id)

        assert n_taskruns == 0, n_taskruns


    def test_n_task_taskruns_returns_number_of_taskruns(self):
        """Test CACHE PROJECTS n_task_taskruns returns 0 for a task with no
        contributions"""

        project = AppFactory.create()
        task = TaskFactory.create(app=project)
        TaskRunFactory.create_batch(2, task=task)

        n_taskruns = cached_apps.n_task_taskruns(task.id)

        assert n_taskruns == 2, n_taskruns
