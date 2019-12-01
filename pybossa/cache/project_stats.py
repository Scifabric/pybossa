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
"""Cache module for project stats."""
from flask import current_app
from sqlalchemy.sql import text
from pybossa.core import db
from pybossa.cache import memoize, ONE_DAY, FIVE_MINUTES
import pybossa.cache.projects as cached_projects
from pybossa.model.project_stats import ProjectStats
from flask_babel import gettext

import operator
import time
import datetime
import os


session = db.slave_session


@memoize(timeout=ONE_DAY)
def n_tasks(project_id):
    """Return number of tasks of project.

    Data is cached for one day.
    """
    from pybossa.cache import projects
    return projects.n_tasks(project_id)


@memoize(timeout=ONE_DAY)
def stats_users(project_id, period=None):
    """Return users's stats for a given project_id."""
    users = {}
    auth_users = []
    anon_users = []

    # Get Authenticated Users
    params = dict(project_id=project_id)
    sql = text('''SELECT task_run.user_id AS user_id,
               COUNT(task_run.id) as n_tasks FROM task_run
               WHERE task_run.user_id IS NOT NULL AND
               task_run.user_ip IS NULL AND
               task_run.project_id=:project_id
               GROUP BY task_run.user_id ORDER BY n_tasks DESC
               LIMIT 5;''')\
        .execution_options(stream=True)
    if period:
        sql = text('''SELECT task_run.user_id AS user_id,
                   COUNT(task_run.id) as n_tasks FROM task_run
                   WHERE task_run.user_id IS NOT NULL AND
                   task_run.user_ip IS NULL AND
                   task_run.project_id=:project_id AND
                   TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                   >= NOW() AT TIME ZONE 'utc' - :period ::INTERVAL
                   GROUP BY task_run.user_id ORDER BY n_tasks DESC
                   LIMIT 5;''')\
            .execution_options(stream=True)
        params['period'] = period

    results = session.execute(sql, params)

    for row in results:
        auth_users.append([row.user_id, row.n_tasks])

    sql = text('''SELECT count(distinct(task_run.user_id)) AS user_id
               FROM task_run WHERE task_run.user_id IS NOT NULL AND
               task_run.user_ip IS NULL AND
               task_run.project_id=:project_id;''')
    if period:
        sql = text('''SELECT count(distinct(task_run.user_id)) AS user_id
                   FROM task_run WHERE task_run.user_id IS NOT NULL AND
                   task_run.user_ip IS NULL AND
                   task_run.project_id=:project_id AND
                   TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                   >= NOW() AT TIME ZONE 'utc' - :period ::INTERVAL
                   ;''')

    results = session.execute(sql, params)
    for row in results:
        users['n_auth'] = row[0]

    # Get all Anonymous Users
    sql = text('''SELECT task_run.user_ip AS user_ip,
               COUNT(task_run.id) as n_tasks FROM task_run
               WHERE task_run.user_ip IS NOT NULL AND
               task_run.user_id IS NULL AND
               task_run.project_id=:project_id
               GROUP BY task_run.user_ip ORDER BY n_tasks DESC;''')\
        .execution_options(stream=True)

    if period:
        sql = text('''SELECT task_run.user_ip AS user_ip,
                   COUNT(task_run.id) as n_tasks FROM task_run
                   WHERE task_run.user_ip IS NOT NULL AND
                   task_run.user_id IS NULL AND
                   task_run.project_id=:project_id AND
                   TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                   >= NOW() AT TIME ZONE 'utc' - :period ::INTERVAL
                   GROUP BY task_run.user_ip ORDER BY n_tasks DESC;''')\
            .execution_options(stream=True)

    results = session.execute(sql, params)

    for row in results:
        anon_users.append([row.user_ip, row.n_tasks])

    sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip)) AS user_ip
               FROM task_run WHERE task_run.user_ip IS NOT NULL AND
               task_run.user_id IS NULL AND
               task_run.project_id=:project_id;''')
    if period:
        sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip)) AS user_ip
                   FROM task_run WHERE task_run.user_ip IS NOT NULL AND
                   task_run.user_id IS NULL AND
                   task_run.project_id=:project_id AND
                   TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                   >= NOW() AT TIME ZONE 'utc' - :period ::INTERVAL
                   ;''')

    results = session.execute(sql, params)

    for row in results:
        users['n_anon'] = row[0]

    return users, anon_users, auth_users


def convert_period_to_days(period):
    """Convert SQL period into integer days."""
    try:
        if 'day' in period:
            int_period = int(period.split(' ')[0])
        elif 'week' in period:
            int_period = int(period.split(' ')[0]) * 7
        elif 'month' in period:
            int_period = int(period.split(' ')[0]) * 30
        elif 'year' in period:
            int_period = int(period.split(' ')[0]) * 365
        else:
            int_period = 0
    except ValueError:
        int_period = 0
    return int_period


@memoize(timeout=ONE_DAY)
def stats_dates(project_id, period='15 day'):
    """Return statistics with dates for a project."""
    dates = {}
    dates_anon = {}
    dates_auth = {}

    n_tasks(project_id)

    params = dict(project_id=project_id, period=period)

    # Get all completed tasks
    sql = text('''
               WITH myquery AS (
               SELECT task.id, coalesce(ct, 0) as n_task_runs, task.n_answers
               FROM task LEFT OUTER JOIN
               (SELECT task_id, COUNT(id) AS ct FROM task_run
               WHERE project_id=:project_id AND
               TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
               >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
               GROUP BY task_id) AS log_counts
               ON task.id=log_counts.task_id
               WHERE task.project_id=:project_id ORDER BY id ASC)
               select myquery.id, max(task_run.finish_time) as day
               from task_run, myquery where task_run.task_id=myquery.id
               and
               TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
               >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
               group by myquery.id order by day;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)
    for row in results:
        day = row.day[:10]
        if day in list(dates.keys()):
            dates[day] += 1
        else:
            dates[day] = 1

    # No completed tasks in the last period
    def _fill_empty_days(days, obj):
        if len(days) < convert_period_to_days(period):
            base = datetime.datetime.today()
            for x in range(0, convert_period_to_days(period)):
                tmp_date = base - datetime.timedelta(days=x)
                if tmp_date.strftime('%Y-%m-%d') not in days:
                    obj[tmp_date.strftime('%Y-%m-%d')] = 0
        return obj

    dates = _fill_empty_days(list(dates.keys()), dates)

    # Get all answers per date for auth
    sql = text('''
                WITH myquery AS (
                    SELECT TO_DATE(finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    as d, COUNT(id)
                    FROM task_run WHERE project_id=:project_id
                    AND user_ip IS NULL AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY d)
                SELECT to_char(d, 'YYYY-MM-DD') as d, count from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)
    for row in results:
        dates_auth[row.d] = row.count

    dates_auth = _fill_empty_days(list(dates_auth.keys()), dates_auth)

    # Get all answers per date for anon
    sql = text('''
                WITH myquery AS (
                    SELECT TO_DATE(finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    as d, COUNT(id)
                    FROM task_run WHERE project_id=:project_id
                    AND user_id IS NULL AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY d)
               SELECT to_char(d, 'YYYY-MM-DD') as d, count  from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)
    for row in results:
        dates_anon[row.d] = row.count

    dates_anon = _fill_empty_days(list(dates_anon.keys()), dates_anon)

    return dates, dates_anon, dates_auth


@memoize(timeout=ONE_DAY)
def stats_hours(project_id, period='2 week'):
    """Return statistics of a project per hours."""
    hours = {}
    hours_anon = {}
    hours_auth = {}
    max_hours = 0
    max_hours_anon = 0
    max_hours_auth = 0

    # initialize hours keys
    for i in range(0, 24):
        hours[str(i).zfill(2)] = 0
        hours_anon[str(i).zfill(2)] = 0
        hours_auth[str(i).zfill(2)] = 0

    params = dict(project_id=project_id, period=period)
    # Get hour stats for all users
    sql = text('''
               WITH myquery AS
                (SELECT to_char(
                    DATE_TRUNC('hour',
                        TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ),
                    'HH24') AS h, COUNT(id)
                    FROM task_run WHERE project_id=:project_id AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY h)
               SELECT h, count from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)

    for row in results:
        hours[row.h] = row.count

    # Get maximum stats for all users
    sql = text('''
               WITH myquery AS
                (SELECT to_char(
                    DATE_TRUNC('hour',
                        TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ),
                    'HH24') AS h, COUNT(id)
                    FROM task_run WHERE project_id=:project_id  AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY h)
               SELECT max(count) from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)
    for row in results:
        max_hours = row.max

    # Get hour stats for Anonymous users
    sql = text('''
               WITH myquery AS
                (SELECT to_char(
                    DATE_TRUNC('hour',
                        TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ),
                    'HH24') AS h, COUNT(id)
                    FROM task_run WHERE project_id=:project_id
                    AND user_id IS NULL AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY h)
               SELECT h, count from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)

    for row in results:
        hours_anon[row.h] = row.count

    # Get maximum stats for Anonymous users
    sql = text('''
               WITH myquery AS
                (SELECT to_char(
                    DATE_TRUNC('hour',
                        TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ),
                    'HH24') AS h, COUNT(id)
                    FROM task_run WHERE project_id=:project_id
                    AND user_id IS NULL AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY h)
               SELECT max(count) from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)
    for row in results:
        max_hours_anon = row.max

    # Get hour stats for Auth users
    sql = text('''
               WITH myquery AS
                (SELECT to_char(
                    DATE_TRUNC('hour',
                        TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ),
                    'HH24') AS h, COUNT(id)
                    FROM task_run WHERE project_id=:project_id
                    AND user_ip IS NULL AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY h)
               SELECT h, count from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)

    for row in results:
        hours_auth[row.h] = row.count

    # Get hour stats for Anon users
    sql = text('''
               WITH myquery AS
                (SELECT to_char(
                    DATE_TRUNC('hour',
                        TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                    ),
                    'HH24') AS h, COUNT(id)
                    FROM task_run WHERE project_id=:project_id
                    AND user_ip IS NULL AND
                    TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
                    >= NOW() AT TIME ZONE 'utc' - :period :: INTERVAL
                    GROUP BY h)
               SELECT max(count) from myquery;
               ''').execution_options(stream=True)

    results = session.execute(sql, params)
    for row in results:
        max_hours_auth = row.max

    return hours, hours_anon, hours_auth, max_hours, max_hours_anon, \
        max_hours_auth


@memoize(timeout=ONE_DAY)
def stats_format_dates(project_id, dates, dates_anon, dates_auth):
    """Format dates stats into a JSON format."""
    dayNewStats = dict(label=gettext("Anon + Auth"), values=[])
    dayCompletedTasks = dict(label=gettext("Completed Tasks"),
                             disabled="True", values=[])
    dayNewAnonStats = dict(label=gettext("Anonymous"), values=[])
    dayNewAuthStats = dict(label=gettext("Authenticated"), values=[])

    answer_dates = sorted(list(set(list(dates_anon.keys()) + list(dates_auth.keys()))))
    total = 0

    for d in sorted(dates.keys()):
        # JavaScript expects miliseconds since EPOCH
        # Total tasks completed per day
        total = total + dates[d]
        dayCompletedTasks['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), total])

    for d in answer_dates:
        anon_ans = dates_anon[d] if d in list(dates_anon.keys()) else 0
        auth_ans = dates_auth[d] if d in list(dates_auth.keys()) else 0
        total_ans = anon_ans + auth_ans

        # New answers per day
        dayNewStats['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), total_ans])
        # Anonymous answers per day
        dayNewAnonStats['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), anon_ans])
        # Authenticated answers per day
        dayNewAuthStats['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), auth_ans])

    return dayNewStats, dayNewAnonStats, dayNewAuthStats, \
        dayCompletedTasks


@memoize(timeout=ONE_DAY)
def stats_format_hours(project_id, hours, hours_anon, hours_auth,
                       max_hours, max_hours_anon, max_hours_auth):
    """Format hours stats into a JSON format."""
    hourNewStats = dict(label=gettext("Anon + Auth"),
                        disabled="True", values=[], max=0)
    hourNewAnonStats = dict(label=gettext("Anonymous"), values=[], max=0)
    hourNewAuthStats = dict(label=gettext("Authenticated"),
                            values=[], max=0)

    hourNewStats['max'] = max_hours
    hourNewAnonStats['max'] = max_hours_anon
    hourNewAuthStats['max'] = max_hours_auth

    for h in sorted(hours.keys()):
        # New answers per hour
        if (hours[h] != 0):
            hourNewStats['values'].append([int(h), hours[h],
                                           (hours[h] * 5) / max_hours])
        else:
            hourNewStats['values'].append([int(h), hours[h], 0])

        # New Anonymous answers per hour
        if h in list(hours_anon.keys()):
            if (hours_anon[h] != 0):
                tmph = (hours_anon[h] * 5) / max_hours
                hourNewAnonStats['values'].append([int(h), hours_anon[h], tmph])
            else:
                hourNewAnonStats['values'].append([int(h), hours_anon[h], 0])

        # New Authenticated answers per hour
        if h in list(hours_auth.keys()):
            if (hours_auth[h] != 0):
                tmph = (hours_auth[h] * 5) / max_hours
                hourNewAuthStats['values'].append([int(h), hours_auth[h], tmph])
            else:
                hourNewAuthStats['values'].append([int(h), hours_auth[h], 0])
    return hourNewStats, hourNewAnonStats, hourNewAuthStats


@memoize(timeout=ONE_DAY)
def stats_format_users(project_id, users, anon_users, auth_users):
    """Format User Stats into JSON."""
    userStats = dict(label="User Statistics", values=[])
    userAnonStats = dict(label="Anonymous Users", values=[], top5=[], locs=[])
    userAuthStats = dict(label="Authenticated Users", values=[], top5=[])

    userStats['values'].append(dict(label="Anonymous",
                                    value=[0, users['n_anon']]))
    userStats['values'].append(dict(label="Authenticated",
                                    value=[0, users['n_auth']]))

    for u in anon_users:
        userAnonStats['values'].append(dict(label=u[0], value=[u[1]]))

    for u in auth_users:
        userAuthStats['values'].append(dict(label=u[0], value=[u[1]]))

    # Get location for Anonymous users
    top5_anon = []
    top5_auth = []
    for u in anon_users:
        top5_anon.append(dict(ip=u[0], tasks=u[1]))

    for u in auth_users:
        sql = text('''SELECT name, fullname, restrict from "user" 
                   where id=:id and restrict=false;''')
        results = session.execute(sql, dict(id=u[0]))
        fullname = None
        name = None
        restrict = None
        for row in results:
            fullname = row.fullname
            name = row.name
            restrict = row.restrict
        if (fullname and name and restrict is False):
            top5_auth.append(dict(name=name,
                                  fullname=fullname,
                                  tasks=u[1],
                             restrict=restrict))

    userAnonStats['top5'] = top5_anon[0:5]
    userAuthStats['top5'] = top5_auth

    return dict(users=userStats, anon=userAnonStats, auth=userAuthStats,
                n_anon=users['n_anon'], n_auth=users['n_auth'])


def update_stats(project_id, period='2 week'):
    """Update the stats of a given project."""
    hours, hours_anon, hours_auth, max_hours, \
        max_hours_anon, max_hours_auth = stats_hours(project_id, period)
    users, anon_users, auth_users = stats_users(project_id, period)
    dates, dates_anon, dates_auth = stats_dates(project_id, period)


    sum(dates.values())

    sorted(iter(dates.items()), key=operator.itemgetter(0))

    dates_stats = stats_format_dates(project_id, dates,
                                     dates_anon, dates_auth)

    hours_stats = stats_format_hours(project_id, hours, hours_anon, hours_auth,
                                     max_hours, max_hours_anon, max_hours_auth)

    users_stats = stats_format_users(project_id, users, anon_users, auth_users)

    data = dict(dates_stats=dates_stats,
                hours_stats=hours_stats,
                users_stats=users_stats)
    ps = session.query(ProjectStats).filter_by(project_id=project_id).first()

    n_tasks = cached_projects.n_tasks(project_id)
    n_task_runs = cached_projects.n_task_runs(project_id)
    n_results = cached_projects.n_results(project_id)
    overall_progress = cached_projects.overall_progress(project_id)
    last_activity = cached_projects.last_activity(project_id)
    n_volunteers = cached_projects.n_volunteers(project_id)
    n_completed_tasks = cached_projects.n_completed_tasks(project_id)
    average_time = cached_projects.average_contribution_time(project_id)
    n_blogposts = cached_projects.n_blogposts(project_id)

    if ps is None:
        ps = ProjectStats(project_id=project_id, info=data,
                          n_tasks=n_tasks,
                          n_task_runs=n_task_runs,
                          n_results=n_results,
                          n_volunteers=n_volunteers,
                          n_completed_tasks=n_completed_tasks,
                          average_time=average_time,
                          overall_progress=overall_progress,
                          n_blogposts=n_blogposts,
                          last_activity=last_activity)
        db.session.add(ps)
    else:
        ps.info = data
        ps.n_tasks = n_tasks
        ps.n_task_runs = n_task_runs
        ps.overall_progress = overall_progress
        ps.last_activity = last_activity
        ps.n_results = n_results
        ps.n_completed_tasks = n_completed_tasks
        ps.n_volunteers = n_volunteers
        ps.average_time = average_time
        ps.n_blogposts = n_blogposts
    db.session.commit()
    return dates_stats, hours_stats, users_stats


@memoize(timeout=FIVE_MINUTES)
def get_stats(project_id, period='2 week', full=False):
    """Get project's stats."""
    ps = session.query(ProjectStats).filter_by(project_id=project_id).first()
    if full:
        return ps
    else:
        return ps.info['dates_stats'], ps.info['hours_stats'], ps.info['users_stats']
