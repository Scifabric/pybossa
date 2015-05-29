# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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
"""Dashboard Jobs module for running background tasks in PyBossa server."""
from sqlalchemy import text
from pybossa.core import db
from datetime import datetime

MINUTE = 60


def get_dashboard_jobs():  # pragma: no cover
    """Return dashboard jobs."""
    yield dict(name=dashboard_active_users_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_active_anon_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_new_projects_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_update_projects_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_new_tasks_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_new_task_runs_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_new_users_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=dashboard_returning_users_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')


def dashboard_active_users_week():
    """Get active users last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_users');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_users''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_users AS
                       WITH crafters_per_day AS
                            (select to_date(task_run.finish_time,
                                            'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                                    user_id, COUNT(task_run.user_id) AS day_crafters
                            FROM task_run
                            WHERE to_date(task_run.finish_time,
                                          'YYYY-MM-DD\THH24:MI:SS.US')
                                >= NOW() - ('1 week'):: INTERVAL
                            GROUP BY day, task_run.user_id)
                       SELECT day, COUNT(crafters_per_day.user_id) AS n_users
                       FROM crafters_per_day GROUP BY day ORDER BY day;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"


def dashboard_active_anon_week():
    """Get active anon last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_anon');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_anon''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_anon AS
                       WITH crafters_per_day AS
                            (select to_date(task_run.finish_time,
                                            'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                                    user_ip, COUNT(task_run.user_ip) AS day_crafters
                            FROM task_run
                            WHERE to_date(task_run.finish_time,
                                          'YYYY-MM-DD\THH24:MI:SS.US')
                                >= NOW() - ('1 week'):: INTERVAL
                            GROUP BY day, task_run.user_ip)
                       SELECT day, COUNT(crafters_per_day.user_ip) AS n_users
                       FROM crafters_per_day GROUP BY day ORDER BY day;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"

def dashboard_new_projects_week():
    """Get new created projects last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_project_new');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_project_new''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_project_new AS
                       SELECT TO_DATE(project.created, 'YYYY-MM-DD\THH24:MI:SS.US') as day,
                       project.id, short_name, project.name,
                       owner_id, "user".name as u_name, "user".email_addr
                       FROM project, "user"
                       WHERE TO_DATE(project.created,
                                    'YYYY-MM-DD\THH24:MI:SS.US') >= now() -
                                    ('1 week')::INTERVAL
                       AND "user".id=project.owner_id
                       GROUP BY project.id, "user".name, "user".email_addr;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"


def dashboard_update_projects_week():
    """Get updated projects last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_project_update');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_project_update''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_project_update AS
                       SELECT TO_DATE(project.updated, 'YYYY-MM-DD\THH24:MI:SS.US') as day,
                       project.id, short_name, project.name,
                       owner_id, "user".name as u_name, "user".email_addr
                       FROM project, "user"
                       WHERE TO_DATE(project.updated,
                                    'YYYY-MM-DD\THH24:MI:SS.US') >= now() -
                                    ('1 week')::INTERVAL
                       AND "user".id=project.owner_id
                       GROUP BY project.id, "user".name, "user".email_addr;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"


def dashboard_new_tasks_week():
    """Get new tasks last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_new_task');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_new_task''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_new_task AS
                          SELECT TO_DATE(task.created,
                                         'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                          COUNT(task.id) AS day_tasks
                          FROM task WHERE TO_DATE(task.created,
                                                  'YYYY-MM-DD\THH24:MI:SS.US')
                                              >= now() - ('1 week'):: INTERVAL
                          GROUP BY day;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"


def dashboard_new_task_runs_week():
    """Get new task_runs last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_new_task_run');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_new_task_run''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_new_task_run AS
                          SELECT TO_DATE(task_run.finish_time,
                                         'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                          COUNT(task_run.id) AS day_task_runs
                          FROM task_run WHERE TO_DATE(task_run.finish_time,
                                                  'YYYY-MM-DD\THH24:MI:SS.US')
                                              >= now() - ('1 week'):: INTERVAL
                          GROUP BY day;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"

def dashboard_new_users_week():
    """Get new users last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_new_users');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_new_users''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_new_users AS
                          SELECT TO_DATE("user".created,
                                         'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                          COUNT("user".id) AS day_users
                          FROM "user" WHERE TO_DATE("user".created,
                                                  'YYYY-MM-DD\THH24:MI:SS.US')
                                              >= now() - ('1 week'):: INTERVAL
                          GROUP BY day;''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"

def dashboard_returning_users_week():
    """Get returning users last week."""
    # Check first if the materialized view exists
    sql = text('''SELECT EXISTS (SELECT relname FROM pg_class WHERE
               relname='dashboard_week_returning_users');''')
    results = db.slave_session.execute(sql)
    for row in results:
        if row.exists:
            sql = text('''REFRESH MATERIALIZED VIEW
                       dashboard_week_returning_users''')
            db.session.execute(sql)
            return "Materialized view refreshed"
        else:
            sql = text('''CREATE MATERIALIZED VIEW dashboard_week_returning_users AS
                       WITH data AS (
                        SELECT user_id, TO_DATE(task_run.finish_time,
                        'YYYY-MM-DD\THH24:MI:SS.US') AS day
                       FROM task_run
                       WHERE TO_DATE(task_run.finish_time,
                       'YYYY-MM-DD\THH24:MI:SS.US') >= NOW()
                       - ('1 week')::INTERVAL GROUP BY day, task_run.user_id)
                       SELECT user_id, COUNT(user_id) AS n_days
                       FROM data GROUP BY user_id HAVING(count(user_id) > 1)
                       ORDER by n_days;
                          ''')
            results = db.session.execute(sql)
            db.session.commit()
            return "Materialized view created"

def format_users_week():
    """Return a variable with users data."""
    session = db.slave_session
    # Registered users
    sql = text('''select * from dashboard_week_users''')
    results = session.execute(sql)
    labels = []
    series = []
    for row in results:
        labels.append(row.day.strftime('%Y-%m-%d'))
        series.append(int(row.n_users))
    if len(labels) == 0:
        labels.append(datetime.now().strftime('%Y-%m-%d'))
    if len(series) == 0:
        series.append(0)
    active_users_last_week = dict(labels=labels, series=[series])
    return active_users_last_week

def format_anon_week():
    """Return a variable with anon data."""
    session = db.slave_session
    # Anon users
    sql = text('''select * from dashboard_week_anon''')
    results = session.execute(sql)
    labels = []
    series = []
    for row in results:
        labels.append(row.day.strftime('%Y-%m-%d'))
        series.append(int(row.n_users))
    if len(labels) == 0:
        labels.append(datetime.now().strftime('%Y-%m-%d'))
    if len(series) == 0:
        series.append(0)
    active_anon_last_week = dict(labels=labels, series=[series])
    return active_anon_last_week

def format_new_projects():
    """Return new projects data."""
    session = db.slave_session
    # New projects
    sql = text('''select * from dashboard_week_project_new''')
    results = session.execute(sql)
    new_projects_last_week = []
    for row in results:
        datum = dict(day=row.day, id=row.id, short_name=row.short_name,
                     p_name=row.name, owner_id=row.owner_id, u_name=row.u_name,
                     email_addr=row.email_addr)
        new_projects_last_week.append(datum)
    return new_projects_last_week

def format_update_projects():
    """Return updated projects data."""
    session = db.slave_session
    # Updated projects
    sql = text('''select * from dashboard_week_project_update''')
    results = session.execute(sql)
    update_projects_last_week = []
    for row in results:
        datum = dict(day=row.day, id=row.id, short_name=row.short_name,
                     p_name=row.name, owner_id=row.owner_id, u_name=row.u_name,
                     email_addr=row.email_addr)
        update_projects_last_week.append(datum)
    return update_projects_last_week

def format_new_tasks():
    """Return new tasks data."""
    session = db.slave_session
    # New task
    sql = text('''select * from dashboard_week_new_task''')
    results = session.execute(sql)
    labels = []
    series = []
    for row in results:
        labels.append(row.day.strftime('%Y-%m-%d'))
        series.append(row.day_tasks)
    if len(labels) == 0:
        labels.append(datetime.now().strftime('%Y-%m-%d'))
    if len(series) == 0:
        series.append(0)
    new_tasks_week = dict(labels=labels, series=[series])
    return new_tasks_week

def format_new_task_runs():
    """Return new task runs data."""
    session = db.slave_session
    # New task_runs
    sql = text('''select * from dashboard_week_new_task_run''')
    results = session.execute(sql)
    labels = []
    series = []
    for row in results:
        labels.append(row.day.strftime('%Y-%m-%d'))
        series.append(row.day_task_runs)
    if len(labels) == 0:
        labels.append(datetime.now().strftime('%Y-%m-%d'))
    if len(series) == 0:
        series.append(0)
    new_task_runs_week = dict(labels=labels, series=[series])
    return new_task_runs_week


def format_new_users():
    """Return new registered users data."""
    session = db.slave_session
    # New Users
    sql = text('''select * from dashboard_week_new_users''')
    results = session.execute(sql)
    labels = []
    series = []
    for row in results:
        labels.append(row.day.strftime('%Y-%m-%d'))
        series.append(row.day_users)
    if len(labels) == 0:
        labels.append(datetime.now().strftime('%Y-%m-%d'))
    if len(series) == 0:
        series.append(0)

    new_users_week = dict(labels=labels, series=[series])
    return new_users_week

def format_returning_users():
    """Return returning users data."""
    session = db.slave_session
    # Returning Users
    labels = []
    series = []
    for i in range(1, 8):
        if (i == 1):
            label = "%s day" % i
        else:
            label = "%s days" % i
        sql = text('''SELECT COUNT(user_id)
                   FROM dashboard_week_returning_users
                   WHERE n_days=:n_days''')
        results = session.execute(sql, dict(n_days=i))
        total = 0
        for row in results:
            total = row.count
        labels.append(label)
        series.append(total)

    returning_users_week = dict(labels=labels, series=[series])
    return returning_users_week
