# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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
from sqlalchemy.sql import text
from pybossa.core import db, timeouts
from pybossa.cache import cache, memoize, delete_memoized
from pybossa.util import pretty_date
from pybossa.model.user import User
import json


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_leaderboard(n, user_id):
    """Return the top n users with their rank."""
    sql = text('''
               WITH global_rank AS (
                    WITH scores AS (
                        SELECT user_id, COUNT(*) AS score FROM task_run
                        WHERE user_id IS NOT NULL GROUP BY user_id)
                    SELECT user_id, score, rank() OVER (ORDER BY score desc)
                    FROM scores)
               SELECT rank, id, name, fullname, email_addr, info, score FROM global_rank
               JOIN public."user" on (user_id=public."user".id) ORDER BY rank
               LIMIT :limit;
               ''')

    results = db.engine.execute(sql, limit=n)

    top_users = []
    user_in_top = False
    for row in results:
        if (row.id == user_id):
            user_in_top = True
        user=dict(
            rank=row.rank,
            id=row.id,
            name=row.name,
            fullname=row.fullname,
            email_addr=row.email_addr,
            info=dict(json.loads(row.info)),
            score=row.score)
        top_users.append(user)
    if (user_id != 'anonymous'):
        if not user_in_top:
            sql = text('''
                       WITH global_rank AS (
                            WITH scores AS (
                                SELECT user_id, COUNT(*) AS score FROM task_run
                                WHERE user_id IS NOT NULL GROUP BY user_id)
                            SELECT user_id, score, rank() OVER (ORDER BY score desc)
                            FROM scores)
                       SELECT rank, id, name, fullname, email_addr, info, score FROM global_rank
                       JOIN public."user" on (user_id=public."user".id)
                       WHERE user_id=:user_id ORDER BY rank;
                       ''')
            user_rank = db.engine.execute(sql, user_id=user_id)
            u = User.query.get(user_id)
            # Load by default user data with no rank
            user=dict(
                rank=-1,
                id=u.id,
                name=u.name,
                fullname=u.fullname,
                email_addr=u.email_addr,
                info=u.info,
                score=-1)
            for row in user_rank: # pragma: no cover
                user=dict(
                    rank=row.rank,
                    id=row.id,
                    name=row.name,
                    fullname=row.fullname,
                    email_addr=row.email_addr,
                    info=dict(json.loads(row.info)),
                    score=row.score)
            top_users.append(user)

    return top_users


@cache(key_prefix="front_page_top_users",
       timeout=timeouts.get('USER_TOP_TIMEOUT'))
def get_top(n=10):
    """Return the n=10 top users"""
    sql = text('''SELECT "user".id, "user".name, "user".fullname, "user".email_addr,
               "user".created, "user".info, COUNT(task_run.id) AS task_runs FROM task_run, "user"
               WHERE "user".id=task_run.user_id GROUP BY "user".id
               ORDER BY task_runs DESC LIMIT :limit''')
    results = db.engine.execute(sql, limit=n)
    top_users = []
    for row in results:
        user = dict(id=row.id, name=row.name, fullname=row.fullname,
                    email_addr=row.email_addr,
                    created=row.created,
                    task_runs=row.task_runs,
                    info=dict(json.loads(row.info)))
        top_users.append(user)
    return top_users


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_user_summary(name):
    # Get USER
    sql = text('''
               SELECT "user".id, "user".name, "user".fullname, "user".created,
               "user".api_key, "user".twitter_user_id, "user".facebook_user_id,
               "user".google_user_id, "user".info,
               "user".email_addr, COUNT(task_run.user_id) AS n_answers
               FROM "user" LEFT OUTER JOIN task_run ON "user".id=task_run.user_id
               WHERE "user".name=:name
               GROUP BY "user".id;
               ''')
    results = db.engine.execute(sql, name=name)
    user = dict()
    for row in results:
        user = dict(id=row.id, name=row.name, fullname=row.fullname,
                    created=row.created, api_key=row.api_key,
                    twitter_user_id=row.twitter_user_id,
                    google_user_id=row.google_user_id,
                    facebook_user_id=row.facebook_user_id,
                    info=dict(json.loads(row.info)),
                    email_addr=row.email_addr, n_answers=row.n_answers,
                    registered_ago=pretty_date(row.created))

    # Rank
    # See: https://gist.github.com/tokumine/1583695
    sql = text('''
               WITH global_rank AS (
                    WITH scores AS (
                        SELECT user_id, COUNT(*) AS score FROM task_run
                        WHERE user_id IS NOT NULL GROUP BY user_id)
                    SELECT user_id, score, rank() OVER (ORDER BY score desc)
                    FROM scores)
               SELECT * from global_rank WHERE user_id=:user_id;
               ''')

    if user:
        results = db.engine.execute(sql, user_id=user['id'])
        for row in results:
            user['rank'] = row.rank
            user['score'] = row.score

        # Get the APPs where the USER has participated
        sql = text('''
                   SELECT app.id, app.name, app.short_name, app.info,
                   COUNT(task_run.app_id) AS n_answers FROM app, task_run
                   WHERE app.id=task_run.app_id AND
                   task_run.user_id=:user_id GROUP BY app.id
                   ORDER BY n_answers DESC;
                   ''')
        results = db.engine.execute(sql, user_id=user['id'])
        apps = []
        for row in results:
            app = dict(id=row.id, name=row.name, info=dict(json.loads(row.info)),
                       short_name=row.short_name,
                       n_answers=row.n_answers)
            apps.append(app)

        # Get the CREATED APPS by the USER
        sql = text('''
                   SELECT app.id, app.name, app.short_name, app.info, app.created
                   FROM app
                   WHERE app.owner_id=:user_id
                   ORDER BY app.created DESC;
                   ''')
        results = db.engine.execute(sql, user_id=user['id'])
        apps_created = []
        for row in results:
            app = dict(id=row.id, name=row.name,
                       short_name=row.short_name,
                       info=dict(json.loads(row.info)))
            apps_created.append(app)

        return user, apps, apps_created
    else:
        return None, None, None


@cache(timeout=timeouts.get('USER_TOTAL_TIMEOUT'),
       key_prefix="site_total_users")
def get_total_users():
    count = User.query.count()
    return count


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_users_page(page, per_page=24):
    offset = (page - 1) * per_page
    sql = text('''SELECT "user".id, "user".name, "user".fullname, "user".email_addr,
               "user".created, "user".info, COUNT(task_run.id) AS task_runs
               FROM task_run, "user"
               WHERE "user".id=task_run.user_id GROUP BY "user".id
               ORDER BY "user".created DESC LIMIT :limit OFFSET :offset''')
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    accounts = []
    for row in results:
        user = dict(id=row.id, name=row.name, fullname=row.fullname,
                    email_addr=row.email_addr, created=row.created,
                    task_runs=row.task_runs, info=dict(json.loads(row.info)),
                    registered_ago=pretty_date(row.created))
        accounts.append(user)
    return accounts


def delete_user_summary(name):
    """Delete from cache the user summary."""
    delete_memoized(get_user_summary, name)
