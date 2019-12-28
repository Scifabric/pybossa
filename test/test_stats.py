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
import time
from factories import ProjectFactory, TaskFactory, TaskRunFactory, AnonymousTaskRunFactory
from default import Test, with_context
from pybossa.model.task_run import TaskRun
import pybossa.cache.project_stats as stats
from pybossa.core import user_repo


class TestStats(Test):

    def prepare_data(self):
        self.project = ProjectFactory.create()
        for task in TaskFactory.create_batch(4, project=self.project, n_answers=3):
            TaskRunFactory.create(task=task)
            AnonymousTaskRunFactory.create(task=task)

    @with_context
    def test_stats_dates_no_completed_tasks_on_different_days(self):
        """Test STATS stats_dates with no completed tasks"""
        self.prepare_data()
        today = str(datetime.date.today())
        dates, dates_anon, dates_auth = stats.stats_dates(self.project.id)
        assert len(list(dates.keys())) == 15, "There should be 15 days."
        for d in list(dates.keys()):
            if d == today:
                assert dates[d] == 4, "There should be 4 completed tasks."
            else:
                assert dates[d] == 0, "There should be 0 completed tasks."
        assert dates_anon[today] == 4, dates_anon[today]
        assert dates_auth[today] == 4, dates_auth[today]

    @with_context
    def test_n_tasks_returns_total_number_tasks(self):
        """Test STATS n_tasks returns the total amount of tasks of the project"""
        self.prepare_data()
        assert stats.n_tasks(self.project.id) == 4, stats.n_tasks(self.project.id)

    @with_context
    def test_stats_dates_completed_tasks(self):
        """Test STATS stats_dates with tasks completed tasks"""
        self.prepare_data()
        today = str(datetime.date.today())
        TaskRunFactory.create(task=self.project.tasks[1])
        dates, dates_anon, dates_auth = stats.stats_dates(self.project.id)
        assert dates[today] == 4, dates
        assert dates_anon[today] == 4, dates_anon[today]
        assert dates_auth[today] == 5, dates_auth[today]

    @with_context
    def test_02_stats_hours(self):
        """Test STATS hours method works"""
        self.prepare_data()
        hour = str(datetime.datetime.utcnow().strftime('%H'))
        hours, hours_anon, hours_auth, max_hours,\
            max_hours_anon, max_hours_auth = stats.stats_hours(self.project.id)
        print(hours)
        for i in range(0, 24):
            # There should be only 8 answers at current hour
            if str(i).zfill(2) == hour:
                err_msg = "At time %s there should be 8 answers" \
                          "but there are %s" % (str(i).zfill(2),
                                                hours[str(i).zfill(2)])
                assert hours[str(i).zfill(2)] == 8, "There should be 8 answers"
            else:
                err_msg = "At time %s there should be 0 answers" \
                          "but there are %s" % (str(i).zfill(2),
                                                hours[str(i).zfill(2)])
                assert hours[str(i).zfill(2)] == 0, err_msg

            if str(i).zfill(2) == hour:
                tmp = (hours_anon[hour] + hours_auth[hour])
                assert tmp == 8, "There should be 8 answers"
            else:
                tmp = (hours_anon[str(i).zfill(2)] + hours_auth[str(i).zfill(2)])
                assert tmp == 0, "There should be 0 answers"
        err_msg = "It should be 8, as all answers are submitted in the same hour"
        assert max_hours == 8, err_msg
        assert (max_hours_anon + max_hours_auth) == 8, err_msg

    @with_context
    def test_03_stats(self):
        """Test STATS stats method works"""
        self.prepare_data()
        today = str(datetime.date.today())
        hour = int(datetime.datetime.utcnow().strftime('%H'))
        date_ms = time.mktime(time.strptime(today, "%Y-%m-%d")) * 1000
        anon = 0
        auth = 0
        tr1 = TaskRunFactory.create(task=self.project.tasks[0])
        tr2 = TaskRunFactory.create(task=self.project.tasks[1])
        user = user_repo.get(tr1.user_id)
        user.restrict = True
        user_repo.update(user)
        stats.update_stats(self.project.id)
        dates_stats, hours_stats, user_stats = stats.get_stats(self.project.id)
        for item in dates_stats:
            if item['label'] == 'Anon + Auth':
                assert item['values'][-1][0] == date_ms, item['values'][0][0]
                assert item['values'][-1][1] == 10, "There should be 10 answers"
            if item['label'] == 'Anonymous':
                assert item['values'][-1][0] == date_ms, item['values'][0][0]
                anon = item['values'][-1][1]
            if item['label'] == 'Authenticated':
                assert item['values'][-1][0] == date_ms, item['values'][0][0]
                auth = item['values'][-1][1]
            if item['label'] == 'Total Tasks':
                assert item['values'][-1][0] == date_ms, item['values'][0][0]
                assert item['values'][-1][1] == 4, "There should be 4 tasks"
            if item['label'] == 'Expected Answers':
                assert item['values'][0][0] == date_ms, item['values'][0][0]
                for i in item['values']:
                    assert i[1] == 100, "Each date should have 100 answers"
                assert item['values'][0][1] == 100, "There should be 10 answers"
        assert auth + anon == 10, "date stats sum of auth and anon should be 10"

        max_hours = 0
        for item in hours_stats:
            if item['label'] == 'Anon + Auth':
                max_hours = item['max']
                print(item)
                assert item['max'] == 10, item['max']
                assert item['max'] == 10, "Max hours value should be 10"
                for i in item['values']:
                    if i[0] == hour:
                        assert i[1] == 10, "There should be 10 answers"
                        assert i[2] == 5, "The size of the bubble should be 5"
                    else:
                        assert i[1] == 0, "There should be 0 answers"
                        assert i[2] == 0, "The size of the buggle should be 0"
            if item['label'] == 'Anonymous':
                anon = item['max']
                for i in item['values']:
                    if i[0] == hour:
                        assert i[1] == anon, "There should be anon answers"
                        assert i[2] == (anon * 5) / max_hours, "The size of the bubble should be 5"
                    else:
                        assert i[1] == 0, "There should be 0 answers"
                        assert i[2] == 0, "The size of the buggle should be 0"
            if item['label'] == 'Authenticated':
                auth = item['max']
                for i in item['values']:
                    if i[0] == hour:
                        assert i[1] == auth, "There should be anon answers"
                        assert i[2] == (auth * 5) / max_hours, "The size of the bubble should be 5"
                    else:
                        assert i[1] == 0, "There should be 0 answers"
                        assert i[2] == 0, "The size of the buggle should be 0"
        assert auth + anon == 10, "date stats sum of auth and anon should be 8"

        err_msg = "user stats sum of auth and anon should be 7"
        assert user_stats['n_anon'] + user_stats['n_auth'] == 7, err_msg
        for u in user_stats['auth']['top5']:
            assert u['restrict'] is False, u
