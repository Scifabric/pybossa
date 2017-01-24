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

from pybossa.dashboard.jobs import (
    draft_projects_week, published_projects_week, update_projects_week
    )
from pybossa.dashboard.data import (
    format_draft_projects, format_published_projects, format_update_projects
    )
from pybossa.core import db, auditlog_repo
from pybossa.repositories import ProjectRepository
from factories.project_factory import ProjectFactory
from default import Test, with_context
from mock import patch, MagicMock
from datetime import datetime, date
from pybossa.auditlogger import AuditLogger


class TestDashBoardDraftProject(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = draft_projects_week()
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
        res = draft_projects_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_format_new_projects(self):
        """Test format draft_projects_week works."""
        ProjectFactory.create(published=True)
        p = ProjectFactory.create(published=False)
        draft_projects_week()
        day = datetime.utcnow().strftime('%Y-%m-%d')

        res = format_draft_projects()

        assert len(res) == 1, res
        res = res[0]
        assert res['day'] == day, res['day']
        assert res['id'] == p.id
        assert res['short_name'] == p.short_name
        assert res['p_name'] == p.name
        assert res['email_addr'] == p.owner.email_addr
        assert res['owner_id'] == p.owner.id
        assert res['u_name'] == p.owner.name


class TestDashBoardPublishedProject(Test):

    @with_context
    @patch('pybossa.dashboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock):
        """Test JOB dashboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = published_projects_week()
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
        res = published_projects_week()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_format_published_projects_week(self):
        """Test format published_projects_week works."""
        ProjectFactory.create(published=False)
        p = ProjectFactory.create(published=True)
        auditlogger = AuditLogger(auditlog_repo, caller='web')
        auditlogger.log_event(p, p.owner, 'update', 'published', False, True)
        published_projects_week()
        day = datetime.utcnow().strftime('%Y-%m-%d')

        res = format_published_projects()

        assert len(res) == 1, res
        res = res[0]
        assert res['day'] == day, res['day']
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
    def test_format_updated_projects(self):
        """Test format updated projects works."""
        old_date = date(2014, 11, 24)
        old_project = ProjectFactory.create(updated=old_date)
        p = ProjectFactory.create()
        p.name = 'NewNewNew'
        project_repo = ProjectRepository(db)
        project_repo.update(p)
        update_projects_week()
        day = datetime.utcnow().strftime('%Y-%m-%d')

        res = format_update_projects()

        assert len(res) == 1, res
        res = res[0]
        assert res['day'] == day, res['day']
        assert res['id'] == p.id
        assert res['short_name'] == p.short_name
        assert res['p_name'] == p.name
        assert res['email_addr'] == p.owner.email_addr
        assert res['owner_id'] == p.owner.id
        assert res['u_name'] == p.owner.name

