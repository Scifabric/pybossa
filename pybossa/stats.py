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

from flask import current_app
from sqlalchemy.sql import text
from pybossa.core import db, get_session
from pybossa.cache import cache, memoize, ONE_DAY
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.cache import FIVE_MINUTES, memoize

import string
import pygeoip
import operator
import datetime
import time
from datetime import timedelta



@memoize(timeout=ONE_DAY)
def stats_users(app_id):
    """Return users's stats for a given app_id"""
    try:
        session = get_session(db, bind='slave')

        users = {}
        auth_users = []
        anon_users = []

        # Get Authenticated Users
        sql = text('''SELECT task_run.user_id AS user_id,
                   COUNT(task_run.id) as n_tasks FROM task_run
                   WHERE task_run.user_id IS NOT NULL AND
                   task_run.user_ip IS NULL AND
                   task_run.app_id=:app_id
                   GROUP BY task_run.user_id ORDER BY n_tasks DESC
                   LIMIT 5;''')
        results = session.execute(sql, dict(app_id=app_id))

        for row in results:
            auth_users.append([row.user_id, row.n_tasks])

        sql = text('''SELECT count(distinct(task_run.user_id)) AS user_id FROM task_run
                   WHERE task_run.user_id IS NOT NULL AND
                   task_run.user_ip IS NULL AND
                   task_run.app_id=:app_id;''')

        results = session.execute(sql, dict(app_id=app_id))
        for row in results:
            users['n_auth'] = row[0]

        # Get all Anonymous Users
        sql = text('''SELECT task_run.user_ip AS user_ip,
                   COUNT(task_run.id) as n_tasks FROM task_run
                   WHERE task_run.user_ip IS NOT NULL AND
                   task_run.user_id IS NULL AND
                   task_run.app_id=:app_id
                   GROUP BY task_run.user_ip ORDER BY n_tasks DESC;''').execution_options(stream=True)
        results = session.execute(sql, dict(app_id=app_id))

        for row in results:
            anon_users.append([row.user_ip, row.n_tasks])

        sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip)) AS user_ip FROM task_run
                   WHERE task_run.user_ip IS NOT NULL AND
                   task_run.user_id IS NULL AND
                   task_run.app_id=:app_id;''')

        results = session.execute(sql, dict(app_id=app_id))

        for row in results:
            users['n_anon'] = row[0]

        return users, anon_users, auth_users
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()

### This function ALREADY EXISTS in cache/apps.py, use that one instead!!
def n_tasks(app_id):
    try:
        sql = text('''SELECT COUNT(task.id) AS n_tasks FROM task
                      WHERE task.app_id=:app_id''')
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        n_tasks = 0
        for row in results:
            n_tasks = row.n_tasks
        return n_tasks
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()

@memoize(timeout=ONE_DAY)
def stats_dates(app_id):
    try:
        dates = {}
        dates_anon = {}
        dates_auth = {}
        dates_n_tasks = {}

        session = get_session(db, bind='slave')

        total_n_tasks = n_tasks(app_id)

        # Get all completed tasks
        sql = text('''
                WITH answers AS (
                    SELECT TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US') AS day, task.id, task.n_answers AS n_answers, COUNT(task_run.id) AS day_answers
                    FROM task_run, task WHERE task_run.app_id=:app_id AND task.id=task_run.task_id GROUP BY day, task.id)
                SELECT to_char(day_of_completion, 'YYYY-MM-DD') AS day, COUNT(task_id) AS completed_tasks FROM (
                    SELECT MIN(day) AS day_of_completion, task_id FROM (
                        SELECT ans1.day, ans1.id as task_id, floor(avg(ans1.n_answers)) AS n_answers, sum(ans2.day_answers) AS accum_answers
                        FROM answers AS ans1 INNER JOIN answers AS ans2
                        ON ans1.id=ans2.id WHERE ans1.day >= ans2.day
                        GROUP BY ans1.id, ans1.day) AS answers_day_task
                    WHERE n_answers <= accum_answers
                    GROUP BY task_id) AS completed_tasks_by_day
                GROUP BY day;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))
        for row in results:
            dates[row.day] = row.completed_tasks
            dates_n_tasks[row.day] = total_n_tasks


        # Get all answers per date for auth
        sql = text('''
                    WITH myquery AS (
                        SELECT TO_DATE(finish_time, 'YYYY-MM-DD\THH24:MI:SS.US') as d,
                                       COUNT(id)
                        FROM task_run WHERE app_id=:app_id AND user_ip IS NULL GROUP BY d)
                   SELECT to_char(d, 'YYYY-MM-DD') as d, count from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))
        for row in results:
            dates_auth[row.d] = row.count

        # Get all answers per date for anon
        sql = text('''
                    WITH myquery AS (
                        SELECT TO_DATE(finish_time, 'YYYY-MM-DD\THH24:MI:SS.US') as d,
                                       COUNT(id)
                        FROM task_run WHERE app_id=:app_id AND user_id IS NULL GROUP BY d)
                   SELECT to_char(d, 'YYYY-MM-DD') as d, count  from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))
        for row in results:
            dates_anon[row.d] = row.count

        return dates, dates_n_tasks, dates_anon, dates_auth
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=ONE_DAY)
def stats_hours(app_id):
    try:
        hours = {}
        hours_anon = {}
        hours_auth = {}
        max_hours = 0
        max_hours_anon = 0
        max_hours_auth = 0

        session = get_session(db, bind='slave')

        # initialize hours keys
        for i in range(0, 24):
            hours[str(i).zfill(2)] = 0
            hours_anon[str(i).zfill(2)] = 0
            hours_auth[str(i).zfill(2)] = 0

        # Get hour stats for all users
        sql = text('''
                   WITH myquery AS
                    (SELECT to_char(
                        DATE_TRUNC('hour',
                            TO_TIMESTAMP(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                        ),
                        'HH24') AS h, COUNT(id)
                        FROM task_run WHERE app_id=:app_id GROUP BY h)
                   SELECT h, count from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))

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
                        FROM task_run WHERE app_id=:app_id GROUP BY h)
                   SELECT max(count) from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))
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
                        FROM task_run WHERE app_id=:app_id AND user_id IS NULL GROUP BY h)
                   SELECT h, count from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))

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
                        FROM task_run WHERE app_id=:app_id AND user_id IS NULL GROUP BY h)
                   SELECT max(count) from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))
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
                        FROM task_run WHERE app_id=:app_id AND user_ip IS NULL GROUP BY h)
                   SELECT h, count from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))

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
                        FROM task_run WHERE app_id=:app_id AND user_ip IS NULL GROUP BY h)
                   SELECT max(count) from myquery;
                   ''').execution_options(stream=True)

        results = session.execute(sql, dict(app_id=app_id))
        for row in results:
            max_hours_auth = row.max

        return hours, hours_anon, hours_auth, max_hours, max_hours_anon, max_hours_auth
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=ONE_DAY)
def stats_format_dates(app_id, dates, dates_n_tasks, dates_estimate,
                       dates_anon, dates_auth):
    """Format dates stats into a JSON format"""
    dayNewStats = dict(label="Anon + Auth",   values=[])
    dayTotalTasks = dict(label="Total Tasks",   values=[])
    dayEstimates = dict(label="Estimation",   values=[])
    dayCompletedTasks = dict(label="Completed Tasks", disabled="True", values=[])
    dayNewAnonStats = dict(label="Anonymous", values=[])
    dayNewAuthStats = dict(label="Authenticated", values=[])

    total = 0
    for d in sorted(dates.keys()):
        # JavaScript expects miliseconds since EPOCH
        dayTotalTasks['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
             dates_n_tasks[d]])

        # Total tasks completed per day
        total = total + dates[d]
        dayCompletedTasks['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), total])

    anon_auth_dates = sorted(list(set(dates_anon.keys() + dates_auth.keys())))
    for d in anon_auth_dates:
        anon_ans = dates_anon[d] if d in dates_anon.keys() else 0
        auth_ans = dates_auth[d] if d in dates_auth.keys() else 0
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

    for d in sorted(dates_estimate.keys()):
        dayEstimates['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
             dates_estimate[d]])

        dayTotalTasks['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
             dates_n_tasks.values()[0]])

    return dayNewStats, dayNewAnonStats, dayNewAuthStats, \
        dayCompletedTasks, dayTotalTasks, dayEstimates


@memoize(timeout=ONE_DAY)
def stats_format_hours(app_id, hours, hours_anon, hours_auth,
                       max_hours, max_hours_anon, max_hours_auth):
    """Format hours stats into a JSON format"""
    hourNewStats = dict(label="Anon + Auth", disabled="True", values=[], max=0)
    hourNewAnonStats = dict(label="Anonymous", values=[], max=0)
    hourNewAuthStats = dict(label="Authenticated", values=[], max=0)

    hourNewStats['max'] = max_hours
    hourNewAnonStats['max'] = max_hours_anon
    hourNewAuthStats['max'] = max_hours_auth

    for h in sorted(hours.keys()):
        # New answers per hour
        #hourNewStats['values'].append(dict(x=int(h), y=hours[h], size=hours[h]*10))
        if (hours[h] != 0):
            hourNewStats['values'].append([int(h), hours[h],
                                           (hours[h] * 5) / max_hours])
        else:
            hourNewStats['values'].append([int(h), hours[h], 0])

        # New Anonymous answers per hour
        if h in hours_anon.keys():
            #hourNewAnonStats['values'].append(dict(x=int(h), y=hours[h], size=hours_anon[h]*10))
            if (hours_anon[h] != 0):
                hourNewAnonStats['values'].append([int(h), hours_anon[h],
                                                   (hours_anon[h] * 5) / max_hours])
            else:
                hourNewAnonStats['values'].append([int(h), hours_anon[h], 0])

        # New Authenticated answers per hour
        if h in hours_auth.keys():
            #hourNewAuthStats['values'].append(dict(x=int(h), y=hours[h], size=hours_auth[h]*10))
            if (hours_auth[h] != 0):
                hourNewAuthStats['values'].append([int(h), hours_auth[h],
                                                   (hours_auth[h] * 5) / max_hours])
            else:
                hourNewAuthStats['values'].append([int(h), hours_auth[h], 0])
    return hourNewStats, hourNewAnonStats, hourNewAuthStats


@memoize(timeout=ONE_DAY)
def stats_format_users(app_id, users, anon_users, auth_users, geo=False):
    """Format User Stats into JSON"""
    try:
        session = get_session(db, bind='slave')
        userStats = dict(label="User Statistics", values=[])
        userAnonStats = dict(label="Anonymous Users", values=[], top5=[], locs=[])
        userAuthStats = dict(label="Authenticated Users", values=[], top5=[])

        userStats['values'].append(dict(label="Anonymous", value=[0, users['n_anon']]))
        userStats['values'].append(dict(label="Authenticated", value=[0, users['n_auth']]))

        for u in anon_users:
            userAnonStats['values'].append(dict(label=u[0], value=[u[1]]))

        for u in auth_users:
            userAuthStats['values'].append(dict(label=u[0], value=[u[1]]))

        # Get location for Anonymous users
        top5_anon = []
        top5_auth = []
        loc_anon = []
        # Check if the GeoLiteCity.dat exists
        geolite = current_app.root_path + '/../dat/GeoLiteCity.dat'
        if geo: # pragma: no cover
            gic = pygeoip.GeoIP(geolite)
        for u in anon_users:
            if geo: # pragma: no cover
                loc = gic.record_by_addr(u[0])
            else:
                loc = {}
            if loc is None: # pragma: no cover
                loc = {}
            if (len(loc.keys()) == 0):
                loc['latitude'] = 0
                loc['longitude'] = 0
            top5_anon.append(dict(ip=u[0], loc=loc, tasks=u[1]))

        for u in anon_users:
            if geo: # pragma: no cover
                loc = gic.record_by_addr(u[0])
            else:
                loc = {}
            if loc is None: # pragma: no cover
                loc = {}
            if (len(loc.keys()) == 0):
                loc['latitude'] = 0
                loc['longitude'] = 0
            loc_anon.append(dict(ip=u[0], loc=loc, tasks=u[1]))

        for u in auth_users:
            sql = text('''SELECT name, fullname from "user" where id=:id;''')
            results = session.execute(sql, dict(id=u[0]))
            for row in results:
                fullname = row.fullname
                name = row.name
            top5_auth.append(dict(name=name, fullname=fullname, tasks=u[1]))

        userAnonStats['top5'] = top5_anon[0:5]
        userAnonStats['locs'] = loc_anon
        userAuthStats['top5'] = top5_auth

        return dict(users=userStats, anon=userAnonStats, auth=userAuthStats,
                    n_anon=users['n_anon'], n_auth=users['n_auth'])
    except:
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=ONE_DAY)
def get_stats(app_id, geo=False):
    """Return the stats of a given app"""
    hours, hours_anon, hours_auth, max_hours, \
        max_hours_anon, max_hours_auth = stats_hours(app_id)
    users, anon_users, auth_users = stats_users(app_id)
    dates, dates_n_tasks, dates_anon, dates_auth = stats_dates(app_id)

    total_n_tasks = n_tasks(app_id)
    total_completed = sum(dates.values())
    dates_estimate = {}

    sorted_answers = sorted(dates.iteritems(), key=operator.itemgetter(0))
    if len(sorted_answers) > 0 and total_completed < total_n_tasks:
        first_day = datetime.datetime.strptime(sorted_answers[0][0], "%Y-%m-%d")
        days_since_first_completed = (datetime.datetime.today() - first_day).days
        avg_completed_per_day = total_completed / (days_since_first_completed + 1)
        days_to_finish = (total_n_tasks - total_completed) / avg_completed_per_day
        pace = total_completed
        for i in range(0, int(days_to_finish) + 2):
            tmp = datetime.datetime.today() + timedelta(days=(i))
            tmp_str = tmp.date().strftime('%Y-%m-%d')
            dates_estimate[tmp_str] = pace
            pace = pace + avg_completed_per_day

    dates_stats = stats_format_dates(app_id, dates, dates_n_tasks, dates_estimate,
                                     dates_anon, dates_auth)

    hours_stats = stats_format_hours(app_id, hours, hours_anon, hours_auth,
                                     max_hours, max_hours_anon, max_hours_auth)

    users_stats = stats_format_users(app_id, users, anon_users, auth_users, geo)

    return dates_stats, hours_stats, users_stats
