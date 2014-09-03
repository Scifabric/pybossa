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

from sqlalchemy.sql import func, text
from pybossa.core import db, timeouts, get_session
from pybossa.model.featured import Featured
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.util import pretty_date
from pybossa.cache import memoize, cache, delete_memoized, delete_cached

import json
import string
import operator
import datetime
import time
from datetime import timedelta


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def get_app(short_name):
    try:
        session = get_session(db, bind='slave')
        app = session.query(App).filter_by(short_name=short_name).first()
        return app
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@cache(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'),
       key_prefix="front_page_featured_apps")
def get_featured_front_page():
    """Return featured apps"""
    try:
        sql = text('''SELECT app.id, app.name, app.short_name, app.info FROM
                   app, featured where app.id=featured.app_id and app.hidden=0''')
        session = get_session(db, bind='slave')
        results = session.execute(sql)
        featured = []
        for row in results:
            app = dict(id=row.id, name=row.name, short_name=row.short_name,
                       info=dict(json.loads(row.info)),
                       n_volunteers=n_volunteers(row.id),
                       n_completed_tasks=n_completed_tasks(row.id))
            featured.append(app)
        return featured
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@cache(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'),
       key_prefix="front_page_top_apps")
def get_top(n=4):
    """Return top n=4 apps"""
    try:
        sql = text('''SELECT app.id, app.name, app.short_name, app.description, app.info,
                  COUNT(app_id) AS total FROM task_run, app
                  WHERE app_id IS NOT NULL AND app.id=app_id AND app.hidden=0
                  GROUP BY app.id ORDER BY total DESC LIMIT :limit;''')
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(limit=n))
        top_apps = []
        for row in results:
            app = dict(id=row.id, name=row.name, short_name=row.short_name,
                       description=row.description,
                       info=json.loads(row.info),
                       n_volunteers=n_volunteers(row.id),
                       n_completed_tasks=n_completed_tasks(row.id))
            top_apps.append(app)
        return top_apps
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('BROWSE_TASKS_TIMEOUT'))
def browse_tasks(project_id):
    try:
        sql = text('''
                   SELECT task.id, count(task_run.id) as n_task_runs, task.n_answers
                   FROM task LEFT OUTER JOIN task_run ON (task.id=task_run.task_id)
                   WHERE task.app_id=:app_id GROUP BY task.id ORDER BY task.id''')
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=project_id))
        tasks = []
        for row in results:
            task = dict(id=row.id, n_task_runs=row.n_task_runs,
                        n_answers=row.n_answers)
            task['pct_status'] = _pct_status(row.n_task_runs, row.n_answers)
            tasks.append(task)
        return tasks
    except: #pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


def _pct_status(n_task_runs, n_answers):
    if n_answers != 0 and n_answers != None:
        # Check if it's bigger the n_task_runs that n_answers
        if n_task_runs > n_answers:
            return float(1)
        else:
            return float(n_task_runs) / n_answers
    return float(0)


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
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


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def n_completed_tasks(app_id):
    try:
        sql = text('''SELECT COUNT(task.id) AS n_completed_tasks FROM task
                    WHERE task.app_id=:app_id AND task.state=\'completed\';''')

        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        n_completed_tasks = 0
        for row in results:
            n_completed_tasks = row.n_completed_tasks
        return n_completed_tasks
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('REGISTERED_USERS_TIMEOUT'))
def n_registered_volunteers(app_id):
    try:
        sql = text('''SELECT COUNT(DISTINCT(task_run.user_id)) AS n_registered_volunteers FROM task_run
               WHERE task_run.user_id IS NOT NULL AND
               task_run.user_ip IS NULL AND
               task_run.app_id=:app_id;''')
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        n_registered_volunteers = 0
        for row in results:
            n_registered_volunteers = row.n_registered_volunteers
        return n_registered_volunteers
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('ANON_USERS_TIMEOUT'))
def n_anonymous_volunteers(app_id):
    try:
        sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip)) AS n_anonymous_volunteers FROM task_run
               WHERE task_run.user_ip IS NOT NULL AND
               task_run.user_id IS NULL AND
               task_run.app_id=:app_id;''')

        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        n_anonymous_volunteers = 0
        for row in results:
            n_anonymous_volunteers = row.n_anonymous_volunteers
        return n_anonymous_volunteers
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize()
def n_volunteers(app_id):
    return n_anonymous_volunteers(app_id) + n_registered_volunteers(app_id)


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def n_task_runs(app_id):
    try:
        sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run
                      WHERE task_run.app_id=:app_id''')

        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        n_task_runs = 0
        for row in results:
            n_task_runs = row.n_task_runs
        return n_task_runs
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def overall_progress(app_id):
    """Returns the percentage of submitted Tasks Runs done when a task is
    completed"""
    try:
        sql = text('''SELECT task.id, n_answers,
                   COUNT(task_run.task_id) AS n_task_runs
                   FROM task LEFT OUTER JOIN task_run ON task.id=task_run.task_id
                   WHERE task.app_id=:app_id GROUP BY task.id''')
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        n_expected_task_runs = 0
        n_task_runs = 0
        for row in results:
            tmp = row[2]
            if row[2] > row[1]:
                tmp = row[1]
            n_expected_task_runs += row[1]
            n_task_runs += tmp
        pct = float(0)
        if n_expected_task_runs != 0:
            pct = float(n_task_runs) / float(n_expected_task_runs)
        return (pct * 100)
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def last_activity(app_id):
    try:
        sql = text('''SELECT finish_time FROM task_run WHERE app_id=:app_id
                   ORDER BY finish_time DESC LIMIT 1''')
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(app_id=app_id))
        for row in results:
            if row is not None:
                return row[0]
            else:  # pragma: no cover
                return None
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


# This function does not change too much, so cache it for a longer time
@cache(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'),
       key_prefix="number_featured_apps")
def _n_featured():
    """Return number of featured apps"""
    try:
        sql = text('''SELECT COUNT(*) FROM featured;''')
        session = get_session(db, bind='slave')
        results = session.execute(sql)
        for row in results:
            count = row[0]
        return count
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


# This function does not change too much, so cache it for a longer time
@memoize(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'))
def get_featured(category, page=1, per_page=5):
    """Return a list of featured apps with a pagination"""
    try:
        sql = text('''SELECT app.id, app.name, app.short_name, app.info, app.created,
                   app.description,
                   "user".fullname AS owner FROM app, featured, "user"
                   WHERE app.id=featured.app_id AND app.hidden=0
                   AND "user".id=app.owner_id GROUP BY app.id, "user".id
                   OFFSET(:offset) LIMIT(:limit);
                   ''')
        offset = (page - 1) * per_page

        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(limit=per_page, offset=offset))
        apps = []
        for row in results:
            app = dict(id=row.id, name=row.name, short_name=row.short_name,
                       created=row.created, description=row.description,
                       overall_progress=overall_progress(row.id),
                       last_activity=pretty_date(last_activity(row.id)),
                       last_activity_raw=last_activity(row.id),
                       owner=row.owner,
                       featured=row.id,
                       info=dict(json.loads(row.info)))
            apps.append(app)
        return apps
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@cache(key_prefix="number_published_apps",
       timeout=timeouts.get('STATS_APP_TIMEOUT'))
def n_published():
    """Return number of published apps"""
    try:
        sql = text('''
                   WITH published_apps as
                   (SELECT app.id FROM app, task WHERE
                   app.id=task.app_id AND app.hidden=0 AND app.info
                   LIKE('%task_presenter%') GROUP BY app.id)
                   SELECT COUNT(id) FROM published_apps;
                   ''')

        session = get_session(db, bind='slave')
        results = session.execute(sql)
        for row in results:
            count = row[0]
        return count
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


# Cache it for longer times, as this is only shown to admin users
@cache(timeout=timeouts.get('STATS_DRAFT_TIMEOUT'),
       key_prefix="number_draft_apps")
def _n_draft():
    """Return number of draft projects"""
    try:
        sql = text('''SELECT COUNT(app.id) FROM app
                   LEFT JOIN task on app.id=task.app_id
                   WHERE task.app_id IS NULL AND app.info NOT LIKE('%task_presenter%')
                   AND app.hidden=0;''')

        session = get_session(db, bind='slave')
        results = session.execute(sql)
        for row in results:
            count = row[0]
        return count
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'))
def get_draft(category, page=1, per_page=5):
    """Return list of draft projects"""
    try:
        sql = text('''SELECT app.id, app.name, app.short_name, app.created,
                   app.description, app.info, "user".fullname as owner
                   FROM "user", app LEFT JOIN task ON app.id=task.app_id
                   WHERE task.app_id IS NULL AND app.info NOT LIKE('%task_presenter%')
                   AND app.hidden=0
                   AND app.owner_id="user".id
                   OFFSET :offset
                   LIMIT :limit;''')

        offset = (page - 1) * per_page
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(limit=per_page, offset=offset))
        apps = []
        for row in results:
            app = dict(id=row.id, name=row.name, short_name=row.short_name,
                       created=row.created,
                       description=row.description,
                       owner=row.owner,
                       last_activity=pretty_date(last_activity(row.id)),
                       last_activity_raw=last_activity(row.id),
                       overall_progress=overall_progress(row.id),
                       info=dict(json.loads(row.info)))
            apps.append(app)
        return apps
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('N_APPS_PER_CATEGORY_TIMEOUT'))
def n_count(category):
    """Count the number of apps in a given category"""
    if category == 'featured':
        return _n_featured()
    if category == 'draft':
        return _n_draft()
    try:
        sql = text('''
                   WITH uniq AS (
                   SELECT COUNT(app.id) FROM task, app
                   LEFT OUTER JOIN category ON app.category_id=category.id
                   WHERE
                   category.short_name=:category
                   AND app.hidden=0
                   AND app.info LIKE('%task_presenter%')
                   AND task.app_id=app.id
                   GROUP BY app.id)
                   SELECT COUNT(*) FROM uniq
                   ''')

        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(category=category))
        count = 0
        for row in results:
            count = row[0]
        return count
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def get(category, page=1, per_page=5):
    """Return a list of apps with at least one task and a task_presenter
       with a pagination for a given category"""
    try:
        sql = text('''SELECT app.id, app.name, app.short_name, app.description,
                   app.info, app.created, app.category_id, "user".fullname AS owner,
                   featured.app_id as featured
                   FROM "user", task, app
                   LEFT OUTER JOIN category ON app.category_id=category.id
                   LEFT OUTER JOIN featured ON app.id=featured.app_id
                   WHERE
                   category.short_name=:category
                   AND app.hidden=0
                   AND "user".id=app.owner_id
                   AND app.info LIKE('%task_presenter%')
                   AND task.app_id=app.id
                   GROUP BY app.id, "user".id, featured.app_id ORDER BY app.name
                   OFFSET :offset
                   LIMIT :limit;''')

        offset = (page - 1) * per_page
        session = get_session(db, bind='slave')
        results = session.execute(sql, dict(category=category, limit=per_page, offset=offset))
        apps = []
        for row in results:
            app = dict(id=row.id,
                       name=row.name, short_name=row.short_name,
                       created=row.created,
                       description=row.description,
                       owner=row.owner,
                       featured=row.featured,
                       last_activity=pretty_date(last_activity(row.id)),
                       last_activity_raw=last_activity(row.id),
                       overall_progress=overall_progress(row.id),
                       info=dict(json.loads(row.info)))
            apps.append(app)
        return apps
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


def reset():
    """Clean the cache"""
    delete_cached("index_front_page")
    delete_cached('front_page_featured_apps')
    delete_cached('front_page_top_apps')
    delete_cached('number_featured_apps')
    delete_cached('number_published_apps')
    delete_cached('number_draft_apps')
    delete_memoized(get_featured)
    delete_memoized(get_draft)
    delete_memoized(n_count)
    delete_memoized(get)


def delete_app(short_name):
    """Reset app values in cache"""
    delete_memoized(get_app, short_name)


def delete_n_tasks(app_id):
    """Reset n_tasks value in cache"""
    delete_memoized(n_tasks, app_id)


def delete_n_completed_tasks(app_id):
    """Reset n_completed_tasks value in cache"""
    delete_memoized(n_completed_tasks, app_id)


def delete_n_task_runs(app_id):
    """Reset n_tasks value in cache"""
    delete_memoized(n_task_runs, app_id)


def delete_overall_progress(app_id):
    """Reset overall_progress value in cache"""
    delete_memoized(overall_progress, app_id)


def delete_last_activity(app_id):
    """Reset last_activity value in cache"""
    delete_memoized(last_activity, app_id)


def delete_n_registered_volunteers(app_id):
    """Reset n_registered_volunteers value in cache"""
    delete_memoized(n_registered_volunteers, app_id)


def delete_n_anonymous_volunteers(app_id):
    """Reset n_anonymous_volunteers value in cache"""
    delete_memoized(n_anonymous_volunteers, app_id)


def delete_n_volunteers(app_id):
    """Reset n_volunteers value in cache"""
    delete_memoized(n_volunteers, app_id)


def clean(app_id):
    """Clean all items in cache"""
    reset()
    delete_n_tasks(app_id)
    delete_n_completed_tasks(app_id)
    delete_n_task_runs(app_id)
    delete_overall_progress(app_id)
    delete_last_activity(app_id)
    delete_n_registered_volunteers(app_id)
    delete_n_anonymous_volunteers(app_id)
    delete_n_volunteers(app_id)
