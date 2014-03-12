# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
"""
PyBossa api module for exposing domain object TaskRun via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * task_runs

"""
from flask import request
from flask.ext.login import current_user
from api_base import APIBase
from pybossa.model import Task, TaskRun
from itsdangerous import URLSafeSerializer
from werkzeug.exceptions import Forbidden


class TaskRunAPI(APIBase):

    """Class API for domain object TaskRun."""

    __class__ = TaskRun

    def _update_object(self, taskrun):
        """Update task_run object with user id or ip."""
        # validate the task and app for that taskrun are ok
        task = Task.query.get(taskrun.task_id)
        if task is None:  # pragma: no cover
            raise Forbidden('Invalid task_id')
        if (task.app_id != taskrun.app_id):
            raise Forbidden('Invalid app_id')

        # Add the user info so it cannot post again the same taskrun
        if current_user.is_anonymous():
            taskrun.user_ip = request.remote_addr
        else:
            taskrun.user = current_user

