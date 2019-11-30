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

import datetime
from default import db, Test, with_context
from pybossa.cache import site_stats as stats
from factories import (UserFactory, ProjectFactory, AnonymousTaskRunFactory,
                       TaskRunFactory, TaskFactory)
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
        two_days_ago = (datetime.datetime.utcnow() -
                        datetime.timedelta(2)).isoformat()

        tr = TaskRunFactory.create(project=recently_contributed_project)
        tr = TaskRunFactory.create(
            project=long_ago_contributed_project, finish_time=two_days_ago)

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
            assert field in list(top5[0].keys())

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
        two_days_ago = (datetime.datetime.utcnow() -
                        datetime.timedelta(2)).isoformat()

        TaskRunFactory.create(user=recently_contributing_user)
        TaskRunFactory.create(
            user=long_ago_contributing_user, finish_time=two_days_ago)

        top5 = stats.get_top5_users_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert recently_contributing_user.id in top5_ids
        assert long_ago_contributing_user.id not in top5_ids
