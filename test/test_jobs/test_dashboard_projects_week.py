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

from pybossa.dashboard.jobs import new_projects_week, update_projects_week
from pybossa.dashboard.data import format_new_projects, format_update_projects
from pybossa.core import db
from pybossa.repositories import ProjectRepository
from factories.project_factory import ProjectFactory
from default import Test, with_context
from mock import patch, MagicMock
from datetime import datetime


class TestDashBoardNewProject(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = new_projects_week()
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
        res = new_projects_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_new_projects_week(self):
        """Test JOB update projects week works."""
        p = ProjectFactory.create()
        new_projects_week()
        sql = "select * from dashboard_week_project_new;"
        results = db.session.execute(sql)
        for row in results:
            assert row.id == p.id
            assert row.name == p.name
            assert row.owner_id == p.owner_id
            assert row.u_name == p.owner.name
            assert row.email_addr == p.owner.email_addr

    @with_context
    def test_format_new_projects(self):
        """Test format new projects works."""
        p = ProjectFactory.create()
        new_projects_week()
        res = format_new_projects()
        day = datetime.utcnow().strftime('%Y-%m-%d')
        res = res[0]
        assert res['day'].strftime('%Y-%m-%d') == day, res['day']
        assert res['id'] == p.id
        assert res['short_name'] == p.short_name
        assert res['p_name'] == p.name
        assert res['email_addr'] == p.owner.email_addr
        assert res['owner_id'] == p.owner.id
        assert res['u_name'] == p.owner.name


class TestDashBoardUpdateProject(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = update_projects_week()
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
        res = update_projects_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_update_projects_week(self):
        """Test JOB update projects week works."""
        p = ProjectFactory.create()
        p.name = 'NewNameName'
        project_repository = ProjectRepository(db)
        project_repository.update(p)
        update_projects_week()
        sql = "select * from dashboard_week_project_update;"
        results = db.session.execute(sql)
        for row in results:
            assert row.id == p.id
            assert row.name == p.name
            assert row.owner_id == p.owner_id
            assert row.u_name == p.owner.name
            assert row.email_addr == p.owner.email_addr

    @with_context
    def test_format_updated_projects(self):
        """Test format updated projects works."""
        p = ProjectFactory.create()
        p.name = 'NewNewNew'
        project_repo = ProjectRepository(db)
        project_repo.update(p)
        update_projects_week()
        res = format_update_projects()
        day = datetime.utcnow().strftime('%Y-%m-%d')
        res = res[0]
        assert res['day'].strftime('%Y-%m-%d') == day, res['day']
        assert res['id'] == p.id
        assert res['short_name'] == p.short_name
        assert res['p_name'] == p.name
        assert res['email_addr'] == p.owner.email_addr
        assert res['owner_id'] == p.owner.id
        assert res['u_name'] == p.owner.name

