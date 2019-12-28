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
"""Cache module for site statistics."""
from sqlalchemy.sql import text
from flask import current_app

from pybossa.core import db
from pybossa.cache import cache, ONE_DAY

session = db.slave_session


@cache(timeout=ONE_DAY, key_prefix="site_n_auth_users")
def n_auth_users():
    """Return number of authenticated users."""
    sql = text('''SELECT COUNT("user".id) AS n_auth FROM "user";''')
    results = session.execute(sql)
    for row in results:
        n_auth = row.n_auth
    return n_auth or 0


@cache(timeout=ONE_DAY, key_prefix="site_n_anon_users")
def n_anon_users():
    """Return number of anonymous users."""
    sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip))
               AS n_anon FROM task_run;''')

    results = session.execute(sql)
    for row in results:
        n_anon = row.n_anon
    return n_anon or 0


@cache(timeout=ONE_DAY, key_prefix="site_n_tasks")
def n_tasks_site():
    """Return number of tasks in the server."""
    sql = text('''SELECT COUNT(task.id) AS n_tasks FROM task''')
    results = session.execute(sql)
    for row in results:
        n_tasks = row.n_tasks
    return n_tasks or 0


@cache(timeout=ONE_DAY, key_prefix="site_n_total_tasks")
def n_total_tasks_site():
    """Return number of total tasks based on redundancy."""
    sql = text('''SELECT SUM(n_answers) AS n_tasks FROM task''')
    results = session.execute(sql)
    for row in results:
        total = row.n_tasks
    return total or 0


@cache(timeout=ONE_DAY, key_prefix="site_n_task_runs")
def n_task_runs_site():
    """Return number of task runs in the server."""
    sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run''')
    results = session.execute(sql)
    for row in results:
        n_task_runs = row.n_task_runs
    return n_task_runs or 0


@cache(timeout=ONE_DAY, key_prefix="site_n_results")
def n_results_site():
    """Return number of results in the server."""
    sql = text('''
               SELECT COUNT(id) AS n_results FROM result
               WHERE info IS NOT NULL
               AND cast(info AS TEXT) != 'null'
               AND cast(info AS TEXT) != '';
               ''')
    results = session.execute(sql)
    for row in results:
        n_results = row.n_results
    return n_results or 0


@cache(timeout=ONE_DAY, key_prefix="site_top5_apps_24_hours")
def get_top5_projects_24_hours():
    """Return the top 5 projects more active in the last 24 hours."""
    # Top 5 Most active projects in last 24 hours
    sql = text('''SELECT project.id, project.name, project.short_name, project.info,
               COUNT(task_run.project_id) AS n_answers FROM project, task_run
               WHERE project.id=task_run.project_id
               AND DATE(task_run.finish_time) > NOW() AT TIME ZONE 'utc' - INTERVAL '24 hour'
               AND DATE(task_run.finish_time) <= NOW() AT TIME ZONE 'utc'
               GROUP BY project.id
               ORDER BY n_answers DESC LIMIT 5;''')

    results = session.execute(sql, dict(limit=5))
    top5_apps_24_hours = []
    for row in results:
        print(row)
        tmp = dict(id=row.id, name=row.name, short_name=row.short_name,
                   info=row.info, n_answers=row.n_answers)
        top5_apps_24_hours.append(tmp)
    return top5_apps_24_hours


@cache(timeout=ONE_DAY, key_prefix="site_top5_users_24_hours")
def get_top5_users_24_hours():
    """Return top 5 users in last 24 hours."""
    # Top 5 Most active users in last 24 hours
    sql = text('''SELECT "user".id, "user".fullname, "user".name,
               "user".restrict,
               COUNT(task_run.project_id) AS n_answers FROM "user", task_run
               WHERE "user".restrict=false AND "user".id=task_run.user_id
               AND DATE(task_run.finish_time) > NOW() AT TIME ZONE 'utc' - INTERVAL '24 hour'
               AND DATE(task_run.finish_time) <= NOW() AT TIME ZONE 'utc'
               GROUP BY "user".id
               ORDER BY n_answers DESC LIMIT 5;''')

    results = session.execute(sql, dict(limit=5))
    top5_users_24_hours = []
    for row in results:
        user = dict(id=row.id, fullname=row.fullname,
                    name=row.name,
                    n_answers=row.n_answers)
        top5_users_24_hours.append(user)
    return top5_users_24_hours
