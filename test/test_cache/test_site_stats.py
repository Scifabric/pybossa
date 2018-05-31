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
# along with PYBOSSA.  If not,  see <http://www.gnu.org/licenses/>.

import datetime
from default import db, Test, with_context
from pybossa.cache import site_stats as stats
from factories import (UserFactory, ProjectFactory, AnonymousTaskRunFactory,
                       TaskRunFactory, TaskFactory, CategoryFactory)
from pybossa.repositories import ResultRepository
from mock import patch, Mock

result_repo = ResultRepository(db)


class TestSiteStatsCache(Test):

    @with_context
    def create_result(self, n_results=1, n_answers=1, owner=None,
                      filter_by=False):
        if owner:
            owner = owner
        else:
            owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        tasks = []
        for i in range(n_results):
            tasks.append(TaskFactory.create(n_answers=n_answers,
                                            project=project))
        for i in range(n_answers):
            for task in tasks:
                TaskRunFactory.create(task=task, project=project)
        if filter_by:
            return result_repo.filter_by(project_id=1)
        else:
            return result_repo.get_by(project_id=1)

    @with_context
    def test_n_auth_users_returns_number_of_registered_users(self):
        UserFactory.create_batch(2)
        users = stats.n_auth_users()

        assert users == 2, users

    @with_context
    def test_n_anon_users_returns_number_of_distinct_anonymous_contributors(self):
        AnonymousTaskRunFactory.create(user_ip="1.1.1.1")
        AnonymousTaskRunFactory.create(user_ip="1.1.1.1")
        AnonymousTaskRunFactory.create(user_ip="2.2.2.2")

        anonymous_users = stats.n_anon_users()

        assert anonymous_users == 2, anonymous_users

    @with_context
    def test_n_tasks_site_returns_number_of_total_tasks(self):
        TaskFactory.create_batch(2)

        tasks = stats.n_tasks_site()

        assert tasks == 2, tasks

    @with_context
    def test_n_total_tasks_site_returns_aggregated_number_of_required_tasks(self):
        TaskFactory.create(n_answers=2)
        TaskFactory.create(n_answers=2)

        tasks = stats.n_total_tasks_site()

        assert tasks == 4, tasks

    @with_context
    def test_n_total_task_runs_site_returns_total_number_of_answers(self):
        AnonymousTaskRunFactory.create()
        TaskRunFactory.create()

        task_runs = stats.n_task_runs_site()

        assert task_runs == 2, task_runs

    @with_context
    def test_n_results_site_returns_zero_results_when_no_info(self):
        n_results = stats.n_results_site()

        assert n_results == 0, n_results

        self.create_result()
        n_results = stats.n_results_site()

        assert n_results == 0, n_results

        self.create_result(n_results=2)
        n_results = stats.n_results_site()

        assert n_results == 0, n_results

    @with_context
    def test_n_results_site_returns_valid_results_with_info(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(n_answers=1, project=project)
        TaskRunFactory.create(task=task, project=project)
        result = result_repo.get_by(project_id=project.id)
        result.info = dict(foo='bar')
        result_repo.update(result)
        n_results = stats.n_results_site()

        assert n_results == 1, n_results

        project = ProjectFactory.create()
        task = TaskFactory.create(n_answers=1, project=project)
        TaskRunFactory.create(task=task, project=project)
        result = result_repo.get_by(project_id=project.id)
        result.info = dict(foo='bar2')
        result_repo.update(result)
        n_results = stats.n_results_site()

        assert n_results == 2, n_results

        self.create_result(n_results=10)

        assert n_results == 2, n_results

    @with_context
    def test_get_top5_projects_24_hours_returns_best_5_only(self):
        projects = ProjectFactory.create_batch(5)
        i = 5
        for project in projects:
            TaskRunFactory.create_batch(i, project=project)
            i -= 1

        worst_project = ProjectFactory.create()

        top5 = stats.get_top5_projects_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert len(top5) == 5
        assert worst_project.id not in top5_ids
        for i in range(len(top5)):
            assert projects[i].id == top5_ids[i]

    @with_context
    def test_get_top5_projects_24_hours_considers_last_24_hours_contributions_only(self):
        recently_contributed_project = ProjectFactory.create()
        long_ago_contributed_project = ProjectFactory.create()
        two_days_ago = (datetime.datetime.utcnow() -  datetime.timedelta(2)).isoformat()

        TaskRunFactory.create(project=recently_contributed_project)
        TaskRunFactory.create(project=long_ago_contributed_project, finish_time=two_days_ago)

        top5 = stats.get_top5_projects_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert recently_contributed_project.id in top5_ids
        assert long_ago_contributed_project.id not in top5_ids

    @with_context
    def test_get_top5_projects_24_hours_returns_required_fields(self):
        fields = ('id', 'name', 'short_name', 'info', 'n_answers')
        TaskRunFactory.create()

        top5 = stats.get_top5_projects_24_hours()

        for field in fields:
            assert field in top5[0].keys()

    @with_context
    def test_get_top5_users_24_hours_returns_best_5_users_only(self):
        users = UserFactory.create_batch(4)
        restricted = UserFactory.create(restrict=True)
        users.append(restricted)
        i = 5
        for user in users:
            TaskRunFactory.create_batch(i, user=user)
            i -= 1

        worst_user = UserFactory.create()

        top5 = stats.get_top5_users_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert len(top5) == 4, len(top5)
        assert worst_user.id not in top5_ids
        for i in range(len(top5)):
            assert users[i].id == top5_ids[i]
            assert users[i].restrict is False
            assert users[i].id != restricted.id

    @with_context
    def test_get_top5_users_24_hours_considers_last_24_hours_contributions_only(self):
        recently_contributing_user = UserFactory.create()
        long_ago_contributing_user = UserFactory.create()
        two_days_ago = (datetime.datetime.utcnow() -  datetime.timedelta(2)).isoformat()

        TaskRunFactory.create(user=recently_contributing_user)
        TaskRunFactory.create(user=long_ago_contributing_user, finish_time=two_days_ago)

        top5 = stats.get_top5_users_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert recently_contributing_user.id in top5_ids
        assert long_ago_contributing_user.id not in top5_ids

    @with_context
    def test_number_of_created_jobs(self):
        """Test number of projects created in last 30 days"""
        date_now = datetime.datetime.utcnow()
        date_60_days_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()
        projects = ProjectFactory.create_batch(5, created=date_now)
        old_project = ProjectFactory.create(created=date_60_days_old)
        total_projects = stats.number_of_created_jobs()
        assert total_projects == 5, "Total number of projects created in last 30 days should be 5"

    @with_context
    def test_number_of_active_jobs(self):
        """Test number of active projects with submissions in last 30 days"""
        recently_contributed_project = ProjectFactory.create()
        long_ago_contributed_project = ProjectFactory.create()
        date_60_days_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()

        recently_contributed_project = ProjectFactory.create()
        long_ago_contributed_project = ProjectFactory.create()

        TaskRunFactory.create(project=recently_contributed_project)
        TaskRunFactory.create(project=long_ago_contributed_project, finish_time=date_60_days_old)

        total_active_projects = stats.number_of_active_jobs()
        assert total_active_projects == 1, "Total number of active projects in last 30 days should be 1"

        all_projects = stats.number_of_active_jobs(days='all')
        assert all_projects == 2, "Total number of all projects should be 2"

    @with_context
    def test_number_of_created_tasks(self):
        """Test number of tasks created in last 30 days"""
        date_60_days_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()

        TaskFactory.create()
        TaskFactory.create()
        TaskFactory.create(created=date_60_days_old)
        tasks = stats.number_of_created_tasks()

        assert tasks == 2, "Total number tasks created in last 30 days should be 2"

    @with_context
    def test_number_of_completed_tasks(self):
        """Test number of tasks completed in last 30 days"""
        date_now = datetime.datetime.utcnow()
        date_60_days_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()

        recent_project = ProjectFactory.create(created=date_now)
        old_project = ProjectFactory.create(created=date_60_days_old)

        # recent tasks completed
        recent_taskruns = 5
        for i in range(recent_taskruns):
            task = TaskFactory.create(n_answers=1, project=recent_project, created=date_now)
            TaskRunFactory.create(task=task, project=recent_project, finish_time=date_now)

        # old tasks completed
        for i in range(3):
            task = TaskFactory.create(n_answers=1, project=old_project, created=date_60_days_old)
            TaskRunFactory.create(task=task, project=recent_project, finish_time=date_60_days_old)

        total_tasks = stats.number_of_completed_tasks()
        assert total_tasks == recent_taskruns, "Total completed tasks in last 30 days should be {}".format(recent_taskruns)

    @with_context
    def test_number_of_active_users(self):
        """Test number of active users in last 30 days"""
        date_now = datetime.datetime.utcnow()
        date_60_days_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()

        recent_users = 4
        users = UserFactory.create_batch(recent_users)
        i = recent_users
        for user in users:
            TaskRunFactory.create_batch(i, user=user, finish_time=date_now)
            i -= 1

        old_user = UserFactory.create()
        TaskRunFactory.create(user=old_user, finish_time=date_60_days_old)

        total_users = stats.number_of_active_users()
        assert total_users == recent_users, "Total active users in last 30 days should be {}".format(recent_users)

    @with_context
    def test_get_categories_with_recent_projects(self):
        """Test categories with projects created in last 30 days"""
        date_now = datetime.datetime.utcnow()
        date_60_days_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()

        categories = CategoryFactory.create_batch(3)
        unused_category = CategoryFactory.create()

        ProjectFactory.create(category=categories[0], created=date_now)
        ProjectFactory.create(category=categories[1], created=date_now)
        ProjectFactory.create(category=categories[0], created=date_now)

        ProjectFactory.create(category=categories[2], created=date_60_days_old)
        total_categories = stats.categories_with_new_projects()
        assert total_categories == 2, "Total categories with recent projects should be 2"

    @with_context
    def test_avg_task_per_job(self):
        """Test average task per job created since current time"""
        date_recent = (datetime.datetime.utcnow() -  datetime.timedelta(29)).isoformat()
        date_old = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()
        date_now = datetime.datetime.utcnow().isoformat()
        expected_avg_tasks = 5

        project = ProjectFactory.create(created=date_recent)
        old_project = ProjectFactory.create(created=date_old)

        TaskFactory.create_batch(5, n_answers=1, project=project, created=date_now)
        TaskFactory.create_batch(5, n_answers=1, project=old_project, created=date_old)

        avg_tasks = stats.avg_task_per_job()
        assert avg_tasks == expected_avg_tasks, "Average task created per job should be {}".format(expected_avg_tasks)

    @with_context
    def test_avg_time_to_complete_task(self):
        """Test average time to complete tasks in last 30 days"""
        date_15m_old = (datetime.datetime.utcnow() -  datetime.timedelta(minutes=15)).isoformat()
        date_now = datetime.datetime.utcnow()

        expected_avg_time = '15m 00s'
        for i in range(5):
            TaskRunFactory.create(created=date_15m_old, finish_time=date_now)

        avg_time = stats.avg_time_to_complete_task()
        assert avg_time == expected_avg_time, \
            "Average time to complete tasks in last 30 days should be {}".format(expected_avg_time)

    @with_context
    def test_avg_tasks_per_category(self):
        """Test average tasks per category created since current time"""
        date_recent = (datetime.datetime.utcnow() -  datetime.timedelta(31)).isoformat()
        date_now = (datetime.datetime.utcnow() -  datetime.timedelta(1)).isoformat()
        expected_avg_tasks = 3

        categories = CategoryFactory.create_batch(3)
        project1 = ProjectFactory.create(category=categories[0], created=date_now)
        project2 = ProjectFactory.create(category=categories[1], created=date_recent)
        project3 = ProjectFactory.create(category=categories[2], created=date_recent)

        for i in range(5):
            TaskFactory.create(project=project1, created=date_now)

        for i in range(2):
            TaskFactory.create(project=project2, created=date_recent)

        for i in range(3):
            TaskFactory.create(project=project3, created=date_recent)

        avg_tasks = round(stats.tasks_per_category())
        assert avg_tasks == expected_avg_tasks, "Average tasks created per category should be {}".format(expected_avg_tasks)

    @with_context
    def test_charts(self):
        """Test project chart"""
        date_old = (datetime.datetime.utcnow() -  datetime.timedelta(30*36)).isoformat()
        date_4_mo = (datetime.datetime.utcnow() -  datetime.timedelta(120)).isoformat()
        date_3_mo = (datetime.datetime.utcnow() -  datetime.timedelta(90)).isoformat()
        date_2_mo = (datetime.datetime.utcnow() -  datetime.timedelta(60)).isoformat()
        date_1_mo = (datetime.datetime.utcnow() -  datetime.timedelta(30)).isoformat()
        expected_tasks = 6
        expected_categories = 2
        expected_projects = 4
        expected_taskruns = 5

        CategoryFactory.create(created=date_1_mo)
        CategoryFactory.create(created=date_2_mo)
        CategoryFactory.create(created=date_3_mo)

        ProjectFactory.create(created=date_1_mo)
        ProjectFactory.create(created=date_2_mo)
        ProjectFactory.create(created=date_3_mo)
        ProjectFactory.create(created=date_4_mo)
        ProjectFactory.create(created=date_old)

        TaskFactory.create(created=date_1_mo)
        TaskFactory.create(created=date_2_mo)
        TaskFactory.create(created=date_3_mo)

        TaskRunFactory.create(created=date_1_mo)
        TaskRunFactory.create(created=date_2_mo)
        TaskRunFactory.create(created=date_3_mo)
        TaskRunFactory.create(created=date_4_mo)
        TaskRunFactory.create(created=date_old)

        projects = stats.project_chart()
        assert projects['series'][0][24] == expected_projects, "{} projects created in last 24 months".format(expected_projects)
        categories = stats.category_chart()
        assert categories['series'][0][24] == expected_categories, "{} categories created in last 24 months".format(expected_categories)
        tasks = stats.task_chart()
        assert tasks['series'][0][24] == expected_tasks, "{} tasks created in last 24 months".format(expected_tasks)
        taskruns = stats.submission_chart()
        assert taskruns['series'][0][24] == expected_taskruns, "{} taskruns created in last 24 months".format(expected_taskruns)
