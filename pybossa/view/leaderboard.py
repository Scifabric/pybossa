# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template
from flaskext.wtf import Form, IntegerField, TextField, BooleanField, validators, HiddenInput
from flaskext.login import login_required, current_user
from sqlalchemy.exc import UnboundExecutionError
from sqlalchemy.sql import func, text
from sqlalchemy import func

import pybossa.model as model
from pybossa.core import db
from pybossa.auth import require

blueprint = Blueprint('leaderboard', __name__)


@blueprint.route('/')
def index():
    """Get the last activity from users and apps"""
    # Top 20 users
    limit = 20
    sql = text('''
               WITH global_rank AS (
                    WITH scores AS (
                        SELECT user_id, COUNT(*) AS score FROM task_run
                        WHERE user_id IS NOT NULL GROUP BY user_id)
                    SELECT user_id, score, rank() OVER (ORDER BY score desc)
                    FROM scores)
               SELECT rank, id, fullname, email_addr, score FROM global_rank
               JOIN public."user" on (user_id=public."user".id) ORDER BY rank
               LIMIT :limit;
               ''')

    results = db.engine.execute(sql, limit=20)

    top_users = []
    user_in_top = False
    if current_user.is_authenticated():
        for user in results:
            if (user.id == current_user.id):
                user_in_top = True
            top_users.append(user)
        if not user_in_top:
            sql = text('''
                       WITH global_rank AS (
                            WITH scores AS (
                                SELECT user_id, COUNT(*) AS score FROM task_run
                                WHERE user_id IS NOT NULL GROUP BY user_id)
                            SELECT user_id, score, rank() OVER (ORDER BY score desc)
                            FROM scores)
                       SELECT rank, id, fullname, email_addr, score FROM global_rank
                       JOIN public."user" on (user_id=public."user".id)
                       WHERE user_id=:user_id ORDER BY rank;
                       ''')
            user_rank = db.engine.execute(sql, user_id=current_user.id)
            for row in user_rank:
                top_users.append(row)
    else:
        top_users = results

    return render_template('/stats/index.html', title="Community Leaderboard",
                           top_users=top_users)
