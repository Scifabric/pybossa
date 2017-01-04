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

from pybossa.dashboard.jobs import new_users_week, returning_users_week
from pybossa.dashboard.data import format_new_users, format_returning_users
from pybossa.core import db
from datetime import datetime, timedelta
from default import Test, with_context
from factories.user_factory import UserFactory
from factories.taskrun_factory import TaskRunFactory
from mock import patch, MagicMock
from sqlalchemy import text


class TestDashBoardNewUsers(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = new_users_week()
        assert db_mock.session.execute.called
        assert res == 'Materialized view refreshed'

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_created(self, db_mock):
        """Test JOB dashboard materialized view is created."""
        result = MagicMock()
        result.exists = False
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = new_users_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_number_users(self):
        """Test JOB dashboard returns number of users."""
        UserFactory.create()
        new_users_week()
        sql = "select * from dashboard_week_new_users;"
        results = db.session.execute(sql).fetchall()

        assert results[0].day_users == 1
        assert str(results[0].day) in datetime.utcnow().strftime('%Y-%m-%d')

    @with_context
    def test_format_new_users(self):
        """Test format new users works."""
        UserFactory.create()
        new_users_week()
        res = format_new_users()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day
        assert len(res['series']) == 1
        assert res['series'][0][0] == 1, res['series'][0][0]

    @with_context
    @patch('pybossa.dashboard.data.db')
    def test_format_new_users_empty(self, db_mock):
        """Test format new users empty works."""
        db_mock.slave_session.execute.return_value = []
        new_users_week()
        res = format_new_users()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day
        assert len(res['series']) == 1
        assert res['series'][0][0] == 0, res['series'][0][0]

class TestDashBoardReturningUsers(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = returning_users_week()
        assert db_mock.session.execute.called
        assert res == 'Materialized view refreshed'

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_created(self, db_mock):
        """Test JOB dashboard materialized view is created."""
        result = MagicMock()
        result.exists = False
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = returning_users_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_returning_users(self):
        """Test JOB dashboard returns number of returning users."""
        once_only_user = UserFactory.create()
        returning_user = UserFactory.create()
        TaskRunFactory.create(user=once_only_user)
        TaskRunFactory.create(user=returning_user)
        task_run = TaskRunFactory.create(user=returning_user)
        day = datetime.utcnow() - timedelta(days=1)
        TaskRunFactory.create(user=returning_user, finish_time=day.isoformat())
        returning_users_week()
        sql = "select * from dashboard_week_returning_users;"
        results = db.session.execute(sql).fetchall()

        assert results[0].n_days == 2
        assert results[0].user_id == task_run.user_id

    @with_context
    @patch('pybossa.dashboard.data.db')
    def test_format_returning_users_emtpy(self, db_mock):
        """Test format returning users works."""
        db_mock.slave_session.execute.return_value = []
        TaskRunFactory.create()
        day = datetime.utcnow() - timedelta(days=1)
        TaskRunFactory.create(finish_time=day.isoformat())
        returning_users_week()
        res = format_returning_users()
        for i in range(1,8):
            if i == 1:
                day = '%s day' % i
            else:
                day = "%s days" % i
            err = "%s != %s" % (res['labels'][i - 1], day)
            assert res['labels'][i - 1] == day, err
            assert res['series'][0][i - 1] == 0, res['series'][i][0]

    @with_context
    def test_format_returning_users(self):
        """Test format returning users works."""
        user = UserFactory.create()
        TaskRunFactory.create(user=user)
        TaskRunFactory.create(user=user)
        TaskRunFactory.create(user=user)
        TaskRunFactory.create(user=user)
        TaskRunFactory.create(user=user)
        TaskRunFactory.create(user=user)
        day = datetime.utcnow() - timedelta(days=2)
        TaskRunFactory.create(user=user, finish_time=day.isoformat())
        day = datetime.utcnow() - timedelta(days=1)
        TaskRunFactory.create(user=user, finish_time=day.isoformat())
        TaskRunFactory.create(user=user, finish_time=day.isoformat())
        TaskRunFactory.create(user=user, finish_time=day.isoformat())
        TaskRunFactory.create(user=user, finish_time=day.isoformat())
        TaskRunFactory.create(user=user, finish_time=day.isoformat())
        returning_users_week()
        res = format_returning_users()
        for i in range(1,8):
            if i == 1:
                day = '%s day' % i
            else:
                day = "%s days" % i
            err = "%s != %s" % (res['labels'][i - 1], day)
            assert res['labels'][i - 1] == day, err
            if day == '3 days':
                assert res['labels'][i - 1] == day, day
                assert res['series'][0][i - 1] == 1, res['series'][0][i - 1]
            else:
                assert res['series'][0][i - 1] == 0, res
