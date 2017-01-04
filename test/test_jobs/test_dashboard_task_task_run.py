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

from pybossa.dashboard.jobs import new_tasks_week, new_task_runs_week
from pybossa.dashboard.data import format_new_task_runs, format_new_tasks
from pybossa.core import db
from datetime import datetime, timedelta
from factories.taskrun_factory import TaskRunFactory, AnonymousTaskRunFactory
from factories.task_factory import TaskFactory
from default import Test, with_context
from mock import patch, MagicMock


class TestDashBoardNewTask(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = new_tasks_week()
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
        res = new_tasks_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_new_tasks(self):
        """Test JOB dashboard returns new task."""
        TaskFactory.create()
        new_tasks_week()
        sql = "select * from dashboard_week_new_task;"
        results = db.session.execute(sql).fetchall()

        assert results[0].day_tasks == 1, results[0].day_tasks

    @with_context
    @patch('pybossa.dashboard.data.db')
    def test_format_new_tasks_emtpy(self, db_mock):
        """Test format new tasks empty works."""
        db_mock.slave_session.execute.return_value = []
        new_tasks_week()
        res = format_new_tasks()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day
        assert len(res['series']) == 1
        assert res['series'][0][0] == 0, res['series'][0][0]

    @with_context
    def test_format_new_tasks(self):
        """Test format new tasks works."""
        TaskFactory.create()
        new_tasks_week()
        res = format_new_tasks()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day
        assert len(res['series']) == 1
        assert res['series'][0][0] == 1, res['series'][0][0]

class TestDashBoardNewTaskRuns(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = new_task_runs_week()
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
        res = new_task_runs_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_new_task_runs(self):
        """Test JOB dashboard returns new task runs."""
        day = datetime.utcnow() - timedelta(days=2)
        TaskRunFactory.create(finish_time=day.isoformat())
        day = datetime.utcnow() - timedelta(days=1)
        TaskRunFactory.create(finish_time=day.isoformat())
        new_task_runs_week()
        sql = "select * from dashboard_week_new_task_run;"
        results = db.session.execute(sql).fetchall()

        assert results[0].day_task_runs == 1, results[0].day_task_runs

    @with_context
    @patch('pybossa.dashboard.data.db')
    def test_format_new_task_runs_emtpy(self, db_mock):
        """Test format new task_runs empty works."""
        db_mock.slave_session.execute.return_value = []
        new_task_runs_week()
        res = format_new_task_runs()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day, res
        assert len(res['series']) == 1
        assert res['series'][0][0] == 0, res['series'][0][0]

    @with_context
    def test_format_new_task_runs(self):
        """Test format new task_runs works."""
        TaskRunFactory.create()
        AnonymousTaskRunFactory.create()
        new_task_runs_week()
        res = format_new_task_runs()
        assert len(res['labels']) == 1
        day = datetime.utcnow().strftime('%Y-%m-%d')
        assert res['labels'][0] == day, res
        assert len(res['series']) == 1
        assert res['series'][0][0] == 2, res['series'][0][0]
