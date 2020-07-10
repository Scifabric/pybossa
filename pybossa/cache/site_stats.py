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
from functools import wraps
from sqlalchemy.sql import text
from flask import current_app

from pybossa.core import db
from pybossa.cache import cache, memoize, ONE_DAY, ONE_WEEK
import app_settings
from pybossa.cache import sentinel, management_dashboard_stats
from pybossa.cache import get_cache_group_key, delete_cache_group

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
    if app_settings.config.get('DISABLE_ANONYMOUS_ACCESS'):
        return 0

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
               WHERE info IS NOT NULL;
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
               AND DATE(task_run.finish_time) > current_timestamp - interval '1 day'
               GROUP BY project.id
               ORDER BY n_answers DESC LIMIT 5;''')

    results = session.execute(sql, dict(limit=5))
    top5_apps_24_hours = []
    for row in results:
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
               AND DATE(task_run.finish_time) > current_timestamp - interval '1 day'
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


def allow_all_time(func):
    @wraps(func)
    def wrapper(days=30):
        if days == 'all':
            days = 999999
        return func(days=days)
    return wrapper


@memoize(ONE_WEEK, cache_group_keys=['number_of_created_jobs'])
@allow_all_time
def number_of_created_jobs(days=30):
    """Number of created jobs"""
    sql = text('''
        SELECT COUNT(id) FROM project
        WHERE
        clock_timestamp() - to_timestamp(created, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            < interval ':days days';
    ''')
    return session.execute(sql, dict(days=days)).scalar()


@memoize(ONE_WEEK, cache_group_keys=['number_of_active_jobs'])
@allow_all_time
def number_of_active_jobs(days=30):
    """Number of jobs with submissions"""
    sql = text('''
        WITH activity AS (SELECT project.id as id,
               MAX(task_run.finish_time) as last_activity
            FROM project LEFT JOIN task_run
            ON project.id = task_run.project_id
            GROUP BY project.id)
        SELECT COUNT(id) FROM activity
        WHERE clock_timestamp() -
              to_timestamp(last_activity, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            < interval ':days days';
        ''')
    return session.execute(sql, dict(days=days)).scalar()


@memoize(ONE_WEEK, cache_group_keys=['number_of_created_tasks'])
@allow_all_time
def number_of_created_tasks(days=30):
    """Number of created tasks"""
    sql = text('''
        SELECT count(id) FROM task
        WHERE
        to_timestamp(created, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            > NOW() - interval ':days days';
        ''')
    return session.execute(sql, dict(days=days)).scalar()


@memoize(ONE_WEEK, cache_group_keys=['number_of_completed_tasks'])
@allow_all_time
def number_of_completed_tasks(days=30):
    """Number of completed tasks"""
    sql = text('''
        WITH taskruns AS (
            SELECT DISTINCT task_id FROM task_run
            WHERE to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            >= NOW() -  interval ':days days')
        SELECT COUNT(*) FROM task JOIN taskruns
        ON task.id = taskruns.task_id
        WHERE task.state = 'completed';
        ''')
    return session.execute(sql, dict(days=days)).scalar()


@memoize(ONE_WEEK, cache_group_keys=['number_of_active_users'])
@allow_all_time
def number_of_active_users(days=30):
    """Number of active users"""
    sql = text('''
        WITH active_users AS (
            SELECT DISTINCT(user_id) as id FROM task_run
            WHERE to_timestamp(task_run.finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            > NOW() - interval ':days days')
        SELECT COUNT(id) FROM active_users;
    ''')
    return session.execute(sql, dict(days=days)).scalar()


@memoize(ONE_WEEK, cache_group_keys=['categories_with_new_projects'])
@allow_all_time
def categories_with_new_projects(days=30):
    """Categories with new projects"""
    sql = text('''
        WITH active_categories AS(
            SELECT category.id as id FROM category JOIN project
            ON category.id = project.category_id
            WHERE clock_timestamp() -
                  to_timestamp(project.created, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                  < interval ':days days'
            GROUP BY category.id)
        SELECT COUNT(id) from active_categories;
    ''')
    return session.execute(sql, dict(days=days)).scalar()


@memoize(ONE_WEEK, cache_group_keys=['avg_time_to_complete_task'])
@allow_all_time
def avg_time_to_complete_task(days=30):
    """Average time to complete a task"""
    sql = text('''
        WITH taskruns AS (
            SELECT finish_time, created FROM task_run
            WHERE to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            > NOW() -  interval ':days days'
        )
        SELECT to_char(
            AVG(
                to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24-MI-SS.US') -
                to_timestamp(created, 'YYYY-MM-DD"T"HH24-MI-SS.US')
            ),
            'MI"m" SS"s"'
        )
        AS average_time from taskruns;
    ''')
    return session.execute(sql, dict(days=days)).scalar() or 'N/A'


@memoize(ONE_WEEK, cache_group_keys=['avg_task_per_job'])
def avg_task_per_job():
    """Average number of tasks per job"""
    sql = text('''
        SELECT AVG(ct) FROM (
            SELECT project_id, count(task.id) AS ct
            FROM task
            GROUP BY project_id
        ) AS t WHERE ct > 0;
        ''')
    return session.execute(sql).scalar()


@memoize(ONE_WEEK, cache_group_keys=['tasks_per_category'])
def tasks_per_category():
    """Average number of tasks per category"""
    sql = text('''
        SELECT AVG(ct) FROM (
            SELECT p.category_id, COUNT(t.id) AS ct
            FROM project p LEFT OUTER JOIN task t
            ON p.id = t.project_id
            GROUP BY p.category_id
        ) AS t WHERE ct > 0;
    ''')
    return session.execute(sql).scalar() or 'N/A'


@memoize(ONE_WEEK, cache_group_keys=['project_chart'])
def project_chart():
    """
    Fetch data for a monthly chart of the number of projects
    """
    sql = text('''
        WITH dates AS (
            SELECT * FROM
            generate_series(
                date_trunc('month', clock_timestamp()) - interval '24 month',
                clock_timestamp(),
                '1 month') as date
        )
        SELECT date, count(project.id) as num_created FROM
        dates LEFT JOIN project ON
            to_timestamp(project.created, 'YYYY-MM-DD"T"HH24:MI:SS.US') < dates.date
        GROUP BY date ORDER  BY date ASC;
        ''')
    rows = session.execute(sql).fetchall()
    labels = [date.strftime('%b %Y') for date, _ in rows]
    series = [count for _, count in rows]
    return dict(labels=labels, series=[series])


@memoize(ONE_WEEK, cache_group_keys=['category_chart'])
def category_chart():
    """
    Fetch data for a monthly chart of the number of categories
    """
    sql = text('''
        WITH dates AS (
            SELECT * FROM
            generate_series(
                date_trunc('month', clock_timestamp()) - interval '24 month',
                clock_timestamp(),
                '1 month') as date
        )
        SELECT date, count(category.id) as num_created FROM
        dates LEFT JOIN category ON
            to_timestamp(category.created, 'YYYY-MM-DD"T"HH24:MI:SS.US') < dates.date
        GROUP BY date ORDER  BY date ASC;
        ''')
    rows = session.execute(sql).fetchall()
    labels = [date.strftime('%b %Y') for date, _ in rows]
    series = [count for _, count in rows]
    return dict(labels=labels, series=[series])


@memoize(ONE_WEEK, cache_group_keys=['task_chart'])
def task_chart():
    """
    Fetch data for a monthly chart of the number of tasks
    """
    sql = text('''
        SELECT  count(id),
        date_trunc('month', to_timestamp(created, 'YYYY-MM-DD"T"HH24:MI:SS.US'::text))
        AS created_monthly
        FROM task
        GROUP BY created_monthly
        ORDER BY created_monthly DESC
        LIMIT 24;
        ''')
    rows = session.execute(sql).fetchall()
    labels = [date.strftime('%b %Y') for _, date in rows]
    series = [count for count, _ in rows]
    labels.reverse()
    series.reverse()
    return dict(labels=labels, series=[series])


@memoize(ONE_WEEK, cache_group_keys=['submission_chart'])
def submission_chart():
    """
    Fetch data for a monthly chart of the number of submissions
    """
    sql = text('''
        SELECT  count(id),
        date_trunc('month', to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US'::text))
        AS task_run_monthly
        FROM task_run
        GROUP BY task_run_monthly
        ORDER BY task_run_monthly DESC
        LIMIT 24;
        ''')
    rows = session.execute(sql).fetchall()
    labels = [date.strftime('%b %Y') for _, date in rows]
    series = [count for count, _ in rows]
    labels.reverse()
    series.reverse()
    return dict(labels=labels, series=[series])


def management_dashboard_stats_cached():
    stats_cached = all([bool(list(sentinel.slave.smembers(get_cache_group_key((ms)))))
        for ms in management_dashboard_stats])

    if not stats_cached:
        # reset stats for any missing stat
        map(delete_cache_group, management_dashboard_stats)
    return stats_cached
