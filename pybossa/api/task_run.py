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
from flask import request, Response
from flask import current_app as app
from flask.ext.login import current_user
from pybossa.model.task_run import TaskRun
from werkzeug.exceptions import Forbidden, BadRequest

from api_base import APIBase
from pybossa.util import get_user_id_or_ip
from pybossa.core import task_repo, sentinel, anonymizer
from pybossa.uploader.s3_uploader import s3_upload_from_string
from pybossa.uploader.s3_uploader import s3_upload_file_storage
from pybossa.contributions_guard import ContributionsGuard
from pybossa.auth import jwt_authorize_project
from datetime import datetime
from pybossa.sched import can_post, after_save

from pybossa.model.completion_event import mark_if_complete


class TaskRunAPI(APIBase):

    """Class API for domain object TaskRun."""

    DEFAULT_DATETIME = '1900-01-01T00:00:00.000000'
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    __class__ = TaskRun
    reserved_keys = set(['id', 'created', 'finish_time'])

    def _preprocess_post_data(self, data):
        if current_user.is_anonymous():
            raise Forbidden('')
        task_id = data['task_id']
        project_id = data['project_id']
        user_id = current_user.id
        self.check_can_post(project_id, task_id, user_id)
        info = data.get('info')
        if info is None:
            return
        path = "{0}/{1}/{2}".format(project_id, task_id, user_id)
        _upload_files_from_json(info, path)
        _upload_files_from_request(info, request.files, path)
        if app.config.get('PRIVATE_INSTANCE'):
            data['info'] = {
                'pyb_answer_url': _upload_task_run(info, path)
            }

    def check_can_post(self, project_id, task_id, user_id):
        if not can_post(project_id, task_id, user_id):
            raise Forbidden("You must request a task first!")

    def _update_object(self, taskrun):
        """Update task_run object with user id or ip."""
        task = task_repo.get_task(taskrun.task_id)
        guard = ContributionsGuard(sentinel.master)

        self._validate_project_and_task(taskrun, task)
        self._ensure_task_was_requested(task, guard)
        self._add_user_info(taskrun)
        self._add_timestamps(taskrun, task, guard)

    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _validate_project_and_task(self, taskrun, task):
        if task is None:  # pragma: no cover
            raise Forbidden('Invalid task_id')
        if (task.project_id != taskrun.project_id):
            raise Forbidden('Invalid project_id')
        if taskrun.external_uid:
            resp = jwt_authorize_project(task.project,
                                         request.headers.get('Authorization'))
            if type(resp) == Response:
                msg = json.loads(resp.data)['description']
                raise Forbidden(msg)

    def _ensure_task_was_requested(self, task, guard):
        if not guard.check_task_stamped(task, get_user_id_or_ip()):
            raise Forbidden('You must request a task first!')

    def _add_user_info(self, taskrun):
        if taskrun.external_uid is None:
            if current_user.is_anonymous():
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

    def _after_save(self, instance):
        after_save(instance.project_id, instance.task_id, instance.user_id)
        mark_if_complete(instance.task_id, instance.project_id)

    def _add_timestamps(self, taskrun, task, guard):
        finish_time = datetime.utcnow().isoformat()

        # /cachePresentedTime API only caches when there is a user_id
        # otherwise it returns an arbitrary valid timestamp so that answer can be submitted
        if guard.retrieve_presented_timestamp(task, get_user_id_or_ip()):
            created = self._validate_datetime(guard.retrieve_presented_timestamp(task, get_user_id_or_ip()))
        else:
            created = datetime.strptime(self.DEFAULT_DATETIME, self.DATETIME_FORMAT).isoformat()

        # sanity check
        if created < finish_time:
            taskrun.created = created
            taskrun.finish_time = finish_time
        else:
            # return an arbitrary valid timestamp so that answer can be submitted
            created = datetime.strptime(self.DEFAULT_DATETIME, self.DATETIME_FORMAT)
            taskrun.created = created.isoformat()
            taskrun.finish_time = finish_time

    def _validate_datetime(self, timestamp):
        try:
            timestamp = datetime.strptime(timestamp, self.DATETIME_FORMAT)
        except:
            # return an arbitrary valid timestamp so that answer can be submitted
            timestamp = datetime.strptime(self.DEFAULT_DATETIME, self.DATETIME_FORMAT)
        return timestamp.isoformat()


def _upload_files_from_json(task_run_info, upload_path):
    if not isinstance(task_run_info, dict):
        return
    for key, value in task_run_info.iteritems():
        if key.endswith('__upload_url'):
            filename = value.get('filename')
            content = value.get('content')
            if filename is None or content is None:
                continue
            out_url = s3_upload_from_string(app.config.get("S3_BUCKET"),
                                            content,
                                            filename,
                                            directory=upload_path)
            task_run_info[key] = out_url


def _upload_files_from_request(task_run_info, files, upload_path):
    for key in files:
        if not key.endswith('__upload_url'):
            raise BadRequest("File upload field should end in __upload_url")
        file_obj = request.files[key]
        s3_url = s3_upload_file_storage(app.config.get("S3_BUCKET"),
                                        file_obj,
                                        directory=upload_path)
        task_run_info[key] = s3_url


def _upload_task_run(task_run, upload_path):
    content = json.dumps(task_run, ensure_ascii=False)
    return s3_upload_from_string(app.config.get("S3_BUCKET"),
                                 content, 'pyb_answer.json',
                                 directory=upload_path)
