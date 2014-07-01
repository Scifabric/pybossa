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
    if user:
        rank_score = rank_and_score(user['id'])
        user['rank'] = rank_score['rank']
        user['score'] = rank_score['score']
        user['total'] = get_total_users()
        return user
    else: # pragma: no cover
        return None


def rank_and_score(user_id):
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
    results = db.engine.execute(sql, user_id=user_id)
    rank_and_score = dict(rank=None, score=None)
    for row in results:
        rank_and_score['rank'] = row.rank
        rank_and_score['score'] = row.score
    return rank_and_score


def apps_contributed(user_id):
    sql = text('''
               SELECT app.name, app.short_name, app.info,
               COUNT(*) as n_task_runs
               FROM task_run JOIN app ON
               (task_run.app_id=app.id) WHERE task_run.user_id=:user_id
               GROUP BY app.name, app.short_name, app.info
               ORDER BY n_task_runs DESC;''')

    results = db.engine.execute(sql, user_id=user_id)
    apps_contributed = []
    for row in results:
        app = dict(name=row.name, short_name=row.short_name,
                   info=json.loads(row.info), n_task_runs=row.n_task_runs)
        apps_contributed.append(app)
    return apps_contributed


def published_apps(user_id):
    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
               app.owner_id,
               app.info
               FROM app, task
               WHERE app.id=task.app_id AND app.owner_id=:user_id AND
               app.hidden=0 AND app.info LIKE('%task_presenter%')
               GROUP BY app.id, app.name, app.short_name,
               app.description,
               app.info;''')
    apps_published = []
    results = db.engine.execute(sql, user_id=user_id)
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   owner_id=row.owner_id,
                   description=row.description,
                   info=json.loads(row.info))
        apps_published.append(app)
    return apps_published


def draft_apps(user_id):
    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
               owner_id,
               app.info
               FROM app
               WHERE app.owner_id=:user_id
               AND app.info NOT LIKE('%task_presenter%')
               GROUP BY app.id, app.name, app.short_name,
               app.description,
               app.info;''')
    apps_draft = []
    results = db.engine.execute(sql, user_id=user_id)
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   owner_id=row.owner_id,
                   description=row.description,
                   info=json.loads(row.info))
        apps_draft.append(app)
    return apps_draft


def hidden_apps(user_id):
    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
               app.owner_id,
               app.info
               FROM app, task
               WHERE app.id=task.app_id AND app.owner_id=:user_id AND
               app.hidden=1 AND app.info LIKE('%task_presenter%')
               GROUP BY app.id, app.name, app.short_name,
               app.description,
               app.info;''')
    apps_published = []
    results = db.engine.execute(sql, user_id=user_id)
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   owner_id=row.owner_id,
                   description=row.description,
                   info=json.loads(row.info))
        apps_published.append(app)
    return apps_published


#TOTEST
@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def apps_created(user_id):
    # Get the CREATED APPS by the USER without any filter
    sql = text('''
               SELECT app.id, app.name, app.short_name, app.info, app.created
               FROM app
               WHERE app.owner_id=:user_id
               ORDER BY app.created DESC;
               ''')
    results = db.engine.execute(sql, user_id=user_id)
    apps_created = []
    for row in results:
        app = dict(id=row.id, name=row.name,
                   short_name=row.short_name, created=row.apps_created,
                   info=dict(json.loads(row.info)))
        apps_created.append(app)
    return apps_created


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
