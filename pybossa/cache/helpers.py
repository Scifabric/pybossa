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

from sqlalchemy.sql import text
from pybossa.core import db, timeouts
from pybossa.cache import memoize
from pybossa.cache.apps import overall_progress



@memoize(timeout=60)
def n_available_tasks(app_id, user_id=None, user_ip=None):
    """Returns the number of tasks for a given app a user can contribute to,
    based on the completion of the app tasks, and previous task_runs submitted
    by the user"""

    if user_id and not user_ip:
        query = text('''SELECT COUNT(id) AS n_tasks FROM task WHERE NOT EXISTS
                       (SELECT task_id FROM task_run WHERE
                       app_id=:app_id AND user_id=:user_id AND task_id=task.id)
                       AND app_id=:app_id AND state !='completed';''')
        result = db.engine.execute(query, app_id=app_id, user_id=user_id)
    else:
        if not user_ip:
            user_ip = '127.0.0.1'
        query = text('''SELECT COUNT(id) AS n_tasks FROM task WHERE NOT EXISTS
                       (SELECT task_id FROM task_run WHERE
                       app_id=:app_id AND user_ip=:user_ip AND task_id=task.id)
                       AND app_id=:app_id AND state !='completed';''')
        result = db.engine.execute(query, app_id=app_id, user_ip=user_ip)
    n_tasks = 0
    for row in result:
        n_tasks = row.n_tasks
    return n_tasks


def check_contributing_state(app, user_id=None, user_ip=None):
    """Returns the state of a given app for a given user, depending on whether
    the app is completed or not and the user can contribute more to it or not"""

    app_id = app['id'] if type(app) == dict else app.id
    states = ('completed', 'draft', 'can_contribute', 'cannot_contribute')
    if overall_progress(app_id) >= 100:
        return states[0]
    if _has_no_presenter(app) or _has_no_tasks(app_id):
        return states[1]
    if n_available_tasks(app_id, user_id=user_id, user_ip=user_ip) > 0:
        return states[2]
    return states[3]


def add_custom_contrib_button_to(app, user_id_or_ip):
    if type(app) == dict:
        app_id = app['id']
    else:
        app_id = app.id
        app = app.dictize()
    app['contrib_button'] = check_contributing_state(app, **user_id_or_ip)
    return app


def _has_no_presenter(app):
    try:
        return 'task_presenter' not in app.info
    except AttributeError:
        try:
            return 'task_presenter' not in app.get('info')
        except AttributeError:
            return True

def _has_no_tasks(app_id):
    query = text('''SELECT COUNT(id) AS n_tasks FROM task
               WHERE app_id=:app_id;''')
    result = db.engine.execute(query, app_id=app_id)
    for row in result:
        n_tasks = row.n_tasks
    return n_tasks == 0
