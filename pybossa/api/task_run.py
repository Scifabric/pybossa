# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
import json
from flask import request
from flask.ext.login import current_user
from pybossa.model.task_run import TaskRun
from werkzeug.exceptions import Forbidden, BadRequest

from api_base import APIBase
from pybossa.util import get_user_id_or_ip
from pybossa.core import task_repo, sentinel
from pybossa.contributions_guard import ContributionsGuard


class TaskRunAPI(APIBase):

    """Class API for domain object TaskRun."""

    __class__ = TaskRun
    reserved_keys = set(['id', 'created', 'finish_time'])

    def _update_object(self, taskrun):
        """Update task_run object with user id or ip."""
        task = task_repo.get_task(taskrun.task_id)
        guard = ContributionsGuard(sentinel.master)

        self._validate_project_and_task(taskrun, task)
        self._ensure_task_was_requested(task, guard)
        self._add_user_info(taskrun)
        self._add_created_timestamp(taskrun, task, guard)

    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _validate_project_and_task(self, taskrun, task):
        if task is None:  # pragma: no cover
            raise Forbidden('Invalid task_id')
        if (task.project_id != taskrun.project_id):
            raise Forbidden('Invalid project_id')

    def _ensure_task_was_requested(self, task, guard):
        if not guard.check_task_stamped(task, get_user_id_or_ip()):
            raise Forbidden('You must request a task first!')

    def _add_user_info(self, taskrun):
        if current_user.is_anonymous():
            taskrun.user_ip = request.remote_addr
        else:
            taskrun.user_id = current_user.id

    def _add_created_timestamp(self, taskrun, task, guard):
        taskrun.created = guard.retrieve_timestamp(task, get_user_id_or_ip())
