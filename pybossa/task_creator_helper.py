# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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
"""Module with PyBossa create task helper."""
from flask import current_app
import hashlib
from pybossa.cloud_store_api.s3 import upload_json_data, get_content_from_s3
from pybossa.util import get_now_plus_delta_ts
from flask import url_for
import json

TASK_PRIVATE_GOLD_ANSWER_FILE_NAME = 'task_private_gold_answer.json'
TASK_GOLD_ANSWER_URL_KEY = 'gold_ans__upload_url'


def encrypted():
    return current_app.config.get('ENABLE_ENCRYPTION')


def bucket_name():
    return current_app.config.get("S3_REQUEST_BUCKET")


def s3_conn_type():
    return current_app.config.get('S3_CONN_TYPE')


def get_task_expiration(current_expiration):
    """
    Find the appropriate expiration to be added to a task with expiring data.
    If no expiration is set, return the data expiration; otherwise, return
    the smallest between the current expiration and the data expiration.
    current_expiration can be a iso datetime string or a datetime object
    """
    validity = current_app.config.get('REQUEST_FILE_VALIDITY_IN_DAYS', 60)
    task_exp = get_now_plus_delta_ts(days=validity)
    if isinstance(current_expiration, str):
        task_exp = task_exp.isoformat()
    current_expiration = current_expiration or task_exp
    return min(task.expiration, task_exp)


def set_gold_answers(task, gold_answers):
    if not gold_answers:
        return
    if encrypted():
        url = upload_files_priv(task, task.project_id, gold_answers, TASK_PRIVATE_GOLD_ANSWER_FILE_NAME)['externalUrl']
        gold_answers = dict([(TASK_GOLD_ANSWER_URL_KEY, url)])
        task.expiration = get_task_expiration(task.expiration)

    task.gold_answers = gold_answers
    task.calibration = 1
    task.exported = True
    if task.state == u'completed':
        task.state = u'ongoing'


def upload_files_priv(task, project_id, data, file_name):
    bucket = bucket_name()
    task_hash = hashlib.md5(str(task)).hexdigest()
    path = "{}/{}".format(project_id, task_hash)
    values = dict(
        store=s3_conn_type(),
        bucket=bucket,
        project_id=project_id,
        path='{}/{}'.format(task_hash, file_name)
    )
    file_url = url_for('fileproxy.encrypted_file', **values)
    internal_url = upload_json_data(
        bucket=bucket,
        json_data=data,
        upload_path=path,
        file_name=file_name,
        encryption=True,
        conn_name='S3_TASK_REQUEST'
    )
    return { 'externalUrl': file_url, 'internalUrl': internal_url }


def get_gold_answers(task):
    gold_answers = task.gold_answers

    if not encrypted() or gold_answers is None:
        return gold_answers

    url = gold_answers.get(TASK_GOLD_ANSWER_URL_KEY)
    if not url:
        raise Exception('Cannot retrieve Private Gigwork gold answers for task id {}. URL is missing.'.format(task.id))

    # The task instance here is not the same as the one that was used to generate the hash
    # in the upload url. So we can't regenerate that hash here, and instead we have to parse it
    # from the url.

    parts = url.split('/')
    key_name = '/{}/{}/{}'.format(*parts[-3:])
    decrypted = get_content_from_s3(s3_bucket=parts[-4], path=key_name, conn_name='S3_TASK_REQUEST', decrypt=True)
    return json.loads(decrypted)
