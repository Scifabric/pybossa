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
"""Dashboard queries to be used in admin dashboard view."""
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from pybossa.core import db
from datetime import datetime


def _select_from_materialized_view(view, n_days=None):
    if n_days is None:
        sql = text("select * from %s" % view)
        options = {}
    else:
        sql = text("""SELECT COUNT(user_id)
                   FROM %s
                   WHERE n_days=:n_days""" % view)
        options = dict(n_days=n_days)
    try:
        session = db.slave_session
        return session.execute(sql, options)
    except ProgrammingError:
        db.slave_session.rollback()
        raise


def format_users_week():
    """Return a variable with users data."""
    results = _select_from_materialized_view('dashboard_week_users')
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
    results = _select_from_materialized_view('dashboard_week_anon')
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
    results = _select_from_materialized_view('dashboard_week_project_new')
    new_projects_last_week = []
    for row in results:
        datum = dict(day=row.day, id=row.id, short_name=row.short_name,
                     p_name=row.name, owner_id=row.owner_id, u_name=row.u_name,
                     email_addr=row.email_addr)
        new_projects_last_week.append(datum)
    return new_projects_last_week


def format_update_projects():
    """Return updated projects data."""
    results = _select_from_materialized_view('dashboard_week_project_update')
    update_projects_last_week = []
    for row in results:
        datum = dict(day=row.day, id=row.id, short_name=row.short_name,
                     p_name=row.name, owner_id=row.owner_id, u_name=row.u_name,
                     email_addr=row.email_addr)
        update_projects_last_week.append(datum)
    return update_projects_last_week


def format_new_tasks():
    """Return new tasks data."""
    results = _select_from_materialized_view('dashboard_week_new_task')
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
    results = _select_from_materialized_view('dashboard_week_new_task_run')
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
    results = _select_from_materialized_view('dashboard_week_new_users')
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
    # Returning Users
    labels = []
    series = []
    for i in range(1, 8):
        if i == 1:
            label = "%s day" % i
        else:
            label = "%s days" % i
        results = _select_from_materialized_view('dashboard_week_returning_users',
                                                 n_days=i)
        total = 0
        for row in results:
            total = row.count
        labels.append(label)
        series.append(total)

    returning_users_week = dict(labels=labels, series=[series])
    return returning_users_week
