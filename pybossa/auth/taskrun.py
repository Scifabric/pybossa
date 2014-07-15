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
from flask import abort
from pybossa.core import db

from pybossa.repositories import TaskRepository
task_repo = TaskRepository(db)



def create(taskrun=None):
    authorized = task_repo.get_task_run_by(app_id=taskrun.app_id,
                                           task_id=taskrun.task_id,
                                           user=taskrun.user,
                                           user_ip=taskrun.user_ip) is None
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

