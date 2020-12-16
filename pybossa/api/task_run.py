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
from copy import deepcopy
import json
import time

from datetime import datetime

from flask import request, Response, current_app
from flask import current_app as app
from flask_login import current_user
from werkzeug.exceptions import Forbidden, BadRequest

from api_base import APIBase
from pybossa.model.task_run import TaskRun
from pybossa.util import get_user_id_or_ip
from pybossa.core import task_repo, sentinel, anonymizer, project_repo, user_repo, task_repo
from pybossa.core import performance_stats_repo
from pybossa.cloud_store_api.s3 import s3_upload_from_string
from pybossa.cloud_store_api.s3 import s3_upload_file_storage
from pybossa.contributions_guard import ContributionsGuard
from pybossa.auth import jwt_authorize_project
from pybossa.sched import can_post
from pybossa.model.completion_event import mark_if_complete
from pybossa.cloud_store_api.s3 import upload_json_data
from pybossa.model.performance_stats import StatType, PerformanceStats
from pybossa.stats.gold import ConfusionMatrix, RightWrongCount
from pybossa.task_creator_helper import get_gold_answers
from pybossa.view.fileproxy import encrypt_task_response_data


class TaskRunAPI(APIBase):

    """Class API for domain object TaskRun."""

    DEFAULT_DATETIME = '1900-01-01T00:00:00.000000'
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    __class__ = TaskRun
    reserved_keys = set(['id', 'created', 'finish_time'])

    immutable_keys = set(['project_id', 'task_id'])

    def _preprocess_post_data(self, data):
        with_encryption = app.config.get('ENABLE_ENCRYPTION')
        upload_root_dir = app.config.get('S3_UPLOAD_DIRECTORY')
        if current_user.is_anonymous:
            raise Forbidden('')
        task_id = data['task_id']
        project_id = data['project_id']
        self.check_can_post(project_id, task_id)
        preprocess_task_run(project_id, task_id, data)
        if with_encryption:
            info = data['info']
            path = "{0}/{1}/{2}".format(project_id, task_id, current_user.id)

            # for tasks with private_json_encrypted_payload, generate
            # encrypted response payload under private_json__encrypted_response
            encrypted_response = encrypt_task_response_data(task_id, project_id, info)
            data['info'] = {}
            pyb_answer_url = upload_json_data(json_data=info, upload_path=path,
                file_name='pyb_answer.json', encryption=with_encryption,
                conn_name='S3_TASKRUN', upload_root_dir=upload_root_dir
            )
            if pyb_answer_url:
                data['info']['pyb_answer_url'] = pyb_answer_url
            if encrypted_response:
                data['info']['private_json__encrypted_response'] = encrypted_response


    def check_can_post(self, project_id, task_id):
        if not can_post(project_id, task_id, get_user_id_or_ip()):
            raise Forbidden("You must request a task first!")

    def _custom_filter(self, filters):
        if request.args.get('from_finish_time'):
            filters['from_finish_time'] = request.args['from_finish_time']
        if request.args.get('to_finish_time'):
            filters['to_finish_time'] = request.args['to_finish_time']
        return filters

    def _update_object(self, taskrun):
        """Update task_run object with user id or ip."""
        self.check_can_post(taskrun.project_id, taskrun.task_id)
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

    def _after_save(self, original_data, instance):
        mark_if_complete(instance.task_id, instance.project_id)
        task = task_repo.get_task(instance.task_id)
        gold_answers = get_gold_answers(task)
        update_gold_stats(instance.user_id, instance.task_id, original_data, gold_answers)
        update_quiz(instance.project_id, original_data['info'], gold_answers)

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

    def _copy_original(self, item):
        return deepcopy(item)

    def _customize_response_dict(self, response_dict):
        task = task_repo.get_task(response_dict['task_id'])
        response_dict['gold_answers'] = get_gold_answers(task)


def _upload_files_from_json(task_run_info, upload_path, with_encryption):
    if not isinstance(task_run_info, dict):
        return
    for key, value in task_run_info.iteritems():
        if key.endswith('__upload_url'):
            filename = value.get('filename')
            content = value.get('content')
            upload_root_dir = app.config.get('S3_UPLOAD_DIRECTORY')
            if filename is None or content is None:
                continue
            out_url = s3_upload_from_string(app.config.get("S3_BUCKET"),
                                            content,
                                            filename,
                                            directory=upload_path, conn_name='S3_TASKRUN',
                                            with_encryption=with_encryption,
                                            upload_root_dir=upload_root_dir)
            task_run_info[key] = out_url


def _upload_files_from_request(task_run_info, files, upload_path, with_encryption):
    for key in files:
        if not key.endswith('__upload_url'):
            raise BadRequest("File upload field should end in __upload_url")
        file_obj = request.files[key]
        s3_url = s3_upload_file_storage(app.config.get("S3_BUCKET"),
                                        file_obj,
                                        directory=upload_path, conn_name='S3_TASKRUN',
                                        with_encryption=with_encryption)
        task_run_info[key] = s3_url


def update_gold_stats(user_id, task_id, data, gold_answers=None):
    task = task_repo.get_task(task_id)
    if not task.calibration:
        return

    if gold_answers is None:
        gold_answers = get_gold_answers(task)
    answer_fields = project_repo.get(task.project_id).info.get('answer_fields', {})
    answer = data['info']
    _update_gold_stats(
        task.project_id,
        user_id,
        answer_fields,
        gold_answers,
        answer
    )

def update_quiz(project_id, answer, gold_answers):
    project = project_repo.get(project_id)
    user = user_repo.get(current_user.id)
    if not user.get_quiz_in_progress(project):
        return

    if gold_answers == answer:
        user.add_quiz_right_answer(project)
    else:
        user.add_quiz_wrong_answer(project)

    user_repo.update(user)

field_to_stat_type = {
    'categorical': StatType.confusion_matrix,
    'freetext': StatType.accuracy
}


type_to_class = {
    StatType.confusion_matrix: ConfusionMatrix,
    StatType.accuracy: RightWrongCount
}


def _update_gold_stats(project_id, user_id, gold_fields, gold_answer, answer):
    for path, specs in gold_fields.items():
        current_app.logger.info(path)
        current_app.logger.info(specs)
        stat_type = field_to_stat_type[specs['type']]
        stats = performance_stats_repo.filter_by(project_id=project_id,
            user_id=user_id, field=path, stat_type=stat_type)
        current_app.logger.info(stats)
        create = False
        if not stats:
            stat_row = PerformanceStats(
                project_id=project_id,
                user_id=user_id,
                field=path,
                stat_type=stat_type,
                info={})
            create = True
        else:
            stat_row = stats[0]
        current_app.logger.info(stat_row)

        stat_class = type_to_class[stat_type]
        specs['config'].update(stat_row.info)
        stat = stat_class(**specs['config'])
        stat.compute(answer, gold_answer, path)
        stat_row.info = stat.value
        current_app.logger.info('save stats')
        current_app.logger.info(stat_row)
        if create:
            performance_stats_repo.save(stat_row)
        else:
            performance_stats_repo.update(stat_row)

def preprocess_task_run(project_id, task_id, data):
        with_encryption = app.config.get('ENABLE_ENCRYPTION')
        info = data.get('info')
        if info is None:
            return
        path = "{0}/{1}/{2}".format(project_id, task_id, current_user.id)
        _upload_files_from_json(info, path, with_encryption)
        _upload_files_from_request(info, request.files, path, with_encryption)
