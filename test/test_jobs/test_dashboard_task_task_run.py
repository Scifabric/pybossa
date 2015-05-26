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

from pybossa.dashboard import dashboard_new_tasks_week
from pybossa.dashboard import dashboard_new_task_runs_week
from pybossa.core import db
from datetime import datetime, timedelta
from factories.taskrun_factory import TaskRunFactory
from factories.task_factory import TaskFactory
from default import Test, with_context
from mock import patch, MagicMock


class TestDashBoardNewTask(Test):

    @with_context
    @patch('pybossa.dashboard.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = dashboard_new_tasks_week()
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
        res = dashboard_new_tasks_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_new_tasks(self):
        """Test JOB dashboard returns new task."""
        TaskFactory.create()
        dashboard_new_tasks_week()
        sql = "select * from dashboard_week_new_task;"
        results = db.session.execute(sql)
        for row in results:
            assert row.day_tasks == 1, row.day_tasks

class TestDashBoardNewTaskRuns(Test):

    @with_context
    @patch('pybossa.dashboard.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = dashboard_new_task_runs_week()
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
        res = dashboard_new_task_runs_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_new_task_runs(self):
        """Test JOB dashboard returns new task runs."""
        day = datetime.utcnow() - timedelta(days=2)
        TaskRunFactory.create(finish_time=day.isoformat())
        day = datetime.utcnow() - timedelta(days=1)
        TaskRunFactory.create(finish_time=day.isoformat())
        dashboard_new_task_runs_week()
        sql = "select * from dashboard_week_new_task_run;"
        results = db.session.execute(sql)
        for row in results:
            assert row.day_task_runs == 1, row.day_task_runs
