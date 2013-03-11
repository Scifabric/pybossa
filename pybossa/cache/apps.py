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
from pybossa.model import Featured, App, TaskRun
from pybossa.util import pretty_date

# 15 minutes to cache this items
@cache.memoize(timeout=60*15)
def format_top_featured_app(app_id):
    """Format app for template"""
    app = db.session.query(App).get(app_id)
    if not app.hidden:
        return app
    else:
        return None

def get_featured_front_page():
    """Return featured apps"""
    featured_ids = db.session.query(Featured).all()
    featured = []
    for f in featured_ids:
        app = format_top_featured_app(f.app_id)
        if app:
            featured.append(app)
    return featured

def get_top(n=4):
    """Return top n=4 apps"""
    sql = text('''
    SELECT app_id, count(*) AS total FROM task_run WHERE app_id IS NOT NULL GROUP BY
    app_id ORDER BY total DESC LIMIT :limit;
    ''')

    results = db.engine.execute(sql, limit=n)
    top_apps = []
    for row in results:
        app = format_top_featured_app(row[0])
        if app:
            top_apps.append(app)
    return top_apps


@cache.memoize(timeout=60 * 5)
def completion_status(app):
    """Returns the percentage of submitted Tasks Runs done"""
    sql = text('''SELECT COUNT(task_id) FROM task_run WHERE app_id=:app_id''')
    results = db.engine.execute(sql, app_id=app.id)
    for row in results:
        n_task_runs = float(row[0])
    sql = text('''SELECT SUM(n_answers) FROM task WHERE app_id=:app_id''')
    results = db.engine.execute(sql, app_id=app.id)
    for row in results:
        if row[0] is None:
            n_expected_task_runs = float(30 * n_task_runs)
        else:
            n_expected_task_runs = float(row[0])
    pct = float(0)
    if n_expected_task_runs != 0:
        pct = n_task_runs / n_expected_task_runs
    return pct

@cache.memoize(timeout=60*5)
def n_completed_tasks(app):
    """Returns the number of Tasks that are completed"""
    completed = db.session.query(model.Task).filter_by(state="completed").count()
    return completed

@cache.memoize(timeout=60*5)
def last_activity(app):
    sql = text('''SELECT finish_time FROM task_run WHERE app_id=:app_id
               ORDER BY finish_time DESC LIMIT 1''')
    results = db.engine.execute(sql, app_id=app.id)
    for row in results:
        if row is not None:
            return pretty_date(row[0])
        else:
            return None

@cache.memoize(timeout=60*5)
def format_app(app):
    """Ads an app to the cache"""
    app.info['last_activity'] = last_activity(app)
    app.info['overall_progress'] = completion_status(app)*100
    app.info['owner'] = app.owner.name
    if db.session.query(Featured).filter_by(app_id=app.id).first():
        app.info['featured'] = True
    return app

def get_featured(page=1, per_page=5):
    """Return a list of featured apps with a pagination"""

    sql = text('''select count(*) from featured;''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]

    sql = text('''select app_id from featured offset(:offset) limit(:limit);''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = db.session.query(App).get(row[0])
        apps.append(format_app(app))
    return apps, count

def get_published(page=1, per_page=5):
    """Return a list of apps with a pagination"""

    sql = text('''
select count(*) from app where (app.id IN (select distinct on (task.app_id) task.app_id from task where task.app_id is not null)) and (app.hidden = 0) and (app.info LIKE('%task_presenter%'));''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]

    sql = text('''
select id from app where (app.id IN (select distinct on (task.app_id) task.app_id from task where task.app_id is not null)) and (app.hidden = 0) and (app.info LIKE('%task_presenter%')) order by (app.name) offset(:offset) limit(:limit);''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = db.session.query(App).get(row[0])
        apps.append(format_app(app))
    return apps, count

def get_draft(page=1, per_page=5):
    sql = text('''
    select count(*) from app where app.info not like ('%task_presenter%') and (app.hidden = 0);''')
    results = db.engine.execute(sql)
    for row in results:
        count = row[0]

    sql = text('''
    select id from app where app.info not like ('%task_presenter%')  and (app.hidden = 0) order by (app.name) offset(:offset) limit(:limit);''')

    offset = (page - 1) * per_page
    results = db.engine.execute(sql, limit=per_page, offset=offset)
    apps = []
    for row in results:
        app = db.session.query(App).get(row[0])
        apps.append(format_app(app))

    return apps, count
