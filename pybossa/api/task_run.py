# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""
PYBOSSA api module for exposing domain object TaskRun via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * task_runs

"""
import json
import time
from flask import request, Response, current_app
from flask_login import current_user
from pybossa.model.task_run import TaskRun
from werkzeug.exceptions import Forbidden, BadRequest

from .api_base import APIBase
from pybossa.util import get_user_id_or_ip, get_avatar_url
from pybossa.core import task_repo, sentinel, anonymizer, project_repo
from pybossa.core import uploader
from pybossa.contributions_guard import ContributionsGuard
from pybossa.auth import jwt_authorize_project
from pybossa.auth import ensure_authorized_to, is_authorized
from pybossa.sched import can_post


class TaskRunAPI(APIBase):

    """Class API for domain object TaskRun."""

    __class__ = TaskRun
    reserved_keys = set(['id', 'created', 'finish_time'])

    def check_can_post(self, project_id, task_id, user_ip_or_id):
        if not can_post(project_id, task_id, user_ip_or_id):
            raise Forbidden("You must request a task first!")

    def _update_object(self, taskrun):
        """Update task_run object with user id or ip."""
        self.check_can_post(taskrun.project_id,
                            taskrun.task_id, get_user_id_or_ip())
        task = task_repo.get_task(taskrun.task_id)
        guard = ContributionsGuard(sentinel.master)

        self._validate_project_and_task(taskrun, task)
        self._ensure_task_was_requested(task, guard)
        self._add_user_info(taskrun)
        self._add_created_timestamp(taskrun, task, guard)

    def _forbidden_attributes(self, data):
        for key in list(data.keys()):
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _validate_project_and_task(self, taskrun, task):
        if task is None:  # pragma: no cover
            raise Forbidden('Invalid task_id')
        if (task.project_id != taskrun.project_id):
            raise Forbidden('Invalid project_id')
        if taskrun.external_uid:
            request_headers = request.headers.get('Authorization')
            resp = jwt_authorize_project(task.project, request_headers)
            if type(resp) == Response:
                msg = json.loads(resp.data)['description']
                raise Forbidden(msg)

    def _ensure_task_was_requested(self, task, guard):
        if not guard.check_task_stamped(task, get_user_id_or_ip()):
            raise Forbidden('You must request a task first!')

    def _add_user_info(self, taskrun):
        if taskrun.external_uid is None:
            if current_user.is_anonymous:
                taskrun.user_ip = anonymizer.ip(request.remote_addr or
                                                '127.0.0.1')
            else:
                taskrun.user_id = current_user.id
        else:
            taskrun.user_ip = None
            taskrun.user_id = None

    def _add_created_timestamp(self, taskrun, task, guard):
        taskrun.created = guard.retrieve_timestamp(task, get_user_id_or_ip())
        guard._remove_task_stamped(task, get_user_id_or_ip())

    def _file_upload(self, data):
        """Method that must be overriden by the class to allow file uploads for
        only a few classes."""
        cls_name = self.__class__.__name__.lower()
        content_type = 'multipart/form-data'
        request_headers = request.headers.get('Content-Type')
        if request_headers is None:
            request_headers = []
        if (content_type in request_headers and
                cls_name in self.allowed_classes_upload):
            data = dict()
            for key in list(request.form.keys()):
                if key in ['project_id', 'task_id']:
                    data[key] = int(request.form[key])
                elif key == 'info':
                    data[key] = json.loads(request.form[key])
                else:
                    data[key] = request.form[key]
            # inst = self._create_instance_from_request(data)
            data = self.hateoas.remove_links(data)
            inst = self.__class__(**data)
            self._add_user_info(inst)
            is_authorized(current_user, 'create', inst)
            upload_method = current_app.config.get('UPLOAD_METHOD')
            if request.files.get('file') is None:
                raise AttributeError
            _file = request.files['file']
            if current_user.is_authenticated:
                container = "user_%s" % current_user.id
            else:
                container = "anonymous"
            if _file.filename == 'blob' or _file.filename is None:
                _file.filename = "%s.png" % time.time()
            uploader.upload_file(_file,
                                 container=container)
            avatar_absolute = current_app.config.get('AVATAR_ABSOLUTE')
            file_url = get_avatar_url(upload_method,
                                      _file.filename,
                                      container,
                                      avatar_absolute)
            data['media_url'] = file_url
            if data.get('info') is None:
                data['info'] = dict()
            data['info']['container'] = container
            data['info']['file_name'] = _file.filename
            return data
        else:
            return None

    def _file_delete(self, request, obj):
        """Delete file object."""
        cls_name = self.__class__.__name__.lower()
        if cls_name in self.allowed_classes_upload:
            if type(obj.info) == dict:
                keys = list(obj.info.keys())
                if 'file_name' in keys and 'container' in keys:
                    ensure_authorized_to('delete', obj)
                    uploader.delete_file(obj.info['file_name'],
                                         obj.info['container'])
