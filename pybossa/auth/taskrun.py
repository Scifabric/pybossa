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
from pybossa.model import TaskRun
from werkzeug.exceptions import Forbidden


def create(taskrun=None):
    authorized = (TaskRun.query.filter_by(app_id=taskrun.app_id)
                    .filter_by(task_id=taskrun.task_id)
                    .filter_by(user=taskrun.user)
                    .filter_by(user_ip=taskrun.user_ip)
                    .first()) is None
    if not authorized:
        raise Forbidden
    return authorized


def read(taskrun=None):
    return True


def update(taskrun):
    if taskrun.user is None:
        raise Forbidden
    if current_user.is_anonymous():
        return False
    else:
        return current_user.admin or taskrun.user.id == current_user.id


def delete(taskrun):
    if current_user.is_anonymous():
        return False
    if taskrun.user is None:
        return current_user.admin
    else:
        return current_user.admin or taskrun.user.id == current_user.id

