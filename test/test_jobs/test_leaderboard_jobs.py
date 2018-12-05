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
from pybossa.jobs import get_leaderboard_jobs
from factories import UserFactory, TaskRunFactory
from default import Test, with_context
from mock import patch, MagicMock
from sqlalchemy.exc import ProgrammingError


class TestLeaderboard(Test):


    @with_context
    def test_get_leaderboard_jobs_reads_settings(self):
        """Test JOB returns all leaderboard jobs."""
        with patch.dict(self.flask_app.config, {'LEADERBOARDS': ['n']}):
            jobs = []
            for job in get_leaderboard_jobs():
                jobs.append(job)
            assert len(jobs) == 2
            assert jobs[0]['kwargs'] == {'info': 'n'}, jobs[0]

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
        db.session.execute('''delete from "user";''')
        from pybossa.core import user_repo
        users = UserFactory.create_batch(20)
        restricted = UserFactory.create(restrict=True)
        users.append(restricted)
        for user in users:
            TaskRunFactory.create(user=user)
        leaderboard()
        top_users = get_leaderboard()
        assert len(top_users) == 20, len(top_users)
        for u in top_users:
            assert u['name'] != restricted.name, u

        results = db.session.execute('select * from users_rank');
        for r in results:
            assert r.restrict is False, r

    @with_context
    def test_leaderboard_foo_key(self):
        """Test JOB leaderboard returns users for foo key."""
        users = []
        for score in range(1, 11):
            users.append(UserFactory.create(info=dict(foo=score)))
        users.append(UserFactory.create(restrict=True, info=dict(foo=11)))
        leaderboard(info='foo')
        top_users = get_leaderboard(info='foo')
        assert len(top_users) == 10, len(top_users)
        score = 10
        for user in top_users:
            user['score'] == score, user
            score = score - 1

        results = db.session.execute('select * from users_rank_foo');
        for r in results:
            assert r.restrict is False, r

    @with_context
    def test_leaderboard_foo_dash_key(self):
        """Test JOB leaderboard returns users for foo-dash key."""
        users = []
        for score in range(1, 11):
            users.append(UserFactory.create(info={'foo-dash': score}))
        users.append(UserFactory.create(restrict=True, info={'foo-dash': 11}))
        leaderboard(info='foo-dash')
        top_users = get_leaderboard(info='foo-dash')
        assert len(top_users) == 10, len(top_users)
        score = 10
        for user in top_users:
            user['score'] == score, user
            score = score - 1

        results = db.session.execute('select * from "users_rank_foo-dash"');
        for r in results:
            assert r.restrict is False, r

    @with_context
    def test_leaderboard_foo_key_current_user(self):
        """Test JOB leaderboard returns users for foo key with current user."""
        users = []
        for score in range(1, 11):
            users.append(UserFactory.create(info=dict(foo=score)))

        users.append(UserFactory.create(restrict=True, info=dict(foo=11)))

        leaderboard(info='foo')
        top_users = get_leaderboard(user_id=users[0].id, info='foo')
        assert len(top_users) == 11, len(top_users)
        score = 10
        for user in top_users[0:10]:
            user['score'] == score, user
            score = score - 1
        assert top_users[-1]['name'] == users[0].name
        assert top_users[-1]['score'] == users[0].info.get('foo')

        results = db.session.execute('select * from users_rank_foo');
        for r in results:
            assert r.restrict is False, r

    @with_context
    def test_leaderboard_foo_dash_key_current_user(self):
        """Test JOB leaderboard returns users for foo-dash key with current user."""
        users = []
        for score in range(1, 11):
            users.append(UserFactory.create(info={'foo-dash': score}))

        users.append(UserFactory.create(restrict=True, info={'foo-dash': 11}))

        leaderboard(info='foo-dash')
        top_users = get_leaderboard(user_id=users[0].id, info='foo-dash')
        assert len(top_users) == 11, len(top_users)
        score = 10
        for user in top_users[0:10]:
            user['score'] == score, user
            score = score - 1
        assert top_users[-1]['name'] == users[0].name
        assert top_users[-1]['score'] == users[0].info.get('foo-dash')

        results = db.session.execute('select * from "users_rank_foo-dash"');
        for r in results:
            assert r.restrict is False, r

    @with_context
    def test_leaderboard_foo_key_current_user_window(self):
        """Test JOB leaderboard returns users for foo key with current user and
        window."""
        UserFactory.create_batch(10, info=dict(n=0))
        UserFactory.create_batch(10, info=dict(n=2))
        UserFactory.create_batch(10, info=dict(n=2), restrict=True)
        users = []
        for score in range(11, 22):
            users.append(UserFactory.create(info=dict(n=score)))
        myself = UserFactory.create(info=dict(n=1))

        leaderboard(info='n')

        top_users = get_leaderboard(user_id=myself.id, info='n', window=5)

        assert len(top_users) == 20 + 5 + 1 + 5, len(top_users)
        assert top_users[25]['name'] == myself.name
        assert top_users[25]['score'] == myself.info.get('n')
        assert top_users[24]['score'] >= myself.info.get('n')
        assert top_users[26]['score'] <= myself.info.get('n')

        results = db.session.execute('select * from users_rank_n');
        for r in results:
            assert r.restrict is False, r


    @with_context
    def test_leaderboard_foo_dash_key_current_user_window(self):
        """Test JOB leaderboard returns users for foo-dash key with current user and
        window."""
        UserFactory.create_batch(10, info={'foo-dash': 0})
        UserFactory.create_batch(10, info={'foo-dash': 2})
        UserFactory.create_batch(10, info={'foo-dash': 2}, restrict=True)
        users = []
        for score in range(11, 22):
            users.append(UserFactory.create(info={'foo-dash': score}))
        myself = UserFactory.create(info={'foo-dash': 1})

        leaderboard(info='foo-dash')

        top_users = get_leaderboard(user_id=myself.id, info='foo-dash', window=5)

        assert len(top_users) == 20 + 5 + 1 + 5, len(top_users)
        assert top_users[25]['name'] == myself.name
        assert top_users[25]['score'] == myself.info.get('foo-dash')
        assert top_users[24]['score'] >= myself.info.get('foo-dash')
        assert top_users[26]['score'] <= myself.info.get('foo-dash')

        results = db.session.execute('select * from "users_rank_foo-dash"');
        for r in results:
            assert r.restrict is False, r
