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
"""Leaderboard Jobs module for running background tasks in PYBOSSA server."""
from sqlalchemy import text
from pybossa.core import db
from pybossa.util import exists_materialized_view, refresh_materialized_view


def leaderboard(info=None):
    """Create or update leaderboard materialized view."""
    materialized_view = 'users_rank'
    materialized_view_idx = 'users_rank_idx'
    if info:
        materialized_view = 'users_rank_%s' % info
        materialized_view_idx = 'users_rank_%s_idx' % info

    if exists_materialized_view(db, materialized_view):
        return refresh_materialized_view(db, materialized_view)
    else:
        sql = '''
                   CREATE MATERIALIZED VIEW "{}" AS WITH scores AS (
                        SELECT "user".*, COUNT(task_run.user_id) AS score
                        FROM "user" LEFT JOIN task_run
                        ON task_run.user_id="user".id where
                        "user".restrict=false GROUP BY "user".id
                    ) SELECT *, row_number() OVER (ORDER BY score DESC) as rank FROM scores;
              '''.format(materialized_view)
        if info:
            sql = '''
                       CREATE MATERIALIZED VIEW "{}" AS WITH scores AS (
                            SELECT "user".*, COALESCE(CAST("user".info->>'{}' AS INTEGER), 0) AS score
                            FROM "user" where "user".restrict=false ORDER BY score DESC) SELECT *, row_number() OVER (ORDER BY score DESC) as rank FROM scores;
                  '''.format(materialized_view, info)
        db.session.execute(sql)
        db.session.commit()
        sql = '''
              CREATE UNIQUE INDEX "{}"
               on "{}"(id, rank);
              '''.format(materialized_view_idx, materialized_view)
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"
