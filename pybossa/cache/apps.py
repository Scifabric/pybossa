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

STATS_TIMEOUT=50

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


@cache.memoize(timeout=60*5)
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
    sql = text('''SELECT COUNT(task_id) FROM task_run WHERE app_id=:app_id''')
    results = db.engine.execute(sql, app_id=app_id)
    for row in results:
        n_task_runs = float(row[0])
    sql = text('''SELECT SUM(n_answers) FROM task WHERE app_id=:app_id''')
    results = db.engine.execute(sql, app_id=app_id)
    for row in results:
        if row[0] is None:
            n_expected_task_runs = float(30 * n_task_runs)
        else:
            n_expected_task_runs = float(row[0])
    pct = float(0)
    if n_expected_task_runs != 0:
        pct = n_task_runs / n_expected_task_runs
    return pct*100


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

@cache.memoize(timeout=50)
def get_featured(page=1, per_page=5):
    """Return a list of featured apps with a pagination"""

    count = n_featured()

    sql = text('''SELECT app.id, app.name, app.short_name, app.info, app.created,
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
                   created=row.name,
                   overall_progress=overall_progress(row.id),
                   last_activity=last_activity(row.id),
                   owner=row.owner,
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

@cache.memoize(timeout=50)
def get_published(page=1, per_page=5):
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

@cache.memoize(timeout=50)
def get_draft(page=1, per_page=5):
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


def clean(app_id):
    """Clean all items in cache"""
    reset()
    cache.delete_memoized(last_activity, app_id)
    cache.delete_memoized(overall_progress, app_id)
