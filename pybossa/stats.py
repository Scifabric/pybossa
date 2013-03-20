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
from flask import current_app
from sqlalchemy.sql import text
from pybossa.core import cache
from pybossa.core import db
from pybossa.model import TaskRun, Task

import string
import pygeoip
import operator
import datetime
import time
from datetime import timedelta


# Cache Stats for 24 hours
STATS_TIMEOUT = 24*60*60


@cache.memoize(timeout=STATS_TIMEOUT)
def get_task_runs(app_id):
    """Return all the Task Runs for a given app_id"""
    task_runs = db.session.query(TaskRun).filter_by(app_id=app_id).all()
    return task_runs


@cache.memoize(timeout=STATS_TIMEOUT)
def get_tasks(app_id):
    """Return all the tasks for a given app_id"""
    tasks = db.session.query(Task).filter_by(app_id=app_id).all()
    return tasks


@cache.memoize(timeout=STATS_TIMEOUT)
def get_avg_n_tasks(app_id):
    """Return the average number of answers expected per task,
    and the number of tasks"""
    sql = text('''SELECT COUNT(task.id) as n_tasks,
               AVG(task.n_answers) AS "avg" FROM task
               WHERE task.app_id=:app_id;''')

    results = db.engine.execute(sql, app_id=app_id)
    for row in results:
        avg = float(row.avg)
        total_n_tasks = row.n_tasks
    return avg, total_n_tasks


@cache.memoize(timeout=STATS_TIMEOUT)
def stats_users(app_id):
    """Return users's stats for a given app_id"""
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
    results = db.engine.execute(sql, app_id=app_id)

    for row in results:
        auth_users.append([row.user_id, row.n_tasks])

    sql = text('''SELECT count(distinct(task_run.user_id)) AS user_id FROM task_run
               WHERE task_run.user_id IS NOT NULL AND
               task_run.user_ip IS NULL AND
               task_run.app_id=:app_id;''')
    results = db.engine.execute(sql, app_id=app_id)
    for row in results:
        users['n_auth'] = row[0]

    # Get Anonymous Users
    sql = text('''SELECT task_run.user_ip AS user_ip,
               COUNT(task_run.id) as n_tasks FROM task_run
               WHERE task_run.user_ip IS NOT NULL AND
               task_run.user_id IS NULL AND
               task_run.app_id=:app_id
               GROUP BY task_run.user_ip ORDER BY n_tasks DESC
               LIMIT 5;''')
    results = db.engine.execute(sql, app_id=app_id)

    for row in results:
        anon_users.append([row.user_ip, row.n_tasks])

    sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip)) AS user_ip FROM task_run
               WHERE task_run.user_ip IS NOT NULL AND
               task_run.user_id IS NULL AND
               task_run.app_id=:app_id;''')
    results = db.engine.execute(sql, app_id=app_id)

    for row in results:
        users['n_anon'] = row[0]

    return users, anon_users, auth_users


@cache.memoize(timeout=STATS_TIMEOUT)
def stats_dates(app_id):
    dates = {}
    dates_anon = {}
    dates_auth = {}
    dates_n_tasks = {}

    task_runs = get_task_runs(app_id)

    avg, total_n_tasks = get_avg_n_tasks(app_id)

    for tr in task_runs:
        # Data for dates
        date, hour = string.split(tr.finish_time, "T")
        tr.finish_time = string.split(tr.finish_time, '.')[0]
        hour = string.split(hour, ":")[0]

        # Dates
        if date in dates.keys():
            dates[date] += 1
        else:
            dates[date] = 1

        if date in dates_n_tasks.keys():
            dates_n_tasks[date] = total_n_tasks * avg
        else:
            dates_n_tasks[date] = total_n_tasks * avg

        if tr.user_id is None:
            if date in dates_anon.keys():
                dates_anon[date] += 1
            else:
                dates_anon[date] = 1
        else:
            if date in dates_auth.keys():
                dates_auth[date] += 1
            else:
                dates_auth[date] = 1
    return dates, dates_n_tasks, dates_anon, dates_auth


@cache.memoize(timeout=STATS_TIMEOUT)
def stats_hours(app_id):
    hours = {}
    hours_anon = {}
    hours_auth = {}
    max_hours = 0
    max_hours_anon = 0
    max_hours_auth = 0

    task_runs = get_task_runs(app_id)

    # initialize hours keys
    for i in range(0, 24):
        hours[str(i).zfill(2)] = 0
        hours_anon[str(i).zfill(2)] = 0
        hours_auth[str(i).zfill(2)] = 0

    for tr in task_runs:
        # Hours
        date, hour = string.split(tr.finish_time, "T")
        tr.finish_time = string.split(tr.finish_time, '.')[0]
        hour = string.split(hour, ":")[0]

        if hour in hours.keys():
            hours[hour] += 1
            if (hours[hour] > max_hours):
                max_hours = hours[hour]

        if tr.user_id is None:
            if hour in hours_anon.keys():
                hours_anon[hour] += 1
                if (hours_anon[hour] > max_hours_anon):
                    max_hours_anon = hours_anon[hour]

        else:
            if hour in hours_auth.keys():
                hours_auth[hour] += 1
                if (hours_auth[hour] > max_hours_auth):
                    max_hours_auth = hours_auth[hour]
    return hours, hours_anon, hours_auth, max_hours, max_hours_anon, max_hours_auth


@cache.memoize(timeout=STATS_TIMEOUT)
def stats_format_dates(app_id, dates, dates_n_tasks, dates_estimate,
                       dates_anon, dates_auth):
    """Format dates stats into a JSON format"""
    dayNewStats = dict(label="Anon + Auth",   values=[])
    dayAvgAnswers = dict(label="Expected Answers",   values=[])
    dayEstimates = dict(label="Estimation",   values=[])
    dayTotalStats = dict(label="Total", disabled="True", values=[])
    dayNewAnonStats = dict(label="Anonymous", values=[])
    dayNewAuthStats = dict(label="Authenticated", values=[])

    total = 0
    for d in sorted(dates.keys()):
        # JavaScript expects miliseconds since EPOCH
        # New answers per day
        dayNewStats['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), dates[d]])

        dayAvgAnswers['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
             dates_n_tasks[d]])

        # Total answers per day
        total = total + dates[d]
        dayTotalStats['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), total])

        # Anonymous answers per day
        if d in (dates_anon.keys()):
            dayNewAnonStats['values'].append(
                [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
                 dates_anon[d]])
        else:
            dayNewAnonStats['values'].append(
                [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), 0])

        # Authenticated answers per day
        if d in (dates_auth.keys()):
            dayNewAuthStats['values'].append(
                [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
                 dates_auth[d]])
        else:
            dayNewAuthStats['values'].append(
                [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000), 0])

    for d in sorted(dates_estimate.keys()):
        dayEstimates['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
             dates_estimate[d]])

        dayAvgAnswers['values'].append(
            [int(time.mktime(time.strptime(d, "%Y-%m-%d")) * 1000),
             dates_n_tasks.values()[0]])

    return dayNewStats, dayNewAnonStats, dayNewAuthStats, \
        dayTotalStats, dayAvgAnswers, dayEstimates


@cache.memoize(timeout=STATS_TIMEOUT)
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


@cache.memoize(timeout=STATS_TIMEOUT)
def stats_format_users(app_id, users, anon_users, auth_users, geo=False):
    """Format User Stats into JSON"""
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
    if geo:
        gic = pygeoip.GeoIP(geolite)
    for u in anon_users:
        if geo:
            loc = gic.record_by_addr(u[0])
        else:
            loc = {}
        if (len(loc.keys()) == 0):
            loc['latitude'] = 0
            loc['longitude'] = 0
        top5_anon.append(dict(ip=u[0], loc=loc, tasks=u[1]))

    for u in anon_users:
        if geo:
            loc = gic.record_by_addr(u[0])
        else:
            loc = {}
        if (len(loc.keys()) == 0):
            loc['latitude'] = 0
            loc['longitude'] = 0
        loc_anon.append(dict(ip=u[0], loc=loc, tasks=u[1]))

    for u in auth_users:
        sql = text('''SELECT fullname from "user" where id=:id;''')
        results = db.engine.execute(sql, id=u[0])
        for row in results:
            fullname = row.fullname
        top5_auth.append(dict(fullname=fullname, tasks=u[1]))

    userAnonStats['top5'] = top5_anon
    userAnonStats['locs'] = loc_anon
    userAuthStats['top5'] = top5_auth

    return dict(users=userStats, anon=userAnonStats, auth=userAuthStats,
                n_anon=users['n_anon'], n_auth=users['n_auth'])


@cache.memoize(timeout=STATS_TIMEOUT)
def get_stats(app_id, geo=False):
    """Return the stats a given app"""
    hours, hours_anon, hours_auth, max_hours, \
        max_hours_anon, max_hours_auth = stats_hours(app_id)
    users, anon_users, auth_users = stats_users(app_id)
    dates, dates_n_tasks, dates_anon, dates_auth = stats_dates(app_id)

    avg, total_n_tasks = get_avg_n_tasks(app_id)

    sorted_answers = sorted(dates.iteritems(), key=operator.itemgetter(0))
    if len(sorted_answers) > 0:
        last_day = datetime.datetime.strptime(sorted_answers[-1][0], "%Y-%m-%d")
    total_answers = sum(dates.values())
    if len(dates) > 0:
        avg_answers_per_day = total_answers / len(dates)
    required_days_to_finish = ((avg * total_n_tasks) - total_answers) / avg_answers_per_day

    pace = total_answers

    dates_estimate = {}
    for i in range(0, int(required_days_to_finish) + 2):
        tmp = last_day + timedelta(days=(i))
        tmp_str = tmp.date().strftime('%Y-%m-%d')
        dates_estimate[tmp_str] = pace
        pace = pace + avg_answers_per_day

    dates_stats = stats_format_dates(app_id, dates, dates_n_tasks, dates_estimate,
                                     dates_anon, dates_auth)

    hours_stats = stats_format_hours(app_id, hours, hours_anon, hours_auth,
                                     max_hours, max_hours_anon, max_hours_auth)

    users_stats = stats_format_users(app_id, users, anon_users, auth_users, geo)
    return dates_stats, hours_stats, users_stats
