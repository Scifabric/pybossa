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
from flask import request, current_app
from flask.ext.login import current_user
from api_base import APIBase
from pybossa.model import Task, TaskRun
from itsdangerous import URLSafeSerializer
from werkzeug.exceptions import Unauthorized, Forbidden
from pybossa.core import db


class TaskRunAPI(APIBase):

    """Class API for domain object TaskRun."""

    __class__ = TaskRun

    def _update_object(self, obj):
        """Validate the task_run object and update it with user id or ip."""
        s = URLSafeSerializer(current_app.config.get('SECRET_KEY'))
        # Get the cookie with the task signed for the current task_run
        cookie_id = 'task_run_for_task_id_%s' % obj.task_id
        task_cookie = request.cookies.get(cookie_id)
        if task_cookie is None:
            raise Unauthorized("Missing task cookie for posting"
                               " a valid task_run")
        # Load the real task from the DB
        task_cookie = s.loads(task_cookie)
        #task = db.session.query(model.Task).get(task_cookie['id'])
        task = Task.query.get(task_cookie['id'])
        if ((task is None) or (task.id != obj.task_id)):  # pragma: no cover
            raise Forbidden('Invalid task_id')
        if (task.app_id != obj.app_id):
            raise Forbidden('Invalid app_id')
        if not current_user.is_anonymous():
            obj.user = current_user
        else:
            obj.user_ip = request.remote_addr
        # Check if this task_run has already been posted
        # task_run = db.session.query(model.TaskRun)\
        task_run = TaskRun.query\
            .filter_by(app_id=obj.app_id)\
            .filter_by(task_id=obj.task_id)\
            .filter_by(user=obj.user)\
            .filter_by(user_ip=obj.user_ip)\
            .first()
        if task_run is not None:
            raise Forbidden('You have already posted this task_run')
