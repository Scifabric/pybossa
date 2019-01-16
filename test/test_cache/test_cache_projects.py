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

from default import Test, with_context
from pybossa.cache import projects as cached_projects
from factories import UserFactory, ProjectFactory, TaskFactory, \
    TaskRunFactory, AnonymousTaskRunFactory
from mock import patch
import datetime
from pybossa.core import result_repo
from pybossa.model.project import Project
from pybossa.cache.project_stats import update_stats


class TestProjectsCache(Test):


    def create_project_with_tasks(self, completed_tasks, ongoing_tasks):
        project = ProjectFactory.create()
        TaskFactory.create_batch(completed_tasks, state='completed', project=project)
        TaskFactory.create_batch(ongoing_tasks, state='ongoing', project=project)
        return project

    def create_project_with_contributors(self, anonymous, registered,
                                     two_tasks=False, name='my_app', info={}):
        project = ProjectFactory.create(name=name, info=info)
        task = TaskFactory(project=project)
        if two_tasks:
            task2 = TaskFactory(project=project)
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
        return project


    @with_context
    def test_get_featured_only_returns_featured(self):
        """Test CACHE PROJECTS get_featured returns only featured projects"""

        featured_project = ProjectFactory.create(featured=True)
        non_featured_project = ProjectFactory.create()

        featured = cached_projects.get_featured()

        assert len(featured) is 1, featured


    @with_context
    def test_get_featured_returns_required_fields(self):
        """Test CACHE PROJECTS get_featured returns the required info
        about each featured project"""

        fields = ('id', 'name', 'short_name', 'info', 'created', 'description',
                  'last_activity', 'last_activity_raw', 'overall_progress',
                  'n_tasks', 'n_volunteers', 'owner', 'info', 'updated')

        ProjectFactory.create(featured=True)

        featured = cached_projects.get_featured()[0]

        for field in fields:
            assert field in featured, "%s not in project info" % field


    @with_context
    def test_get_only_return_published(self):
        """Test CACHE PROJECTS get returns only published projects"""

        project = ProjectFactory.create(published=True)
        ProjectFactory.create(category=project.category, published=False)
        projects = cached_projects.get(project.category.short_name)

        assert len(projects) is 1, projects


    @with_context
    def test_get_dont_return_projects_with_password(self):
        """Test CACHE PROJECTS get does not return projects with a password"""

        project = ProjectFactory.create(published=True, info={'passwd_hash': '2'})
        ProjectFactory.create(category=project.category, published=True)
        projects = cached_projects.get(project.category.short_name)

        assert len(projects) is 1, projects


    @with_context
    def test_get_only_returns_projects_from_category(self):
        """Test CACHE PROJECTS get returns only projects from required category"""

        project = ProjectFactory.create(published=True)
        ProjectFactory.create(published=True)

        projects = cached_projects.get(project.category.short_name)

        assert len(projects) is 1, projects


    @with_context
    def test_get_returns_required_fields(self):
        """Test CACHE PROJECTS get returns the required info
        about each project"""

        fields = ('id', 'name', 'short_name', 'info', 'created', 'description',
                  'last_activity', 'last_activity_raw', 'overall_progress',
                  'n_tasks', 'n_volunteers', 'owner', 'info', 'updated')

        project = ProjectFactory.create(published=True)

        retrieved_project = cached_projects.get(project.category.short_name)[0]

        for field in fields:
            assert field in retrieved_project, "%s not in project info" % field


    @with_context
    def test_get_draft_not_returns_published_projects(self):
        """Test CACHE PROJECTS get_draft does not return published projects"""

        published = ProjectFactory.create(published=True)

        drafts = cached_projects.get_draft()

        assert len(drafts) is 0, drafts


    @with_context
    def test_get_draft_returns_required_fields(self):
        """Test CACHE PROJECTS get_draft returns the required info
        about each project"""

        fields = Project().public_attributes()

        ProjectFactory.create(published=False)

        draft = cached_projects.get_draft()[0]

        for field in fields:
            assert field in draft, "%s not in project info" % field
            if field == 'info':
                assert sorted(draft['info'].keys()) == sorted(Project().public_info_keys())


    @with_context
    def test_get_top_returns_projects_with_most_taskruns(self):
        """Test CACHE PROJECTS get_top returns the projects with most taskruns in order"""

        rankded_3_project = self.create_project_with_contributors(8, 0, name='three')
        ranked_2_project = self.create_project_with_contributors(9, 0, name='two')
        ranked_1_project = self.create_project_with_contributors(10, 0, name='one')
        ranked_4_project = self.create_project_with_contributors(7, 0, name='four')

        top_projects = cached_projects.get_top()

        assert top_projects[0]['name'] == 'one', top_projects
        assert top_projects[1]['name'] == 'two', top_projects
        assert top_projects[2]['name'] == 'three', top_projects
        assert top_projects[3]['name'] == 'four', top_projects


    @with_context
    def test_get_top_respects_limit(self):
        """Test CACHE PROJECTS get_top returns only the top n projects"""

        ranked_3_project = self.create_project_with_contributors(8, 0, name='three')
        ranked_2_project = self.create_project_with_contributors(9, 0, name='two')
        ranked_1_project = self.create_project_with_contributors(10, 0, name='one')

        top_projects = cached_projects.get_top(n=2)

        assert len(top_projects) is 2, len(top_projects)


    @with_context
    def test_get_top_returns_only_projects_without_password(self):
        """Test CACHE PROJECTS get_top returns projects that don't have a password"""

        ranked_2_project = self.create_project_with_contributors(9, 0, name='two')
        ranked_1_project = self.create_project_with_contributors(
            10, 0, name='one', info={'passwd_hash': 'something'})

        top_projects = cached_projects.get_top()

        assert len(top_projects) is 1, len(top_projects)


    @with_context
    def test_n_completed_tasks_no_completed_tasks(self):
        """Test CACHE PROJECTS n_completed_tasks returns 0 if no completed tasks"""

        project = self.create_project_with_tasks(completed_tasks=0, ongoing_tasks=5)
        completed_tasks = cached_projects.n_completed_tasks(project.id)

        err_msg = "Completed tasks is %s, it should be 0" % completed_tasks
        assert completed_tasks == 0, err_msg


    @with_context
    def test_n_completed_tasks_with_completed_tasks(self):
        """Test CACHE PROJECTS n_completed_tasks returns number of completed tasks
        if there are any"""

        project = self.create_project_with_tasks(completed_tasks=5, ongoing_tasks=5)
        completed_tasks = cached_projects.n_completed_tasks(project.id)

        err_msg = "Completed tasks is %s, it should be 5" % completed_tasks
        assert completed_tasks == 5, err_msg


    @with_context
    def test_n_completed_tasks_with_all_tasks_completed(self):
        """Test CACHE PROJECTS n_completed_tasks returns number of tasks if all
        tasks are completed"""

        project = self.create_project_with_tasks(completed_tasks=4, ongoing_tasks=0)
        completed_tasks = cached_projects.n_completed_tasks(project.id)

        err_msg = "Completed tasks is %s, it should be 4" % completed_tasks
        assert completed_tasks == 4, err_msg


    @with_context
    def test_n_tasks_returns_number_of_total_tasks(self):
        project = self.create_project_with_tasks(completed_tasks=1, ongoing_tasks=1)

        tasks = cached_projects.n_tasks(project.id)

        assert tasks == 2, tasks


    @with_context
    def test_n_task_runs_returns_number_of_total_taskruns(self):
        project = self.create_project_with_contributors(anonymous=1, registered=1)

        taskruns = cached_projects.n_task_runs(project.id)

        assert taskruns == 2, taskruns


    @with_context
    def test_n_results_returns_number_of_total_results(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(n_answers=1, project=project)
        TaskRunFactory.create(task=task, project=project)

        results = cached_projects.n_results(project.id)

        assert results == 0, results

        result = result_repo.get_by(project_id=project.id)

        result.info = dict(foo='bar')

        result_repo.update(result)

        results = cached_projects.n_results(project.id)

        assert results == 1, results


    @with_context
    def test_n_registered_volunteers(self):
        """Test CACHE PROJECTS n_registered_volunteers returns number of volunteers
        that contributed to a project when each only submited one task run"""

        project = self.create_project_with_contributors(anonymous=0, registered=3)
        registered_volunteers = cached_projects.n_registered_volunteers(project.id)

        err_msg = "Volunteers is %s, it should be 3" % registered_volunteers
        assert registered_volunteers == 3, err_msg


    @with_context
    def test_n_registered_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE PROJECTS n_registered_volunteers returns number of volunteers
        that contributed to a project when any submited more than one task run"""

        project = self.create_project_with_contributors(anonymous=0, registered=2, two_tasks=True)
        registered_volunteers = cached_projects.n_registered_volunteers(project.id)

        err_msg = "Volunteers is %s, it should be 2" % registered_volunteers
        assert registered_volunteers == 2, err_msg


    @with_context
    def test_n_anonymous_volunteers(self):
        """Test CACHE PROJECTS n_anonymous_volunteers returns number of volunteers
        that contributed to a project when each only submited one task run"""

        project = self.create_project_with_contributors(anonymous=3, registered=0)
        anonymous_volunteers = cached_projects.n_anonymous_volunteers(project.id)

        err_msg = "Volunteers is %s, it should be 3" % anonymous_volunteers
        assert anonymous_volunteers == 3, err_msg


    @with_context
    def test_n_anonymous_volunteers_with_more_than_one_taskrun(self):
        """Test CACHE PROJECTS n_anonymous_volunteers returns number of volunteers
        that contributed to a project when any submited more than one task run"""

        project = self.create_project_with_contributors(anonymous=2, registered=0, two_tasks=True)
        anonymous_volunteers = cached_projects.n_anonymous_volunteers(project.id)

        err_msg = "Volunteers is %s, it should be 2" % anonymous_volunteers
        assert anonymous_volunteers == 2, err_msg


    @with_context
    def test_n_volunteers(self):
        """Test CACHE PROJECTS n_volunteers returns the sum of the anonymous
        plus registered volunteers that contributed to a project"""

        project = self.create_project_with_contributors(anonymous=2, registered=3, two_tasks=True)
        total_volunteers = cached_projects.n_volunteers(project.id)

        err_msg = "Volunteers is %s, it should be 5" % total_volunteers
        assert total_volunteers == 5, err_msg


    @with_context
    def test_n_draft_no_drafts(self):
        """Test CACHE PROJECTS _n_draft returns 0 if there are no draft projects"""
        project = ProjectFactory.create(published=True)

        number_of_drafts = cached_projects._n_draft()

        assert number_of_drafts == 0, number_of_drafts


    @with_context
    def test_n_draft_with_drafts(self):
        """Test CACHE PROJECTS _n_draft returns 2 if there are 2 draft projects"""
        ProjectFactory.create_batch(2, published=False)

        number_of_drafts = cached_projects._n_draft()

        assert number_of_drafts == 2, number_of_drafts


    @with_context
    def test_browse_tasks_returns_no_tasks(self):
        """Test CACHE PROJECTS browse_tasks returns an empty list if a project
        has no tasks"""

        project = ProjectFactory.create()

        browse_tasks = cached_projects.browse_tasks(project.id)

        assert browse_tasks == [], browse_tasks


    @with_context
    def test_browse_tasks_returns_all_tasks(self):
        """Test CACHE PROJECTS browse_tasks returns a list with all the tasks
        from a given project"""

        project = ProjectFactory.create()
        TaskFactory.create_batch(2, project=project)

        browse_tasks = cached_projects.browse_tasks(project.id)

        assert len(browse_tasks) == 2, browse_tasks


    @with_context
    def test_browse_tasks_returns_required_attributes(self):
        """Test CACHE PROJECTS browse_tasks returns a list with objects
        with the required task attributes"""

        project = ProjectFactory.create()
        task = TaskFactory.create( project=project, info={})
        attributes = ('id', 'n_answers')

        cached_task = cached_projects.browse_tasks(project.id)[0]

        for attr in attributes:
            assert cached_task.get(attr) == getattr(task, attr), attr


    @with_context
    def test_browse_tasks_returns_pct_status(self):
        """Test CACHE PROJECTS browse_tasks returns also the completion
        percentage of each task"""

        project = ProjectFactory.create()
        task = TaskFactory.create( project=project, info={}, n_answers=4)

        cached_task = cached_projects.browse_tasks(project.id)[0]
        # 0 if no task runs
        assert cached_task.get('pct_status') == 0, cached_task.get('pct_status')

        TaskRunFactory.create(task=task)
        cached_task = cached_projects.browse_tasks(project.id)[0]
        # Gets updated with new task runs
        assert cached_task.get('pct_status') == 0.25, cached_task.get('pct_status')

        TaskRunFactory.create_batch(3, task=task)
        cached_task = cached_projects.browse_tasks(project.id)[0]
        # To a maximum of 1
        assert cached_task.get('pct_status') == 1.0, cached_task.get('pct_status')

        TaskRunFactory.create(task=task)
        cached_task = cached_projects.browse_tasks(project.id)[0]
        # And it does not go over 1 (that is 100%!!)
        assert cached_task.get('pct_status') == 1.0, cached_task.get('pct_status')


    @with_context
    def test_n_featured_returns_nothing(self):
        """Test CACHE PROJECTS _n_featured 0 if there are no featured projects"""
        number_of_featured = cached_projects._n_featured()

        assert number_of_featured == 0, number_of_featured


    @with_context
    def test_n_featured_returns_featured(self):
        """Test CACHE PROJECTS _n_featured returns number of featured projects"""
        ProjectFactory.create(featured=True)

        number_of_featured = cached_projects._n_featured()

        assert number_of_featured == 1, number_of_featured


    @with_context
    @patch('pybossa.cache.pickle')
    @patch('pybossa.cache.projects._n_draft')
    def test_n_count_calls_n_draft(self, _n_draft, pickle):
        """Test CACHE PROJECTS n_count calls _n_draft when called with argument
        'draft'"""
        pickle.dumps.return_value = 'str'
        cached_projects.n_count('draft')

        _n_draft.assert_called_with()


    @with_context
    @patch('pybossa.cache.pickle')
    @patch('pybossa.cache.projects._n_featured')
    def test_n_count_calls_n_featuredt(self, _n_featured, pickle):
        """Test CACHE PROJECTS n_count calls _n_featured when called with
        argument 'featured'"""
        pickle.dumps.return_value = 'str'
        cached_projects.n_count('featured')

        _n_featured.assert_called_with()


    @with_context
    def test_n_count_with_different_category(self):
        """Test CACHE PROJECTS n_count returns 0 if there are no published
        projects from requested category"""
        project = self.create_project_with_tasks(1, 0)

        n_projects = cached_projects.n_count('nocategory')

        assert n_projects == 0, n_projects


    @with_context
    def test_n_count_with_published_projects(self):
        """Test CACHE PROJECTS n_count returns the number of published projects
        of a given category"""
        project = ProjectFactory.create(published=True)
        ProjectFactory.create(published=True)
        ProjectFactory.create(category=project.category, published=False)

        n_projects = cached_projects.n_count(project.category.short_name)

        assert n_projects == 1, n_projects


    @with_context
    def test_n_count_with_password_protected_projects(self):
        """Test CACHE PROJECTS n_count returns the number of published projects
        of a given category, excluding projects with a password"""
        project = ProjectFactory.create(published=True, info={'passwd_hash': '2'})
        ProjectFactory.create(category=project.category, published=True)

        n_projects = cached_projects.n_count(project.category.short_name)

        assert n_projects == 1, n_projects


    @with_context
    def test_get_from_pro_user_projects_no_projects(self):
        """Test CACHE PROJECTS get_from_pro_user returns empty list if no projects
        with 'pro' owners"""
        pro_user = UserFactory.create(pro=True)
        ProjectFactory.create()

        pro_owned_projects = cached_projects.get_from_pro_user()

        assert pro_owned_projects == [], pro_owned_projects


    @with_context
    def test_get_from_pro_user_projects(self):
        """Test CACHE PROJECTS get_from_pro_user returns list of projects with
        'pro' owners only"""
        pro_user = UserFactory.create(pro=True)
        ProjectFactory.create()
        pro_project = ProjectFactory.create(owner=pro_user)

        pro_owned_projects = cached_projects.get_from_pro_user()

        assert len(pro_owned_projects) is 1, len(pro_owned_projects)
        assert pro_owned_projects[0]['short_name'] == pro_project.short_name


    @with_context
    def test_get_from_pro_users_returns_required_fields(self):
        """Test CACHE PROJECTS get_from_pro_user returns required fields"""
        pro_user = UserFactory.create(pro=True)
        ProjectFactory.create(owner=pro_user)
        fields = ('id', 'short_name')

        pro_owned_projects = cached_projects.get_from_pro_user()

        for field in fields:
            assert field in list(pro_owned_projects[0].keys()), field


    @with_context
    def test_overall_progress_returns_0_if_no_tasks(self):
        project = ProjectFactory.create()

        progress = cached_projects.overall_progress(project.id)

        assert progress == 0, progress


    @with_context
    def test_overall_progres_returns_actual_progress_percentage(self):
        total_tasks = 4
        completed_tasks = 2
        project = self.create_project_with_tasks(
                            completed_tasks=completed_tasks,
                            ongoing_tasks=total_tasks-completed_tasks)

        progress = cached_projects.overall_progress(project.id)

        assert progress == 50, progress


    @with_context
    def test_last_activity_returns_None_if_no_contributions(self):
        project = ProjectFactory.create()

        activity = cached_projects.last_activity(project.id)

        assert activity is None, activity


    @with_context
    def test_last_activity_returns_date_of_latest_contribution(self):
        project = ProjectFactory.create()
        first_task_run = TaskRunFactory.create(project=project)
        last_task_run = TaskRunFactory.create(project=project)

        activity = cached_projects.last_activity(project.id)

        assert activity == last_task_run.finish_time, last_task_run


    @with_context
    def test_n_published_counts_published_projects(self):
        published_project = ProjectFactory.create_batch(2, published=True)
        ProjectFactory.create(published=False)

        number_of_published = cached_projects.n_published()

        assert number_of_published == 2, number_of_published


    @with_context
    def test_average_contribution_time_returns_0_if_no_contributions(self):
        project = ProjectFactory.create()

        average_time = cached_projects.average_contribution_time(project.id)

        assert average_time == 0, average_time

    @with_context
    def test_average_contribution_time_returns_average_contribution_time(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        first_task_time = datetime.timedelta(0, 5)
        second_task_time = datetime.timedelta(0, 7)
        expected_average_time = datetime.timedelta(0, 6)
        now = datetime.datetime.utcnow()
        TaskRunFactory.create(task=task, created=now, finish_time=now+first_task_time)
        TaskRunFactory.create(task=task, created=now, finish_time=now+second_task_time)
        update_stats(project.id)
        average_time = cached_projects.average_contribution_time(project.id)

        assert average_time == expected_average_time.total_seconds(), average_time
