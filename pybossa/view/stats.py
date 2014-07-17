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
import json
import pygeoip
from flask import Blueprint, current_app
from flask import render_template
from sqlalchemy.sql import text

from pybossa.core import db, get_session
from pybossa.cache import cache, ONE_DAY
from pybossa.cache import apps as cached_apps

blueprint = Blueprint('stats', __name__)


@cache(timeout=ONE_DAY, key_prefix="site_n_auth_users")
def n_auth_users():
    try:
        session = get_session(db, bind='slave')
        sql = text('''SELECT COUNT("user".id) AS n_auth FROM "user";''')
        results = session.execute(sql)
        for row in results:
            n_auth = row.n_auth
        return n_auth or 0
    except:
        session.rollback()
        raise
    finally:
        session.close()

@cache(timeout=ONE_DAY, key_prefix="site_n_anon_users")
def n_anon_users():
    try:
        session = get_session(db, bind='slave')
        sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip))
                   AS n_anon FROM task_run;''')

        results = session.execute(sql)
        for row in results:
            n_anon = row.n_anon
        return n_anon or 0
    except:
        session.rollback()
        raise
    finally:
        session.close()


@cache(timeout=ONE_DAY, key_prefix="site_n_tasks")
def n_tasks_site():
    try:
        session = get_session(db, bind='slave')
        sql = text('''SELECT COUNT(task.id) AS n_tasks FROM task''')
        results = session.execute(sql)
        for row in results:
            n_tasks = row.n_tasks
        return n_tasks or 0
    except:
        session.rollback()
        raise
    finally:
        session.close()


@cache(timeout=ONE_DAY, key_prefix="site_n_total_tasks")
def n_total_tasks_site():
    try:
        session = get_session(db, bind='slave')
        sql = text('''SELECT SUM(n_answers) AS n_tasks FROM task''')
        results = session.execute(sql)
        for row in results:
            total = row.n_tasks
        return total or 0
    except:
        session.rollback()
        raise
    finally:
        session.close()


@cache(timeout=ONE_DAY, key_prefix="site_n_task_runs")
def n_task_runs_site():
    try:
        session = get_session(db, bind='slave')
        sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run''')
        results = session.execute(sql)
        for row in results:
            n_task_runs = row.n_task_runs
        return n_task_runs or 0
    except:
        session.rollback()
        raise
    finally:
        session.close()


@cache(timeout=ONE_DAY, key_prefix="site_top5_apps_24_hours")
def get_top5_apps_24_hours():
    # Top 5 Most active apps in last 24 hours
    sql = text('''SELECT app.id, app.name, app.short_name, app.info,
               COUNT(task_run.app_id) AS n_answers FROM app, task_run
               WHERE app.id=task_run.app_id
               AND app.hidden=0
               AND DATE(task_run.finish_time) > NOW() - INTERVAL '24 hour'
               AND DATE(task_run.finish_time) <= NOW()
               GROUP BY app.id
               ORDER BY n_answers DESC LIMIT 5;''')

    results = db.engine.execute(sql, limit=5)
    top5_apps_24_hours = []
    for row in results:
        tmp = dict(id=row.id, name=row.name, short_name=row.short_name,
                   info=dict(json.loads(row.info)), n_answers=row.n_answers)
        top5_apps_24_hours.append(tmp)
    return top5_apps_24_hours


@cache(timeout=ONE_DAY, key_prefix="site_top5_users_24_hours")
def get_top5_users_24_hours():
    # Top 5 Most active users in last 24 hours
    sql = text('''SELECT "user".id, "user".fullname, "user".name,
               COUNT(task_run.app_id) AS n_answers FROM "user", task_run
               WHERE "user".id=task_run.user_id
               AND DATE(task_run.finish_time) > NOW() - INTERVAL '24 hour'
               AND DATE(task_run.finish_time) <= NOW()
               GROUP BY "user".id
               ORDER BY n_answers DESC LIMIT 5;''')

    results = db.engine.execute(sql, limit=5)
    top5_users_24_hours = []
    for row in results:
        user = dict(id=row.id, fullname=row.fullname,
                    name=row.name,
                    n_answers=row.n_answers)
        top5_users_24_hours.append(user)
    return top5_users_24_hours


@cache(timeout=ONE_DAY, key_prefix="site_locs")
def get_locs(): # pragma: no cover
    # All IP addresses from anonymous users to create a map
    locs = []
    if current_app.config['GEO']:
        sql = '''SELECT DISTINCT(user_ip) from task_run WHERE user_ip IS NOT NULL;'''
        results = db.engine.execute(sql)

        geolite = current_app.root_path + '/../dat/GeoLiteCity.dat'
        gic = pygeoip.GeoIP(geolite)
        for row in results:
            loc = gic.record_by_addr(row.user_ip)
            if loc is None:
                loc = {}
            if (len(loc.keys()) == 0):
                loc['latitude'] = 0
                loc['longitude'] = 0
            locs.append(dict(loc=loc))
    return locs


@blueprint.route('/')
def index():
    """Return Global Statistics for the site"""

    title = "Global Statistics"

    n_auth = n_auth_users()

    n_anon = n_anon_users()

    n_total_users = n_anon + n_auth

    n_published_apps = cached_apps.n_published()
    n_draft_apps = cached_apps.n_draft()
    n_total_apps = n_published_apps + n_draft_apps

    n_tasks = n_tasks_site()

    n_task_runs = n_task_runs_site()

    top5_apps_24_hours = get_top5_apps_24_hours()

    top5_users_24_hours = get_top5_users_24_hours()

    locs = get_locs()

    show_locs = False
    if len(locs) > 0:
        show_locs = True

    stats = dict(n_total_users=n_total_users, n_auth=n_auth, n_anon=n_anon,
                 n_published_apps=n_published_apps,
                 n_draft_apps=n_draft_apps,
                 n_total_apps=n_total_apps,
                 n_tasks=n_tasks,
                 n_task_runs=n_task_runs)

    users = dict(label="User Statistics",
                 values=[
                     dict(label='Anonymous', value=[0, n_anon]),
                     dict(label='Authenticated', value=[0, n_auth])])

    apps = dict(label="Apps Statistics",
                values=[
                    dict(label='Published', value=[0, n_published_apps]),
                    dict(label='Draft', value=[0, n_draft_apps])])

    tasks = dict(label="Task and Task Run Statistics",
                 values=[
                     dict(label='Tasks', value=[0, n_tasks]),
                     dict(label='Answers', value=[1, n_task_runs])])

    return render_template('/stats/global.html', title=title,
                           users=json.dumps(users),
                           apps=json.dumps(apps),
                           tasks=json.dumps(tasks),
                           locs=json.dumps(locs),
                           show_locs=show_locs,
                           top5_users_24_hours=top5_users_24_hours,
                           top5_apps_24_hours=top5_apps_24_hours,
                           stats=stats)
