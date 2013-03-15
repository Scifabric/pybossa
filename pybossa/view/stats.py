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
import json
from flask import Blueprint
from flask import render_template
from sqlalchemy.sql import text

from pybossa.core import db, cache
from pybossa.cache import apps as cached_apps

blueprint = Blueprint('stats', __name__)


@cache.cached(timeout=300)
@blueprint.route('/')
def index():
    """Return Global Statistics for the site"""

    title = "Global Statistics"
    sql = text('''SELECT COUNT("user".id) AS n_auth FROM "user";''')
    results = db.engine.execute(sql)
    for row in results:
        n_auth = row.n_auth

    sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip))
               AS n_anon FROM task_run;''')

    results = db.engine.execute(sql)
    for row in results:
        n_anon = row.n_anon

    n_total_users = n_anon + n_auth

    n_published_apps = cached_apps.n_published()
    n_draft_apps = cached_apps.n_draft()
    n_total_apps = n_published_apps + n_draft_apps

    sql = text('''SELECT COUNT(task.id) AS n_tasks FROM task''')
    results = db.engine.execute(sql)
    for row in results:
        n_tasks = row.n_tasks

    sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run''')
    results = db.engine.execute(sql)
    for row in results:
        n_task_runs = row.n_task_runs

    # TODO: Most active apps in last 24 hours
    # TODO: Most active users in last 24 hours

    stats = dict(n_total_users=n_total_users, n_auth=n_auth, n_anon=n_anon,
                 n_published_apps=n_published_apps,
                 n_draft_apps=n_draft_apps,
                 n_total_apps=n_total_apps,
                 n_tasks=n_tasks,
                 n_task_runs=n_task_runs)

    users = dict(label="User Statistics",
                 values=[
                     dict(label='Anonymous', value=[0, n_anon]),
                     dict(label='Authenticated', value=[0, n_auth])])

    apps = dict(label="Apps Statistics",
                values=[
                    dict(label='Published', value=[0, n_published_apps]),
                    dict(label='Authenticated', value=[0, n_draft_apps])])

    tasks = dict(label="Task and Task Run Statistics",
                 values=[
                     dict(label='Tasks', value=[0, n_tasks]),
                     dict(label='Answers', value=[1, n_task_runs])])

    return render_template('/stats/global.html', title=title,
                           users=json.dumps(users),
                           apps=json.dumps(apps),
                           tasks=json.dumps(tasks),
                           stats=stats)
