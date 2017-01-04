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

from pybossa.dashboard.jobs import active_users_week
from pybossa.dashboard.data import format_users_week
from pybossa.core import db
from factories.taskrun_factory import TaskRunFactory, AnonymousTaskRunFactory
from default import Test, with_context
from datetime import datetime
from mock import patch, MagicMock


class TestDashBoardActiveUsers(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = active_users_week()
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
        res = active_users_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_active_week(self):
        """Test JOB dashboard returns active users week runs."""
        TaskRunFactory.create()
        AnonymousTaskRunFactory.create()
        active_users_week()
        sql = "select * from dashboard_week_users;"
        results = db.session.execute(sql).fetchall()

        assert results[0].n_users == 1, results[0].n_users

    @with_context
    def test_format_users_week(self):
        """Test format users week works."""
        TaskRunFactory.create()
        active_users_week()
        res = format_users_week()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day
        assert len(res['series']) == 1
        assert res['series'][0][0] == 1, res['series'][0][0]

    @with_context
    @patch('pybossa.dashboard.data.db')
    def test_format_users_week_empty(self, db_mock):
        """Test format users week empty works."""
        db_mock.slave_session.execute.return_value = []
        AnonymousTaskRunFactory.create()
        active_users_week()
        res = format_users_week()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day
        assert len(res['series']) == 1
        assert res['series'][0][0] == 0, res['series'][0][0]
