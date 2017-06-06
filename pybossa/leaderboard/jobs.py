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


def leaderboard():
    """Create or update leaderboard materialized view."""
    if exists_materialized_view(db, 'users_rank'):
        return refresh_materialized_view(db, 'users_rank')
    else:
        sql = text('''
                   CREATE MATERIALIZED VIEW users_rank AS WITH global_rank AS (
                        WITH scores AS (
                            SELECT user_id, COUNT(*) AS score FROM task_run
                            WHERE user_id IS NOT NULL GROUP BY user_id)
                        SELECT user_id, score, rank() OVER (ORDER BY score desc)
                        FROM scores)
                   SELECT rank, id, name, fullname, email_addr, info, created,
                   score FROM global_rank
                   JOIN public."user" on (user_id=public."user".id) ORDER BY rank;
                   ''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"
