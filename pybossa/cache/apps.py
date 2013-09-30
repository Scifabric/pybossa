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
from sqlalchemy.sql import func, text
from pybossa.core import cache
from pybossa.core import db
from pybossa.model import Featured, App, TaskRun, Task
from pybossa.util import pretty_date

import json
import string
import operator
import datetime
import time
from datetime import timedelta


@cache.memoize()
def get_app(short_name):
    sql = text('''SELECT * FROM
                  app WHERE app.short_name=:short_name''')
    results = db.engine.execute(sql, short_name=short_name)
    app = App()
    for row in results:
        app = App(id=row.id, name=row.name, short_name=row.short_name,
                  created=row.created,
                  description=row.description,
                  long_description=row.long_description,
                  owner_id=row.owner_id,
                  hidden=row.hidden,
                  info=json.loads(row.info),
                  allow_anonymous_contributors=row.allow_anonymous_contributors)
    return app


@cache.cached(key_prefix="front_page_featured_apps")
def get_featured_front_page():
    """Return featured apps"""
    sql = text('''SELECT app.id, app.name, app.short_name, app.info FROM
               app, featured where app.id=featured.app_id and app.hidden=0''')
    results = db.engine.execute(sql)
    featured = []
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   info=dict(json.loads(row.info)))
        featured.append(app)
    return featured


@cache.cached(key_prefix="front_page_top_apps")
def get_top(n=4):
    """Return top n=4 apps"""
    sql = text('''
    SELECT app.id, app.name, app.short_name, app.description, app.info,
    count(app_id) AS total FROM task_run, app WHERE app_id IS NOT NULL AND
    app.id=app_id AND app.hidden=0 GROUP BY app.id ORDER BY total DESC LIMIT :limit;
    ''')

    results = db.engine.execute(sql, limit=n)
    top_apps = []
    for row in results:
        app = dict(name=row.name, short_name=row.short_name,
                   description=row.description,
                   info=json.loads(row.info))
        top_apps.append(app)
    return top_apps


@cache.memoize()
def n_tasks(app_id):
    sql = text('''SELECT COUNT(task.id) AS n_tasks FROM task
                  WHERE task.app_id=:app_id''')
    results = db.engine.execute(sql, app_id=app_id)
    n_tasks = 0
    for row in results:
        n_tasks = row.n_tasks
    return n_tasks


@cache.memoize()
def n_task_runs(app_id):
    sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run
                  WHERE task_run.app_id=:app_id''')
    results = db.engine.execute(sql, app_id=app_id)
    n_task_runs = 0
    for row in results:
        n_task_runs = row.n_task_runs
    return n_task_runs


@cache.memoize()
def last_activity(app_id):
    sql = text('''SELECT finish_time FROM task_run WHERE app_id=:app_id
               ORDER BY finish_time DESC LIMIT 1''')
    results = db.engine.execute(sql, app_id=app_id)
    for row in results:
        if row is not None:
            print pretty_date(row[0])
            return pretty_date(row[0])
        else:
            return None


@cache.memoize()
def overall_progress(app_id):
    """Returns the percentage of submitted Tasks Runs done when a task is
    completed"""
    sql = text('''SELECT task.id, n_answers,
               count(task_run.task_id) AS n_task_runs
               FROM task LEFT OUTER JOIN task_run ON task.id=task_run.task_id
               WHERE task.app_id=:app_id GROUP BY task.id''')
    results = db.engine.execute(sql, app_id=app_id)
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


@cache.memoize()
def last_activity(app_id):
    sql = text('''SELECT finish_time FROM task_run WHERE app_id=:app_id
               ORDER BY finish_time DESC LIMIT 1''')
    results = db.engine.execute(sql, app_id=app_id)
    for row in results:
        if row is not None:
            return pretty_date(row[0])
        else:
            return None


@cache.cached(key_prefix="number_featured_apps")
def n_featured():
    """Return number of featured apps"""
    sql = text('''select count(*) from featured;''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    return count


@cache.memoize()
def get_featured(category, page=1, per_page=5):
    """Return a list of featured apps with a pagination"""

    count = n_featured()

    sql = text('''SELECT app.id, app.name, app.short_name, app.info, app.created,
               app.description,
               "user".fullname AS owner FROM app, featured, "user"
               WHERE app.id=featured.app_id AND app.hidden=0
               AND "user".id=app.owner_id GROUP BY app.id, "user".id
               OFFSET(:offset) LIMIT(:limit);
               ''')
    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   created=row.created, description=row.description,
                   overall_progress=overall_progress(row.id),
                   last_activity=last_activity(row.id),
                   owner=row.owner,
                   featured=row.id,
                   info=dict(json.loads(row.info)))
        apps.append(app)
    return apps, count

@cache.cached(key_prefix="number_published_apps")
def n_published():
    """Return number of published apps"""
    sql = text('''
               WITH published_apps as
               (SELECT app.id FROM app, task WHERE
               app.id=task.app_id AND app.hidden=0 AND app.info
               LIKE('%task_presenter%') GROUP BY app.id)
               SELECT COUNT(id) FROM published_apps;
               ''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    return count

@cache.memoize()
def get_published(category, page=1, per_page=5):
    """Return a list of apps with a pagination"""

    count = n_published()

    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
               app.info, app.created, "user".fullname AS owner,
               featured.app_id as featured
               FROM task, "user", app LEFT OUTER JOIN featured ON app.id=featured.app_id
               WHERE
               app.id=task.app_id AND app.info LIKE('%task_presenter%')
               AND app.hidden=0
               AND "user".id=app.owner_id
               GROUP BY app.id, "user".id, featured.id ORDER BY app.name
               OFFSET :offset
               LIMIT :limit;''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = dict(id=row.id,
                   name=row.name, short_name=row.short_name,
                   created=row.created,
                   description=row.description,
                   owner=row.owner,
                   featured=row.featured,
                   last_activity=last_activity(row.id),
                   overall_progress=overall_progress(row.id),
                   info=dict(json.loads(row.info)))
        apps.append(app)
    return apps, count

@cache.cached(key_prefix="number_draft_apps")
def n_draft():
    """Return number of draft applications"""
    sql = text('''
               SELECT count(app.id) FROM app
               LEFT JOIN task on app.id=task.app_id
               WHERE task.app_id IS NULL AND app.info NOT LIKE('%task_presenter%')
               AND app.hidden=0;''')

    results = db.engine.execute(sql)
    for row in results:
        count = row[0]
    return count

@cache.memoize()
def get_draft(category, page=1, per_page=5):
    """Return list of draft applications"""

    count = n_draft()

    sql = text('''
               SELECT app.id, app.name, app.short_name, app.created,
               app.description, app.info, "user".fullname as owner
               FROM "user", app LEFT JOIN task ON app.id=task.app_id
               WHERE task.app_id IS NULL AND app.info NOT LIKE('%task_presenter%')
               AND app.hidden=0
               AND app.owner_id="user".id
               OFFSET :offset
               LIMIT :limit;''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = dict(id=row.id, name=row.name, short_name=row.short_name,
                   created=row.created,
                   description=row.description,
                   owner=row.owner,
                   last_activity=last_activity(row.id),
                   overall_progress=overall_progress(row.id),
                   info=dict(json.loads(row.info)))
        apps.append(app)
    return apps, count


@cache.memoize()
def n_count(category):
    """Count the number of apps in a given category"""
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

    results = db.engine.execute(sql, category=category)
    count = 0
    for row in results:
        count = row[0]
    return count


@cache.memoize()
def get(category, page=1, per_page=5):
    """Return a list of apps with at least one task and a task_presenter
       with a pagination for a given category"""

    count = n_count(category)

    sql = text('''
               SELECT app.id, app.name, app.short_name, app.description,
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
    results = db.engine.execute(sql, category=category, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = dict(id=row.id,
                   name=row.name, short_name=row.short_name,
                   created=row.created,
                   description=row.description,
                   owner=row.owner,
                   featured=row.featured,
                   last_activity=last_activity(row.id),
                   overall_progress=overall_progress(row.id),
                   info=dict(json.loads(row.info)))
        apps.append(app)
    return apps, count


def reset():
    """Clean the cache"""
    cache.delete('front_page_featured_apps')
    cache.delete('front_page_top_apps')
    cache.delete('number_featured_apps')
    cache.delete('number_published_apps')
    cache.delete('number_draft_apps')
    cache.delete_memoized(get_published)
    cache.delete_memoized(get_featured)
    cache.delete_memoized(get_draft)
    cache.delete_memoized(n_count)
    cache.delete_memoized(get)


def delete_app(app_id):
    """Reset app values in cache"""
    cache.delete_memoized(get_app, app_id)


def delete_n_tasks(app_id):
    """Reset n_tasks value in cache"""
    cache.delete_memoized(n_tasks, app_id)


def delete_n_task_runs(app_id):
    """Reset n_tasks value in cache"""
    cache.delete_memoized(n_task_runs, app_id)


def delete_overall_progress(app_id):
    """Reset overall_progress value in cache"""
    cache.delete_memoized(overall_progress, app_id)


def delete_last_activity(app_id):
    """Reset last_activity value in cache"""
    cache.delete_memoized(last_activity, app_id)


def clean(app_id):
    """Clean all items in cache"""
    reset()
    cache.delete_memoized(n_tasks, app_id)
    cache.delete_memoized(n_task_runs, app_id)
    cache.delete_memoized(last_activity, app_id)
    cache.delete_memoized(overall_progress, app_id)
