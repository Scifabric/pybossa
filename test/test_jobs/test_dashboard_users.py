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

from pybossa.dashboard import dashboard_new_users_week
from pybossa.dashboard import dashboard_returning_users_week
from pybossa.core import db
from datetime import datetime, timedelta
from default import Test, with_context
from factories.user_factory import UserFactory
from factories.taskrun_factory import TaskRunFactory
from mock import patch, MagicMock


class TestDashBoardNewUsers(Test):

    @with_context
    @patch('pybossa.dashboard.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = dashboard_new_users_week()
        assert db_mock.session.execute.called
        assert res == 'Materialized view refreshed'

    @with_context
    @patch('pybossa.dashboard.db')
    def test_materialized_view_created(self, db_mock):
        """Test JOB dashboard materialized view is created."""
        result = MagicMock()
        result.exists = False
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = dashboard_new_users_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_number_users(self):
        """Test JOB dashboard returns number of users."""
        UserFactory.create()
        dashboard_new_users_week()
        sql = "select * from dashboard_week_new_users;"
        results = db.session.execute(sql)
        for row in results:
            assert row.day_users == 1
            assert str(row.day) in datetime.utcnow().strftime('%Y-%m-%d')


class TestDashBoardReturningUsers(Test):

    @with_context
    @patch('pybossa.dashboard.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = dashboard_returning_users_week()
        assert db_mock.session.execute.called
        assert res == 'Materialized view refreshed'

    @with_context
    @patch('pybossa.dashboard.db')
    def test_materialized_view_created(self, db_mock):
        """Test JOB dashboard materialized view is created."""
        result = MagicMock()
        result.exists = False
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = dashboard_returning_users_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_returning_users(self):
        """Test JOB dashboard returns number of returning users."""
        task_run = TaskRunFactory.create()
        day = datetime.utcnow() - timedelta(days=1)
        TaskRunFactory.create(created=day)
        dashboard_returning_users_week()
        sql = "select * from dashboard_week_returning_users;"
        results = db.session.execute(sql)
        for row in results:
            assert row.n_days == 2
            assert row.user_id == task_run.user_id
