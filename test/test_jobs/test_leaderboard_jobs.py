# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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

from pybossa.leaderboard.jobs import leaderboard
from pybossa.leaderboard.data import get_leaderboard
from pybossa.core import db
from factories import UserFactory, TaskRunFactory
from default import Test, with_context
from mock import patch, MagicMock
from sqlalchemy.exc import ProgrammingError


class TestDashBoardActiveAnon(Test):

    @with_context
    @patch('pybossa.leaderboard.jobs.db')
    def test_materialized_view_refreshed_concurrently(self, db_mock):
        """Test JOB leaderboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = leaderboard()
        assert db_mock.session.execute.called
        assert res == 'Materialized view refreshed concurrently'

    @with_context
    @patch('pybossa.leaderboard.jobs.exists_materialized_view')
    @patch('pybossa.leaderboard.jobs.db')
    def test_materialized_view_refreshed(self, db_mock, exists_mock):
        """Test JOB leaderboard materialized view is refreshed."""
        result = MagicMock()
        result.exists = True
        results = [result]
        exists_mock.return_value = True
        db_mock.slave_session.execute.side_effect = results
        db_mock.session.execute.side_effect = [ProgrammingError('foo',
                                                                'bar',
                                                                'bar'),
                                               True]
        res = leaderboard()
        assert db_mock.session.execute.called
        assert res == 'Materialized view refreshed'

    @with_context
    @patch('pybossa.leaderboard.jobs.db')
    def test_materialized_view_created(self, db_mock):
        """Test JOB leaderboard materialized view is created."""
        result = MagicMock()
        result.exists = False
        results = [result]
        db_mock.slave_session.execute.return_value = results
        res = leaderboard()
        assert db_mock.session.commit.called
        assert res == 'Materialized view created'

    @with_context
    def test_anon_week(self):
        """Test JOB leaderboard returns anon active week runs."""
        users = UserFactory.create_batch(20)
        for user in users:
            TaskRunFactory.create(user=user)
        leaderboard()
        top_users = get_leaderboard()
        assert len(top_users) == 20, len(top_users)

    #@with_context
    #def test_format_anon_week(self):
    #    """Test format anon week works."""
    #    AnonymousTaskRunFactory.create()
    #    leaderboard()
    #    res = format_anon_week()
    #    assert len(res['labels']) == 1
    #    day = datetime.utcnow().strftime('%Y-%m-%d')
    #    assert res['labels'][0] == day
    #    assert len(res['series']) == 1
    #    assert res['series'][0][0] == 1, res['series'][0][0]

    #@with_context
    #@patch('pybossa.leaderboard.data.db')
    #def test_format_anon_week_empty(self, db_mock):
    #    """Test format anon week empty works."""
    #    db_mock.slave_session.execute.return_value = []
    #    TaskRunFactory.create()
    #    leaderboard()
    #    res = format_anon_week()
    #    assert len(res['labels']) == 1
    #    day = datetime.utcnow().strftime('%Y-%m-%d')
    #    assert res['labels'][0] == day
    #    assert len(res['series']) == 1
    #    assert res['series'][0][0] == 0, res['series'][0][0]
