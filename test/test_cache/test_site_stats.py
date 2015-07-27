# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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

import datetime
from default import Test
from pybossa.cache import site_stats as stats
from factories import (UserFactory, ProjectFactory, AnonymousTaskRunFactory,
    TaskRunFactory, TaskFactory)


class TestSiteStatsCache(Test):

    def test_n_auth_users_returns_number_of_registered_users(self):
        UserFactory.create_batch(2)
        users = stats.n_auth_users()

        assert users == 2, users

    def test_n_anon_users_returns_number_of_distinct_anonymous_contributors(self):
        AnonymousTaskRunFactory.create(user_ip="1.1.1.1")
        AnonymousTaskRunFactory.create(user_ip="1.1.1.1")
        AnonymousTaskRunFactory.create(user_ip="2.2.2.2")

        anonymous_users = stats.n_anon_users()

        assert anonymous_users == 2, anonymous_users

    def test_n_tasks_site_returns_number_of_total_tasks(self):
        TaskFactory.create_batch(2)

        tasks = stats.n_tasks_site()

        assert tasks == 2, tasks

    def test_n_total_tasks_site_returns_aggregated_number_of_required_tasks(self):
        TaskFactory.create(n_answers=2)
        TaskFactory.create(n_answers=2)

        tasks = stats.n_total_tasks_site()

        assert tasks == 4, tasks

    def test_n_total_task_runs_site_returns_total_number_of_answers(self):
        AnonymousTaskRunFactory.create()
        TaskRunFactory.create()

        task_runs = stats.n_task_runs_site()

        assert task_runs == 2, task_runs

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

    def test_get_top5_projects_24_hours_does_not_include_hidden_projects(self):
        good_project = ProjectFactory.create()
        best_but_hidden_project = ProjectFactory.create(hidden=1)

        TaskRunFactory.create(project=good_project)
        TaskRunFactory.create_batch(2, project=best_but_hidden_project)

        top5 = stats.get_top5_projects_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert good_project.id in top5_ids
        assert best_but_hidden_project.id not in top5_ids

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

    def test_get_top5_projects_24_hours_returns_required_fields(self):
        fields = ('id', 'name', 'short_name', 'info', 'n_answers')
        TaskRunFactory.create()

        top5 = stats.get_top5_projects_24_hours()

        for field in fields:
            assert field in top5[0].keys()

    def test_get_top5_users_24_hours_returns_best_5_users_only(self):
        users = UserFactory.create_batch(5)
        i = 5
        for user in users:
            TaskRunFactory.create_batch(i, user=user)
            i -= 1

        worst_user = UserFactory.create()

        top5 = stats.get_top5_users_24_hours()
        top5_ids = [top['id'] for top in top5]

        assert len(top5) == 5
        assert worst_user.id not in top5_ids
        for i in range(len(top5)):
            assert users[i].id == top5_ids[i]

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
