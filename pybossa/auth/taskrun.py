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

from flask.ext.login import current_user
from pybossa.core import db, get_session
from pybossa.model.task_run import TaskRun
from flask import abort
from sqlalchemy.sql import text

def create(taskrun=None):
    authorized = False
    try:
        session = get_session(db, bind='slave')
        if taskrun.user_ip:
            sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run
                          WHERE task_run.app_id=:app_id AND
                          task_run.task_id=:task_id AND
                          task_run.user_ip=:user_ip;''')
            results = session.execute(sql, dict(app_id=taskrun.app_id,
                                                task_id=taskrun.task_id,
                                                user_ip=taskrun.user_ip))
        elif taskrun.user_id:
            sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run
                          WHERE task_run.app_id=:app_id AND
                          task_run.task_id=:task_id AND
                          task_run.user_id=:user_id;''')
            results = session.execute(sql, dict(app_id=taskrun.app_id,
                                                task_id=taskrun.task_id,
                                                user_id=taskrun.user_id))
        else:
            return False
        n_task_runs = 0
        for row in results:
            n_task_runs = row.n_task_runs
        authorized = (n_task_runs <= 0)
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()
    if not authorized:
        raise abort(403)
    return authorized

def read(taskrun=None):
    return True


def update(taskrun):
    return False


def delete(taskrun):
    if current_user.is_anonymous():
        return False
    if taskrun.user_id is None:
        return current_user.admin
    return current_user.admin or taskrun.user_id == current_user.id

