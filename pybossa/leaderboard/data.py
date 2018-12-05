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
"""Leaderboard queries in leaderboard view."""
from sqlalchemy import text
from pybossa.core import db
from pybossa.model.user import User

u = User()


def get_leaderboard(top_users=20, user_id=None, window=0, info=None):
    """Return a list of top_users and if user_id return its position."""
    materialized_view = "users_rank_%s" % info
    sql = text('''SELECT * from users_rank WHERE rank <= :top_users 
               ORDER BY rank;''')
    if info:
        sql = text('''SELECT * from "{}" WHERE rank <= :top_users 
                    ORDER BY rank;'''.format(materialized_view))

    results = db.session.execute(sql, dict(top_users=top_users))
    top_users = [format_user(user) for user in results]

    if user_id:
        sql = text('''SELECT * from users_rank where id=:user_id;''')
        if info:
            sql = text('''SELECT * from "{}" where
                       id=:user_id;'''.format(materialized_view))
        results = db.session.execute(sql, dict(user_id=user_id))
        user = None
        for row in results:
            user = format_user(row)
        if user and window != 0:
            sql = text('''SELECT * from users_rank
                       WHERE rank >= :low AND rank <= :top order by rank;
                       ''')
            if info:
                sql = text('''SELECT * from "{}" 
                           WHERE rank >= :low AND rank <= :top order by rank;
                           '''.format(materialized_view))
            low = user['rank'] - window
            top = user['rank'] + window
            results = db.session.execute(sql, dict(user_id=user_id,
                                         top=top,
                                         low=low))
            for row in results:
                top_users.append(format_user(row))
        else:
            if user:
                top_users.append(user)
        return top_users
    return top_users


def format_user(user):
    """Return an User object."""
    user = dict(
        rank=user.rank,
        id=user.id,
        name=user.name,
        fullname=user.fullname,
        email_addr=user.email_addr,
        info=user.info,
        created=user.created,
        restrict=user.restrict,
        score=user.score)
    tmp = u.to_public_json(data=user)
    return tmp
