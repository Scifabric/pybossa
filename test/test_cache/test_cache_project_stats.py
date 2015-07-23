# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

from default import Test, with_context
from pybossa.cache.project_stats import *
from factories import UserFactory, ProjectFactory, TaskFactory, \
    TaskRunFactory, AnonymousTaskRunFactory
import pytz
from datetime import date, datetime, timedelta


class TestProjectsStatsCache(Test):

    def test_convert_period_to_days(self):
        """Test CACHE PROJECT STATS convert period to days works."""
        period = '7 day'
        res = convert_period_to_days(period)
        assert res == 7, res
        period = '1 week'
        res = convert_period_to_days(period)
        assert res == 7, res
        period = '1 month'
        res = convert_period_to_days(period)
        assert res == 30, res
        period = '1 year'
        res = convert_period_to_days(period)
        assert res == 365, res
        period = '1 wrong'
        res = convert_period_to_days(period)
        assert res == 0, res
        period = '1week'
        res = convert_period_to_days(period)
        assert res == 0, res

    def test_stats_users(self):
        """Test CACHE PROJECT STATS user stats works."""
        pr = ProjectFactory.create()
        TaskRunFactory.create(project=pr)
        AnonymousTaskRunFactory.create(project=pr)
        users, anon_users, auth_users = stats_users(pr.id)
        assert len(users) == 2, len(users)
        assert len(anon_users) == 1, len(anon_users)
        assert len(auth_users) == 1, len(auth_users)

    def test_stats_users_with_period(self):
        """Test CACHE PROJECT STATS user stats with period works."""
        pr = ProjectFactory.create()
        d = date.today() - timedelta(days=6)
        TaskRunFactory.create(project=pr, created=d, finish_time=d)
        d = date.today() - timedelta(days=16)
        AnonymousTaskRunFactory.create(project=pr, created=d, finish_time=d)
        users, anon_users, auth_users = stats_users(pr.id, '1 week')
        assert len(users) == 2, len(users)
        assert len(anon_users) == 0, len(anon_users)
        assert len(auth_users) == 1, len(auth_users)

    def test_stats_dates(self):
        """Test CACHE PROJECT STATS date works."""
        pr = ProjectFactory.create()
        task = TaskFactory.create(n_answers=1)
        TaskFactory.create()
        TaskRunFactory.create(project=pr, task=task)
        AnonymousTaskRunFactory.create(project=pr)
        dates, dates_anon, dates_auth = stats_dates(pr.id)
        assert len(dates) == 15, len(dates)
        assert len(dates_anon) == 1, len(dates_anon)
        assert len(dates_auth) == 1, len(dates_auth)

    def test_stats_dates_with_period(self):
        """Test CACHE PROJECT STATS dates with period works."""
        pr = ProjectFactory.create()
        d = date.today() - timedelta(days=6)
        task = TaskFactory.create(n_answers=1, created=d)
        TaskRunFactory.create(project=pr, task=task, created=d, finish_time=d)
        d = date.today() - timedelta(days=16)
        AnonymousTaskRunFactory.create(project=pr, created=d, finish_time=d)
        dates, dates_anon, dates_auth = stats_dates(pr.id, '1 week')
        assert len(dates) == 7, len(dates)
        assert len(dates_anon) == 0, len(dates_anon)
        assert len(dates_auth) == 1, len(dates_auth)

    def test_stats_hours(self):
        """Test CACHE PROJECT STATS hours works."""
        pr = ProjectFactory.create()
        task = TaskFactory.create(n_answers=1)
        today = datetime.now(pytz.utc)
        TaskFactory.create()
        TaskRunFactory.create(project=pr, task=task)
        AnonymousTaskRunFactory.create(project=pr)
        hours, hours_anon, hours_auth, max_hours, \
            max_hours_anon, max_hours_auth = stats_hours(pr.id)
        assert len(hours) == 24, len(hours)
        assert hours[today.strftime('%H')] == 2, hours[today.strftime('%H')]
        assert hours_anon[today.strftime('%H')] == 1, hours_anon[today.strftime('%H')]
        assert hours_auth[today.strftime('%H')] == 1, hours_auth[today.strftime('%H')]
        assert max_hours == 2
        assert max_hours_anon == 1
        assert max_hours_auth == 1


    # def test_stats_hours_with_period(self):
    #     """Test CACHE PROJECT STATS hours with period works."""
    #     pr = ProjectFactory.create()
    #     d = date.today() - timedelta(days=6)
    #     task = TaskFactory.create(n_answers=1, created=d)
    #     TaskRunFactory.create(project=pr, task=task, created=d, finish_time=d)
    #     d = date.today() - timedelta(days=16)
    #     AnonymousTaskRunFactory.create(project=pr, created=d, finish_time=d)
    #     dates, dates_anon, dates_auth = stats_dates(pr.id, '1 week')
    #     assert len(dates) == 7, len(dates)
    #     assert len(dates_anon) == 0, len(dates_anon)
    #     assert len(dates_auth) == 1, len(dates_auth)
